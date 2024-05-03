# -*- coding: utf-8 -*-

import psutil
import os
import tkinter as tk
from tkinter import ttk, font as tkFont, filedialog, Listbox, messagebox
from PIL import Image, UnidentifiedImageError
import pygetwindow as gw
from pynput.keyboard import Key, Controller
from tkinter import Toplevel, Label
import time
import psutil
import getpass
import json
import subprocess
import threading
import win32api
import win32con
import win32gui
import win32process
import keyboard
import pyautogui
import shutil
import requests
import zipfile
import sys
import webbrowser
import configparser

def lower_process_priority():
    process = psutil.Process(os.getpid())
    process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)

lower_process_priority()

keyboard_controller = Controller()
detected_skin_path = ""
opentabletdriver_executables = ['OpenTabletDriver.Daemon.exe', 'OpenTabletDriver.UX.Wpf.exe']
running = True
is_australia_mode_active = False
hotkeys_enabled = False
display_count = 0
display_count_refresh = 0
config = configparser.ConfigParser()
config_file_path = 'user_settings.ini'
should_rotate_screen = False
rotate_on_refresh_var = None


def check_for_updates_in_background(current_version, version_url, download_page_url):
    try:
        response = requests.get(version_url)
        latest_version = response.text.strip()

        if latest_version > current_version:
            root = tk.Tk()
            root.withdraw()
            if messagebox.askyesno("Update Available", "There is an update available. Would you like to download it?"):
                webbrowser.open(download_page_url)
            root.destroy()
    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")

def check_for_updates():
    current_version = "0.9.6"
    version_url = "https://shikkesora.com/version.txt"
    download_page_url = "https://shikkesora.com/downloads"

    update_thread = threading.Thread(
        target=check_for_updates_in_background,
        args=(current_version, version_url, download_page_url),
        daemon=True
    )
    update_thread.start()

check_for_updates()      

def save_config(section, key, value):
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, value)
    with open(config_file_path, 'w') as f:
        config.write(f)

def read_config(section, key, fallback=None):
    config.read(config_file_path)
    if config.has_section(section) and config.has_option(section, key):
        return config.get(section, key)
    else:
        return fallback


def setup_message_box():
    show_first_run_message()
    messagebox.showinfo("Welcome", "Welcome to Shikkesora's Anti-Mindblock program! Here are some important things to note:\n\n\n"
                                    "- SETUP YOUR MONITOR IN Settings Tab BEFORE USING!!!!\n\n"
                                    "- Press SHIFT+ALT+A to disable Australia Mode when enabled.\n\n"
                                    "- Press SHIFT+ALT+D to reset display orientation when rotated.\n\n"
                                    "- Press CTRL+ALT+SHIFT+S to refresh the skin ingame if the program doesn't do it.\n\n"
                                    "- Text Display guide for hotkeys won't display if you're using the program in a second display, so please use the program in your main screen unless you already memorized the hotkeys.\n\n"
                                    "- Recommend using SHIFT+TAB mid map to minimize flipped clutter.\n\n"
                                    "- If you use Australia Mode, when rotating your area, you might see somewhere a black console looking window opened, that's the tablet driver Daemon, don't close it, just minimize and ignore.\n\n"
                                    "- Make sure osu! is running, TabletDriver is opened, and the skin is selected before activating Australia Mode.\n\n"
                                    "- Some skins' hitcircle numbers with confusing prefixes won't be rotated (most skins are fine)\n\n"
                                    "- Backup your skins before using Australia Mode to avoid losing any data.\n\n"
                                    "- Australia button is ONLY for tablet users for now.\n\n"
                                    "- Mouse mode coming very soon. I first wanted to hot-fix the existing issues!\n\n"
                                    "- Contact me in Discord ID: 'Shikkesora' for any questions or reports.\n\n\n"
                                    "- Enjoy using the program!\n\n\n"
                                    )


def check_first_run():
    try:
        config = configparser.ConfigParser()
        config.read('user_settings.ini')
        if 'General' not in config or not config['General'].getboolean('FirstRun'):
            # Either user_settings.ini or FirstRun flag not found, treat it as first run
            save_config('General', 'FirstRun', 'True')  # Set FirstRun to True
            return True
        else:
            return False
    except FileNotFoundError:
        # user_settings.ini file not found, treat it as first run
        save_config('General', 'FirstRun', 'True')  # Set FirstRun to True
        return True
    
