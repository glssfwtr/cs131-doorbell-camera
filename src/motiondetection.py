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

import cv2
import time
import datetime
import os

import zmq
import base64

# Configuration
VIDEO_DURATION = 5  # seconds to record after motion is detected
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 20
LOCAL_CLIP_PATH = 'clips'
RASPBERRY_PI_IP = '100.75.45.21'
PORT = 5555

os.makedirs(LOCAL_CLIP_PATH, exist_ok=True)

# ZeroMQ PUSH Socket
context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect(f"tcp://{RASPBERRY_PI_IP}:{PORT}")

def record_clip(cap, filename):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, FPS, (FRAME_WIDTH, FRAME_HEIGHT))

    start_time = time.time()
    while time.time() - start_time < VIDEO_DURATION:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    out.release()

def send_clip_zmq(filepath):
    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read())    # base64 encoding -> safer transmission
        socket.send_multipart([filepath.encode(), encoded])
        print(f"Sent clip {os.path.basename(filepath)} to Raspberry Pi")

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    _, prev_frame = cap.read()
    prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    prev_frame = cv2.GaussianBlur(prev_frame, (21, 21), 0)

    print("Motion detection started...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        delta = cv2.absdiff(prev_frame, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        motion_detected = cv2.countNonZero(thresh) > 5000

        if motion_detected:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(LOCAL_CLIP_PATH, f"motion_{timestamp}.mp4")
            print(f"[{timestamp}] Motion detected! Saving to {filename}")
            record_clip(cap, filename)
            send_clip_zmq(filename)     # send file to PI
            time.sleep(1)  # prevent immediate re-trigger

        prev_frame = gray

    cap.release()
    print("Motion detection ended.")

if __name__ == "__main__":
    main()


