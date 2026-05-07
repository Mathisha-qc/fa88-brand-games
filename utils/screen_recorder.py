import cv2
import numpy as np
import pyautogui
import threading
import time


class ScreenRecorder:
    def __init__(self, driver, path, fps=2):
        self.driver = driver
        self.path = str(path)
        self.fps = fps
        self.running = False
        self.thread = None

        # ✅ Get browser window size & position
        rect = driver.get_window_rect()
        self.x = rect["x"]
        self.y = rect["y"]
        self.w = rect["width"]
        self.h = rect["height"]

        self.size = (self.w, self.h)

        fourcc = cv2.VideoWriter_fourcc(*"vp09")
        self.out = cv2.VideoWriter(self.path, fourcc, fps, self.size)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.record)
        self.thread.start()

    def record(self):
       frame_time = 1 / self.fps

       while self.running:
        start = time.time()

        img = pyautogui.screenshot(
            region=(self.x, self.y, self.w, self.h)
        )

        frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
        self.out.write(frame)

        # ✅ maintain stable frame rate
        elapsed = time.time() - start
        sleep_time = max(0, frame_time - elapsed)
        time.sleep(sleep_time)

            

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.out.release()