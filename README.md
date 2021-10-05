# sMDT Tube Bending Tester

Assistant tester for sMDT tube bending test with OpenCV

## Quick Start

- setup python environment: **python 3.8** is recommended (dev version)
- install dependent packages:

  ```shell
  pip install numpy opencv-python pygame
  ```

- run example

  ```shell
  python main.py share/job/example.yaml
  ```

  in real measurement, press **ENTER** to go to next tube (will clear cache), press **"r"** to reset, press **"q"** to exit

- run example of auto-mode

  ```shell
  python main.py -a share/job/example2.yaml
  ```

## Key Components

- main: main code to run the tester
- tube_data: cache class to save tube information
- utils: helper functions including intermediate image processing, all tuning/optimization happens here
