from collections import deque
from dataclasses import dataclass
import numpy as np
from typing import Optional, Tuple

@dataclass
class ScheduledItem:
    kind: str            # "MID" or "REAL"
    payload: Tuple[np.ndarray, ...]  # ("MID": (A,B), "REAL": (frame,))
    pts: float           # ideal presentation timestamp

class DoublerScheduler:
    """
    For each input frame pair (prev, curr), schedule:
      - MID at Tmid
      - REAL at Tcurr
    Output cadence = ~2× average input cadence.
    If late, we drop MID but never drop REAL.
    """
    def __init__(self, history: int = 30):
        self.queue: deque[ScheduledItem] = deque()
        self.prev_frame: Optional[np.ndarray] = None
        self.prev_t: Optional[float] = None
        self.periods: deque[float] = deque(maxlen=history)
        self.Tin_avg = 1 / 30.0  # start with 30 fps
        self.Tout = self.Tin_avg / 2.0

    def on_input_frame(self, frame: np.ndarray, t_sec: float):
        if self.prev_frame is not None and self.prev_t is not None:
            Tin = max(1e-6, t_sec - self.prev_t)
            self.periods.append(Tin)
            self.Tin_avg = sum(self.periods) / len(self.periods)
            self.Tout = self.Tin_avg / 2.0

            Tmid = self.prev_t + Tin * 0.5
            # Schedule MID then REAL
            self.queue.append(ScheduledItem("MID", (self.prev_frame, frame), Tmid))
            self.queue.append(ScheduledItem("REAL", (frame,), t_sec))

        self.prev_frame = frame
        self.prev_t = t_sec

    def pop_due(self, now: float, slack: float = 0.003) -> Optional[ScheduledItem]:
        """
        Return the best-due item. Policy:
          - If both MID and REAL are due, prefer REAL (never delay it).
          - If only MID is due and REAL is close but not yet due, return MID.
          - If MID is very late and REAL is about to be due, drop the MID.
        """
        if not self.queue:
            return None

        # Find due items
        due_idxs = [i for i, it in enumerate(self.queue) if it.pts <= now + slack]
        if not due_idxs:
            return None

        # Prefer REAL if present among due
        for idx in due_idxs:
            if self.queue[idx].kind == "REAL":
                return self.queue.pop(idx)

        # Otherwise return earliest MID
        idx = due_idxs[0]
        return self.queue.pop(idx)

    def drop_stale_mids(self, now: float, horizon: float = 0.004):
        """Drop mids that are now too late if a REAL is imminent."""
        if len(self.queue) < 2:
            return
        # If first two items are MID then REAL, and MID is late, drop MID
        first = self.queue[0]
        if first.kind == "MID" and first.pts + horizon < now:
            # Peek ahead: if REAL is next and due very soon, drop MID
            if len(self.queue) >= 2 and self.queue[1].kind == "REAL":
                self.queue.popleft()

    def current_Tout(self) -> float:
        return self.Tout
