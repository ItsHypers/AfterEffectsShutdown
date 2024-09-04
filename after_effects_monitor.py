import os
import time
import tkinter as tk
from tkinter import ttk
import subprocess
import platform
import threading
import psutil


# Path to the directory where After Effects renders output
OUTPUT_DIR = r"D:\Videos\Call of Duty  Modern Warfare 3 (2023)\Editing\DysEp\Render"  # Change this to your actual output directory

# Debug mode variable
DEBUG_MODE = False  # Set to True to enable debugging mode

# Initialize global variables
render_stopped_time = None
rendering = False
last_file_times = {}
shutdown_scheduled = False

def close_after_effects():
    """Function to wait 10 seconds, then close After Effects and shut down the PC if MP4 files are found."""
    mp4_files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith('.mp4')]
    
    if mp4_files:
        update_gui_message("MP4 files found. Waiting 10 seconds before proceeding.")
        root.after(10000, proceed_after_effects)  # Wait 10 seconds before proceeding
    else:
        update_gui_message("No MP4 files found. Continuing to check rendering status.")
        start_checking_rendering()  # Continue checking rendering status

def proceed_after_effects():
    """Proceed with closing After Effects or debugging based on DEBUG_MODE."""
    if DEBUG_MODE:
        update_gui_message("DEBUG MODE: Detected MP4 files. Skipping closing After Effects and shutdown.")
        print("DEBUG MODE: Detected MP4 files. Skipping closing After Effects and shutdown.")
    else:
        terminate_after_effects()

def terminate_after_effects():
    """Terminate After Effects gracefully and then forcefully if necessary."""
    update_gui_message("Attempting to close After Effects...")
    print("DEBUG MODE: Attempting to close After Effects...")
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'].lower() == "afterfx.exe":
            process.terminate()  # Graceful termination
            time.sleep(3)  # Wait a moment to allow process termination
            if process.is_running():
                process.kill()  # Force kill if it didn't terminate
            update_gui_message("After Effects has been closed.")
            print("DEBUG MODE: After Effects has been closed.")
            if not DEBUG_MODE:
                start_shutdown_countdown()  # Start shutdown countdown if not in debugging mode
            break

def update_gui_message(message):
    """Update the GUI with a new message."""
    root.after(0, lambda: message_var.set(message))

def update_gui_values(file_activity):
    """Update the GUI values for file activity."""
    root.after(0, lambda: file_activity_var.set("Detected" if file_activity else "Not Detected"))

def is_rendering_by_file_activity():
    """Check if rendering is happening by monitoring file activity using polling."""
    global last_file_times

    file_activity_detected = False
    for filename in os.listdir(OUTPUT_DIR):
        file_path = os.path.join(OUTPUT_DIR, filename)
        if os.path.isfile(file_path):
            current_mtime = os.path.getmtime(file_path)
            if filename in last_file_times:
                if current_mtime != last_file_times[filename]:
                    file_activity_detected = True
                    last_file_times[filename] = current_mtime
            else:
                last_file_times[filename] = current_mtime

    return file_activity_detected

def check_mp4_file():
    """Check if MP4 files are present in the output folder."""
    return any(f.lower().endswith('.mp4') for f in os.listdir(OUTPUT_DIR))

def update_status():
    global render_stopped_time, rendering

    while True:
        try:
            file_activity = is_rendering_by_file_activity()
            if file_activity:
                rendering = True
                update_gui_values(True)
                root.after(0, lambda: status_var.set("Yes"))
                render_stopped_time = None  # Reset the stop timer since rendering is ongoing
            else:
                if render_stopped_time is None:
                    render_stopped_time = time.time()
                elif time.time() - render_stopped_time >= 10:
                    close_after_effects()
                    render_stopped_time = None  # Reset after handling
                    continue

            time.sleep(1)  # Adjust sleep time as needed to balance responsiveness and CPU usage
        except Exception as e:
            update_gui_message(f"Error: {e}")
            break

def start_checking_rendering():
    """Continue checking rendering status without GUI countdown."""
    status_thread = threading.Thread(target=update_status, daemon=True)
    status_thread.start()

def start_shutdown_countdown():
    """Start the countdown to shut down the PC."""
    update_gui_message("Shutting down PC in 10 seconds...")
    print("DEBUG MODE: Shutting down PC in 10 seconds...")
    root.after(10000, shutdown_pc)

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
        update_gui_message("Unsupported OS for shutdown.")
    root.quit()  # Close the Tkinter event loop

# GUI setup
root = tk.Tk()
root.title("After Effects Rendering Monitor")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

status_var = tk.StringVar(value="No")
file_activity_var = tk.StringVar(value="Not Detected")  # File activity display variable
message_var = tk.StringVar(value="")  # General message display variable

ttk.Label(frame, text="Is After Effects Rendering?").grid(row=0, column=0, padx=5, pady=5, sticky="w")
status_label = ttk.Label(frame, textvariable=status_var, font=("Helvetica", 16))
status_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame, text="File Activity:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
file_activity_label = ttk.Label(frame, textvariable=file_activity_var, font=("Helvetica", 12))
file_activity_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame, text="Message:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
message_label = ttk.Label(frame, textvariable=message_var, font=("Helvetica", 10), wraplength=300)
message_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")

# Start monitoring
start_checking_rendering()

# Start the Tkinter event loop
print("Starting Tkinter main loop...")
root.mainloop()