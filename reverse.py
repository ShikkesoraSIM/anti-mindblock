import tkinter as tk
from tkinter import ttk, font as tkFont, filedialog, Listbox, messagebox
import os
from PIL import Image, UnidentifiedImageError
import pygetwindow as gw
from pynput.keyboard import Key, Controller
import time
import psutil
import getpass
import json
import subprocess
import threading
import win32api
import win32con
import keyboard
import pyautogui
import shutil
import requests
import sys
import webbrowser


def check_for_updates():
    current_version = "0.9.2"  # Replace with your current app version
    version_url = "https://shikkesora.com/version.txt"
    download_page_url = "https://shikkesora.com/downloads.html"  # Replace with your actual download page URL

    try:
        response = requests.get(version_url)
        latest_version = response.text.strip()

        if latest_version > current_version:
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            if messagebox.askyesno("Update Available", "There is an update available. Would you like to download it?"):
                webbrowser.open(download_page_url)
                sys.exit()  # Exit the program
            root.destroy()
    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")

def display_hotkey_warning():
    messagebox.showwarning("Warning", "You're enabling activation with hotkeys. Remember to have the correct skin selected")

def activate_with_hotkeys():
    global hotkeys_enabled
    hotkeys_enabled = True
    # Display a warning message when enabling hotkeys
    display_hotkey_warning()

def deactivate_with_hotkeys():
    global hotkeys_enabled
    hotkeys_enabled = False

def handle_hotkey():
    global hotkeys_enabled
    if hotkeys_enabled:
        # Do something when the hotkey is triggered
        print("Hotkey triggered!")
    else:
        # Hotkeys are disabled, ignore the hotkey
        pass

def display_australia_mode_text():
    global display_count
    text_window = tk.Toplevel()
    text_window.title("Australia Mode Activation")

    custom_font = tkFont.Font(family="Century Gothic", size=60)
    text_content = "SHIFT+ALT+A To Disable"
    text_width = custom_font.measure(text_content)
    text_height = custom_font.metrics("linespace")

    window_width, window_height = max(800, text_width), max(200, text_height)

    # Get the primary monitor information
    monitor_info = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0,0)))
    monitor_area = monitor_info['Monitor']
    screen_width, screen_height = monitor_area[2] - monitor_area[0], monitor_area[3] - monitor_area[1]

    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2

    # Adjust x and y to the coordinates of the primary monitor
    x += monitor_area[0]
    y += monitor_area[1]

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

def invert_mouse_y():
    screen_width, screen_height = pyautogui.size()
    while running:
        x, y = pyautogui.position()
        pyautogui.moveTo(x, screen_height - y, _pause=False)
        time.sleep(0.01)

def find_osu_window():
    osu_windows = [win for win in gw.getAllWindows() if "osu!" in win.title]
    if osu_windows:
        return osu_windows[0]  # Assuming the first matching window is the one we want
    return None

