from LORA import LORA
from datetime import datetime

print("Initialising LoRa...")
lora = LORA()
print("LoRa ready. Listening for messages...\n")

while True:
    msg = lora.recieve()
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    if msg.strip().lower() == "ping":
        lora.transmit("pong")
        print(f"[{timestamp}] Replied: pong")
