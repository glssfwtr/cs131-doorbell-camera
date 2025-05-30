import cv2
import time
import datetime
import os
from collections import deque
import zmq
import base64

# Configuration
VIDEO_BEFORE = 10  # seconds of frames to keep before motion
VIDEO_AFTER = 10   # seconds of frames to save after motion
COOLDOWN = 15      # seconds to ignore motion after recording
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 24
MOTION_THRESHOLD = 25000
LOCAL_CLIP_PATH = 'incoming'
MAX_FRAMES = VIDEO_BEFORE * FPS

RASPBERRY_PI_IP = '100.75.45.21'
PORT = 5555

# Setup
context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect(f"tcp://{RASPBERRY_PI_IP}:{PORT}")
frame_buffer = deque(maxlen=MAX_FRAMES)
os.makedirs(LOCAL_CLIP_PATH, exist_ok=True)

def send_clip_zmq(filepath):
    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read())
        socket.send_multipart([filepath.encode(), encoded])
        print(f"Sent: {os.path.basename(filepath)}")

def save_clip(filename, before_buffer, after_buffer):
    print(f"Saving: {filename} ({len(before_buffer)} before, {len(after_buffer)} after frames)")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, FPS, (FRAME_WIDTH, FRAME_HEIGHT))
    for frame in before_buffer + after_buffer:
        out.write(frame)
    out.release()

def record_clip(cap, buffered_frames):
    before_buffer = deque(buffered_frames)
    after_buffer = deque()
    for _ in range(FPS * VIDEO_AFTER):
        ret, frame = cap.read()
        if not ret:
            break
        after_buffer.append(frame)
        time.sleep(1 / FPS)  # maintain real-time pacing
    return before_buffer, after_buffer

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    if not cap.isOpened():
        print("Error: Camera failed to open.")
        return

    ret, prev_frame = cap.read()
    if not ret:
        print("Error: Initial frame failed.")
        return

    prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    prev_frame = cv2.GaussianBlur(prev_frame, (21, 21), 0)

    print("Motion detection running...")

    last_recorded_time = time.time() - COOLDOWN

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
            motion_pixels = cv2.countNonZero(thresh)
            motion_detected = motion_pixels > MOTION_THRESHOLD

            now = time.time()
            if motion_detected and (now - last_recorded_time > COOLDOWN):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(LOCAL_CLIP_PATH, f"motion_{timestamp}.mp4")
                print(f"[{timestamp}] Motion triggered, recording...")
                before, after = record_clip(cap, list(frame_buffer))
                save_clip(filename, before, after)
                send_clip_zmq(filename)
                frame_buffer.clear()
                last_recorded_time = time.time()

            prev_frame = gray

    except KeyboardInterrupt:
        print("Interrupted by user.")

    finally:
        cap.release()
        print("Motion detection stopped.")

if __name__ == "__main__":
    main()
