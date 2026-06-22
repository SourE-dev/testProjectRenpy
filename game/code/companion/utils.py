import time
import os
from config import LOG_FILE

def log_debug(msg):
    """Writes a timestamped message to the log file and prints to console."""
    timestamp = time.strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    with open(LOG_FILE, "a") as f:
        f.write(formatted + "\n")
    print(formatted)

def get_asset_path(relative_path):
    # This assumes utils.py is in the same folder as main.py
    # Adjust path if utils.py is moved into a subfolder
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', relative_path)