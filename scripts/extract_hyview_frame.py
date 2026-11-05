"""Save one unchanged decoded frame from a HyView recording as PNG."""

import argparse
from pathlib import Path


def extract(source: Path, index: int, destination: Path):
    import cv2

    if index < 0 or destination.suffix.lower() != ".png":
        raise ValueError("Use a nonnegative frame index and a PNG destination")
    video = cv2.VideoCapture(str(source))
    try:
        if not video.isOpened():
            raise ValueError(f"Cannot open recording: {source}")
        for i in range(index + 1):
            ok, frame = video.read()
            if not ok:
                raise ValueError(f"Cannot decode frame {i} in {source}")
        ok, png = cv2.imencode(".png", frame)
        if not ok:
            raise ValueError("PNG encoding failed")
        destination.write_bytes(png.tobytes())
        print(f"{destination}: frame {index}, {frame.shape[1]} x {frame.shape[0]}")
    finally:
        video.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("index", type=int, help="Zero-based recording frame index")
    parser.add_argument("destination", type=Path)
    extract(**vars(parser.parse_args()))
