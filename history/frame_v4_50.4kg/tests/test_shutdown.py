"""shutdown.py: every shutdown device kills ignition and fuel pump; wiring sized."""
import shutdown as S


def test_all_shutdown_checks_pass():
    failed = [(n, d) for n, ok, d in S.checks() if not ok]
    assert not failed, failed


def test_all_closed_runs_the_engine():
    assert set(S.KILLED) <= S.powered()


def test_any_series_device_open_kills_the_engine():
    for d in S.SHUTDOWN_SERIES:
        assert not set(S.KILLED) & S.powered(open_devices=(d,))
