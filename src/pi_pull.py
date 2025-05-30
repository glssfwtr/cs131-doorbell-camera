import base64
import datetime
import os
import zmq

incoming_dir = "/home/immortal/"

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://0.0.0.0:5555")

def save_clip(data, filename):
    with open(filename, "wb") as f:
        f.write(base64.b64decode(data))
    print(f"Saved to {filename}")

def run_inference(filename):
    # Stub: always return True for testing
    print(f"Running inference on {filename}")
    return True

def detect_person(filename):
    # Use AI chip logic to detect person
    return run_inference(filename)  # your detection function

while True:
    filename, encoded_data = socket.recv_multipart()
    filename = filename.decode()
    decoded_data = base64.b64decode(encoded_data)

    save_path = os.path.join(incoming_dir, filename)
    with open(save_path, "wb") as f:
        f.write(decoded_data)

    print(f"Saved to: {save_path}")