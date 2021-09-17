import numpy as np
import cv2
import sqlite3

from datetime import datetime




class Tube_Cache(object):
    def __init__(self, base_img, real_size=(90, 68), aml=20, threshold=1.8) -> None:
        super().__init__()
        self.r_range = base_img.shape[0]  # row range
        self.c_range = base_img.shape[1]  # column range
        self.min_x = float("inf")
        self.min_y = int(self.r_range * 0.75)
        self.max_x = -1
        self.max_y = int(self.r_range * 0.25)
        self.mid_y = int(self.r_range * 0.5)
        self.range_x = float("inf")
        self.base_img = np.zeros(base_img.shape, dtype=base_img.dtype)
        self.real_size = real_size
        self.unit_x = real_size[0] / self.c_range / aml
        self.threshold = threshold

    def update_x(self, x):
        if x and x > self.max_x:
            self.max_x = x
        if x and x < self.min_x:
            self.min_x = x
        self.range_x = self.max_x - self.min_x

    def reset_x(self):
        self.min_x = float("inf")
        self.max_x = 0

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
            dy = dist/2
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
        return [img, status, dy, dist]


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





def write_db(box = 'M123456', tubeid = -100, dist = -999.9 , dy = -999.9 ):
    con = sqlite3.connect('{}.db'.format(box))
    cur = con.cursor()

    # Check if 'tubes' table exsit, otherwise create it  
    tabl_exist = False
    table_list = [a for a in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
    for tmp_1 in table_list:
        if 'tubes' in tmp_1:
            tabl_exist = True
    
    if tabl_exist == False:
        cur.execute('''CREATE TABLE tubes(box text, date text, time text, tubeid interger, dist real, dy real)''')

    today = datetime.today()
    dt_string = today.strftime("%Y/%m/%d")
    now = datetime.now() 
    time_string = now.strftime("%H:%M:%S")
    

    tubeval_list = [
        (box, dt_string,time_string, tubeid, dist, dy)
    ]
    
    cur.executemany("insert into tubes values (?, ?, ?, ?, ?, ?)", tubeval_list)


    # Save (commit) the changes
    con.commit()

    con.close()