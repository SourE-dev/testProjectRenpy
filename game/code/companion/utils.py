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



def resolve_image_path(name):
    """
    If the user provides a simple name, look in the images directory.
    Otherwise, return the string as-is.
    """
    # Check if the name looks like a path (has slash or extension)
    if "/" in name or "." in name:
        return name
    
    # Otherwise, assume it's a simple name in the images directory
    # Adjust this to match your project's specific folder structure
    return os.path.join("images", name + ".png")