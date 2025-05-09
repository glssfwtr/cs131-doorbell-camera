"""
motiondetected.py

This script runs on Jetson #1 and is responsible for detecting motion using a live video feed
from a connected camera. It uses a OpenCV based frame differencing method to efficiently detect
significant changes between consecutive frames. When motion is detected, the script can trigger 
further action such as recording a short video clip and sending it to Jetson #2 for further 
processing such as object detection.

By using this approach we minimize the computational load on Jetson #1 by avoiding real time 
AI inference and offloading heavy processing on Jetson #2 for object detection on smaller 
video clips instead of an entire video stream

Libraries:

OpenCV (cv2)
time (for timing)
datetime (for timestamped filenames)
os (for file system operations)
paramiko (for secure file transfer)
subprocess (for running scp commands)


Authors: Angel Franco 
Date: May 8th, 2025

"""

#implementation coming soon