def show_first_run_message():
    message = "You are on version 0.9.6!\n\nHere are the changes in the new version:\n\n0. The program is now more safe and convenient to use.\n\n1. Now program only rotates and doesn't make UI transparent. You can press Shift+Tab mid-map for a similar effect. This is done to avoid bugs and issues, and protect your skins.\n\n2. Bug fixes and performance enhancements.\n\n3. Backup Tab where you can create as many Backups of your Skins in-case anything happens.\n\n4. Fixed Tablet area not being rotated if OpenTabletDriver is not being ran in portable mode.\n\n Please click OK to continue."
    messagebox.showinfo("Welcome", message)

if check_first_run():
    setup_message_box()


def get_monitors():
    monitors = []
    # EnumDisplayMonitors returns a handle, a device context, and a rectangle for each monitor
    for monitor in win32api.EnumDisplayMonitors():
        monitor_info = win32api.GetMonitorInfo(monitor[0])
        monitors.append(monitor_info)
    return monitors

def get_default_monitor(monitors):
    # This function will return the primary monitor as default if it's available.
    primary_monitor = next((m for m in monitors if m['Flags'] == win32con.MONITORINFOF_PRIMARY), monitors[0])
    return f"Monitor 1: {primary_monitor['Device']}"

    global hotkeys_enabled
    if hotkeys_enabled:
        # Do something when the hotkey is triggered
        print("Hotkey triggered!")
    else:
        # Hotkeys are disabled, ignore the hotkey
        pass

import win32api

##########################################################
#                 Backup related code                    # 

backup_directory = "ShikkeAustraliaSkinBackup"
backup_filename_prefix = "SkinsBackup"


def create_backup_zip(skins_folder, progress_var, popup_window):
    osu_directory = os.path.dirname(skins_folder)
    backup_directory = os.path.join(osu_directory, "ShikkeAustraliaSkinBackup")

    if not os.path.exists(backup_directory):
        os.makedirs(backup_directory)

    # Determine a unique filename
    counter = 1
    while os.path.exists(os.path.join(backup_directory, f"{backup_filename_prefix}{counter}.zip")):
        counter += 1
    backup_filename = f"{backup_filename_prefix}{counter}.zip"
    backup_filepath = os.path.join(backup_directory, backup_filename)

    try:
        # Create the zip file manually to track progress
        file_list = []
        for root, _, files in os.walk(skins_folder):
            for file in files:
                file_list.append(os.path.join(root, file))

        total_files = len(file_list)
        with zipfile.ZipFile(backup_filepath, 'w') as zip_file:
            for idx, file_path in enumerate(file_list):
                arcname = os.path.relpath(file_path, skins_folder)
                zip_file.write(file_path, arcname)
                progress_var.set((idx + 1) / total_files * 100)
                popup_window.update_idletasks()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to create backup: {e}")
        popup_window.destroy()
        return

    # Close the popup
    time.sleep(0.5)
    popup_window.destroy()
    messagebox.showinfo("Backup Complete", f"Skins backed up to {backup_filepath}\n(Inside your osu! folder)")

def backup_skins(directory):
    skins_folder = os.path.join(directory, "Skins")
    if os.path.exists(skins_folder):
        popup_window = Toplevel()
        popup_window.title("Backing Up Skins")

        # Set the width of the progress bar
        progress_var = tk.DoubleVar()
        progress_bar_length = 300  # Adjust the length as needed
        progress_bar = ttk.Progressbar(popup_window, variable=progress_var, maximum=100, length=progress_bar_length)
        progress_bar.pack(pady=20, padx=20, fill=tk.X)

        thread = threading.Thread(target=create_backup_zip, args=(skins_folder, progress_var, popup_window))
        thread.start()
    else:
        print(f"Skins folder not found in {directory}")
        messagebox.showerror("Error", f"Skins folder not found in {directory}")

def create_backup_tab(tab_control):
    backup_tab = ttk.Frame(tab_control)
    tab_control.add(backup_tab, text="Backup Skins")

    frame = ttk.Frame(backup_tab)
    frame.pack(padx=10, pady=10)

    osu_directory_entry_backup = ttk.Entry(frame, width=50)
    osu_directory_entry_backup.pack(side=tk.LEFT, padx=(0, 10))

    select_directory_button_backup = ttk.Button(frame, text="Select osu! Directory",
                                                command=lambda: select_osu_directory_for_backup(osu_directory_entry_backup))
    select_directory_button_backup.pack(side=tk.LEFT)

    auto_detect_button_backup = ttk.Button(backup_tab, text="Auto-Detect osu! Directory",
                                           command=lambda: auto_detect_osu_directory_for_backup(osu_directory_entry_backup))
    auto_detect_button_backup.pack(pady=10)

    backup_button = ttk.Button(backup_tab, text="Backup Skins", command=lambda: backup_skins(osu_directory_entry_backup.get()))
    backup_button.pack(pady=10)

