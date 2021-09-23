import cv2
import numpy as np
import logging

logger = logging.getLogger()


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

