import argparse
import time
import cv2
import numpy as np
import pyvirtualcam

from utils import monotonic_seconds, RateTimer
from scheduler import DoublerScheduler
import fruc  # MVP stub: duplicate or blend

def open_cam(index: int, w: int, h: int, prefer_fps: int):
    cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    # Prefer FPS (some cams ignore this)
    cap.set(cv2.CAP_PROP_FPS, prefer_fps)
    # Keep only 1 buffer to reduce latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # Warm-up
    for _ in range(5):
        cap.read()
    return cap

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--prefer_fps", type=int, default=30)
    ap.add_argument("--mid", choices=["duplicate", "blend"], default="duplicate")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    cap = open_cam(args.device, args.width, args.height, args.prefer_fps)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera")

    # pyvirtualcam: advertise 60 fps initially; we’ll pace frames ourselves
    advertised_fps = max(2 * args.prefer_fps, 30)

    mid_func = fruc.mid_duplicate if args.mid == "duplicate" else fruc.mid_blend

    with pyvirtualcam.Camera(width=args.width, height=args.height,
                             fps=advertised_fps,
                             fmt=pyvirtualcam.PixelFormat.BGR) as vcam:
        print(f"[cam-doubler] Virtual camera started: {vcam.device}")

        sched = DoublerScheduler(history=30)
        rate = RateTimer()

        prev = None
        prev_t = None
        last_frame = None

        while True:
            ok, frame = cap.read()
            if not ok:
                continue
            t = monotonic_seconds()

            # Ensure resolution
            if frame.shape[1] != args.width or frame.shape[0] != args.height:
                frame = cv2.resize(frame, (args.width, args.height), interpolation=cv2.INTER_AREA)

            # Feed scheduler
            if prev is not None:
                sched.on_input_frame(frame, t)
            prev, prev_t = frame, t

            # Emit due items at ~2× cadence
            # We'll tick at Tout; if nothing due, re-send last_frame to maintain cadence
            Tout = sched.current_Tout()
            target = t + (Tout * 0.5)  # modest spacing before next cadence tick

            # Service a short burst to catch up if multiple due
            now = monotonic_seconds()
            sched.drop_stale_mids(now)

            item = sched.pop_due(now)
            if item is None:
                # No MID/REAL due; keep cadence by repeating last_frame
                out = last_frame if last_frame is not None else frame
            else:
                if item.kind == "MID":
                    A, B = item.payload
                    out = mid_func(A, B)
                else:
                    (real,) = item.payload
                    out = real

            # Send to virtual cam
            vcam.send(out)
            vcam.sleep_until_next_frame()  # keeps advertised fps pacing

            last_frame = out

            # Optional preview
            if args.preview:
                cv2.imshow("cam-doubler (preview)", out)
                if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
                    break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