def select_osu_directory_for_backup(entry_widget):
    dir_path = filedialog.askdirectory(title="Select osu! Directory")
    if dir_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, dir_path)


def auto_detect_osu_directory_for_backup(entry_widget):
    osu_path = find_osu_directory()
    if osu_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, osu_path)
        print(f"Auto-detected osu! directory: {osu_path}")
    else:
        messagebox.showerror("Error", "osu! directory not found.")
##########################################################

def display_australia_mode_text():
    global display_count
    text_window = tk.Toplevel()
    text_window.title("Australia Mode Activation")

    custom_font = tkFont.Font(family="Century Gothic", size=60)
    text_content = "SHIFT+ALT+A To Disable"
    text_width = custom_font.measure(text_content)
    text_height = custom_font.metrics("linespace")

    window_width, window_height = max(800, text_width), max(200, text_height)

    # Read the selected monitor from settings
    saved_monitor = read_config('DisplaySettings', 'selected_monitor')
    device_name = saved_monitor.split(':')[-1].strip()

    # Get the monitor info using device_name
    monitors = get_monitors()
    monitor_info = next((m for m in monitors if m['Device'] == device_name), monitors[0])
    monitor_area = monitor_info['Work']

    # Calculate window position centered on the selected monitor
    x = monitor_area[0] + (monitor_area[2] - monitor_area[0] - window_width) // 2
    y = monitor_area[1] + (monitor_area[3] - monitor_area[1] - window_height) // 2

    text_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    text_window.overrideredirect(True)
    text_window.attributes("-transparentcolor", "white")

    canvas = tk.Canvas(text_window, bg='white', width=window_width, height=window_height, highlightthickness=0)
    canvas.pack()
    canvas.create_text(window_width // 2, window_height // 2, text=text_content, font=custom_font, fill="#AFA1FF", angle=180)
    text_window.attributes("-topmost", True)

    # Decide the display duration based on the number of times shown
    if display_count < 2:
        duration = 2500  # 4000 milliseconds = 4 seconds
    else:
        duration = 1000  # 1000 milliseconds = 1 second

    text_window.after(duration, text_window.destroy)
    display_count += 1

def display_refresh_text():
    global display_count_refresh
    text_window = tk.Toplevel()
    text_window.title("Refresh Skin")

    custom_font = tkFont.Font(family="Century Gothic", size=60)
    text_content = "SHIFT+ALT+D To Disable"
    text_width = custom_font.measure(text_content)
    text_height = custom_font.metrics("linespace")

    window_width, window_height = max(800, text_width), max(200, text_height)

    # Read the selected monitor from settings
    saved_monitor = read_config('DisplaySettings', 'selected_monitor')
    device_name = saved_monitor.split(':')[-1].strip()

    # Get the monitor info using device_name
    monitors = get_monitors()
    monitor_info = next((m for m in monitors if m['Device'] == device_name), monitors[0])
    monitor_area = monitor_info['Work']

    # Calculate window position centered on the selected monitor
    x = monitor_area[0] + (monitor_area[2] - monitor_area[0] - window_width) // 2
    y = monitor_area[1] + (monitor_area[3] - monitor_area[1] - window_height) // 2

    text_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    text_window.overrideredirect(True)
    text_window.attributes("-transparentcolor", "white")

    canvas = tk.Canvas(text_window, bg='white', width=window_width, height=window_height, highlightthickness=0)
    canvas.pack()
    canvas.create_text(window_width // 2, window_height // 2, text=text_content, font=custom_font, fill="#AFA1FF", angle=180)
    text_window.attributes("-topmost", True)

    # Decide the display duration based on the number of times shown
    if display_count_refresh < 2:
        duration = 2500  # 4000 milliseconds = 4 seconds
    else:
        duration = 1000  # 1000 milliseconds = 1 second

    text_window.after(duration, text_window.destroy)
    display_count_refresh += 1    

def find_osu_window():
    osu_windows = [win for win in gw.getAllWindows() if "osu!" in win.title]
    if osu_windows:
        return osu_windows[0]  # Assuming the first matching window is the one we want
    return None

def set_display_orientation(rotation_angle):
    
    # Read the selected monitor from settings
    saved_monitor = read_config('DisplaySettings', 'selected_monitor')
    device_name = saved_monitor.split(':')[-1].strip()

    # Define the rotation mappings
    rotation_mapping = {0: win32con.DMDO_DEFAULT, 90: win32con.DMDO_270, 180: win32con.DMDO_180, 270: win32con.DMDO_90}
    rotation_val = rotation_mapping.get(rotation_angle, win32con.DMDO_DEFAULT)

    # Get the current display settings
    dm = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
    if (dm.DisplayOrientation + rotation_val) % 2 == 1:  # Adjust resolution for portrait/landscape switch
        dm.PelsWidth, dm.PelsHeight = dm.PelsHeight, dm.PelsWidth
    dm.DisplayOrientation = rotation_val

    # Attempt to change the display settings
    if win32api.ChangeDisplaySettingsEx(device_name, dm, win32con.CDS_UPDATEREGISTRY) != win32con.DISP_CHANGE_SUCCESSFUL:
        print("Failed to change display orientation")
        return False
    return True

def create_settings_tab(tab_control):
    settings_tab = ttk.Frame(tab_control)
    tab_control.add(settings_tab, text='Settings')

    monitor_label = ttk.Label(settings_tab, text="Select Monitor for Rotation:")
    monitor_label.pack(pady=(10, 5))

    monitor_list = ttk.Combobox(settings_tab, state='readonly')
    monitor_list.pack(pady=5)

    monitors = get_monitors()
    monitor_list['values'] = [f"Monitor {i + 1}: {m['Device']}" for i, m in enumerate(monitors)]

    saved_monitor = read_config('DisplaySettings', 'selected_monitor', fallback='')
    if saved_monitor:
        monitor_list.set(saved_monitor)
    else:
        primary_monitor = f"Monitor 1: {monitors[0]['Device']}" if monitors else ""
        save_config('DisplaySettings', 'selected_monitor', primary_monitor)
        monitor_list.set(primary_monitor)

    def set_display():
        selected_monitor = monitor_list.get()
        save_config('DisplaySettings', 'selected_monitor', selected_monitor)
        messagebox.showinfo('Success', 'Display settings saved successfully!')

    save_button = ttk.Button(settings_tab, text="Save Display Settings", command=set_display)
    save_button.pack(pady=(10, 0))

    return settings_tab

def find_opentabletdriver():
    print("Searching for OpenTabletDriver...")
    active_processes = [proc for proc in psutil.process_iter(['pid', 'name'])]

    for proc in active_processes:
        print(f"Process name: {proc.info['name']} PID: {proc.info['pid']}")

    for proc in active_processes:
        if proc.info['name'] in opentabletdriver_executables:
            try:
                process = psutil.Process(proc.info['pid'])
                path = process.exe()
                directory = os.path.dirname(path)
                print(f"Found OpenTabletDriver at: {directory}")
                return directory
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    print("OpenTabletDriver not found.")
    return None

def get_settings_file_path(directory):
    # Check for portable mode
    portable_settings_path = os.path.join(directory, 'userdata', 'settings.json')
    if os.path.exists(portable_settings_path):
        return portable_settings_path

    # Otherwise, check the default AppData path
    username = getpass.getuser()
    appdata_path = os.path.join(f"C:\\Users\\{username}\\AppData\\Local\\OpenTabletDriver\\settings.json")
    if os.path.exists(appdata_path):
        return appdata_path

    return None

def edit_settings_json(directory):
    settings_file = get_settings_file_path(directory)
    if settings_file:
        with open(settings_file, 'r') as file:
            settings = json.load(file)
        for profile in settings.get('Profiles', []):
            tablet_settings = profile.get('AbsoluteModeSettings', {}).get('Tablet', None)
            if tablet_settings:
                tablet_settings['Rotation'] = (tablet_settings.get('Rotation', 0) + 180) % 360
        with open(settings_file, 'w') as file:
            json.dump(settings, file, indent=4)
        print("Settings updated in:", directory)
    else:
        print("Settings file not found in:", directory)

def restart_opentabletdriver(directory):
    for proc in psutil.process_iter():
        if proc.name() in opentabletdriver_executables:
            proc.kill()

    # Configure startup information
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = win32con.SW_SHOWMINNOACTIVE

    daemon_path = os.path.join(directory, 'OpenTabletDriver.Daemon.exe')
    subprocess.Popen([daemon_path], startupinfo=startupinfo)

    ux_path = os.path.join(directory, 'OpenTabletDriver.UX.Wpf.exe')
    subprocess.Popen([ux_path], startupinfo=startupinfo)

    try:
        windows = gw.getWindowsWithTitle('OpenTabletDriver')
        for window in windows:
            if "OpenTabletDriver" in window.title:
                window.minimize()
                print("Window minimized successfully.")
    except Exception as e:
        print(f"Failed to minimize window: {e}")

def terminate_processes(process_names):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] in process_names:
            try:
                subprocess.run(['taskkill', '/PID', str(proc.info['pid']), '/F'], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error terminating process {proc.info['name']} (PID: {proc.info['pid']}): {e}")
                  
def find_osu_directory():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'osu!.exe':
            return os.path.dirname(proc.exe())
    return None

def automatic_detection():
    global detected_skin_path, last_method_used
    osu_path = find_osu_directory()
    if osu_path:
        username = getpass.getuser()
        current_skin = read_user_skin_config(username)
        if current_skin:
            # Correctly concatenate the skin path using os.path.join
            skins_path = os.path.join(osu_path, 'Skins', current_skin)
            detected_skin_path = skins_path  # This should store the full path
            detected_label.config(text=f"{current_skin} has been detected!")
            last_method_used = 'automatic'
            print(f"Automatically detected skin: {current_skin}")
            # Possibly update the skins_list selection here if needed
        else:
            print("Failed to read the current skin from the config.")
    else:
        print("osu! directory not found.")

def select_osu_directory():
    dir_path = filedialog.askdirectory(title="Select osu! Directory")
    if dir_path:
        osu_directory_entry.delete(0, tk.END)
        osu_directory_entry.insert(0, dir_path)
        save_config('Settings', 'osu_directory', dir_path)  # This line will save the directory
        skins_path = os.path.join(dir_path, 'Skins')
        update_skins_list(skins_path, None)

def read_user_skin_config(username):
    osu_directory = find_osu_directory()
    if osu_directory:
        user_cfg_path = os.path.join(osu_directory, f'osu!.{username}.cfg')
        if os.path.exists(user_cfg_path):
            try:
                with open(user_cfg_path, 'r', encoding='utf-8') as file:  # Added encoding here BECAUSE THE GUI THING SUCKS ASS
                    for line in file:
                        if line.strip().startswith('Skin'):
                            current_skin = line.strip().split('=')[1].strip()
                            return current_skin
                print(f"Skin parameter not found in the configuration file: {user_cfg_path}")
            except Exception as e:
                print(f"Error reading config file: {e}")
        else:
            print(f"Config file {user_cfg_path} not found.")
    else:
        print("osu! directory not found.")
    return None

def update_skins_list(skins_path, current_skin):
    if os.path.exists(skins_path):
        skins = [name for name in os.listdir(skins_path) if os.path.isdir(os.path.join(skins_path, name))]
        skins.sort() 
        skins_list.delete(0, tk.END)
        for skin in skins:
            skins_list.insert(tk.END, skin)
    else:
        print(f"Skins directory not found: {skins_path}")

def rotate_images(skin_path, restore=False):
    print(f"Attempting to access skin path: {skin_path}")
    if not skin_path:  # Make sure the skin_path is not empty
        print("No skin path provided.")
        return
    
    # First attempt to rotate images without reading skin.ini
    files_rotated = 0
    hit_image_prefixes = ["hit", "cursor", "slider"]  # Adjust this list as needed
    
    # Function to recursively search for images in directories
    def rotate_images_recursive(directory):
        nonlocal files_rotated
        for root, dirs, files in os.walk(directory):
            for file_name in files:
                if file_name.startswith("default-") and file_name.endswith(".png"):
                    image_path = os.path.join(root, file_name)
                    try:
                        with Image.open(image_path) as img:
                            img = img.rotate(180 if not restore else -180)
                            img.save(image_path)
                            files_rotated += 1
                            print(f"Rotated {file_name}")
                    except Exception as e:
                        print(f"Error processing {file_name}: {e}")
                elif any(file_name.startswith(prefix) for prefix in hit_image_prefixes) and file_name.endswith(".png"):
                    image_path = os.path.join(root, file_name)
                    try:
                        with Image.open(image_path) as img:
                            img = img.rotate(180 if not restore else -180)
                            img.save(image_path)
                            files_rotated += 1
                            print(f"Rotated {file_name}")
                    except Exception as e:
                        print(f"Error processing {file_name}: {e}")
    
    # Rotate images directly in skin_path
    rotate_images_recursive(skin_path)

    # If not all files were rotated, check skin.ini for folder information
    if files_rotated < 1:  # Check if any images were rotated
        hitcircle_folder = None
        try:
            with open(os.path.join(skin_path, "skin.ini"), "r") as skin_ini_file:
                for line in skin_ini_file:
                    if line.startswith("HitCirclePrefix:"):
                        hitcircle_prefix = line.split(":")[1].strip()
                        hitcircle_folder = os.path.join(skin_path, hitcircle_prefix)
                        if os.path.exists(hitcircle_folder):
                            break
        except FileNotFoundError:
            print("skin.ini file not found.")

        if hitcircle_folder:
            rotate_images_recursive(hitcircle_folder)

    print(f"Rotated {files_rotated} images.")

def refresh_skin_and_rotate():
    set_display_orientation(180)
    press_keys_with_keyboard_library()
    display_refresh_text()

def reset_display_orientation():
    global should_rotate_screen
    if should_rotate_screen:
        if set_display_orientation(0):
            print("Display orientation reset to default.")
        else:
            print("Failed to reset display orientation.")
        should_rotate_screen = False

        rotate_images(True)
        # Refresh the skin in the game after restoring
        press_keys_with_keyboard_library()
        print("Skin refreshed in-game.")
        
def select_skin():
    global detected_skin_path, last_method_used
    selected_skin = skins_list.get(skins_list.curselection())
    detected_skin_path = os.path.join(osu_directory_entry.get(), "Skins", selected_skin)
    selected_skin_label.config(text=f"{selected_skin} skin is selected!")
    print(f"Selected skin path: {detected_skin_path}")
    last_method_used = 'manual'
    
     
from pynput.keyboard import Key, Controller
#idk why this is here but for some reason sometimes it breaks if its not there so just leave it be lmao

def toggle_australia_mode():
    global is_australia_mode_active
    if is_australia_mode_active:
        deactivate_australia_mode()
    else:
        activate_australia_mode()

# def hotkeys_activation_changed():
#     if hotkeys_activation_var.get():
#         keyboard.add_hotkey('shift+alt+a', toggle_australia_mode, suppress=True)
#     else:
#         keyboard.remove_hotkey('shift+alt+a')

def get_explorer_pids():
    explorer_pids = []
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == 'explorer.exe':
            explorer_pids.append(process.info['pid'])
    return explorer_pids


def just_focus_osu(maximize: bool = False):
    try:
        osu_window_prefix = "osu!"
        explorer_pids = get_explorer_pids()
        all_windows = gw.getAllWindows()
        osu_windows = [
            window for window in all_windows 
            if osu_window_prefix in window.title and window._hWnd not in explorer_pids
        ]

        if not osu_windows:
            print("osu! window not found. Make sure osu! is running.")
            return

        osu_window = osu_windows[0]

        # Restore window if minimized
        if osu_window.isMinimized:
            osu_window.restore()

        # Maximize window if requested
        if maximize and not osu_window.isMaximized:
            osu_window.maximize()

        # Focus the window
        osu_window.activate()

        # Wait for the window to activate
        timeout = 10  # Timeout after 10 seconds
        retry_count = 0
        while retry_count < timeout:
            if osu_window.isActive:
                break
            osu_window.activate()
            time.sleep(0.2)
            retry_count += 1

        if not osu_window.isActive:
            print("Failed to activate osu! window.")
            return

    except Exception as e:
        print(f"Error sending key combination: {e}")


def press_keys_with_keyboard_library(maximize: bool = False):
    keyboard_controller = Controller()
    try:
        osu_window_prefix = "osu!"
        explorer_pids = get_explorer_pids()
        all_windows = gw.getAllWindows()
        osu_windows = [
            window for window in all_windows 
            if osu_window_prefix in window.title and window._hWnd not in explorer_pids
        ]

        if not osu_windows:
            print("osu! window not found. Make sure osu! is running.")
            return

        osu_window = osu_windows[0]

        # Restore window if minimized
        if osu_window.isMinimized:
            osu_window.restore()

        # Maximize window if requested
        if maximize and not osu_window.isMaximized:
            osu_window.maximize()

        # Focus the window using pygetwindow and pywinauto
        osu_window.activate()

        # Ensure the window is activated
        timeout = 10
        retry_count = 0
        while retry_count < timeout:
            if osu_window.isActive:
                break
            osu_window.activate()
            time.sleep(0.2)
            retry_count += 1

        if not osu_window.isActive:
            print("Failed to activate osu! window.")
            return

        # Ensure the window has focus before sending hotkeys
        time.sleep(0.5)

        # Send key combination using pynput
        keyboard_controller.press(Key.ctrl)
        keyboard_controller.press(Key.alt)
        keyboard_controller.press(Key.shift)
        keyboard_controller.press('s')

        # Hold the keys briefly to ensure the combination registers
        time.sleep(0.2)

        # Release keys
        keyboard_controller.release('s')
        keyboard_controller.release(Key.shift)
        keyboard_controller.release(Key.alt)
        keyboard_controller.release(Key.ctrl)

    except Exception as e:
        print(f"Error sending key combination: {e}")


last_activation_time = 0

is_australia_mode_successfully_active = False


def activate_australia_mode():
    global is_australia_mode_active, is_australia_mode_successfully_active, last_activation_time, detected_skin_path, last_method_used

    if is_australia_mode_active:
        messagebox.showinfo("Info", "Australia Mode is already active.")
        return  # If already active, do nothing

    current_time = time.time()
    if (current_time - last_activation_time) < 5:  # 5 seconds delay to prevent spam
        return
    last_activation_time = current_time

    directory = find_opentabletdriver()
    if not directory:
        messagebox.showwarning('Warning', 'OpenTabletDriver not found.')
        return

    # Determine the skin path to use based on the last method used
    if last_method_used == 'automatic' and detected_skin_path:
        skin_path_to_use = detected_skin_path
    else:
        skin_path_to_use = os.path.join(osu_directory_entry.get(), "Skins", skins_list.get(tk.ANCHOR))

    def run_australia_mode_actions(directory, skin_path):
        global is_australia_mode_successfully_active       
        rotate_images(skin_path, restore=False)
        edit_settings_json(directory)
        restart_opentabletdriver(directory)
        set_display_orientation(180)
        time.sleep(0.5)
        press_keys_with_keyboard_library()
        time.sleep(0.5)
        just_focus_osu()
        time.sleep(1.5)
        display_australia_mode_text()
        

        australia_mode_button.config(state='normal')
        is_australia_mode_successfully_active = True  # Mark successful activation

    is_australia_mode_active = True
    is_australia_mode_successfully_active = False
    australia_mode_button.config(state='disabled')

    thread = threading.Thread(target=lambda: run_australia_mode_actions(directory, skin_path_to_use))
    thread.daemon = True
    thread.start()

def deactivate_australia_mode():
    global is_australia_mode_active, is_australia_mode_successfully_active

    if not is_australia_mode_active or not is_australia_mode_successfully_active:
        messagebox.showinfo("Info", "Australia Mode is not active or wasn't properly activated.")
        return

    directory = find_opentabletdriver()
    if not directory:
        messagebox.showwarning('Warning', 'OpenTabletDriver not found.')
        return

    skin_path = detected_skin_path

    def run_deactivation_actions(directory, skin_path):
        global is_australia_mode_active, is_australia_mode_successfully_active
        rotate_images(skin_path, restore=True)
        set_display_orientation(0)
        time.sleep(0.2)
        just_focus_osu()
        press_keys_with_keyboard_library()
        time.sleep(0.1)
        edit_settings_json(directory)
        restart_opentabletdriver(directory)
        time.sleep(1)
        just_focus_osu()

        is_australia_mode_active = False
        is_australia_mode_successfully_active = False
        australia_mode_button.config(state='normal')

    australia_mode_button.config(state='disabled')

    thread = threading.Thread(target=lambda: run_deactivation_actions(directory, skin_path))
    thread.daemon = True
    thread.start()


def setup_hotkeys():
    def try_reset_display_orientation():
        set_display_orientation(0)

    def try_deactivate_australia_mode():
        if is_australia_mode_active and is_australia_mode_successfully_active:
            deactivate_australia_mode()
        else:
            print("Australia Mode is not active or wasn't properly activated. Hotkey ignored.")

    keyboard.add_hotkey('shift+alt+a', try_deactivate_australia_mode)
    keyboard.add_hotkey('shift+alt+d', try_reset_display_orientation)

hotkey_thread = threading.Thread(target=setup_hotkeys, daemon=True)
hotkey_thread.start() 

root = tk.Tk()
root.title("Shikke's Skin Rotator")
root.bind('<Shift-Alt-a>', lambda event: deactivate_australia_mode())
icon_path = os.path.join(os.path.dirname(__file__), 'favicon.ico')
root.iconbitmap(icon_path)

theme_path = os.path.join(os.path.dirname(__file__), 'forest-dark.tcl')
root.tk.call('source', theme_path)
tab_control = ttk.Notebook(root)
ttk.Style().theme_use('forest-dark')

button_font = ('Helvetica', 16)
button_width = 20

manual_tab = ttk.Frame(tab_control)
tab_control.add(manual_tab, text='Manual')

automatic_tab = ttk.Frame(tab_control)
tab_control.add(automatic_tab, text='Automatic')

rotate_on_refresh_var = tk.BooleanVar()

tab_control.pack(expand=1, fill='both')

main_frame_manual = ttk.Frame(manual_tab)
main_frame_manual.pack(padx=10, pady=10)

osu_directory_entry = ttk.Entry(main_frame_manual, width=50)
osu_directory_entry.pack(side=tk.LEFT, padx=(0, 10))

select_directory_button = ttk.Button(main_frame_manual, text="Select osu! Directory", command=select_osu_directory)
select_directory_button.pack(side=tk.LEFT)

skins_frame_manual = ttk.Frame(manual_tab)
skins_frame_manual.pack(padx=10, pady=(5, 10))

settings_tab = create_settings_tab(tab_control)
tab_control.pack(expand=1, fill='both')

skins_list = Listbox(skins_frame_manual, width=60, height=10) 
skins_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

saved_osu_directory = read_config('Settings', 'osu_directory')
if saved_osu_directory:
    osu_directory_entry.insert(0, saved_osu_directory)
    skins_path = os.path.join(saved_osu_directory, 'Skins')
    update_skins_list(skins_path, None)

selected_skin_label = ttk.Label(manual_tab, text="No skin is selected!")
selected_skin_label.pack(pady=5)

select_skin_button = ttk.Button(manual_tab, text="Select", command=select_skin, style="Accent.TButton")
select_skin_button.pack(pady=5)

rotate_button = ttk.Button(manual_tab, text="Rotate Numbers", command=lambda: rotate_images(restore=False),style="Accent.TButton")
rotate_button.pack(side=tk.LEFT, padx=(10, 5), pady=7)

restore_button = ttk.Button(manual_tab, text="Restore Numbers", command=lambda: rotate_images(restore=True),style="Accent.TButton")
restore_button.pack(side=tk.RIGHT, padx=(5, 10), pady=7)

auto_detect_button = ttk.Button(automatic_tab, text="Auto-Detect osu! Skin", command=automatic_detection, width=button_width, style="Big.TButton")
auto_detect_button.pack(pady=(60, 10))

rotate_button.config(command=lambda: rotate_images(os.path.join(osu_directory_entry.get(), "Skins", skins_list.get(tk.ANCHOR)), restore=False))
restore_button.config(command=lambda: rotate_images(os.path.join(osu_directory_entry.get(), "Skins", skins_list.get(tk.ANCHOR)), restore=True))


detected_label = ttk.Label(automatic_tab, text="")
detected_label.pack(pady=20)

# hotkeys_activation_var = tk.BooleanVar()
# hotkeys_activation_checkbox = ttk.Checkbutton(manual_tab, text="Enable activation with hotkeys", variable=hotkeys_activation_var, command=hotkeys_activation_changed)
# hotkeys_activation_checkbox.pack(pady=8)

# hotkeys_activation_var = tk.BooleanVar()
# hotkeys_activation_checkbox = ttk.Checkbutton(automatic_tab, text="Enable activation with hotkeys", variable=hotkeys_activation_var, command=hotkeys_activation_changed)
# hotkeys_activation_checkbox.pack(pady=5)

#mouse_mode_var = tk.BooleanVar()
#mouse_mode_checkbox = ttk.Checkbutton(manual_tab, text="Mouse Mode", variable=mouse_mode_var)
#mouse_mode_checkbox.pack()

australia_mode_button = ttk.Button(manual_tab, text="Australia Mode", command=activate_australia_mode, width=button_width)
australia_mode_button.pack(pady=(110, 20))

australia_mode_button = ttk.Button(automatic_tab, text="Australia Mode", command=activate_australia_mode, width=button_width, style="Big.TButton")
australia_mode_button.pack(pady=(110, 20))

style = ttk.Style()
style.configure('Big.TButton', font=button_font)

refresh_skin_button = ttk.Button(
    manual_tab,
    text="Refresh Skin in-game!",
    command=press_keys_with_keyboard_library,
    width=button_width,
    style="Big.TButton"
)
refresh_skin_button.pack(side=tk.BOTTOM, pady=(10, 5))

refresh_and_rotate_button = ttk.Button(
    manual_tab,
    text="Refresh Skin and flip Display",
    command=refresh_skin_and_rotate,
    width=30
)
refresh_and_rotate_button.pack(side=tk.BOTTOM, pady=(5, 10))

create_backup_tab(tab_control)

#yeah i know theres better ways to do all this but maybe will fix in the future im too lazy and too bad at coding zzzzzzzzzzzzz

root.resizable(False, False)

root.mainloop()