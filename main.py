import sys
import tkinter as tki
from tkinter import ttk
from tkinter import messagebox
from tkinter import scrolledtext
import serial
import serial.tools.list_ports
import threading
import queue
from datetime import datetime

LOG_FILE = "flightlog.log"

open(LOG_FILE, "a").write(f"\n\n--- Flight Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")

try:
    from LORA import LORA
    lora = LORA()
    lora_available = True
except Exception as e:
    print(f"LoRa init failed: {e}")
    lora = None
    lora_available = False

PayloadActive = False
message_queue = queue.Queue()


def receive_loop():
    while True:
        try:
            msg = lora.recieve()
            message_queue.put(msg)
        except Exception as e:
            message_queue.put(f"[Error] {e}")


def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    console.configure(state="normal")
    console.insert(tki.END, f"[{timestamp}] {msg}\n")
    console.see(tki.END)
    console.configure(state="disabled")
    open(LOG_FILE, "a").write(f"[{timestamp}] {msg}\n")


def poll_messages():
    try:
        msg = message_queue.get_nowait()
        log(msg)
    except queue.Empty:
        pass
    tk.after(100, poll_messages)

def send_start():
    if not lora_available:
        log("[Error] LoRa not available.")
        return
    log("Starting Payload, transmitting 100:1")
    lora.transmit("100:1")


def send_custom():
    msg = custom_entry.get().strip()
    if not msg:
        return
    if not lora_available:
        log(f"[Error] LoRa not available. Could not send: {msg}")
        return
    lora.transmit(msg)
    log(f"Sent: {msg}")
    custom_entry.delete(0, tki.END)


tk = tki.Tk()
tk.title("Ground Station Mission Control")
tk.geometry("1000x1000")

StartButton = ttk.Button(tk, text="Start", command=send_start)
EStopButton = ttk.Button(tk, text="Emergency Stop", command=lambda: messagebox.showinfo("Info", "Emergency Stop Activated"))

PayloadActivationButton = ttk.Button(tk, text="Activate Ground Sequence Early", command=lambda: messagebox.showinfo("Info", "Payload Activated"))
PayloadStopButton = ttk.Button(tk, text="Stop Payload Ground Sequence", command=lambda: messagebox.showinfo("Info", "Payload Stopped"))

StartButton.pack(pady=(10, 2))
EStopButton.pack(pady=2)
PayloadActivationButton.pack(pady=2)

PayloadStopButton.pack(pady=2)

# Console
console_frame = tki.Frame(tk)
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

# Custom message send
send_frame = tki.Frame(tk)
send_frame.pack(fill=tki.X, padx=10, pady=(0, 10))

custom_entry = ttk.Entry(send_frame, font=("Courier", 11))
custom_entry.pack(side=tki.LEFT, fill=tki.X, expand=True, padx=(0, 5))
custom_entry.bind("<Return>", lambda e: send_custom())

send_button = ttk.Button(send_frame, text="Send", command=send_custom)
send_button.pack(side=tki.LEFT)

if lora_available:
    log("LoRa initialised successfully.")
    threading.Thread(target=receive_loop, daemon=True).start()
    tk.after(100, poll_messages)
else:
    log("LoRa not available — running without hardware.")

tk.mainloop()