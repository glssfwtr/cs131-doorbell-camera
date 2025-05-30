"""
motiondetected.py

This script runs on Jetson #1 and is responsible for detecting motion using a live video feed
from a connected camera. It uses a OpenCV based frame differencing method to efficiently detect
significant changes between consecutive frames. When motion is detected, the script can trigger 
further action such as recording a short video clip and sending it to Jetson #2 for further 
processing such as object detection.

Authors: Angel Franco 
Date: May 8th, 2025
"""

import cv2
import time
import datetime
import os
from collections import deque
from multiprocessing import Process
import threading

import zmq
import base64


# Configuration
VIDEO_BUFFER = 10  # seconds of video before motion
VIDEO_AFTER =  10  # seconds of video after motion
LOCAL_CLIP_PATH = 'clips'
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 24
MOTION_THRESHOLD = 5000  # number of changed pixels to trigger motion
MAX_FRAMES = VIDEO_BUFFER * FPS

RASPBERRY_PI_IP = '100.75.45.21'
PORT = 5555

# ZeroMQ PUSH Socket
context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect(f"tcp://{RASPBERRY_PI_IP}:{PORT}")

frame_buffer = deque(maxlen=MAX_FRAMES)


os.makedirs(LOCAL_CLIP_PATH, exist_ok=True)

def send_clip_zmq(filepath):
    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read())    # base64 encoding -> safer transmission
        socket.send_multipart([filepath.encode(), encoded])
        print(f"Sent clip {os.path.basename(filepath)} to Raspberry Pi")


def save_clip(filename, before_buffer, after_buffer):

    print(f"before: {len(before_buffer)}")
    print(f"after: {len(after_buffer)}")

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, FPS, (FRAME_WIDTH, FRAME_HEIGHT))
    
    for frame in before_buffer + after_buffer:
        out.write(frame)
 
    out.release()


def record_clip(cap, filename, frame_buffer):
    after_buffer = deque(maxlen=(FPS * VIDEO_AFTER))
    before_buffer = deque(frame_buffer)
    start = time.time()
    while len(after_buffer) < FPS * VIDEO_AFTER :
        ret, frame = cap.read()
        if not ret:
            break
        after_buffer.append(frame)

    save_clip(filename,before_buffer,after_buffer)




def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    ret, prev_frame = cap.read()
    if not ret:
        print("Failed to read from camera.")
        return

    prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    prev_frame = cv2.GaussianBlur(prev_frame, (21, 21), 0)

    print("Motion detection started...")


    while True:
        ret, frame = cap.read()

        if not ret:
            break
        
        frame_buffer.append(frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        delta = cv2.absdiff(prev_frame, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        motion_detected = cv2.countNonZero(thresh) > MOTION_THRESHOLD


        if motion_detected:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(LOCAL_CLIP_PATH, f"motion_{timestamp}.avi")
            print(f"[{timestamp}] Motion detected! Recording to {filename}")
            record_clip(cap, filename, frame_buffer)
            send_clip_zmq(filename)

        prev_frame = gray

    cap.release()
    print("Motion detection ended.")

if __name__ == "__main__":
    main()
