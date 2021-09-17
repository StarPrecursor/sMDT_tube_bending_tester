import cv2
import numpy as np
import logging

logger = logging.getLogger()


def get_border(img, cThr=[100, 100], showCanny=False, color=(255, 255, 0)):
    img = cv2.convertScaleAbs(img, alpha=2, beta=50)
    cv2.imshow("Debug: Adjust", img)
    img = cv2.GaussianBlur(img, (5, 5), 1)
    cv2.imshow("Debug: Blur", img)
    img = cv2.Canny(img, cThr[0], cThr[1])
    kernel = np.ones((3, 3))
    img = cv2.dilate(img, kernel, iterations=3)
    img = cv2.erode(img, (3, 3), iterations=3)

    border_img = np.copy(img) * 0
    lines = cv2.HoughLinesP(
        img, 1, np.pi / 3600, 15, lines=np.array([]), minLineLength=50, maxLineGap=10
    )

    x = None
    if lines is not None:
        # find average x corodinate among all the lines found
        x = int(np.average(lines[:, :, [0, 2]]))
        cv2.line(border_img, (x, 0), (x, img.shape[0] - 1), color, 2)

    pad = np.ones(border_img.shape, dtype=border_img.dtype)
    border_img = cv2.merge((pad, pad, border_img))

    if showCanny:
        cv2.imshow("Debug: Canny", img)

    return (border_img, x)