def set_display_orientation(rotation_angle):
    osu_window = find_osu_window()
    if not osu_window:
        print("osu! window not found.")
        return False

    # Get the monitor where the osu! window is located
    window_rect = osu_window._rect  # Get the bounding rectangle of the osu! window
    window_center = ((window_rect.left + window_rect.right) // 2, (window_rect.top + window_rect.bottom) // 2)
    
    hmonitor = win32api.MonitorFromPoint(window_center, win32con.MONITOR_DEFAULTTONEAREST)
    monitor_info = win32api.GetMonitorInfo(hmonitor)
    device_name = monitor_info['Device']

    rotation_mapping = {0: win32con.DMDO_DEFAULT, 90: win32con.DMDO_270, 180: win32con.DMDO_180, 270: win32con.DMDO_90}
    rotation_val = rotation_mapping.get(rotation_angle, win32con.DMDO_DEFAULT)

    dm = win32api.EnumDisplaySettings(device_name, win32con.ENUM_CURRENT_SETTINGS)
    if (dm.DisplayOrientation + rotation_val) % 2 == 1:
        dm.PelsWidth, dm.PelsHeight = dm.PelsHeight, dm.PelsWidth
    dm.DisplayOrientation = rotation_val

    if win32api.ChangeDisplaySettingsEx(device_name, dm, win32con.CDS_UPDATEREGISTRY) != win32con.DISP_CHANGE_SUCCESSFUL:
        print("Failed to change display orientation")
        return False
    return True

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
                directory = path[:path.rfind('\\')]
                print(f"Found OpenTabletDriver at: {directory}")
                return directory
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    print("OpenTabletDriver not found.")
    return None

def run_batch_file_in_thread(directory):
    def target():
        flag_file = os.path.join(directory, 'is_portable.flag')
        first_run_flag_file = os.path.join(directory, 'first_run.flag')

        if not os.path.exists(flag_file):
            batch_file = os.path.join(directory, 'convert_to_portable.bat')
            subprocess.Popen(['cmd', '/c', batch_file], creationflags=subprocess.CREATE_NO_WINDOW).wait()
            with open(flag_file, 'w') as f:
                f.write('OpenTabletDriver is now in portable mode.')

            with open(first_run_flag_file, 'w') as f:
                f.write('This marks the first run after conversion to portable mode.')
            restart_opentabletdriver(directory)
            edit_and_restart(directory, first_time=True)
            restart_opentabletdriver(directory)
            time.sleep(1)
            restart_opentabletdriver(directory)
        else:
            edit_and_restart(directory)

    def edit_and_restart(directory, first_time=False):
        edit_settings_json(directory)
        restart_opentabletdriver(directory)
        if first_time:
            time.sleep(1)  # Extra time for initial setup
            restart_opentabletdriver(directory)
            os.remove(os.path.join(directory, 'first_run.flag'))
            restart_opentabletdriver(directory)
        else:
            messagebox.showinfo('Activated', 'Australia mode activated successfully!')

    thread = threading.Thread(target=target)
    thread.start()

def edit_settings_json(directory):
    settings_file = os.path.join(directory, 'userdata', 'settings.json') if 'AppData' not in directory else os.path.join(directory, 'settings.json')
    if os.path.exists(settings_file):
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
    
    daemon_path = os.path.join(directory, 'OpenTabletDriver.Daemon.exe')
    subprocess.Popen([daemon_path], creationflags=subprocess.CREATE_NO_WINDOW)
    
    time.sleep(0.2)
    
    ux_path = os.path.join(directory, 'OpenTabletDriver.UX.Wpf.exe')
    subprocess.Popen([ux_path], creationflags=subprocess.CREATE_NO_WINDOW)
    
    time.sleep(0.7)
    
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

def automatic_detection():
    global detected_skin_path
    osu_path = find_osu_directory()
    if osu_path is not None:
        username = getpass.getuser()
        current_skin = read_user_skin_config(username)
        if current_skin:
            skins_path = os.path.join(osu_path, 'Skins', current_skin)
            detected_skin_path = skins_path  #Store the full path of the detected skin
            detected_label.config(text=f"{current_skin} Has been detected!")
            print(f"Automatically detected skin: {current_skin}")
        else:
            print("Failed to read the current skin from the config.")
    else:
        print("osu! directory not found.")

def select_osu_directory():
    dir_path = filedialog.askdirectory(title="Select osu! Directory")
    if not dir_path:
        return
    osu_directory_entry.delete(0, tk.END)
    osu_directory_entry.insert(0, dir_path)
    skins_path = os.path.join(dir_path, 'Skins')
    update_skins_list(skins_path, None)

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
    if not skin_path:
        print("No skin path provided.")
        return

    temp_folder_path = os.path.join(skin_path, "temp_australia_mode")
    rotate_prefixes = ["default-", "cursor", "spinner", "slider", "play-skip", "hit", "ranking", "section"]
    transparency_prefixes = ["score", "scorebar"]

    #Read skin.ini to dynamically adjust prefixes and paths if available
    skin_ini_path = os.path.join(skin_path, "skin.ini")
    if os.path.exists(skin_ini_path):
        with open(skin_ini_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line.startswith('HitCirclePrefix:'):
                    hit_circle_prefix = line.split(':')[1].strip()
                    rotate_prefixes.append(hit_circle_prefix.split('/')[-1] + '-')
                if line.startswith('ScorePrefix:'):
                    score_prefix = line.split(':')[1].strip()
                    transparency_prefixes.append(score_prefix.split('/')[-1])
                if line.startswith('ComboPrefix:'):
                    combo_prefix = line.split(':')[1].strip()
                    transparency_prefixes.append(combo_prefix.split('/')[-1])

    #Esta mierda sino se rompe todo XD
    if not os.path.exists(temp_folder_path) and not restore:
        os.makedirs(temp_folder_path)

    def process_image_for_rotation(image_path, temp_image_path, restore):
        try:
            if restore:
                shutil.copy2(temp_image_path, image_path)  #Restore
            else:
                shutil.copy2(image_path, temp_image_path)  #Backup
                with Image.open(image_path) as img:
                    img_rotated = img.rotate(180)
                    img_rotated.save(image_path)
        except UnidentifiedImageError:
            print(f"Unidentified image file skipped: {image_path}")
        except Exception as e:
            print(f"Error processing file {image_path}: {e}")

    def process_image_for_transparency(image_path, temp_image_path, restore):
        try:
            if restore:
                shutil.copy2(temp_image_path, image_path)
            else:
                shutil.copy2(image_path, temp_image_path)
                with Image.open(image_path) as img:
                    transparent_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    transparent_img.save(image_path)
        except UnidentifiedImageError:
            print(f"Unidentified image file skipped: {image_path}")
        except Exception as e:
            print(f"Error processing file {image_path}: {e}")

    def process_images():
        for root, dirs, files in os.walk(skin_path):
            if root.endswith("temp_australia_mode"):  #Skip temp directory itself
                continue
            for file in files:
                if file.endswith(".png"):
                    image_path = os.path.join(root, file)
                    temp_image_path = os.path.join(temp_folder_path, file)
                    if any(file.startswith(prefix.rstrip('-')) for prefix in rotate_prefixes) and not any(file.startswith(prefix) for prefix in transparency_prefixes):
                        process_image_for_rotation(image_path, temp_image_path, restore)
                    elif any(file.startswith(prefix) for prefix in transparency_prefixes):
                        process_image_for_transparency(image_path, temp_image_path, restore)

        #Clean up the temporary folder after restoration
        if restore:
            shutil.rmtree(temp_folder_path)

    process_images()
    action = "Restored" if restore else "Processed"
    print(f"{action} images in {skin_path}")

    # Somehow I made it work after 10 hours of trying different things? Don't change this code

def select_skin():
    global detected_skin_path  #En caso de tener que modificarlo luego
    selected_skin = skins_list.get(skins_list.curselection())
    detected_skin_path = os.path.join(osu_directory_entry.get(), "Skins", selected_skin)
    selected_skin_label.config(text=f"{selected_skin} skin is selected!")
    print(f"Selected skin path: {detected_skin_path}")

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

def press_keys_with_keyboard_library():
    keyboard_controller = Controller()
    try:
        osu_window_prefix = "osu!"
        osu_window = None

        #Attempt to find the osu! window and bring it to focus multiple times if needed
        for attempt in range(10):
            all_windows = gw.getAllWindows()
            osu_windows = [window for window in all_windows if osu_window_prefix in window.title]

            if osu_windows:
                osu_window = osu_windows[0]
                if osu_window.isMinimized:
                    osu_window.restore()
                osu_window.activate()
                time.sleep(1)  
                if osu_window.isActive:
                    break

        if not osu_window:
            print("osu! window not found. Make sure osu! is running.")
            return

        if not osu_window.isActive:
            print("Could not focus the osu! window.")
            return

        #Simulate the key press combination
        keyboard_controller.press(Key.ctrl)
        keyboard_controller.press(Key.alt)
        keyboard_controller.press(Key.shift)
        keyboard_controller.press('s')
        time.sleep(0.1)

    except Exception as e:
        print(f"Error sending key combination: {e}")

    finally:
        # Release the keys
        keyboard_controller.release('s')
        keyboard_controller.release(Key.shift)
        keyboard_controller.release(Key.alt)
        keyboard_controller.release(Key.ctrl)



def focus_osu_windows():
    osu_window_prefix = "osu!"
    osu_window = None
    for attempt in range(10):
            all_windows = gw.getAllWindows()
            osu_windows = [window for window in all_windows if osu_window_prefix in window.title]

            if osu_windows:
                osu_window = osu_windows[0]
                if osu_window.isMinimized:
                    osu_window.restore()
                osu_window.activate()
                time.sleep(0.5)  
                if osu_window.isActive:
                    break

def activate_australia_mode():
    global is_australia_mode_active, last_activation_time
    if is_australia_mode_active:
        return  #If already active, do nothing
    
    current_time = time.time()
    if (current_time - last_activation_time) < 5:  # 5 seconds delay to prevent spam
        return
    last_activation_time = current_time
    is_australia_mode_active = True
    australia_mode_button.config(state='disabled')  # Disable the button to prevent reactivation

    def run_australia_mode_actions(directory, skin_path):
        # Check and convert to portable mode if necessary
        run_batch_file_in_thread(directory)
        # Edit the settings.json file
        edit_settings_json(directory)
        terminate_processes(directory)
        # Restart OpenTabletDriver
        restart_opentabletdriver(directory)
        # Rotate the selected skin
        rotate_images(detected_skin_path, restore=False)
        # Flip the screen
        set_display_orientation(180)
        # Display big text indicating Australia Mode is activated
        # Press keys to trigger refresh in osu!
        focus_osu_windows()
        press_keys_with_keyboard_library()
        time.sleep(0.5)
        display_australia_mode_text()
        time.sleep(2)
        focus_osu_windows()
        australia_mode_button.config(state='normal')  # Re-enable the button once process is complete

    directory = find_opentabletdriver()
    if directory:
        selected_skin_path = os.path.join(osu_directory_entry.get(), "Skins", skins_list.get(tk.ANCHOR))
        thread = threading.Thread(target=lambda: run_australia_mode_actions(directory, selected_skin_path))
        thread.daemon = True
        thread.start()
    else:
        messagebox.showwarning('Warning', 'Cannot find OpenTabletDriver on this PC.')
        australia_mode_button.config(state='normal')  # Re-enable button if operation fails
        is_australia_mode_active = False

def deactivate_australia_mode():
    global is_australia_mode_active
    if not is_australia_mode_active:
        return
    directory = find_opentabletdriver()
    if directory:
        set_display_orientation(0)
        edit_settings_json(directory)
        terminate_processes(directory)
        restart_opentabletdriver(directory)
        keyboard_controller.release(Key.ctrl)
        if detected_skin_path:
            rotate_images(detected_skin_path, restore=True) 
        keyboard_controller.release(Key.ctrl)
        press_keys_with_keyboard_library()
        keyboard_controller.release(Key.ctrl)
        is_australia_mode_active = False
        australia_mode_button.config(state='normal')
    else:
        messagebox.showwarning('Warning', 'Cannot find OpenTabletDriver on this PC.')

def setup_hotkeys():
    keyboard.add_hotkey('shift+alt+a', deactivate_australia_mode)


if __name__ == "__main__":
    keyboard_controller = Controller()
    detected_skin_path = ""
    opentabletdriver_executables = ['OpenTabletDriver.Daemon.exe', 'OpenTabletDriver.UX.Wpf.exe']
    running = True
    is_australia_mode_active = False
    hotkeys_enabled = False
    display_count = 0
    
    # Usage
    check_for_updates()

    last_activation_time = 0
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

    tab_control.pack(expand=1, fill='both')

    main_frame_manual = ttk.Frame(manual_tab)
    main_frame_manual.pack(padx=10, pady=10)

    osu_directory_entry = ttk.Entry(main_frame_manual, width=50)
    osu_directory_entry.pack(side=tk.LEFT, padx=(0, 10))

    select_directory_button = ttk.Button(main_frame_manual, text="Select osu! Directory", command=select_osu_directory)
    select_directory_button.pack(side=tk.LEFT)

    skins_frame_manual = ttk.Frame(manual_tab)
    skins_frame_manual.pack(padx=10, pady=(5, 10))

    skins_list = Listbox(skins_frame_manual, width=60, height=10)
    skins_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

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

    refresh_skin_button = ttk.Button(manual_tab, text="Refresh Skin in-game!", command=press_keys_with_keyboard_library, width=button_width, style="Big.TButton")
    refresh_skin_button.pack(side=tk.BOTTOM, pady=10)

    #yeah i know theres better ways to do all this but maybe will fix in the future im too lazy and too bad at coding zzzzzzzzzzzzz

    root.mainloop()
