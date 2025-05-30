import zmq
import base64

PORT = 5555

context = zmq.Context()
socket = context.socket(zmq.PULL)

# Bind to all interfaces to ensure it works over Tailscale
socket.bind(f"tcp://0.0.0.0:{PORT}")

print("Waiting for file...")

try:
    filename, data = socket.recv_multipart()
    decoded = base64.b64decode(data)
    with open(f"received_{filename.decode()}", "wb") as f:
        f.write(decoded)
    print(f"Received and saved as received_{filename.decode()}")
except Exception as e:
    print("Error:", e)
