# sMDT Tube Bending Tester

Assistant tester for sMDT tube bending test with OpenCV

## Quick Start

- setup python environment: **python 3.8** is recommended (dev version)
- install dependent packages:

  ```shell
  pip install numpy opencv-python
  ```

- run example

  ```shell
  python main.py
  ```

  in real measurement, press **ENTER** to go to next tube (will clear cache), press **"q"** to exit

## Key Components

- main: main code to run the tester
- tube_data: cache class to save tube information
- utils: helper functions including intermediate image processing, all tuning/optimization happens here
