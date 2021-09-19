import logging
import winsound

import cv2

import tube_data
import utils

logger = logging.getLogger("bend_tester")
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
logging_format = "%(asctime)s,%(msecs)03d %(levelname)s %(message)s"
logging.basicConfig(format=logging_format, datefmt="%Y-%m-%d:%H:%M:%S")

# Configs
# TODO: need to enable customized config inputs
webcam = True
path = ""
cap = cv2.VideoCapture("./example_data/exp_video.mp4")
box = "test_box"

tube_cache = None

while True:

    # Read image & checks
    if webcam:
        success, img = cap.read()
    else:
        img = cv2.imread(path)
    if img is not None:
        img = cv2.resize(img, (0, 0), None, 0.5, 0.5)
    else:
        logger.critical("no video captured")
        break
    if tube_cache is None:
        tube_cache = tube_data.Tube_Cache(img)
        tube_cache.connect_db(box=box)

    # Update border location
    border_img, x = utils.get_border(img, showCanny=True)
    display_img = cv2.addWeighted(img, 0.8, border_img, 1, 0)

    # Load current limit
    tube_cache.update_x(x)
    limit_img = tube_cache.get_limit_img()
    display_img = cv2.addWeighted(display_img, 1, limit_img, 1, 0)
    status, dy = tube_cache.get_tube_data()

    # Display
    cv2.imshow("Monitor", display_img)
    ky = cv2.waitKey(20)

    # React to keyboard inputs
    if ky == ord("\r"):
        tube_cache.reset_x()
        if status != "PASS":
            winsound.Beep(2500, 1000)
        logger.info(f"New test: status = {status}, dy = {dy * 1000:05f} um")
        tube_cache.write_db(status, dy)
    elif ky == ord("r"):
        logger.info("Resetting tube data")
        tube_cache.reset_x()
    elif ky == ord("q"):
        logger.info("Exiting program ...")
        break


# Release and Disconnect
cap.release()
cv2.destroyAllWindows()
if tube_cache:
    tube_cache.disconnect_db()
