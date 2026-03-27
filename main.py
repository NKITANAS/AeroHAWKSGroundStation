import tkinter as tki
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import time
from datetime import datetime

LOG_FILE = "flightlog.log"

def _write_log_line(text: str) -> None:
    with open(LOG_FILE, "a") as f:
        f.write(text)

_write_log_line(f"\n--- Flight Log Started: {datetime.now()} ---\n")

# --- LoRa Init ---
try:
    from LORA import LORA
    lora = LORA()
    lora_available = True
except Exception as e:
    print(f"LoRa init failed: {e}")
    lora = None
    lora_available = False

message_queue = queue.Queue()

# --- Background Logic ---
def receive_loop():
    """Continuously poll the LoRa module for data."""
    while True:
        try:
            if lora_available:
                msg = lora.receive()
                if msg:
                    message_queue.put(msg)
            time.sleep(0.05)  # Prevent CPU spiking
        except Exception as e:
            message_queue.put(f"[Hardware Error] {e}")
            time.sleep(2)

def _transmit(command: str, description: str):
    if not lora_available:
        log(f"[Error] No Hardware. Cannot send: {command}")
        return
    try:
        lora.transmit(command)
        log(f"{description} (TX: {command})")
    except Exception as e:
        log(f"[TX Error] {e}")

# --- GUI Functions ---
def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    console.configure(state="normal")
    console.insert(tki.END, line)
    console.see(tki.END)
    console.configure(state="disabled")
    _write_log_line(line)

def poll_messages():
    """Check the queue for new messages and update UI."""
    while not message_queue.empty():
        msg = message_queue.get()
        log(f"RX: {msg}")
    root.after(100, poll_messages)

# --- Button Callbacks ---
def send_start(): _transmit("100:1", "Starting Payload")
def send_estop(): 
    _transmit("100:0", "EMERGENCY STOP")
    messagebox.showwarning("E-Stop", "Stop Command Sent")
def send_payload_activate(): _transmit("200:1", "Activating Ground Sequence")
def send_payload_stop(): _transmit("200:0", "Stopping Ground Sequence")
def send_custom():
    msg = custom_entry.get().strip()
    if msg:
        _transmit(msg, "Custom Msg")
        custom_entry.delete(0, tki.END)

# --- UI Setup ---
root = tki.Tk()
root.title("Ground Station Mission Control")
root.geometry("800x600")

btn_frame = tki.Frame(root)
btn_frame.pack(fill=tki.X, padx=10, pady=10)

ttk.Button(btn_frame, text="Start", command=send_start).pack(fill=tki.X, pady=2)
ttk.Button(btn_frame, text="EMERGENCY STOP", command=send_estop).pack(fill=tki.X, pady=2)
ttk.Button(btn_frame, text="Activate Ground Sequence", command=send_payload_activate).pack(fill=tki.X, pady=2)
ttk.Button(btn_frame, text="Stop Ground Sequence", command=send_payload_stop).pack(fill=tki.X, pady=2)

console_frame = tki.Frame(root)
console_frame.pack(fill=tki.BOTH, expand=True, padx=10, pady=5)
tki.Label(console_frame, text="Live Telemetry / Logs").pack(anchor="w")
console = scrolledtext.ScrolledText(console_frame, state="disabled", height=15)
console.pack(fill=tki.BOTH, expand=True)

send_frame = tki.Frame(root)
send_frame.pack(fill=tki.X, padx=10, pady=10)
custom_entry = ttk.Entry(send_frame)
custom_entry.pack(side=tki.LEFT, fill=tki.X, expand=True, padx=(0,5))
custom_entry.bind("<Return>", lambda _: send_custom())
ttk.Button(send_frame, text="Send", command=send_custom).pack(side=tki.LEFT)

# --- Start Threads ---
if lora_available:
    log("SYSTEM READY: LoRa Online.")
    threading.Thread(target=receive_loop, daemon=True).start()
else:
    log("SYSTEM WARNING: LoRa Offline (Hardware not found).")

root.after(100, poll_messages)
root.mainloop()