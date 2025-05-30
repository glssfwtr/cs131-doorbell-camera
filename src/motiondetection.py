"""
Motion detection and clip sending script for Jetson #1.
Captures significant changes between frames and sends clips to Jetson #2.

Author: Angel Franco
Date: May 8th, 2025
"""

import cv2
import time
import datetime
import os
from collections import deque
import zmq
import base64

# Configuration
VIDEO_BUFFER = 10  # seconds before motion
VIDEO_AFTER = 10   # seconds after motion
LOCAL_CLIP_PATH = 'incoming'
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 24
MOTION_THRESHOLD = 25000  # pixels
MAX_FRAMES = VIDEO_BUFFER * FPS

RASPBERRY_PI_IP = '100.75.45.21'
PORT = 5555

# ZeroMQ setup
context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect(f"tcp://{RASPBERRY_PI_IP}:{PORT}")

# Prepare buffer and folder
frame_buffer = deque(maxlen=MAX_FRAMES)
os.makedirs(LOCAL_CLIP_PATH, exist_ok=True)

def send_clip_zmq(filepath):
    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read())
        socket.send_multipart([filepath.encode(), encoded])
        print(f"Sent clip: {os.path.basename(filepath)}")

def save_clip(filename, before_buffer, after_buffer):
    print(f"Saving clip | before: {len(before_buffer)} frames, after: {len(after_buffer)} frames")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, FPS, (FRAME_WIDTH, FRAME_HEIGHT))
    for frame in before_buffer + after_buffer:
        out.write(frame)
    out.release()

def record_clip(cap, filename, buffered_frames):
    after_buffer = deque(maxlen=(FPS * VIDEO_AFTER))
    before_buffer = deque(buffered_frames)  # copy to preserve original
    while len(after_buffer) < FPS * VIDEO_AFTER:
        ret, frame = cap.read()
        if not ret:
            break
        after_buffer.append(frame)
    save_clip(filename, before_buffer, after_buffer)

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    if not cap.isOpened():
        print("Camera failed to open.")
        return

    ret, prev_frame = cap.read()
    if not ret:
        print("Failed to grab initial frame.")
        return

    prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    prev_frame = cv2.GaussianBlur(prev_frame, (21, 21), 0)

    print("Motion detection started...")

    try:
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
                filename = os.path.join(LOCAL_CLIP_PATH, f"motion_{timestamp}.mp4")
                print(f"[{timestamp}] Motion detected — recording to {filename}")
                record_clip(cap, filename, list(frame_buffer))
                send_clip_zmq(filename)
                time.sleep(1)

            prev_frame = gray

    except KeyboardInterrupt:
        print(" Stopped by user.")

    finally:
        cap.release()
        print(" Motion detection ended.")

if __name__ == "__main__":
    main()
