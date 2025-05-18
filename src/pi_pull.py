import zmq
import base64
import datetime

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
    filename_bytes, clip_data = socket.recv_multipart()
    filename = filename_bytes.decode()
    save_clip(clip_data, filename)

    if run_inference(filename):
        print(f"Person detected in {filename}, saving/forwarding")
        # TODO: Save to disk permanently or forward to backend
    else:
        print(f"No person detected in {filename}, discarding")