import tvm


def test_schedule0():
    m = tvm.Var('m')
    l = tvm.Var('l')
    A = tvm.placeholder((m, l), name='A')
    A1 = tvm.compute((m, l), lambda i, j: A[i, j], name='A1')
    s = tvm.Schedule(A1.op)

    bounds = tvm.schedule.InferBound(s)
    assert isinstance(bounds, tvm.collections.Map)
    stmt = tvm.schedule.ScheduleOps(s, bounds)

def test_schedule1():
    m = tvm.Var('m')
    l = tvm.Var('l')
    A = tvm.placeholder((m, l), name='A')
    A1 = tvm.compute((m, l), lambda i, j: A[i, j], name='A1')

    s = tvm.Schedule(A1.op)
    xo, xi = s[A1].split(A1.op.axis[0], 8)
    bounds = tvm.schedule.InferBound(s)
    assert isinstance(bounds, tvm.collections.Map)
    stmt = tvm.schedule.ScheduleOps(s, bounds)


def test_schedule2():
    m = tvm.Var('m')
    l = tvm.Var('l')
    A = tvm.placeholder((m, l), name='A')
    A1 = tvm.compute((m, l), lambda i, j: A[i, j], name='A1')
    A2 = tvm.compute((m, l), lambda i, j: A1[i, j] + 3, name='A2')

    s = tvm.Schedule(A2.op)
    xo, xi = s[A2].split(A2.op.axis[0], 8)
    s[A1].compute_at(s[A2], xo)
    bounds = tvm.schedule.InferBound(s)
    assert isinstance(bounds, tvm.collections.Map)
    stmt = tvm.schedule.ScheduleOps(s, bounds)


def test_schedule_scan():
    m = tvm.Var("m")
    n = tvm.Var("n")
    l = tvm.Var("l")
    t = tvm.IterVar((1, m), name="t")
    x = tvm.compute((m, n), lambda i, j: tvm.const(1, "float32"), name="x")
    s_state = tvm.placeholder((m, n))
    s_init = tvm.compute((1, n), lambda _, i: x[0, i])
    s_update = tvm.compute((n,), lambda i: s_state[t-1, i] + x[t, i])
    res = tvm.scan(t, s_init, s_update, s_state)

    assert tuple(res.shape) == (m, n)
    s = tvm.Schedule(res.op)
    s.normalize()
    bounds = tvm.schedule.InferBound(s)
    assert(bounds[res.op.scan_axis].min.value == 1)
    stmt = tvm.schedule.ScheduleOps(s, bounds)
    print(stmt)


def test_auto_inline():
    m = tvm.Var('m')
    n = tvm.Var('n')
    A = tvm.placeholder((m, n), name='A')
    B = tvm.placeholder((m, n), name='B')
    C = tvm.placeholder((m, n), name='C')
    T1 = tvm.compute((m, n), lambda i, j:  A(i, j) * B(i, j), name='T1')
    T2 = tvm.compute((m, n), lambda i, j: T1(i, j) + C(i, j), name='T2')

    s = tvm.Schedule(T2.op)
    tvm.schedule.AutoInlineElemWise(s)
    bounds = tvm.schedule.InferBound(s)
    stmt = tvm.schedule.ScheduleOps(s, bounds)

def test_schedule_cache():
    m = tvm.Var('m')
    n = tvm.Var('n')
    A = tvm.placeholder((m, n), name='A')
    B = tvm.placeholder((m, n), name='B')
    C = tvm.compute((m, n), lambda i, j:  A(i, j) * B(i, j), name='C')

    s = tvm.Schedule(C.op)
    AA = s.cache_read(A, "shared", readers=[C])
    CC = s.cache_write(C, "shared")
    s[AA].compute_at(s[CC], CC.op.axis[0])
    bounds = tvm.schedule.InferBound(s)
    stmt = tvm.schedule.ScheduleOps(s, bounds)


if __name__ == "__main__":
    test_schedule_scan()
    test_schedule0()
    test_schedule1()
    test_schedule2()
    test_auto_inline()
    test_schedule_cache()
