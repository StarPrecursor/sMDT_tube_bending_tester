import logging
import pathlib
import sqlite3
from datetime import datetime

import cv2
import numpy as np

logger = logging.getLogger("bend_tester")


class Tube_Cache(object):
    def __init__(self, base_img, cfg) -> None:
        super().__init__()
        cm = cfg.main
        self.operator = cfg.job.operator
        # static members
        self.r_range = base_img.shape[0]  # row range
        self.c_range = base_img.shape[1]  # column range
        self.min_y = int(self.r_range * 0.75)
        self.max_y = int(self.r_range * 0.25)
        self.mid_y = int(self.r_range * 0.5)
        self.base_img = np.zeros(base_img.shape, dtype=base_img.dtype)
        self.real_size = cm.real_size
        self.unit_x = cm.real_size[0] / self.c_range / cm.aml
        self.threshold = cm.threshold
        # dynamic members
        self.min_x = float("inf")
        self.max_x = -1
        self.range_x = float("inf")
        self.status = "Unknown"
        self.dy = 0

    def update_x(self, x):
        if x and x > self.max_x:
            self.max_x = x
        if x and x < self.min_x:
            self.min_x = x
        self.range_x = self.max_x - self.min_x

    def reset_x(self):
        # reset dynamic members to default
        self.min_x = float("inf")
        self.max_x = 0
        self.range_x = float("inf")
        self.status = "Unknown"
        self.dy = 0

    def get_limit_img(self, color_l=(255, 0, 0), color_a=(0, 255, 0), thickness=2):
        img = np.copy(self.base_img)
        # draw upper limit
        if 0 <= self.max_x < self.c_range:
            img = cv2.line(
                img,
                (self.max_x, 0),
                (self.max_x, self.r_range - 1),
                color_l,
                thickness=thickness,
            )
            dist = (self.c_range - self.max_x) * self.unit_x
            mid_x = (self.max_x + self.c_range) // 2
            p1 = (self.c_range - 1, self.max_y)
            p2 = (self.max_x, self.max_y)
            org = (mid_x - 40, self.max_y - 15)
            img = plot_arrow(img, p1, p2, dist, org, color_a)
        # draw lower limit
        if 0 <= self.min_x < self.c_range:
            img = cv2.line(
                img,
                (self.min_x, 0),
                (self.min_x, self.r_range - 1),
                color_l,
                thickness=thickness,
            )
            dist = self.min_x * self.unit_x
            mid_x = self.min_x // 2
            p1 = (0, self.min_y)
            p2 = (self.min_x, self.min_y)
            org = (mid_x - 40, self.min_y - 15)
            img = plot_arrow(img, p1, p2, dist, org, color_a)
        # draw range
        if 0 <= self.max_x < self.c_range and 0 <= self.min_x < self.c_range:
            dist = self.range_x * self.unit_x
            mid_x = (self.max_x + self.min_x) // 2
            p1 = (self.min_x, self.mid_y)
            p2 = (self.max_x, self.mid_y)
            org = (mid_x - 40, self.mid_y - 15)
            img = plot_arrow(img, p1, p2, dist, org, color_a)
            org = (mid_x - 65, self.mid_y + 20)
            dy = dist / 2
            img = cv2.putText(
                img,
                f"dy = {dy:.02f} mm",
                org,
                cv2.FONT_HERSHEY_COMPLEX_SMALL,
                1,
                color_a,
            )
            # set status
            status = "PASS"
            color_s = (0, 255, 0)
            if dy > self.threshold:
                status = "FAIL"
                color_s = (0, 0, 255)
            org = (self.c_range // 2 - 80, self.r_range - 20)
            img = cv2.putText(
                img, status, org, cv2.FONT_HERSHEY_COMPLEX_SMALL, 3, color_s,
            )
            # update tube measurement
            self.status = status
            self.dy = dy
        return img

    def get_tube_data(self):
        return self.status, self.dy

    def connect_db(self, dir="run", box="Unknown"):
        # create directory
        db_dir = pathlib.Path(dir)
        db_dir.mkdir(parents=True, exist_ok=True)
        # initialize
        self.box = box
        db_path = db_dir / f"{box}.db"
        logger.info(f"Connecting to {db_path}")
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()
        # create [tubes] table if not exists
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS tubes(box, date, time, operator, tube_id, status, up_pix, low_pix, dy, threshold, unit_x)"""
        )

    def disconnect_db(self):
        self.con.close()

    def write_db(self, tube_id=-1):
        dt_string = datetime.today().strftime("%Y/%m/%d")
        time_string = datetime.now().strftime("%H:%M:%S")
        max_id = self.cur.execute("SELECT MAX(tube_id) FROM tubes").fetchall()
        max_id = max_id[0][0]
        if max_id is None:
            max_id = 0
        if tube_id == -1:
            tube_id = max_id + 1
        values = (
            self.box,
            dt_string,
            time_string,
            " & ".join(self.operator),
            tube_id,
            self.status,
            self.max_x,
            self.min_x,
            self.dy,
            self.threshold,
            self.unit_x,
        )
        logger.debug(f"Inserting values ...")
        self.cur.execute(
            "INSERT INTO tubes (box, date, time, operator, tube_id, status, up_pix, low_pix, dy, threshold, unit_x) Values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            values,
        )
        self.con.commit()


def plot_arrow(img, p1, p2, dist, org, color, thickness=1):
    img = cv2.arrowedLine(
        img, p1, p2, color, thickness=thickness, line_type=8, shift=0, tipLength=0.05,
    )
    img = cv2.arrowedLine(
        img, p2, p1, color, thickness=thickness, line_type=8, shift=0, tipLength=0.05,
    )
    img = cv2.putText(
        img, f"{(dist):.02f} mm", org, cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, color,
    )
    return img
