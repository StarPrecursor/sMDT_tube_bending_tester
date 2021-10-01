import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import logging
import time

import cv2
import numpy as np
from pygame import mixer

mixer.init()
logger = logging.getLogger()


class Test_Sound(object):
    def __init__(self) -> None:
        super().__init__()
        self.add_sound = mixer.Sound("res/add.mp3")
        self.remove_sound = mixer.Sound("res/remove.mp3")
        self.error_sound = mixer.Sound("res/error.mp3")

    def add(self):
        self.add_sound.play()

    def remove(self):
        self.remove_sound.play()

    def error(self):
        self.error_sound.play()


class Job_Cache(object):
    def __init__(self, cfg) -> None:
        """
        Status Code:
            0: Initial
            1: Wait
            2: Pre-test
            3: Test
            4: Post-test
            5: Record
            6: Reset
        Loop: 0 -> (1 -> 2 -> 3 -> 4)
        """
        super().__init__()
        # data
        self.state = 0
        self.time_stamp = time.time()
        self.edge = None
        # settings
        cm = cfg.main
        self.test_delay = cm.test_delay
        self.stable_period = cm.stable_period
        self.rapid_change_reject = cm.rapid_change_reject
        self.record_delay = cm.record_delay
        self.state_dict = {
            0: "INITIAL",
            1: "WAIT",
            2: "PRE-TEST",
            3: "TEST",
            4: "POST-TEST",
            5: "RECORD",
            6: "RESET",
        }

    def get_state(self) -> int:
        return self.state

    def get_state_name(self) -> str:
        return self.state_dict[self.state]

    def set_state(self, value) -> None:
        self.state = value

    def get_period(self) -> float:
        return time.time() - self.time_stamp

    def update(self, edge, tube_cache) -> int:
        self.edge = edge
        state = -1
        # Initial
        if self.state == 0:
            state = 1
        # Wait
        elif self.state == 1:
            if edge:
                state = 2
            else:
                state = 1
        # Pre-test
        elif self.state == 2:
            if edge:
                if self.get_period() >= self.test_delay:
                    state = 3
                else:
                    state = 2
            else:
                state = 1
        # Test
        elif self.state == 3:
            if edge:
                if self.get_period() >= self.stable_period:
                    min_x, max_x = tube_cache.min_x, tube_cache.max_x
                    unit_x = tube_cache.unit_x
                    d1 = (edge - max_x) * unit_x
                    d2 = (min_x - edge) * unit_x
                    if d1 > self.rapid_change_reject or d2 > self.rapid_change_reject:
                        state = 4
                    else:
                        state = 3
                else:
                    state = 3
            else:
                state = 4
        # Post-test
        elif self.state == 4:
            if edge:
                state = 3
            else:
                if self.get_period() >= self.record_delay:
                    state = 5
                else:
                    state = 4
        # Record
        elif self.state == 5:
            state = 6
        # Reset
        elif self.state == 6:
            state = 1
        # Unexpected
        else:
            logger.error("Unknown status code:", self.state)
        if state != self.state:
            self.state = state
            self.time_stamp = time.time()
        return state


def get_border(img, cfg, debug=False):
    cm = cfg.main

    img = cv2.convertScaleAbs(img, alpha=cm.scale_abs.alpha, beta=cm.scale_abs.beta)
    if debug:
        cv2.imshow("Debug: Adjust", img)

    img = cv2.GaussianBlur(img, tuple(cm.gauss_blur.ksize), sigmaX=cm.gauss_blur.sigmaX)
    if debug:
        cv2.imshow("Debug: Blur", img)

    img = cv2.Canny(img, threshold1=cm.canny.threshold1, threshold2=cm.canny.threshold2)
    if debug:
        cv2.imshow("Debug: Canny", img)

    img = cv2.dilate(img, tuple(cm.dilate.kernel), iterations=cm.dilate.iterations)
    if debug:
        cv2.imshow("Debug: Dilate", img)

    img = cv2.erode(img, tuple(cm.erode.kernel), iterations=cm.erode.iterations)
    if debug:
        cv2.imshow("Debug: Erode", img)

    border_img = np.copy(img) * 0
    lines = cv2.HoughLinesP(
        img,
        cm.hough_line_p.rho,
        cm.hough_line_p.theta,
        cm.hough_line_p.threshold,
        lines=np.array([]),
        minLineLength=cm.hough_line_p.minLineLength,
        maxLineGap=cm.hough_line_p.maxLineGap,
    )
    x = None
    if lines is not None:
        # find average x corodinate among all the lines found
        x = int(np.average(lines[:, :, [0, 2]]))
        cv2.line(border_img, (x, 0), (x, img.shape[0] - 1), cm.style.line_color, 2)
    pad = np.ones(border_img.shape, dtype=border_img.dtype)
    border_img = cv2.merge((pad, pad, border_img))

    return (border_img, x)
