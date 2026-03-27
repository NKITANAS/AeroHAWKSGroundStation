import tkinter as tki
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
from datetime import datetime

LOG_FILE = "flightlog.log"


def _write_log_line(text: str) -> None:
    """Append a single line to the log file (properly closes the handle)."""
    with open(LOG_FILE, "a") as f:
        f.write(text)


_write_log_line(
    f"\n\n--- Flight Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n"
)

try:
    from LORA import LORA

    lora = LORA()
    lora_available = True
except Exception as e:
    print(f"LoRa init failed: {e}")
    lora = None
    lora_available = False

message_queue: queue.Queue[str] = queue.Queue()


# ---------------------------------------------------------------------------
# LoRa helpers
# ---------------------------------------------------------------------------

def receive_loop() -> None:
    """Continuously receive LoRa messages and enqueue them for the GUI."""
    while True:
        try:
            msg = lora.receive()
            if msg:
                message_queue.put(msg)
        except Exception as e:
            message_queue.put(f"[Error] {e}")


def _transmit(command: str, description: str) -> None:
    """Transmit *command* via LoRa and log *description*."""
    if not lora_available:
        log(f"[Error] LoRa not available. Could not send: {command}")
        return
    lora.transmit(command)
    log(f"{description} (sent {command})")


# ---------------------------------------------------------------------------
# GUI callbacks
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    """Append a timestamped message to the on-screen console and log file."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}\n"

    console.configure(state="normal")
    console.insert(tki.END, line)
    console.see(tki.END)
    console.configure(state="disabled")

    _write_log_line(line)


def poll_messages() -> None:
    """Drain the message queue into the console (called every 100 ms)."""
    while True:
        try:
            msg = message_queue.get_nowait()
            log(msg)
        except queue.Empty:
            break
    root.after(100, poll_messages)


def send_start() -> None:
    _transmit("100:1", "Starting Payload")


def send_estop() -> None:
    """Emergency-stop: transmit the abort command and confirm to the operator."""
    _transmit("100:0", "EMERGENCY STOP")
    messagebox.showwarning("Emergency Stop", "Emergency-stop command transmitted.")


def send_payload_activate() -> None:
    _transmit("200:1", "Activating ground sequence early")


def send_payload_stop() -> None:
    _transmit("200:0", "Stopping payload ground sequence")


def send_custom() -> None:
    msg = custom_entry.get().strip()
    if not msg:
        return
    _transmit(msg, f"Sent: {msg}")
    custom_entry.delete(0, tki.END)


# ---------------------------------------------------------------------------
# Build the UI
# ---------------------------------------------------------------------------

root = tki.Tk()
root.title("Ground Station Mission Control")
root.geometry("1000x700")
root.minsize(600, 400)

# --- Control buttons ---
btn_frame = tki.Frame(root)
btn_frame.pack(fill=tki.X, padx=10, pady=(10, 0))

start_btn = ttk.Button(btn_frame, text="Start", command=send_start)
estop_btn = ttk.Button(btn_frame, text="Emergency Stop", command=send_estop)
payload_start_btn = ttk.Button(
    btn_frame, text="Activate Ground Sequence Early", command=send_payload_activate
)
payload_stop_btn = ttk.Button(
    btn_frame, text="Stop Payload Ground Sequence", command=send_payload_stop
)

start_btn.pack(pady=2, fill=tki.X)
estop_btn.pack(pady=2, fill=tki.X)
payload_start_btn.pack(pady=2, fill=tki.X)
payload_stop_btn.pack(pady=2, fill=tki.X)

# --- Console ---
console_frame = tki.Frame(root)
console_frame.pack(fill=tki.BOTH, expand=True, padx=10, pady=10)

console_label = tki.Label(console_frame, text="Console", anchor="w")
console_label.pack(fill=tki.X)

console = scrolledtext.ScrolledText(
    console_frame,
    state="disabled",
    bg="white",
    fg="black",
    font=("Courier", 11),
    relief=tki.FLAT,
    wrap=tki.WORD,
)
console.pack(fill=tki.BOTH, expand=True)

# --- Custom message entry ---
send_frame = tki.Frame(root)
send_frame.pack(fill=tki.X, padx=10, pady=(0, 10))

custom_entry = ttk.Entry(send_frame, font=("Courier", 11))
custom_entry.pack(side=tki.LEFT, fill=tki.X, expand=True, padx=(0, 5))
custom_entry.bind("<Return>", lambda _: send_custom())

send_button = ttk.Button(send_frame, text="Send", command=send_custom)
send_button.pack(side=tki.LEFT)

# ---------------------------------------------------------------------------
# Start up
# ---------------------------------------------------------------------------

if lora_available:
    log("LoRa initialised successfully.")
    threading.Thread(target=receive_loop, daemon=True).start()
    root.after(100, poll_messages)
else:
    log("LoRa not available — running without hardware.")

root.mainloop()