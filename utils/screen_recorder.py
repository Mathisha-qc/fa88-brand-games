from pathlib import Path
import threading
import time

import cv2
import numpy as np


class ScreenRecorder:
    def __init__(self, driver, path, fps=2):
        self.driver = driver
        self.path = Path(path)
        self.fps = max(1, int(fps))
        self.running = False
        self.thread = None
        self.out = None

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self.record, daemon=True)
        self.thread.start()

    def _open_writer(self, size):
        """Open a video writer using codec fallbacks for CI stability."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        width, height = size

        # Prefer browser-friendly codecs for HTML report playback.
        candidates = [
            ("VP90", self.path.with_suffix(".webm")),
            ("VP80", self.path.with_suffix(".webm")),
            ("avc1", self.path.with_suffix(".mp4")),
            ("mp4v", self.path.with_suffix(".mp4")),
        ]

        for codec, output_path in candidates:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(str(output_path), fourcc, self.fps, (width, height))
            if writer.isOpened():
                self.out = writer
                self.path = output_path
                return
            writer.release()

        raise RuntimeError("Could not initialize OpenCV VideoWriter with supported codecs.")

    def record(self):
        frame_time = 1.0 / self.fps

        while self.running:
            started_at = time.time()
            try:
                png_bytes = self.driver.get_screenshot_as_png()
                frame = cv2.imdecode(np.frombuffer(png_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                if self.out is None:
                    frame_height, frame_width = frame.shape[:2]
                    self._open_writer((frame_width, frame_height))

                self.out.write(frame)
            except Exception as exc:
                print(f"[WARN] Video frame capture skipped: {exc}")

            elapsed = time.time() - started_at
            time.sleep(max(0.0, frame_time - elapsed))

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        if self.out:
            self.out.release()
