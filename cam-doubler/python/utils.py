import time


def monotonic_seconds() -> float:
    return time.perf_counter()


class RateTimer:
    """Simple high-res timer to sleep until the next target time."""
    def __init__(self):
        self.next_t = None

    def wait_until(self, t_target: float):
        now = time.perf_counter()
        dt = t_target - now
        if dt > 0:
            time.sleep(dt)
