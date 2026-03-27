from LORA import LORA
from datetime import datetime

print("Initialising LoRa...")
lora = LORA()
print("LoRa ready. Listening for messages...\n")

try:
    while True:
        msg = lora.receive()
        if not msg:
            continue
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")
        if msg.strip().lower() == "ping":
            lora.transmit("pong")
            print(f"[{timestamp}] Replied: pong")
except KeyboardInterrupt:
    print("\nStopped.")
