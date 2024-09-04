import psutil
import os
import tkinter as tk
from tkinter import ttk
import time
import threading
import subprocess
import platform

# Path to the directory where After Effects renders output
OUTPUT_DIR = "C:/path/to/your/output/folder"  # Change this to your actual output directory

# Countdown settings
COUNTDOWN_START = 10  # Start countdown from 10 seconds
SHUTDOWN_COUNTDOWN = 10  # Countdown before shutting down the PC

# Threshold settings
FILE_SIZE_THRESHOLD = 1024  # 1 KB change to detect rendering activity
CHECK_INTERVAL = 2  # Interval in seconds to check for rendering activity

def close_after_effects():
    """Function to close After Effects."""
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'].lower() == "afterfx.exe":
            process.terminate()  # Graceful termination
            time.sleep(3)  # Wait a moment to allow process termination
            if process.is_running():
                process.kill()  # Force kill if it didn't terminate
            print("After Effects has been closed.")
            break

def is_rendering_by_file_activity():
    """Check if rendering is happening by monitoring file size and modification time."""
    try:
        file_activity = False
        for filename in os.listdir(OUTPUT_DIR):
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.isfile(filepath):
                # Check both file size and last modification time
                current_size = os.path.getsize(filepath)
                last_modified = os.path.getmtime(filepath)
                time.sleep(CHECK_INTERVAL)  # Wait a moment to detect changes
                new_size = os.path.getsize(filepath)
                new_modified = os.path.getmtime(filepath)
                
                if (new_size > current_size + FILE_SIZE_THRESHOLD) or (new_modified > last_modified):
                    file_activity = True
                    break
        return file_activity
    except Exception as e:
        print(f"Error monitoring output directory: {e}")
        return False

def update_status():
    global render_stopped_time, rendering

    while True:
        if is_rendering_by_file_activity():
            status_var.set("Yes")
            countdown_var.set("")  # Clear the countdown display
            shutdown_var.set("")  # Clear shutdown display
            rendering = True
            render_stopped_time = None  # Reset the stop timer since rendering is ongoing
        else:
            if rendering:
                if render_stopped_time is None:
                    render_stopped_time = time.time()
                elif time.time() - render_stopped_time >= 10:
                    # Rendering has been stopped for 10 seconds
                    rendering = False
                    start_countdown(COUNTDOWN_START)
            else:
                # If countdown is active, display its value
                if countdown is not None:
                    countdown_var.set(f"Closing After Effects in {countdown} seconds...")
                elif shutdown_countdown is not None:
                    shutdown_var.set(f"Shutting down PC in {shutdown_countdown} seconds...")

        # Sleep a little before next check to avoid excessive CPU usage
        time.sleep(1)

def start_countdown(seconds_left):
    """Starts a non-blocking countdown and closes After Effects when it reaches zero."""
    global countdown
    countdown = seconds_left

    if countdown > 0:
        countdown_var.set(f"Closing After Effects in {countdown} seconds...")
        countdown -= 1
        root.after(1000, start_countdown, countdown)
    else:
        close_after_effects()
        start_shutdown_countdown(SHUTDOWN_COUNTDOWN)

def start_shutdown_countdown(seconds_left):
    """Starts a non-blocking shutdown countdown and shuts down the PC when it reaches zero."""
    global shutdown_countdown
    shutdown_countdown = seconds_left

    if shutdown_countdown > 0:
        shutdown_var.set(f"Shutting down PC in {shutdown_countdown} seconds...")
        shutdown_countdown -= 1
        root.after(1000, start_shutdown_countdown, shutdown_countdown)
    else:
        shutdown_pc()

def shutdown_pc():
    """Shut down the PC."""
    system_platform = platform.system()
    if system_platform == "Windows":
        subprocess.call(["shutdown", "/s", "/t", "0"])  # Windows shutdown
    elif system_platform == "Linux":
        subprocess.call(["sudo", "shutdown", "-h", "now"])  # Linux shutdown
    elif system_platform == "Darwin":
        subprocess.call(["sudo", "shutdown", "-h", "now"])  # macOS shutdown
    else:
        print("Unsupported OS for shutdown.")
    root.destroy()  # Close the GUI

def start_monitoring():
    # Start the update_status function in a separate thread
    monitor_thread = threading.Thread(target=update_status, daemon=True)
    monitor_thread.start()

# GUI setup
root = tk.Tk()
root.title("After Effects Rendering Monitor")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

status_var = tk.StringVar(value="No")
countdown_var = tk.StringVar(value="")  # Countdown display variable
shutdown_var = tk.StringVar(value="")  # Shutdown display variable

ttk.Label(frame, text="Is After Effects Rendering?").grid(row=0, column=0, padx=5, pady=5)
status_label = ttk.Label(frame, textvariable=status_var, font=("Helvetica", 16))
status_label.grid(row=0, column=1, padx=5, pady=5)

countdown_label = ttk.Label(frame, textvariable=countdown_var, font=("Helvetica", 12))
countdown_label.grid(row=1, column=0, columnspan=2, pady=5)

shutdown_label = ttk.Label(frame, textvariable=shutdown_var, font=("Helvetica", 12))
shutdown_label.grid(row=2, column=0, columnspan=2, pady=5)

# Initialize variables
render_stopped_time = None  # To keep track of when rendering stopped
rendering = False  # Flag to indicate if rendering was happening
countdown = None  # Countdown timer for After Effects
shutdown_countdown = None  # Countdown timer for shutdown

# Start monitoring in a separate thread
start_monitoring()

# Start the GUI loop
root.mainloop()