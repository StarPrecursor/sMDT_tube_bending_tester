import logging

import cv2

import utils
import tube_data

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Configs
# TODO: need to enable customized config inputs
webcam = True
path = ""
cap = cv2.VideoCapture("./example_data/exp_video.mp4")

tube_cache = None
#dy = 0

while True:

    # Read image & checks
    if webcam:
        success, img = cap.read()
    else:
        img = cv2.imread(path)
    if img is not None:
        img = cv2.resize(img, (0, 0), None, 0.5, 0.5)
    else:
        print("no video captured")
        break
    if tube_cache is None:
        tube_cache = tube_data.Tube_Cache(img)

        
    # Update border location
    border_img, x = utils.get_border(img, showCanny=True)
    display_img = cv2.addWeighted(img, 0.8, border_img, 1, 0)


    # Load current limit
    tube_cache.update_x(x)
    result_tmp = tube_cache.get_limit_img()
    limit_img = result_tmp[0] 
    status = result_tmp[1] 
    dy = result_tmp[2]
    dist = result_tmp[3]
    display_img = cv2.addWeighted(display_img, 1, limit_img, 1, 0)
    
    #print(dy)

    # Display
    cv2.imshow("Monitor", display_img)
    ky = cv2.waitKey(20)

    # React to keyboard inputs
    if ky == ord("\r"):
        tube_cache.reset_x()
        if status == "PASS":
            print('\a')
    elif ky == ord("q"):
        break



# release
cap.release()
cv2.destroyAllWindows()

if(result_tmp):
    print("distance = {}, dy = {}, status = {}".format(dist, dy, status))
    tube_data.write_db('M-00256',1, dist, dy)