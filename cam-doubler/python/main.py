import argparse
import cv2
import numpy as np
import pyvirtualcam

from utils import monotonic_seconds, RateTimer
from scheduler import DoublerScheduler
import fruc  # MVP stub: duplicate or blend

# Helper: list available camera indices
def list_available_cameras(max_index: int = 10) -> list:
    """
    Scan camera indices from 0 to max_index-1 and return those that can be opened.
    """
    available = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_MSMF)
        if cap.isOpened():
            available.append(i)
            cap.release()
        else:
            cap.release()
    return available


def open_cam(index: int, w: int, h: int, prefer_fps: int):
    cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_FPS, prefer_fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    # Warm-up
    for _ in range(5):
        cap.read()
    return cap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=int, default=None, help="Camera index; default: prompt selection")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--prefer_fps", type=int, default=30)
    ap.add_argument("--mid", choices=["duplicate", "blend"], default="duplicate")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    # Determine camera index
    if args.device is None:
               cams = list_available_cameras()
        if not cams:
            raise RuntimeError("No cameras detected")
        print("Available cameras:")
        for idx in cams:
            print(f"{idx}: camera {idx}")
        selected = None
        while selected is None:
            try:
                inp = input(f"Select camera index [{cams[0]}]: ").strip()
                if inp == "":
                    selected = cams[0]
                else:
                    sel = int(inp)
                    if sel in cams:
                        selected = sel
                    else:
                        print("Invalid selection. Choose from listed cameras.")
            except ValueError:
                print("Please enter a valid integer.")
        device_idx = selected
    else:
        device_idx = args.device

    cap = open_cam(device_idx, args.width, args.height, args.prefer_fps)
    mid_func = fruc.mid_duplicate if args.mid == "duplicate" else fruc.mid_blend

    # Advertise 2x FPS; at least 30
    advertised_fps = max(2 * args.prefer_fps, 30)

    with pyvirtualcam.Camera(width=args.width, height=args.height,
                             fps=advertised_fps,
                             fmt=pyvirtualcam.PixelFormat.BGR) as vcam:
        print(f"[cam-doubler] Virtual camera started: {vcam.device}")
        sched = DoublerScheduler(history=30)
        prev = None
        prev_t = None
        last_frame = None

        while True:
            ok, frame = cap.read()
            if not ok:
                continue
            t = monotonic_seconds()
            if frame.shape[1] != args.width or frame.shape[0] != args.height:
                frame = cv2.resize(frame, (args.width, args.height), interpolation=cv2.INTER_AREA)
            if prev is not None:
                sched.on_input_frame(frame, t)
            prev, prev_t = frame, t

            now = monotonic_seconds()
            sched.drop_stale_mids(now)
            item = sched.pop_due(now)
            if item is None:
                out = last_frame if last_frame is not None else frame
            else:
                if item.kind == "MID":
                    A, B = item.payload
                    out = mid_func(A, B)
                else:
                    (real,) = item.payload
                    out = real
            vcam.send(out)
            vcam.sleep_until_next_frame()
            last_frame = out
            if args.preview:
                cv2.imshow("cam-doubler (preview)", out)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
