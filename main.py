import argparse
import logging
import time

import cv2

import config
import tube_data
import utils

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("yaml_config", action="store")
parser.add_argument(
    "-d", "--debug", required=False, help="run in debug mode", action="store_true",
)
args = parser.parse_args()
if not args.yaml_config:
    parser.print_help()
    exit()
# set logging format
logging_format = "%(asctime)s,%(msecs)03d %(levelname)s %(message)s"
logging.basicConfig(format=logging_format, datefmt="%Y-%m-%d:%H:%M:%S")
logger = logging.getLogger("bend_tester")
logger.setLevel(logging.INFO)
# set debug mode
if args.debug:
    logger.info("Setting logger to DEBUG mode")
    logger.setLevel(logging.DEBUG)


# Load configs
logger.info("#" * 80)
logger.info(f"Executing: {args.yaml_config}")
main = config.load_yaml_dict(yaml_path="share/main/main.yaml")
cfg = config.Config(main)
job = config.load_yaml_dict(yaml_path=args.yaml_config)
cfg.update(job)

# Main loop
start_time = time.perf_counter()
cj = cfg.job
tube_cache = None
test_sound = utils.Test_Sound()
if cj.webcam:
    cap = cv2.VideoCapture(cj.webcam_id)
else:
    cap = cv2.VideoCapture(cj.video_path)
while True:
    # Read image & checks
    if cj.use_video:
        success, img = cap.read()
    elif cj.use_img:
        img = cv2.imread(cj.img_path)
    else:
        break
    if img is not None:
        img = cv2.resize(img, cj.dsize, None, cj.fx, cj.fy)
    else:
        logger.critical("no video captured")
        break
    if tube_cache is None:
        tube_cache = tube_data.Tube_Cache(img, cfg)
        tube_cache.connect_db(box=cj.box_id, dir=cfg.job.output_dir)

    # Update border location
    border_img, x = utils.get_border(img, cfg, debug=args.debug)
    display_img = cv2.addWeighted(img, 0.8, border_img, 1, 0)

    # Load current limit
    tube_cache.update_x(x)
    limit_img = tube_cache.get_limit_img()
    display_img = cv2.addWeighted(display_img, 1, limit_img, 1, 0)
    status, dy = tube_cache.get_tube_data()

    # Display
    cv2.imshow("Monitor", display_img)
    ky = cv2.waitKey(cfg.main.interval)

    # React to keyboard inputs
    if ky == ord("\r"):
        if status == "PASS":
            test_sound.add()
        else:
            test_sound.error()
        logger.info(f"New test: status = {status}, dy = {dy * 1000:05f} um")
        tube_cache.write_db()
    elif ky == ord("d"):
        test_sound.remove()
        tube_cache.delete_db()
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
