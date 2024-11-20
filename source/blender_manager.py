# -*- coding: utf-8 -*-
import time
start_time = time.time()
import os
import sys
import locale
import asyncio
import aiohttp
import pystray
import ctypes
from PIL import Image, ImageTk
try:
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8") 
except locale.Error:
    locale.setlocale(locale.LC_ALL, "C")     
import tarfile
from datetime import datetime
import shutil
import subprocess
import requests
import zipfile
import ast
from bs4 import BeautifulSoup
import threading
import queue 
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.simpledialog as simpledialog
from tkinterdnd2 import TkinterDnD, DND_FILES
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import json
import re
import multiprocessing
import traceback
import tempfile
import ast 
import certifi
import ssl
import psutil

end_time = time.time()
print(f"imports loaded in {end_time - start_time}.") 
CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), ".BlenderManager", "config.json")

DEFAULT_SETTINGS = {
    "version": "0.0.6",
    "selected_theme": "darkly",
    "auto_update_checkbox": True,
    "bm_auto_update_checkbox": False,
    "launch_on_startup":False,
    "run_in_background": True,
    "chunk_size_multiplier": 3,
    "window_alpha": 0.98,
    "treeview_font_size": 12,
    "treeview_heading_font_size": 14,
    "treeview_font_family": "Segoe UI",
    "button_font_family": "Segoe UI",
    "button_font_size": 14,
    "show_addon_management": True,
    "show_project_management": True,
    "show_render_management": True,
    "show_version_management": True,
    "show_installation": True
}

BLENDER_MANAGER_DIR = os.path.join(os.path.expanduser("~"), ".BlenderManager")
BLENDER_DIR = os.path.join(os.path.expanduser("~"), ".BlenderManager", 'BlenderVersions')
NOTES_FILE_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'paths', "render_notes.json")
APPDATA_RENDER_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'renders')
RENDERFOLDER_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'paths', 'renderfolderpath.json')
PROJECT_RUNTIME_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'mngaddon', 'project_time.json')
BASE_MESH_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'paths', 'base_mesh_path.json')
BLENDER_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'blender')




def load_config():
    """Load settings from config.json file or create it with default settings."""
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("Error reading config file. Using default settings.")
            save_config(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS.copy()
    else:
        save_config(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

def save_config(config_data):
    """Save the current settings to the config.json file."""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(config_data, f, indent=4)
        print("Config file saved successfully.")
    except Exception as e:
        print(f"Error saving config file: {e}")





def log_error_to_file(error_message):
    """Logs error messages to a file named 'log.txt' in the current directory."""
    log_file_path = os.path.join(os.path.dirname(__file__), 'log.txt')
    try:
        with open(log_file_path, 'a') as log_file:
            log_file.write(error_message + '\n')
    except Exception as e:
        print(f"Failed to write to log file: {e}")



class Redirector:
    """Redirects writes to a Tkinter Text widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.configure(state='normal')
        self.text_widget.insert('end', text)
        self.text_widget.see('end')
        self.text_widget.configure(state='disabled')

    def flush(self):
        pass


class BlenderManagerApp(TkinterDnD.Tk):
    
    def __init__(self):
        
        super().__init__()
        
        start_time = time.time()
        self.tray_name = "Blender Manager"
        self.check_existing_window_and_tray()
        self.title("Blender Manager")     
        self.geometry("900x600")
        threading.Thread(target=self.initialize_app, daemon=True).start()
        self.iconbitmap(r"Assets/Images/bmng.ico")
        self.minsize(900, 600)
        self.maxsize(1920, 1080)
        self.after(100, self.check_queue)
        self.base_install_dir = os.path.join(os.path.expanduser("~"), '.BlenderManager')
        self.blender_install_dir = os.path.join(self.base_install_dir, 'blender')
        self.style = ttkb.Style() 
        self.load_settings_on_begining()

        self.current_folder = self.get_render_folder_path()      
        self.theme_choice = tk.StringVar(value=self.style.theme_use())  
        self.available_themes = {
            'Solar': 'solar',
            'Darkly': 'darkly',
            'Flatly': 'flatly',
            'Cyborg': 'cyborg',
            'Superhero': 'superhero',
            'Default': 'default',
            'Journal': 'journal',
            'Litera': 'litera',
            'Lumen': 'lumen',
            'Lux': 'lux',
            'Minty': 'minty',
            'Morph': 'morph',
            'Pulse': 'pulse',
            'Sandstone': 'sandstone',
            'Sketchy': 'sketchy',
            'Slate': 'slate',
            'United': 'united',
            'Yeti': 'yeti',
            'Zephyr': 'zephyr'
        }

        self.is_installing = False
        self.cancel_event_main = threading.Event() 
        self.cancel_event = threading.Event()
        self.cancel_event_install = threading.Event()
        self.queue = queue.Queue()
        self.create_widgets()
        self.check_queue()
        
        self.notes_data = self._load_notes()
        self.current_render_name = None     
        self.menu_cache = {}  
        self.load_menu_cache()  
        self.create_main_menu()
        self.redirect_output()
        self.start_time = time.time() 
        
        with open(BASE_MESH_PATH, 'r') as file:
            base_meshes = json.load(file)
        self.base_meshes = base_meshes  
        self.base_mesh_var = tk.StringVar()
        self.new_base_mesh_name = tk.StringVar()
        self.new_base_mesh_path = tk.StringVar()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.tray_icon = None
        self.create_tray_icon()
        self.attributes('-fullscreen', False)  
        end_time = time.time()
        print(f"Blender Manager initialized in {end_time - start_time}.")  



#------------------------UPDATE CONTROL-----------------------------------------------
    def bm_show_loading_screen(self):
        """Show a loading screen during the update process."""
        self.loading_window = tk.Toplevel(self)
        self.loading_window.title("Updating Blender Manager")
        self.loading_window.geometry("300x150")
        self.loading_window.resizable(False, False)

        self.loading_window.protocol("WM_DELETE_WINDOW", lambda: None)

        self.update_idletasks() 
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()

        x = main_x + (main_width // 2) - (300 // 2)
        y = main_y + (main_height // 2) - (150 // 2)

        self.loading_window.geometry(f"+{x}+{y}")
        self.loading_window.transient(self)
        self.loading_window.grab_set()

        ttkb.Label(
            self.loading_window,
            text="Downloading and Installing Update...\nPlease wait.",
            font=("Segoe UI", 12),
            anchor="center"
        ).pack(pady=20)

        self.loading_progress_var = tk.DoubleVar()
        self.loading_progress_bar = ttkb.Progressbar(
            self.loading_window,
            variable=self.loading_progress_var,
            maximum=100,
            bootstyle="primary-striped"
        )
        self.loading_progress_bar.pack(fill='x', padx=20, pady=10)

        self.loading_window.update_idletasks()


    def bm_close_loading_screen(self):
        """Close the loading screen after the update is complete."""
        if hasattr(self, 'loading_window') and self.loading_window:
            self.loading_window.destroy()
            self.loading_window = None


    def bm_check_for_updates_threaded(self):
        """Start the update check in a separate thread to prevent GUI freezing."""
        update_thread = threading.Thread(target=self.bm_check_for_updates, daemon=True)
        update_thread.start()
        
    def bm_check_for_updates(self):
        """Check for updates and prompt the user if a new version is available."""
        self.bm_load_current_version()
        print(f"Current version: {self.current_version}")

        self.latest_version = self.bm_get_latest_version()
        print(f"Latest version from GitHub: {self.latest_version}")

        if self.latest_version and self.bm_is_new_version(self.current_version, self.latest_version):
            response = messagebox.askyesno(
                "New Version Available",
                f"A new version {self.latest_version} is available. You are currently using {self.current_version}.\nDo you want to update?"
            )
            if response:
                self.bm_download_and_install_update(self.latest_version)
        else:
            print(f"You are using the latest version: {self.current_version}")



    def bm_load_current_version(self):
        """Load the current version from DEFAULT_SETTINGS."""
        self.current_version = DEFAULT_SETTINGS['version']
        print(f"Loaded current version: {self.current_version}")
    def update_version_in_config(self):
        """Update the version in the config file based on DEFAULT_SETTINGS."""
        if self.settings.get("version") != DEFAULT_SETTINGS['version']:
            self.settings["version"] = DEFAULT_SETTINGS['version']
            save_config(self.settings)
            print(f"Config version updated to: {DEFAULT_SETTINGS['version']}")



    def bm_get_latest_version(self):
        """Fetch the latest version from GitHub releases."""
        url = "https://github.com/verlorengest/BlenderManager/releases"
        try:
            response = requests.get(url)
            response.raise_for_status()
            versions = re.findall(r'v(\d+\.\d+\.\d+)', response.text)
            versions = sorted(versions, key=lambda x: list(map(int, x.split('.'))))
            return versions[-1]
        except Exception as e:
            print(f"Error checking latest version: {e}")
            return None

    def bm_is_new_version(self, current_version, latest_version):
        """Check if the latest version is newer than the current version."""
        try:
            current = list(map(int, current_version.split('.')))
            latest = list(map(int, latest_version.split('.')))
            return latest > current
        except Exception as e:
            print(f"Error comparing versions: {e}")
            return False

    def bm_hide_main_window(self):
        """Hide the main Blender Manager window."""
        self.withdraw()
        
    def bm_download_and_install_update(self, version):
        """Download and install the new version of Blender Manager with feedback."""
        import platform

        download_url = f"https://github.com/verlorengest/BlenderManager/releases/download/v{version}/blender_manager_v{version}.zip"
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "update.zip")

        try:
            self.bm_show_loading_screen()

            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(zip_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        progress = (downloaded_size / total_size) * 100
                        self.loading_progress_var.set(progress)
                        self.loading_window.update_idletasks()

            extract_dir = os.path.join(temp_dir, "extracted")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            current_os = platform.system().lower()

            if current_os == 'windows':
                script_path = self.create_windows_update_script(extract_dir)
            elif current_os == 'darwin':  # macOS
                script_path = self.create_macos_update_script(extract_dir)
            elif current_os == 'linux':
                script_path = self.create_linux_update_script(extract_dir)
            else:
                messagebox.showerror("Update Error", "Unsupported operating system. Please install manually.")
                self.bm_close_loading_screen()
                return

            messagebox.showinfo("Update", "Blender Manager will now close for the update.")
            self.bm_close_loading_screen()
            subprocess.Popen([script_path], shell=True)
            os._exit(0)

        except Exception as e:
            self.bm_close_loading_screen()
            messagebox.showerror("Update Error", f"Failed to install update: {e} Please install manually.")
        finally:
            shutil.rmtree(temp_dir)



    def create_windows_update_script(self, extract_dir):
        """Update function for Windows"""
        script_path = os.path.join(extract_dir, "update.bat")
        executable_path = os.path.join(os.getcwd(), "blender_manager.exe")

        inner_dirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
        if not inner_dirs:
            raise Exception("No inner directory found in the extracted update zip.")

        inner_folder_path = os.path.join(extract_dir, inner_dirs[0])

        with open(script_path, 'w', encoding='utf-8') as script_file:
            script_file.write(f"""
@echo off
chcp 65001 > nul
timeout /t 2 /nobreak > nul

set "source={inner_folder_path}"
set "destination={os.path.dirname(executable_path)}"

xcopy /s /e /y "%source%\\*" "%destination%"
if %errorlevel% neq 0 (
    echo Update failed. Unable to copy files. Please install manually.
    powershell -Command "Add-Type -AssemblyName PresentationFramework; $result = [System.Windows.MessageBox]::Show('Update failed. Unable to copy files. Please install manually.', 'Update Error', 'OK', 'Error'); if ($result -eq 'OK') {{ Start-Process 'https://yourwebsite.com/manual-update' }}"
    exit /b 1
)

start "" "{executable_path}"
del /q /s "{extract_dir}\\*"
rmdir /s /q "{extract_dir}"
exit
            """)

        return script_path



    def create_macos_update_script(self, extract_dir):
        """Create update script for macOS."""
        import os

        script_path = os.path.join(extract_dir, "update.sh")
        executable_path = os.path.join(os.getcwd(), "blender_manager")

        inner_dirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
        if not inner_dirs:
            raise Exception("No inner directory found in the extracted update zip.")

        inner_folder_path = os.path.join(extract_dir, inner_dirs[0])

        with open(script_path, 'w', encoding='utf-8') as script_file:
            script_file.write(f"""
#!/bin/bash
sleep 2

source="{inner_folder_path}"
destination="{os.path.dirname(executable_path)}"

cp -R "$source/." "$destination/"
if [ $? -ne 0 ]; then
    osascript -e 'display alert "Update Error" message "Update failed. Unable to copy files. Please install manually." as critical buttons {{"OK"}} default button "OK"'
    exit 1
fi

open "{executable_path}"
rm -rf "{extract_dir}"
exit 0
            """)

        return script_path



    def create_linux_update_script(self, extract_dir):
        """Create update script for Linux."""
        import os

        script_path = os.path.join(extract_dir, "update.sh")
        executable_path = os.path.join(os.getcwd(), "blender_manager")

        inner_dirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
        if not inner_dirs:
            raise Exception("No inner directory found in the extracted update zip.")

        inner_folder_path = os.path.join(extract_dir, inner_dirs[0])

        with open(script_path, 'w', encoding='utf-8') as script_file:
            script_file.write(f"""
#!/bin/bash
sleep 2

source="{inner_folder_path}"
destination="{os.path.dirname(executable_path)}"

cp -R "$source/." "$destination/"
if [ $? -ne 0 ]; then
    zenity --error --text="Update failed. Unable to copy files. Please install manually."
    exit 1
fi

"{executable_path}" &
rm -rf "{extract_dir}"
exit 0
            """)

        return script_path


#--------------------------------------------------------------------------------------------------




    def initialize_app(self):
        """Initializing the application."""
        print("Initializing app...")

        def background_task():
            """Runs heavy initialization tasks in a background thread."""
            try:
                setup_complete_file = os.path.join(os.path.expanduser("~"), ".BlenderManager", "setup_complete")
                if os.path.exists(setup_complete_file):
                    print("Setup already complete. Skipping initialization.")
                    return  

                base_dir = BLENDER_MANAGER_DIR
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir)

                required_dirs = [
                    "BaseMeshes", "BlenderVersions", "mngaddon",
                    "paths", "Projects", "renders"
                ]
                for dir_name in required_dirs:
                    dir_path = os.path.join(base_dir, dir_name)
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path)

                paths_dir = os.path.join(base_dir, "paths")
                json_files = [
                    "base_mesh_path.json",
                    "project_directory.json", 
                    "render_notes.json",
                    "renderfolderpath.json"
                ]
                for json_file in json_files:
                    file_path = os.path.join(paths_dir, json_file)
                    if not os.path.exists(file_path):
                        with open(file_path, 'w') as file:
                            json.dump({}, file) 

                with open(setup_complete_file, 'w') as file:
                    file.write("Setup complete.")
            finally:
                print("Initialization complete.")
                self.after(0, self.show_window)
                self.after(0, self.deiconify)

        threading.Thread(target=background_task, daemon=True).start()


    def load_menu_cache(self):
        
        try:
           
            self.menu_cache['plugins'] = self.refresh_plugins_list()
            self.menu_cache['projects'] = self.refresh_projects_list()
            self.menu_cache['installed_versions'] = self.get_installed_versions()
        except Exception as e:
            print(f"Error Loading: {e}")
                    

    def load_settings_on_begining(self):
        """Load settings and initialize variables."""
        self.settings = load_config()
        self.bm_load_current_version()
        self.update_version_in_config()

        self.tab_visibility_settings = {
            "Addon Management": self.settings.get("show_addon_management", True),
            "Project Management": self.settings.get("show_project_management", True),
            "Render Management": self.settings.get("show_render_management", True),
            "Version Management": self.settings.get("show_version_management", True),
            "Installation": self.settings.get("show_installation", True),
        }

        selected_theme = self.settings.get("selected_theme", "darkly")
        self.style = ttkb.Style()
        if selected_theme in self.style.theme_names():
            self.style.theme_use(selected_theme)
            print(f"Theme applied: {selected_theme}")
        else:
            self.style.theme_use("darkly")
            self.settings["selected_theme"] = "darkly"
            save_config(self.settings)
            print("Invalid theme. Default theme 'darkly' applied.")

        self.bm_auto_update_var = tk.BooleanVar(value=self.settings.get("bm_auto_update_checkbox", False))
        self.auto_update_var = tk.BooleanVar(value=self.settings.get("auto_update_checkbox", True))
        self.launch_on_startup_var = tk.BooleanVar(value=self.settings.get("launch_on_startup", False))
        self.run_in_background_var = tk.BooleanVar(value=self.settings.get("run_in_background", True))
        self.chunk_size_multiplier = self.settings.get("chunk_size_multiplier", 3)
        self.window_alpha = self.settings.get("window_alpha", 0.98)
        self.attributes("-alpha", self.window_alpha)
        self.treeview_font_family = self.settings.get("treeview_font_family", "Segoe UI")
        self.treeview_font_size = self.settings.get("treeview_font_size", 12)
        self.treeview_heading_font_size = self.settings.get("treeview_heading_font_size", 14)
        self.button_font_family = self.settings.get("button_font_family", "Segoe UI")
        self.button_font_size = self.settings.get("button_font_size", 14)

        self.apply_custom_styles()








    def get_installed_versions(self):
        versions = []
        if os.path.exists(BLENDER_DIR):
            versions = [d for d in sorted(os.listdir(BLENDER_DIR)) if os.path.isdir(os.path.join(BLENDER_DIR, d))]
        return versions
    

    def create_widgets(self):
        """Create the GUI layout."""
        main_frame = ttkb.Frame(self, padding=(20, 20, 20, 20))
        main_frame.pack(expand=1, fill='both')

        self.style.configure("TNotebook.Tab", font=(self.button_font_family, 10))
        self.notebook = ttkb.Notebook(main_frame)
        self.notebook.pack(expand=1, fill='both')

        self.main_menu_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_menu_tab, text="Main Menu")
        self.create_main_menu()

        for tab_name, is_visible in self.tab_visibility_settings.items():
            if is_visible:
                self.toggle_tab_visibility(tab_name, tk.BooleanVar(value=True))


        self.logs_tab = ttkb.Frame(self.notebook)
        self.notebook.add(self.logs_tab, text="Logs")
        self.create_logs_tab()


        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.current_version = self.bm_load_current_version()
        self.latest_version = None
        if self.settings.get("bm_auto_update_checkbox", True):
            print("Checking Blender Manager updates...")
            self.bm_check_for_updates_threaded()

        if self.auto_update_var.get():
            print(f"Auto Update: {self.auto_update_var.get()}")
            self.auto_update()
        else:
            print(f"Auto Update: {self.auto_update_var.get()}")


    def is_tray_icon_running(self):
        """Check if a tray application with the given name is running."""
        try:
            for process in psutil.process_iter(attrs=['name']):
                if process.info['name'] and self.tray_name.lower() in process.info['name'].lower():
                    return True
        except FileNotFoundError as e:
            print(f"FileNotFoundError: {e}")
        except Exception as e:
            print(f"Unexpected error checking tray: {e}")
        return False



    def find_window_with_tray_name(self, tray_name):
        """Find a tray window with the specified name."""
        def enum_windows_callback(hwnd, lParam):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                title = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, title, length + 1)
                if tray_name.lower() in title.value.lower():
                    windows.append(hwnd)
            return True

        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
        windows = []
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(enum_windows_callback), None)
        return windows[0] if windows else None


    def bring_window_to_front(self, hwnd=None):
        """Bring the application's window or tray to the front."""
        try:
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            else:
                hwnd = ctypes.windll.user32.FindWindowW(None, self.tray_name)
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 9)
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"Error bringing window to front: {e}")

    def check_existing_window_and_tray(self):
        try:
            current_pid = os.getpid()
            current_path = os.path.realpath(sys.argv[0])

            hwnd = self.find_window_with_tray_name(self.tray_name)
            if hwnd:
                self.bring_window_to_front(hwnd)
                print(f"Tray window found with name: {self.tray_name}")
                sys.exit()

            for process in psutil.process_iter(attrs=['pid', 'exe']):
                try:
                    if process.pid != current_pid:
                        exe_path = process.info.get('exe')
                        if exe_path and os.path.samefile(os.path.realpath(exe_path), current_path):
                            print(f"Found existing process for path: {exe_path}")
                            self.bring_window_to_front()
                            sys.exit()
                except (psutil.AccessDenied, psutil.NoSuchProcess, FileNotFoundError):
                    continue

        except FileNotFoundError as e:
            print(f"FileNotFoundError while checking window/tray: {e}")
        except Exception as e:
            print(f"Error checking for existing window or tray: {e}")








        #-----------------Tray Functions-------------------


        

        

    def create_tray_icon(self):
        
        image = Image.open(r"Assets/Images/bmng.ico")
        self.tray_icon = pystray.Icon("BlenderManager", image, "Blender Manager", self.create_tray_menu())
        self.tray_icon.run_detached()

    def create_tray_menu(self):
        
        
        project_menu_items = []
        for item in self.recent_projects_tree.get_children():
            project_name = self.recent_projects_tree.item(item, "values")[0]
            project_menu_items.append(pystray.MenuItem(project_name, self.show_project_info))

        return pystray.Menu(
            pystray.MenuItem("Show Blender Manager", self.show_window),
            pystray.MenuItem("Launch Blender", self.launch_blender_from_tray),
            pystray.MenuItem("Projects", pystray.Menu(*project_menu_items)),
            pystray.MenuItem("Create Project", self.create_project_from_tray),
            pystray.MenuItem("Exit", self.exit_app)
        )
    


    def show_project_info(self, icon, item):
        """Displays information about the selected project and selects it in the Treeview."""
        project_name = item.text  

       
        project_found = False
        for tree_item in self.recent_projects_tree.get_children():
            if self.recent_projects_tree.item(tree_item, "values")[0] == project_name:
                self.recent_projects_tree.selection_set(tree_item) 
                self.recent_projects_tree.focus(tree_item)  
                self.recent_projects_tree.see(tree_item)  
                project_found = True
                break

        if project_found:
           
            self.load_main_menu_project()
        else:
            messagebox.showwarning("Project Not Found", f"Project '{project_name}' not found in the list.")

    def launch_blender_from_tray(self, icon, item):
        """Runs the Launch Blender function from the tray menu."""
        self.launch_latest_blender()
        
    def create_project_from_tray(self, icon, item):
        """Runs the Launch Blender function from the tray menu."""
        self.show_window()
        self.open_create_project_window()
        

    def on_closing(self):
        """Handles the window close event based on 'Run in Background' setting."""
        if self.run_in_background_var.get():
            self.withdraw()  
            print("Application minimized to tray.")
        else:
            self.exit_app(None, None)

    def exit_app(self, icon, item):
        """Forcibly and immediately exits the application."""
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception as e:
            print(f"Tray icon stop failed: {e}")
        os._exit(0)

    def show_window(self):
        self.bring_window_to_front()


#-------------------------------------------------------------------------------------------------------




        #------------------------------------------------------------------
        #-----------------------Render Management--------------------------
        #------------------------------------------------------------------


        #-------------GUI---------------

        
    def create_render_management_tab(self):
        """Creates the Render Management tab with Render List on the left, Render Preview on the right,
        buttons under the preview, and notes at the bottom, all dynamically resizing with the window."""

        render_frame = ttk.Frame(self.render_management_tab, padding=(10, 10, 10, 10))
        render_frame.pack(expand=1, fill='both')

        render_frame.columnconfigure(0, weight=1, minsize=150)  
        render_frame.columnconfigure(1, weight=4, minsize=500)  
        render_frame.rowconfigure(0, weight=1, minsize=300)  


        # ====== Render List Section (Left side) ======
        
        

        render_list_frame = ttk.Frame(render_frame)
        render_list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 10))
        render_list_frame.columnconfigure(0, weight=1)
        render_list_frame.rowconfigure(1, weight=1)

        render_list_label = ttk.Label(render_list_frame, text="Render List", font=("Segoe UI", 14, "bold"))
        render_list_label.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))

        self.render_tree = ttk.Treeview(
            render_list_frame,
            columns=("File Name", "File Size", "Resolution", "File Date"),
            show="headings",
            selectmode='browse'
        )

        for column in ("File Name", "File Size", "Resolution", "File Date"):
            self.render_tree.heading(column, text=column, command=lambda c=column: self.sort_treeview(c, False))
            self.render_tree.column(column, anchor="center", stretch=True, minwidth=30)

        self.render_tree.grid(row=1, column=0, sticky="nsew", padx=3, pady=(0, 0))

        for i in range(1, 21):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.render_tree.insert('', 'end', values=("2024-01-01", f"Render_{i}.png", "1920x1080", "00:10", "10MB", "3.5.0"), tags=(tag,))

        
        self.render_tree.bind("<<TreeviewSelect>>", self.load_note_on_select)
        self.render_tree.bind("<<TreeviewSelect>>", self.display_selected_render)

        render_scrollbar_y = ttk.Scrollbar(render_list_frame, orient="vertical", command=self.render_tree.yview)
        self.render_tree.configure(yscroll=render_scrollbar_y.set)
        render_scrollbar_y.grid(row=1, column=1, sticky="ns")

        render_scrollbar_x = ttk.Scrollbar(render_list_frame, orient="horizontal", command=self.render_tree.xview)
        self.render_tree.configure(xscroll=render_scrollbar_x.set)
        render_scrollbar_x.grid(row=2, column=0, sticky="ew")

        right_frame = ttk.Frame(render_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 10))
        right_frame.columnconfigure(0, weight=2)
        right_frame.rowconfigure(0, weight=3) 
        right_frame.rowconfigure(1, weight=1) 

        
        preview_label = ttk.Label(right_frame, text="Render Preview", font=("Segoe UI", 14, "bold"))
        preview_label.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))

        self.preview_frame = ttk.Frame(right_frame, relief="solid", borderwidth=0, width=1000, height=800)
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(0, 10))
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.rowconfigure(0, weight=1)

        self.preview_label = ttk.Label(self.preview_frame, text="No Preview Available", anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nsew")
        


        buttons_frame = ttkb.Frame(right_frame)
        buttons_frame.grid(row=2, column=0, sticky="ew", padx=3, pady=(0, 0))

        buttons_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="button")

        open_button = ttkb.Button(buttons_frame, text="Open", takefocus=False, command=self.open_render)
        open_button.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        refresh_button = ttkb.Button(buttons_frame, text="Refresh", takefocus=False, command=self.refresh_render_list)
        refresh_button.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        browse_button = ttkb.Button(buttons_frame, text="Browse", takefocus=False, command=self.browse_render_directory)
        browse_button.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        delete_button = ttkb.Button(buttons_frame, text="Delete", takefocus=False, command=self.delete_render)
        delete_button.grid(row=0, column=3, sticky="nsew", padx=5, pady=5)

        
        notes_frame = ttk.Frame(render_frame)
        notes_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=(10, 0))
        notes_frame.columnconfigure(0, weight=1)
        notes_frame.rowconfigure(1, weight=1)

        notes_label = ttk.Label(notes_frame, text="Render Notes", font=("Segoe UI", 14, "bold"))
        notes_label.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))

        self.notes_text = tk.Text(notes_frame, height=5, wrap="word", font=("Segoe UI", 10))
        self.notes_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))

        notes_scrollbar = ttk.Scrollbar(notes_frame, orient="vertical", command=self.notes_text.yview)
        self.notes_text.configure(yscrollcommand=notes_scrollbar.set)
        notes_scrollbar.grid(row=1, column=1, sticky="ns", pady=(0,5))

        save_note_button = ttk.Button(notes_frame, text="Save Note", takefocus=False, command=self.save_current_note)
        save_note_button.grid(row=2, column=0, sticky="ew", padx=5, pady=(5, 0))

        render_frame.grid_propagate(True)
        self.render_file_paths = {}
        self.refresh_render_list()


        #--------------Render Menu Methods--------------
        



    def refresh_render_list(self):
        """Refresh the Render List by reloading the current directory files."""
        if hasattr(self, 'current_folder') and self.current_folder:
            self.render_tree.delete(*self.render_tree.get_children())
            self.render_file_paths.clear()

            for file_name in os.listdir(self.current_folder):
                file_path = os.path.join(self.current_folder, file_name)

                if os.path.isfile(file_path) and file_name.lower().endswith(('.png', '.jpeg', '.jpg', '.mp4')):
                    try:
                        file_stats = os.stat(file_path)
                        file_date = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                        file_size = f"{file_stats.st_size / (1024 * 1024):.2f} MB"
                        file_extension = os.path.splitext(file_name)[1].lower()

                        if file_extension in ['.png', '.jpeg', '.jpg']:
                            with Image.open(file_path) as img:
                                resolution = f"{img.width}x{img.height}"
                        elif file_extension == '.mp4':
                            resolution = "N/A"
                        else:
                            resolution = "N/A"

                        blender_version = "N/A" 

                        item_id = self.render_tree.insert(
                            "", 
                            "end", 
                            values=(file_name, file_size, resolution, file_date),
                            tags=('evenrow' if len(self.render_tree.get_children()) % 2 == 0 else 'oddrow',)
                        )

                        self.render_file_paths[item_id] = file_path

                    except PermissionError:
                        messagebox.showwarning("Permission Denied", f"Cannot access file: {file_name}")
                        continue
                    except Exception as e:
                        messagebox.showerror("Error", f"Error processing file {file_name}: {e}")
                        continue
        else:
            messagebox.showwarning("No Folder Loaded", "Please select a folder to load renders first.")



    def sort_treeview(self, col, reverse):
        """Sort Treeview columns when headers are clicked."""
        try:
            l = [(self.render_tree.set(k, col), k) for k in self.render_tree.get_children('')]
            try:
                l = [(float(re.sub('[^0-9.]', '', item[0])), item[1]) for item in l]
            except ValueError:
                pass  

            l.sort(reverse=reverse)

            for index, (val, k) in enumerate(l):
                self.render_tree.move(k, '', index)

            self.render_tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))
        except Exception as e:
            print(f"Error sorting column {col}: {e}")
  

    def open_render(self):
        """Open the selected render file in the default viewer (image or video)."""
        selected_item = self.render_tree.focus()
        if selected_item:
            file_path = self.render_file_paths.get(selected_item)
            if file_path and os.path.exists(file_path):
                try:
                    if sys.platform.startswith('darwin'):
                        subprocess.call(('open', file_path))  
                    elif sys.platform.startswith('win'):
                        os.startfile(file_path)  
                    elif sys.platform.startswith('linux'):
                        subprocess.call(('xdg-open', file_path)) 
                except Exception as e:
                    messagebox.showerror("Open Error", f"Could not open file: {e}")
            else:
                messagebox.showwarning("File Not Found", "The selected file does not exist.")
        else:
            messagebox.showwarning("No Selection", "Please select a render to open.")


            #---Browse Button Functions---
            

    def browse_render_directory(self):
        """Open a dialog to select a folder and display only PNG, JPEG, JPG, and MP4 files in the Render List."""
        folder_path = filedialog.askdirectory(initialdir=APPDATA_RENDER_PATH, title="Select Render Folder")
        if not folder_path:
            return  

        self.current_folder = folder_path
        self.save_render_folder_path(folder_path) 

        self.render_tree.delete(*self.render_tree.get_children())
        self.render_file_paths.clear()

        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            
            if os.path.isfile(file_path) and file_name.lower().endswith(('.png', '.jpeg', '.jpg', '.mp4')):
                try:
                    file_stats = os.stat(file_path)
                    file_date = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                    file_size = f"{file_stats.st_size / (1024 * 1024):.2f} MB"
                    file_extension = os.path.splitext(file_name)[1].lower()
                    if file_extension in ['.png', '.jpeg', '.jpg']:
                        with Image.open(file_path) as img:
                            resolution = f"{img.width}x{img.height}"
                    elif file_extension == '.mp4':
                        resolution = "N/A"
                    else:
                        resolution = "N/A"
                    
                    blender_version = "N/A" 

                    item_id = self.render_tree.insert(
                        "", 
                        "end", 
                        values=(file_name, file_size, resolution, file_date),
                        tags=('evenrow' if len(self.render_tree.get_children()) % 2 == 0 else 'oddrow',)
                    )

                    self.render_file_paths[item_id] = file_path

                except PermissionError:
                    messagebox.showwarning("Permission Denied", f"Cannot access file: {file_name}")
                    continue
                except Exception as e:
                    messagebox.showerror("Error", f"Error processing file {file_name}: {e}")
                    continue

        first_item = self.render_tree.get_children()
        if first_item:
            self.render_tree.selection_set(first_item[0])
            self.render_tree.focus(first_item[0])
            self.render_tree.event_generate("<<TreeviewSelect>>")
            

    def get_render_folder_path(self):
        """Reads and returns the render folder path from renderfolderpath.json, or sets a default if it doesn't exist."""
        try:
            with open(RENDERFOLDER_PATH, 'r') as file:
                data = json.load(file)
                render_path = data.get("render_folder_path", APPDATA_RENDER_PATH)
                print(f"Loaded render folder path: {render_path}")  
                return render_path
        except (FileNotFoundError, json.JSONDecodeError):
            print("No saved path found; using default path.")
            return APPDATA_RENDER_PATH

    def save_render_folder_path(self, path):
        """Saves the given render folder path to renderfolderpath.json."""
        try:
            with open(RENDERFOLDER_PATH, 'w') as file:
                json.dump({"render_folder_path": path}, file, indent=4)
            print(f"Render folder path saved successfully to {RENDERFOLDER_PATH}.")
        except Exception as e:
            print(f"Error saving render folder path: {e}")




    def display_selected_render(self, event):
        """Display the selected render in Render Preview, if it's an image, or play the video."""
        selected_item = self.render_tree.focus()
        if not selected_item:
            return

        file_path = self.render_file_paths.get(selected_item, None)
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("File Error", "The selected file does not exist.")
            self.preview_label.config(image='', text="No Preview Available")
            return

        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in [".jpeg", ".jpg", ".png"]:
            self.display_image_preview(file_path)
        elif file_extension == ".mp4":
            self.display_video_preview(file_path)
        else:
            self.preview_label.config(image='', text="Unsupported File Type")
            messagebox.showwarning("Unsupported File", "The selected file type is not supported for preview.")
        
        file_name = os.path.basename(file_path)
        self.current_render_name = file_name
        self.load_render_note(file_name)


    def display_image_preview(self, file_path):
        """Display the selected image in the Render Preview section."""
        try:
            img = Image.open(file_path)
            img.thumbnail((700, 600))  
            self.render_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.render_image, text="")
            
            if hasattr(self, 'video_player'):
                self.video_player.destroy()
        except Exception as e:
            messagebox.showerror("Image Load Error", f"Could not load image: {e}")
            self.preview_label.config(image='', text="No Preview Available")

    def display_video_preview(self, file_path):
        """Launch the selected video in the default system video player."""
        try:
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', file_path))
            elif sys.platform.startswith('win'):
                os.startfile(file_path)
            elif sys.platform.startswith('linux'):
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            messagebox.showerror("Video Playback Error", f"Could not play video: {e}")



    def load_render_note(self, file_name):
        """Load and display a note associated with a specific render file."""
        note_content = self.notes_data.get(file_name, "")
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert(tk.END, note_content)

    def save_current_note(self):
        """Save the note currently displayed in the notes section for the selected render."""
        if self.current_render_name:
            current_note = self.notes_text.get("1.0", tk.END).strip()
            self.notes_data[self.current_render_name] = current_note
            self.save_notes()
            messagebox.showinfo("Note Saved", f"Note for '{self.current_render_name}' has been saved.")
        else:
            messagebox.showwarning("No Render Selected", "Please select a render to save a note.")
           


    def delete_render(self):
        """Delete the selected render file from Render List and system if confirmed."""
        selected_item = self.render_tree.focus()
        if selected_item:
            render_name = self.render_tree.item(selected_item, 'values')[1]  
            file_path = self.render_file_paths.get(selected_item)
        
            if file_path and os.path.exists(file_path):
                confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{render_name}'?")
                if confirm:
                    try:
                        os.remove(file_path)  
                        self.render_tree.delete(selected_item)  
                        del self.render_file_paths[selected_item]  
                        messagebox.showinfo("File Deleted", f"{render_name} has been deleted.")
                    except Exception as e:
                        messagebox.showerror("Delete Error", f"Failed to delete {render_name}: {e}")
            else:
                messagebox.showwarning("File Not Found", "The selected file does not exist.")
        else:
            messagebox.showwarning("No Selection", "Please select a render to delete.")
            


           #---Notes Section Functions---        
           
    def _load_notes(self):
        """Load notes from JSON file or initialize as an empty dict if it doesn't exist."""
        if os.path.exists(NOTES_FILE_PATH):
            try:
                with open(NOTES_FILE_PATH, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                messagebox.showerror("Load Error", "Could not load notes due to a JSON error.")
                return {}
        return {}

    def save_notes(self):
        """Save notes to the JSON file with error handling."""
        try:
            with open(NOTES_FILE_PATH, 'w') as file:
                json.dump(self.notes_data, file, indent=4)
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save notes: {e}")

    def load_note_on_select(self, event):
        """Load the note associated with the selected render in the Render List."""
        selected_item = self.render_tree.focus()
        if selected_item:
            file_name = self.render_tree.item(selected_item, 'values')[0]
            self.current_render_name = file_name
            self.load_note_for_render(file_name)

    def load_note_on_select(self, event):
        """Load the note associated with the selected render in the Render List."""
        selected_item = self.render_tree.focus()
        if selected_item:
            file_name = self.render_tree.item(selected_item, 'values')[0]
            self.current_render_name = file_name
            self.load_note_for_render(file_name)

    def load_note_for_render(self, file_name):
        """Display the note for the specified render in the text widget."""
        note = self.notes_data.get(file_name, "")
        self.notes_text.delete('1.0', tk.END)
        self.notes_text.insert(tk.END, note)

    def save_current_note(self):
        """Save the current note for the selected render and update notes file."""
        if self.current_render_name:
            current_note = self.notes_text.get("1.0", tk.END).strip()
            self.notes_data[self.current_render_name] = current_note
            self.save_notes()
            messagebox.showinfo("Note Saved", f"Note for '{self.current_render_name}' has been saved.")
        else:
            messagebox.showwarning("No Render Selected", "Please select a render to save a note.")

#-------------------------------------------------------------------------------------------------------------------------------------------------




            
        #--------------------------------------------------------------------------------------------------------
        #---------------------------------------Main Menu--------------------------------------------------------
        #--------------------------------------------------------------------------------------------------------



        #-------------Main Menu GUI-------------

    def create_main_menu(self):
        """Creates the Main Menu tab and its widgets with an enhanced layout and minimalistic design."""

        # Main Menu Frame
        self.main_menu_frame = ttkb.Frame(self.main_menu_tab, padding=10)  
        self.main_menu_frame.grid(row=0, column=0, sticky="nsew")
        self.main_menu_tab.grid_columnconfigure(0, weight=1)
        self.main_menu_tab.grid_rowconfigure(0, weight=1)
        button_font_family = self.button_font_family
        button_font_size = self.button_font_size

        self.style.configure(
            'Custom.Large.TButton',
            font=(button_font_family, button_font_size),  
            padding=(10, 5)         
        )


        self.style.configure(
            'Custom.Large.TLabel',
            font=('Segoe UI', 14),
            padding=(5, 2)          
        )

        self.style.configure(
            'Green.TButton',
            font=(button_font_family, button_font_size),
            padding=(10, 5),
            background='#28a745',  
            foreground='white',
            borderwidth=0,        
            focuscolor='none'
        )

        self.style.map(
            'Green.TButton',
            background=[('active', '#218838'), ('!active', '#28a745')],
            foreground=[('disabled', 'grey'), ('!disabled', 'white')]
        )

        self.style.configure(
            'Custom.Small.TButton',
            font=('Segoe UI', 10),
            padding=(5, 2),
            borderwidth=0  
        )

        # Buttons Frame
        buttons_frame = ttkb.Frame(self.main_menu_frame)
        buttons_frame.grid(row=0, column=0, sticky="n", padx=(0, 10), pady=(0, 0))  

        self.launch_button_shadow = ttkb.Frame(
            buttons_frame,
            style='Green.TButton',
            width=15,
            borderwidth=0  
        )
        self.launch_button_shadow.grid(row=1, column=0, padx=(0, 0), pady=(60, 10), sticky="ew")

        self.launch_button = ttkb.Button(
            buttons_frame,
            text="Launch Blender",
            takefocus=False,
            command=self.launch_latest_blender,
            style='Green.TButton',
            bootstyle=SUCCESS,
            width=15
        )
        self.launch_button.grid(row=1, column=0, pady=(55, 5), sticky="ew", ipady=5)  

        self.create_project_button = ttkb.Button(
            buttons_frame,
            text="Create Project",
            takefocus=False,
            command=self.open_create_project_window,
            style='Custom.Large.TButton',
            bootstyle=SUCCESS,
            width=15
        )
        self.create_project_button.grid(row=2, column=0, pady=(10, 5), sticky="ew")

  
        self.update_button = ttkb.Button(
            buttons_frame,
            text="Check Updates",
            takefocus=False,
            command=self.check_for_updates,
            style='Custom.Large.TButton',
            bootstyle=PRIMARY,  
            width=15 
        )
        self.update_button.grid(row=3, column=0, pady=(10, 5), sticky="ew")

       
        self.cancel_button_main = ttkb.Button(
            buttons_frame,
            text="Cancel Download",
            takefocus=False,
            command=self.cancel_download_main,
            style='Custom.Large.TButton',
            bootstyle="danger",  
            width=15
        )
        self.cancel_button_main.grid(row=6, column=0, pady=(10, 5), sticky="ew")
        self.cancel_button_main.grid_remove() 

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttkb.Progressbar(
            self.main_menu_frame,
            orient="horizontal",
            length=200,  
            mode="determinate",
            variable=self.progress_var,
            bootstyle=WARNING
        )
        self.progress_bar.grid(row=2, column=0, pady=5)
        self.progress_bar.grid_remove()  
        


        self.blender_version_label = ttkb.Label(
            self.main_menu_frame,
            text="Blender Version: ",
            style='Custom.Large.TLabel',
            font=(button_font_family, 8)
        )
        self.blender_version_label.grid(row=0, column=0, sticky="nw", padx=(5, 0), pady=(5, 0))


        self.settings_button = ttkb.Button(
            buttons_frame,
            text="⚙️",
            takefocus=False,
            command=self.open_settings_window,
            style='Custom.Large.TButton',
            width=5  
        )
        self.settings_button.grid(row=5, column=0, pady=(10, 5), sticky="w") 
        
        self.help_button = ttkb.Button(
            buttons_frame,
            text="ℹ",
            takefocus=False,
            command=self.open_help_window, 
            style='Custom.Large.TButton',
            width=5  
        )
        self.help_button.grid(row=5, column=0, pady=(10, 5), sticky="e")  

        #Projects Frame
        projects_frame = ttkb.Frame(self.main_menu_frame)
        projects_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))  
        self.main_menu_frame.grid_columnconfigure(1, weight=3) 
        self.main_menu_frame.grid_rowconfigure(0, weight=1)

        projects_label_frame = ttkb.Frame(projects_frame)
        projects_label_frame.pack(anchor="nw", pady=(0, 5), fill='x')  

        projects_label = ttkb.Label(
            projects_label_frame,
            text="Recent Projects",
            style='Custom.Large.TLabel',
            font=(button_font_family, 15, 'bold')
        )
        projects_label.pack(side="left")

        self.work_hours_label = ttkb.Label(
            projects_label_frame,
            text="Work Time: -",
            style='Custom.Large.TLabel',
            font=(button_font_family, 15)
        )
        self.work_hours_label.pack(side="left", padx=(10, 0))  
        

        tree_frame = ttkb.Frame(projects_frame)
        tree_frame.pack(fill='both', expand=True)

        self.recent_projects_tree = ttkb.Treeview(
            tree_frame,
            columns=("Project Name", "Last Opened", "Path"),
            show="headings",
            height=15,  
            style="Custom.Treeview"
        )
        self.recent_projects_tree.heading("Project Name", text="Project Name")
        self.recent_projects_tree.heading("Last Opened", text="Last Opened")
        self.recent_projects_tree.heading("Path", text="Path")  
        self.recent_projects_tree.column("Project Name", anchor="w", width=300, minwidth=200, stretch=True)
        self.recent_projects_tree.column("Last Opened", anchor="center", width=150, minwidth=100, stretch=False)
        self.recent_projects_tree.column("Path", width=0, stretch=False) 
        self.recent_projects_tree.grid(row=0, column=0, sticky="nsew")

        self.recent_projects_tree.bind("<<TreeviewSelect>>", self.update_work_hours_label)
        self.project_times = self.load_project_times()

        scrollbar = ttkb.Scrollbar(tree_frame, orient="vertical", command=self.recent_projects_tree.yview)
        self.recent_projects_tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # projects_frame expands within main_menu_frame
        projects_frame.grid_columnconfigure(0, weight=1)
        projects_frame.grid_rowconfigure(0, weight=1)

        self.recent_projects_tree.bind("<Button-3>", self.show_context_menu)

        recent_projects = self.load_recent_projects()
        for project in recent_projects:
            project_name, last_opened, project_path = project
            self.recent_projects_tree.insert("", "end", values=(project_name, last_opened, project_path))

        self.recent_projects_tree.bind("<Double-1>", self.on_project_double_click)

        spacer_frame = ttkb.Frame(buttons_frame, height=20)
        spacer_frame.grid(row=10, column=0, pady=(180, 0))  # Adds space below buttons


        self.bm_version_label = ttkb.Label(
            buttons_frame,
            text=f"Blender Manager v{DEFAULT_SETTINGS['version']}",
            style='Custom.Large.TLabel',
            font=(self.button_font_family, 8)
        )
        self.bm_version_label.grid(row=11, column=0, sticky="s", padx=(10, 0), pady=(10, 5))  # Properly spaced at the bottom

        self.update_bm_version_label()

    def update_bm_version_label(self):
        """Update the Blender Manager version label based on the current and latest versions."""
        current_version = self.settings.get("version", "0.0.0")
        latest_version = self.bm_get_latest_version()

        version_text = f"Blender Manager v{current_version}"
    
        if latest_version and self.bm_is_new_version(current_version, latest_version):
            version_text += " ⚠️"
            self.bm_version_label.config(
                text=version_text,
                foreground="orange",
                cursor="hand2",
                font=(self.button_font_family, 8, "underline")
            )
            self.bm_version_label.bind("<Button-1>", self.on_version_label_click)
        else:
            self.bm_version_label.config(
                text=version_text,
                foreground="green",
                cursor="arrow",
                font=(self.button_font_family, 8)
            )
            self.bm_version_label.unbind("<Button-1>")
    def on_version_label_click(self, event):
        self.bm_check_for_updates_threaded()

    # -------- Create Project Menu -----------






    def open_create_project_window(self):
        """Opens a new window for creating a project."""
        self.create_project_button.config(state='disabled')
    
        self.create_project_window = tk.Toplevel(self)
        self.create_project_window.title("Create Project")
        self.create_project_window.geometry("800x600")
        self.create_project_window.resizable(False, False)
        self.center_window(self.create_project_window, 800, 600)
        self.create_project_window.iconbitmap(r"Assets/Images/bmng.ico")
        self.create_project_window.transient(self)
        self.create_project_window.focus_set()
        self.create_project_window.grab_set()

        window_frame = ttkb.Frame(self.create_project_window, padding=20)
        window_frame.pack(fill='both', expand=True)

        notebook = ttkb.Notebook(window_frame)
        notebook.pack(fill='both', expand=True)

        ref_images_tab = ttkb.Frame(notebook)
        notebook.add(ref_images_tab, text="Reference Images")

        base_mesh_tab = ttkb.Frame(notebook)
        notebook.add(base_mesh_tab, text="Base Mesh")

        settings_tab = ttkb.Frame(notebook)
        notebook.add(settings_tab, text="Settings")

        ref_label = ttkb.Label(ref_images_tab, text="Reference Images", font=('Segoe UI', 14, 'bold'))
        ref_label.pack(pady=(10, 0))
        warning_label = ttkb.Label(ref_images_tab, text="Images should be in the same size", font=('Segoe UI', 10, 'italic'))
        warning_label.pack(pady=(0, 10))

        self.reference_images = {}
        images_frame = ttkb.Frame(ref_images_tab)
        images_frame.pack(fill='both', expand=True, padx=20)

        positions = ['Front', 'Back', 'Right', 'Left', 'Top', 'Bottom']
        for idx, position in enumerate(positions):
            label = ttkb.Label(images_frame, text=f"{position} Image:")
            label.grid(row=idx * 2, column=0, sticky='e', pady=5)
            entry = ttkb.Entry(images_frame, width=50)
            entry.grid(row=idx * 2, column=1, pady=5, sticky='w')
            self.reference_images[position.lower()] = entry
            browse_button = ttkb.Button(images_frame, text="Browse", command=lambda pos=position.lower(): self.browse_image(pos))
            browse_button.grid(row=idx * 2, column=2, padx=5, pady=5)

        base_mesh_label = ttkb.Label(base_mesh_tab, text="Base Mesh", font=('Segoe UI', 14, 'bold'))
        base_mesh_label.pack(pady=(10, 10))
        base_mesh_frame = ttkb.Frame(base_mesh_tab)
        base_mesh_frame.pack(fill='both', expand=True, padx=20)

        mesh_label = ttkb.Label(base_mesh_frame, text="Select Base Mesh:")
        mesh_label.grid(row=0, column=0, sticky='e', pady=5)

        self.base_mesh_var = tk.StringVar()
        self.base_mesh_combobox = ttkb.Combobox(base_mesh_frame, textvariable=self.base_mesh_var, state='readonly')
        self.base_mesh_combobox['values'] = list(self.base_meshes.keys())
        self.base_mesh_combobox.grid(row=0, column=1, pady=5, sticky='w')

        add_base_mesh_button = ttkb.Button(base_mesh_frame, text="Add Base Mesh", takefocus=False, command=self.open_add_base_mesh_window)
        add_base_mesh_button.grid(row=1, column=1, pady=10, sticky='w')

        settings_label = ttkb.Label(settings_tab, text="Settings", font=('Segoe UI', 14, 'bold'))
        settings_label.pack(pady=(10, 10))

        settings_frame = ttkb.LabelFrame(settings_tab, text="Project Settings", padding=10)
        settings_frame.pack(fill='both', expand=True, padx=20)

        self.add_light_var = tk.BooleanVar()
        add_light_checkbox = ttkb.Checkbutton(settings_frame, text="Add Light", variable=self.add_light_var)
        add_light_checkbox.grid(row=0, column=0, sticky='w', padx=10, pady=5)

        self.add_camera_var = tk.BooleanVar()
        add_camera_checkbox = ttkb.Checkbutton(settings_frame, text="Add Camera", variable=self.add_camera_var)
        add_camera_checkbox.grid(row=1, column=0, sticky='w', padx=10, pady=5)

        self.activate_autosaver_var = tk.BooleanVar()
        activate_autosaver_checkbox = ttkb.Checkbutton(
            settings_frame,
            text="Enable Autosave",
            variable=self.activate_autosaver_var,
            command=self.toggle_autosave_options
        )
        activate_autosaver_checkbox.grid(row=2, column=0, sticky='w', padx=10, pady=5)

        self.autosave_interval_var = tk.IntVar(value=300) 
        interval_label = ttkb.Label(settings_frame, text="Autosave Interval (seconds):")
        interval_label.grid(row=3, column=0, sticky='w', padx=10, pady=5)

        self.interval_entry = ttkb.Entry(settings_frame, textvariable=self.autosave_interval_var, state='disabled')
        self.interval_entry.grid(row=3, column=1, sticky='w', padx=10, pady=5)

        interval_options = {
            "1 Minute": 60,
            "5 Minutes": 300,
            "10 Minutes": 600,
            "30 Minutes": 1800,
            "1 Hour": 3600,
            "2 Hours": 7200,
            "3 Hours": 10800,
            "4 Hours": 14400,
            "5 Hours": 18000,
            "6 Hours": 21600,
        }

        self.interval_combobox = ttkb.Combobox(
            settings_frame,
            values=list(interval_options.keys()),
            state='disabled'
        )
        self.interval_combobox.set("5 Minutes") 
        self.interval_combobox.grid(row=3, column=2, sticky='w', padx=10, pady=5)

        def update_interval_entry(event=None):
            selected_interval = interval_options[self.interval_combobox.get()]
            self.autosave_interval_var.set(selected_interval)

        self.interval_combobox.bind("<<ComboboxSelected>>", update_interval_entry)


        default_directory = os.path.expanduser("~/.BlenderManager") 
        self.autosave_directory_var = tk.StringVar()
        self.autosave_directory_var.set(default_directory)  

        directory_label = ttkb.Label(settings_frame, text="Autosave Directory:")
        directory_label.grid(row=4, column=0, sticky='w', padx=10, pady=5)

        self.directory_entry = ttkb.Entry(
            settings_frame,
            textvariable=self.autosave_directory_var,
            width=30,
            state='readonly'
        )
        self.directory_entry.grid(row=4, column=1, sticky='w', padx=10, pady=5)

        browse_directory_button = ttkb.Button(
            settings_frame,
            text="Browse",
            command=self.browse_autosave_directory,
            state='disabled'
        )
        browse_directory_button.grid(row=4, column=2, padx=10, pady=5)

        self.autosave_unique_names_var = tk.BooleanVar()
        self.unique_names_checkbox = ttkb.Checkbutton(
            settings_frame,
            text="Save as Different Files Each Time",
            variable=self.autosave_unique_names_var,
            state='disabled'
        )
        self.unique_names_checkbox.grid(row=5, column=0, sticky='w', padx=10, pady=5, columnspan=2)




        self.autosave_directory_var = tk.StringVar()
        directory_label = ttkb.Label(settings_frame, text="Autosave Directory:")
        directory_label.grid(row=4, column=0, sticky='e', pady=5)

        self.directory_entry = ttkb.Entry(settings_frame, textvariable=self.autosave_directory_var, width=30, state='disabled')
        self.directory_entry.grid(row=4, column=1, sticky='w', pady=5)

        self.browse_directory_button = ttkb.Button(settings_frame, text="Browse", command=self.browse_autosave_directory, state='disabled')
        self.browse_directory_button.grid(row=4, column=2, padx=5, pady=5)

        self.create_button = ttkb.Button(self.create_project_window, text="Create Project", takefocus=False, command=self.create_project)
        self.create_button.pack(pady=10)
        


        self.create_project_window.protocol("WM_DELETE_WINDOW", self.on_window_close)




    def toggle_autosave_options(self):
        """Enable or disable autosave options based on the checkbox state."""
        default_directory = os.path.expanduser("~/.BlenderManager")

        if self.activate_autosaver_var.get():
            self.interval_entry.config(state='readonly')
            self.interval_combobox.config(state='readonly')
            self.directory_entry.config(state='readonly')
            self.browse_directory_button.config(state='normal')
            self.unique_names_checkbox.config(state='normal')

            if not self.autosave_directory_var.get():  
                self.autosave_directory_var.set(default_directory)
        else:
            self.interval_entry.config(state='disabled')
            self.interval_combobox.config(state='disabled')
            self.directory_entry.config(state='disabled')
            self.browse_directory_button.config(state='disabled')
            self.unique_names_checkbox.config(state='disabled')

            self.autosave_directory_var.set("")




    def browse_autosave_directory(self):
        """Opens a file dialog to select an autosave directory."""
        directory = filedialog.askdirectory(title="Select Autosave Directory")
        if directory:
            self.autosave_directory_var.set(directory)

    def on_window_close(self):
        self.create_project_button.config(state='normal')
        self.create_project_window.destroy()  # Close the window


    def browse_image(self, position):
        """Opens a file dialog to select an image for the given position."""
        file_path = filedialog.askopenfilename(
            title=f"Select {position.capitalize()} Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if file_path:
            self.reference_images[position].delete(0, tk.END)
            self.reference_images[position].insert(0, file_path)

    def create_project(self):
        """Collects the input data, writes them to a JSON file, and initiates the project creation."""

        self.create_button.config(state="disabled", text="Loading...")

        def perform_project_creation():
            try:
                images = {}
                for position, entry in self.reference_images.items():
                    path = entry.get()
                    if path:
                        images[position] = path


                base_mesh_name = self.base_mesh_var.get()
                base_mesh_path = self.base_meshes.get(base_mesh_name, '')
                add_light = self.add_light_var.get()
                add_camera = self.add_camera_var.get()
                activate_autosave = self.activate_autosaver_var.get()
                autosave_interval = self.autosave_interval_var.get()
                autosave_directory = self.autosave_directory_var.get()
                autosave_unique_names = self.autosave_unique_names_var.get()
                data = {
                    'reference_images': images,
                    'base_mesh': {
                        'name': base_mesh_name,
                        'path': base_mesh_path
                    },
                    'add_light': add_light,
                    'add_camera': add_camera,
                    'activate_autosave': activate_autosave,
                    'autosave_interval': autosave_interval,
                    'autosave_directory': autosave_directory,
                    'autosave_unique_names': autosave_unique_names
                }

                home_dir = os.path.expanduser('~')
                settings_dir = os.path.join(home_dir, '.BlenderManager', 'mngaddon')
                settings_file = os.path.join(settings_dir, 'settings.json')

                os.makedirs(settings_dir, exist_ok=True)

                with open(settings_file, 'w') as f:
                    json.dump(data, f)

                time.sleep(2)

                self.launch_latest_blender()
            finally:
                self.create_button.config(state="normal", text="Create Project")
                self.create_project_window.destroy()

        threading.Thread(target=perform_project_creation, daemon=True).start()




    #-------------Add Base Mesh Window-----------


    def open_add_base_mesh_window(self):
        """Opens a window to add a new base mesh."""
        self.add_base_mesh_window = tk.Toplevel(self.create_project_window)
        self.add_base_mesh_window.title("Add Base Mesh")

        self.add_base_mesh_window.geometry("400x200")
        self.add_base_mesh_window.resizable(False, False)  
        self.center_window(self.add_base_mesh_window, 400, 200)
        self.add_base_mesh_window.iconbitmap(r"Assets/Images/bmng.ico")

        self.add_base_mesh_window.transient(self.create_project_window) 
        self.add_base_mesh_window.grab_set()  
        self.add_base_mesh_window.focus()  

        frame = ttkb.Frame(self.add_base_mesh_window, padding=20)
        frame.pack(fill='both', expand=True)

        name_label = ttkb.Label(frame, text="Base Mesh Name:")
        name_label.grid(row=0, column=0, sticky='e', pady=5)

        self.new_base_mesh_name = tk.StringVar()
        name_entry = ttkb.Entry(frame, textvariable=self.new_base_mesh_name)
        name_entry.grid(row=0, column=1, pady=5, sticky='w')

        path_label = ttkb.Label(frame, text="Base Mesh Path:")
        path_label.grid(row=1, column=0, sticky='e', pady=5)

        self.new_base_mesh_path = tk.StringVar()
        path_entry = ttkb.Entry(frame, textvariable=self.new_base_mesh_path, width=30)
        path_entry.grid(row=1, column=1, pady=5, sticky='w')

        browse_button = ttkb.Button(frame, text="Browse", takefocus=False, command=self.browse_base_mesh)
        browse_button.grid(row=1, column=2, padx=5, pady=5)

        add_button = ttkb.Button(frame, text="Add", takefocus=False, command=self.add_new_base_mesh)
        add_button.grid(row=2, column=1, pady=10, sticky='e')

        self.create_project_window.wait_window(self.add_base_mesh_window)
        

        #--Functions---

    def browse_base_mesh(self):
        """Opens a file dialog to select a base mesh file."""
        file_path = filedialog.askopenfilename(
            title="Select Base Mesh File",
            filetypes=[("Mesh Files", "*.obj;*.fbx;*.stl")]
        )
        if file_path:
            self.new_base_mesh_path.set(file_path)

    def add_new_base_mesh(self):
        """Adds the new base mesh to the combobox and saves it to the JSON file."""
        name = self.new_base_mesh_name.get()
        path = self.new_base_mesh_path.get()

        if name and path:
            if name not in self.base_meshes:
                self.base_meshes[name] = path
            
                self.base_mesh_combobox['values'] = list(self.base_meshes.keys())

                try:
                    with open(BASE_MESH_PATH, 'w') as file:
                        json.dump(self.base_meshes, file, indent=4)
                    messagebox.showinfo("Success", "Base mesh saved successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save to JSON file: {str(e)}")

                self.add_base_mesh_window.destroy()
            else:
                messagebox.showwarning("Warning", "This base mesh name already exists.")
        else:
            messagebox.showwarning("Warning", "Please provide both name and path for the base mesh.")

#---------------------------------------------------------------------------------------------------------------------------------





    #-----------Help Menu----------------
    


    def open_help_window(self):
        """Opens the help window with Documentation, Credits, and Donate tabs."""
        self.help_window = tk.Toplevel(self)
        self.help_button.configure(state='disabled')
        self.help_window.title("Help")

        self.help_window.geometry("600x400")
        self.help_window.resizable(False, False)
        self.center_window(self.help_window, 600, 400)
        self.help_window.iconbitmap(r"Assets/Images/bmng.ico")

        self.help_window.transient(self)
        self.help_window.grab_set()
        self.help_window.focus()

        frame = ttkb.Frame(self.help_window, padding=10)
        frame.pack(fill='both', expand=True)

        notebook = ttkb.Notebook(frame)
        notebook.pack(fill='both', expand=True)

        doc_tab = ttkb.Frame(notebook)
        notebook.add(doc_tab, text="Documentation")

        doc_label = ttkb.Label(doc_tab, text="Blender Manager Documentation", font=('Segoe UI', 8, 'bold'))
        doc_label.pack(pady=(10, 0))

        doc_text = tk.Text(doc_tab, wrap='word', padx=10, pady=10)
        doc_text.insert('1.0', """Overview:

Blender Manager is a comprehensive desktop application that allows users to:

Manage multiple Blender versions and installations.
Simplify project creation and organization.
Automatically track project working times.
Manage reference images and base meshes for streamlined modeling.
Provide a UI for managing renders with notes and previews.
Utilize an autosave feature to prevent data loss.
Integrate with Blender through a custom addon for enhanced features.
Manage addons for every different Blender versions easily.

For detailed documentation:
https://github.com/verlorengest/BlenderManager                       

For Feedbacks and error logs:
majinkaji@proton.me                        

For further details, please refer to the user manual or visit our support site.""")
        doc_text.config(state='disabled')
        doc_text.pack(fill='both', expand=True)

        credits_tab = ttkb.Frame(notebook)
        notebook.add(credits_tab, text="Credits")

        credits_label = ttkb.Label(
            credits_tab, 
            text="Developed by verlorengest",
            font=('Segoe UI', 10, 'italic'),
            anchor='center'
        )
        credits_label.pack(pady=(150, 10)) 

        donate_tab = ttkb.Frame(notebook)
        notebook.add(donate_tab, text="Donate")

        donate_frame = ttkb.Frame(donate_tab, padding=20)
        donate_frame.pack(expand=True)  

        donate_label = ttkb.Label(
            donate_frame,
            text=(
                "This app is completely free.\n"
                "But I need some support to apply more useful features such as:\n"
                "\n"
                "- Cloud storage for projects and addons for more portability,\n"
                "- Multi-artist collaboration features,\n"
                "- Marketplace for addons and 3D models to add your project easily.\n"
                "\n"
                "If you enjoy using this application,\n"
                "consider supporting! ~ ♡"
            ),
            anchor="center"
        )
        donate_label.pack(pady=(10, 20))

        donate_button = ttkb.Button(donate_frame, text="Donate Now", takefocus=False, command=self.redirect_to_donation_page)
        donate_button.pack()
        def on_close():
            self.help_button.configure(state='normal')
            self.help_window.destroy()
            del self.help_window
            
        self.help_window.protocol("WM_DELETE_WINDOW", on_close)

        self.wait_window(self.help_window)
    
    def redirect_to_donation_page(self):
        """Redirects the user to the donation page."""
        import webbrowser
        webbrowser.open("https://verlorengest.gumroad.com/l/blendermanager")


        #-----------------------------------------------------------------------------------------------------------------------------------


            # -------- Main Menu Functions -----------



    def update_project_times(self):
        """Update the project_times attribute with the latest data."""
        self.project_times = self.load_project_times()


    def load_project_times(self):
        """Load work time data from the project_time.json file."""
        time_file = PROJECT_RUNTIME_PATH
        try:
            with open(time_file, 'r') as file:
                project_time_data = json.load(file)
            
            def convert_seconds(time):
                hours = int(time // 3600)
                minutes = int((time % 3600) // 60)
                seconds = int(time % 60)
                return f"{hours} H, {minutes} M, {seconds} S"

            return {os.path.basename(path): convert_seconds(time) for path, time in project_time_data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


    def update_work_hours_label(self, event):
        """Update the work hours label based on the selected project in Treeview."""
        selected_item = self.recent_projects_tree.selection()
        if selected_item:
            project_name = self.recent_projects_tree.item(selected_item[0], "values")[0]  
            work_hours = self.project_times.get(project_name, "-")
            self.work_hours_label.config(text=f"Work Time: {work_hours}")
        else:
            self.work_hours_label.config(text="Work Time: -")





    def show_progress_bar(self):
        """Show progress bar and disable buttons."""
        self.progress_bar.grid()  
        self.launch_button.state(['disabled'])  
        self.update_button.state(['disabled'])


    def hide_progress_bar(self):
        """Hide progress bar and enable buttons."""
        self.progress_bar.grid_remove() 
        self.launch_button.state(['!disabled'])  
        self.update_button.state(['!disabled'])

        
    def cancel_download_main(self):
        """Set the cancel event to stop the download."""
        self.cancel_event_main.set()  
        messagebox.showinfo("Download Cancelled", "The download has been cancelled.")




    def show_context_menu(self, event):
        """Show a right-click context menu with Quick View and Delete Project options for recent projects."""
        menu = tk.Menu(self.recent_projects_tree, tearoff=0)
        menu.add_command(label="Delete Project", command=self.delete_selected_project)
        menu.post(event.x_root, event.y_root)

        



    def get_selected_project_path(self):
        """Gets the selected .blend file path from the recent projects list based on project directory."""
        selected_item = self.recent_projects_tree.focus()
        if selected_item:
            project_path = self.recent_projects_tree.item(selected_item, "values")[2]  
            return project_path if project_path.lower().endswith(".blend") else f"{project_path}.blend"
        return None

    def delete_selected_project(self):
        """Delete the selected project file from the file system and remove it from the recent projects list."""
        selected_item = self.recent_projects_tree.focus()
        if selected_item:
            project_path = self.recent_projects_tree.item(selected_item, "values")[2] 
            project_name = self.recent_projects_tree.item(selected_item, "values")[0]
        
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{project_name}'?")
            if confirm:
                try:
                    os.remove(project_path)
                    messagebox.showinfo("Deleted", f"{project_name} has been deleted successfully.")
                
                    self.recent_projects_tree.delete(selected_item)
                
                except Exception as e:
                    print(f"Failed to delete {project_name}: {e}")
                    messagebox.showerror("Delete Error", f"Could not delete {project_name}. Error: {e}")
        else:
            messagebox.showwarning("No Selection", "Please select a project to delete.")





    def load_recent_projects(self):
        """Loads recent projects from Blender's recent-files.txt for the detected Blender version."""
        blender_foundation_path = os.path.join(os.getenv('APPDATA'), "Blender Foundation", "Blender")
        blender_version = self.get_blender_folder()
    
        if not blender_version:
            print("No Blender version detected for loading recent files.")
            return []

        recent_files_path = os.path.join(blender_foundation_path, blender_version, "config", "recent-files.txt")
        if os.path.exists(recent_files_path):
            print(f"Found recent-files.txt at: {recent_files_path}")
        else:
            print(f"recent-files.txt not found at expected path: {recent_files_path}")
            return []

        recent_projects = []
        try:
            with open(recent_files_path, 'r', encoding='utf-8') as f:
                for line in f:
                    project_path = line.strip()
                    if os.path.exists(project_path):
                        project_name = os.path.basename(project_path)
                        last_opened = datetime.fromtimestamp(os.path.getmtime(project_path)).strftime('%Y-%m-%d')
                        recent_projects.append((project_name, last_opened, project_path))
                    else:
                        print(f"Project file not found, skipping: {project_path}")          
        except Exception as e:
            print(f"Error loading recent projects: {e}")

        return recent_projects




    def get_blender_folder(self):
        """Finds the latest Blender version from folders in the Blendermanager/blender directory."""
        blender_base_path = os.path.join(os.path.expanduser("~"), ".BlenderManager", "blender")

        latest_version = None

        if os.path.exists(blender_base_path):
            for entry in os.listdir(blender_base_path):
                entry_path = os.path.join(blender_base_path, entry)
                if os.path.isdir(entry_path):
                    match = re.match(r"(\d+\.\d+)", entry)
                    if match:
                        folder_version = match.group(1)
                        if not latest_version or list(map(int, folder_version.split('.'))) > list(map(int, latest_version.split('.'))):
                            latest_version = folder_version
                            print(f"Blender version detected from folder: {latest_version}")
        else:
            print("Blender directory not found.")

        if latest_version:
            print(f"Blender version for recent files: {latest_version}")
        else:
            print("No Blender version detected in .Blendermanager/blender directory.")

        return latest_version





    def get_latest_blender_version(self):
        """Finds the latest Blender version in X.Y.Z format from the release page."""
        base_url = "https://download.blender.org/release/"
        try:
            response = requests.get(base_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            major_versions = []
            for link in soup.find_all('a', href=True):
                href = link['href'].strip('/')
                match = re.match(r'Blender(\d+)\.(\d+)', href)
                if match:
                    x_version = int(match.group(1))
                    y_version = int(match.group(2))
                    major_versions.append((x_version, y_version))

            if not major_versions:
                print("No major Blender versions found on the release page.")
                messagebox.showerror("Version Error", "No Blender versions were found on the release page.")
                return None, None

            latest_major_version = max(major_versions, key=lambda v: (v[0], v[1]))
            x, y = latest_major_version
            major_version_url = f"{base_url}Blender{x}.{y}/"

            response = requests.get(major_version_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            minor_versions = []
            for link in soup.find_all('a', href=True):
                href = link['href'].strip('/')
                match = re.match(r'blender-(\d+)\.(\d+)\.(\d+)-windows-x64\.zip', href)
                if match and int(match.group(1)) == x and int(match.group(2)) == y:
                    z_version = int(match.group(3))
                    minor_versions.append(z_version)

            if not minor_versions:
                print("No minor Blender versions found in the specified major version directory.")
                messagebox.showerror("Version Error", "No specific Blender version found in the major directory.")
                return None, None

            latest_minor_version = max(minor_versions)
            version_number = f"{x}.{y}.{latest_minor_version}"
            download_url = f"{major_version_url}blender-{version_number}-windows-x64.zip"

            return version_number, download_url

        except requests.RequestException as e:
            print(f"Network error while fetching latest Blender version: {e}")
            messagebox.showerror("Network Error", "Failed to connect to the Blender release page.")
            return None, None


    def download_blender_zip(self, download_url):
        """Downloads the Blender zip file to a temporary location with progress."""
        self.show_progress_bar()
        self.cancel_button_main.grid()
        temp_dir = tempfile.mkdtemp()
        temp_zip_path = os.path.join(temp_dir, 'blender_latest.zip')
        self.cancel_event_main.clear()  
    
        try:
            response = requests.get(download_url, stream=True)
            total_length = response.headers.get('content-length')
            if total_length is None:
                self.progress_var.set(100) 
            else:
                downloaded = 0
                total_length = int(total_length)
                with open(temp_zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=4096):
                        if self.cancel_event_main.is_set(): 
                            raise Exception("Download cancelled by user.")
                    
                        downloaded += len(chunk)
                        f.write(chunk)
                        self.progress_var.set((downloaded / total_length) * 100) 
            return temp_zip_path
        except Exception as e:
            print(f"Error downloading Blender update: {e}")
            shutil.rmtree(temp_dir)
            return None
        finally:
            self.hide_progress_bar()
            self.cancel_button_main.grid_remove()


    

    def update_blender_files(self, temp_zip_path):
        self.disable_buttons()
        """Extracts Blender files from the downloaded zip to the install directory, replacing old files."""
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            temp_extract_dir = tempfile.mkdtemp()  
            zip_ref.extractall(temp_extract_dir) 
            
            extracted_items = os.listdir(temp_extract_dir)
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_extract_dir, extracted_items[0])):
                extracted_blender_folder = os.path.join(temp_extract_dir, extracted_items[0])
            else:
                extracted_blender_folder = temp_extract_dir  


            if os.path.exists(self.blender_install_dir):
                shutil.rmtree(self.blender_install_dir)
            os.makedirs(self.blender_install_dir, exist_ok=True) 

            for item in os.listdir(extracted_blender_folder):
                source_path = os.path.join(extracted_blender_folder, item)
                dest_path = os.path.join(self.blender_install_dir, item)
                
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, dest_path)
                else:
                    shutil.copy2(source_path, dest_path)
        
        shutil.rmtree(temp_extract_dir)
        os.remove(temp_zip_path)
        self.enable_buttons()


    def show_progress_bar_threadsafe(self):
        self.main_menu_frame.after(0, self.show_progress_bar)

    def hide_progress_bar_threadsafe(self):
        self.main_menu_frame.after(0, self.hide_progress_bar)
        


    def disable_buttons(self):
        self.launch_button.config(text="Wait Please...", state='disabled')
        self.create_project_button.config(state='disabled')
        self.update_button.config(state='disabled')

    def enable_buttons(self):
        self.launch_button.config(state='normal', text="Launch Blender")
        self.create_project_button.config(state='normal')
        self.update_button.config(state='normal')



    def keep_observer_running(self, observer):
        """Keeps the observer running indefinitely until the program exits."""
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def refresh_recent_projects(self):
        """Refreshes the recent projects list in the Treeview."""

        for item in self.recent_projects_tree.get_children():
            self.recent_projects_tree.delete(item)

        recent_projects = self.load_recent_projects()
        for project in recent_projects:
            project_name, last_opened, project_path = project
            self.recent_projects_tree.insert("", "end", values=(project_name, last_opened, project_path))



    def launch_latest_blender(self):
        """Launch Blender if installed, or install it if not."""
        def launch():
            
            blender_exe = os.path.join(self.blender_install_dir, 'blender.exe')
            settings_file = os.path.join(os.path.expanduser('~'), '.BlenderManager', 'mngaddon', 'settings.json')

            if os.path.isfile(blender_exe):
                try:
                    self.launch_button.config(text="Running", state='disabled')
                    self.update_button.config(text="Check Updates", state='disabled')

                    process = subprocess.Popen([blender_exe], creationflags=subprocess.CREATE_NO_WINDOW)

                    def monitor_process():
                        process.wait()  


                        self.main_menu_frame.after(0, self.update_project_times)
                        self.main_menu_frame.after(0, self.refresh_recent_projects)
                        self.main_menu_frame.after(0, lambda: self.launch_button.config(text="Launch Blender", state='normal'))
                        self.main_menu_frame.after(0, lambda: self.update_button.config(text="Check Updates", state='normal'))
                        self.create_project_button.config(state='active')                       
                        self.main_menu_frame.after(0, self.load_project_times)
                        if os.path.exists(settings_file):
                            os.remove(settings_file)
                            print("settings.json deleted after Blender closed.")

                    threading.Thread(target=monitor_process, daemon=True).start()

                except Exception as e:
                    self.main_menu_frame.after(0, lambda: messagebox.showerror("Launch Error", f"Failed to launch Blender:\n{e}"))
            else:
                self.show_install_dialog()

        threading.Thread(target=launch, daemon=True).start()

    def show_install_dialog(self):
        """Show a custom, improved dialog with Yes, No, and Already Installed options."""
        dialog = tk.Toplevel(self)
        dialog.title("Blender is Not Installed")
        dialog.geometry("350x180")
        dialog.resizable(False, False)
        dialog.iconbitmap(r"Assets/Images/bmng.ico")
        dialog.update_idletasks()  
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.transient(self)  
        dialog.grab_set()  

        label = tk.Label(
            dialog,
            text="Blender is not installed. Would you like to install it?",
            font=("Segoe UI", 11)
        )
        label.pack(pady=20)

        button_frame = tk.Frame(dialog, bg="#f7f7f7")
        button_frame.pack(pady=10)

        def on_enter(button, hover_color):
            button['bg'] = hover_color

        def on_leave(button, original_color):
            button['bg'] = original_color

        yes_button = tk.Button(
            button_frame,
            text="Yes",
            command=lambda: self.install_blender(dialog),
            font=("Segoe UI", 10),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            relief="flat",
            width=10
        )
        yes_button.grid(row=0, column=0, padx=10)
        yes_button.bind("<Enter>", lambda e: on_enter(yes_button, "#45a049"))
        yes_button.bind("<Leave>", lambda e: on_leave(yes_button, "#4CAF50"))

        no_button = tk.Button(
            button_frame,
            text="No",
            command=dialog.destroy,
            font=("Segoe UI", 10),
            bg="#f44336",
            fg="white",
            activebackground="#e53935",
            activeforeground="white",
            relief="flat",
            width=10
        )
        no_button.grid(row=0, column=1, padx=10)
        no_button.bind("<Enter>", lambda e: on_enter(no_button, "#e53935"))
        no_button.bind("<Leave>", lambda e: on_leave(no_button, "#f44336"))

        already_installed_button = tk.Button(
            button_frame,
            text="Already Installed",
            command=lambda: self.handle_existing_blender(dialog), 
            font=("Segoe UI", 10),
            bg="#2196F3",
            fg="white",
            activebackground="#1976d2",
            activeforeground="white",
            relief="flat",
            width=15
        )
        already_installed_button.grid(row=0, column=2, padx=10)
        already_installed_button.bind("<Enter>", lambda e: on_enter(already_installed_button, "#1976d2"))
        already_installed_button.bind("<Leave>", lambda e: on_leave(already_installed_button, "#2196F3"))



    def install_blender(self, dialog):
        """Handle the installation of Blender."""
        dialog.destroy()  

        def install():
            latest_version, download_url = self.get_latest_blender_version()
            if latest_version and download_url:
                self.disable_buttons()
                self.show_progress_bar_threadsafe()
                temp_zip_path = self.download_blender_zip(download_url)
                if temp_zip_path:
                    self.update_blender_files(temp_zip_path)
                    self.main_menu_frame.after(0, lambda: messagebox.showinfo("Installation Complete", "Blender has been installed successfully."))
                self.hide_progress_bar_threadsafe()
                self.enable_buttons()

        threading.Thread(target=install, daemon=True).start()




    def handle_existing_blender(self, dialog):
        """Handle the process of selecting an existing Blender installation and moving its contents."""

        def select_and_validate_folder():
            while True:
                selected_folder = filedialog.askdirectory(title="Select Blender Installation Folder")
                if not selected_folder:
                    return None  

                blender_exe_path = os.path.join(selected_folder, "blender.exe")
                if os.path.isfile(blender_exe_path):
                    return selected_folder  
                else:
                    messagebox.showerror("Invalid Folder", "The selected folder does not contain blender.exe. Please try again.")

        def transfer_files(source_folder, target_folder):
            try:
                
                if os.path.exists(target_folder):
                    shutil.rmtree(target_folder)
                os.makedirs(target_folder)

                for item in os.listdir(source_folder):
                    source_item = os.path.join(source_folder, item)
                    target_item = os.path.join(target_folder, item)
                    if os.path.isdir(source_item):
                        shutil.copytree(source_item, target_item)
                    else:
                        shutil.copy2(source_item, target_item)

                shutil.rmtree(source_folder)


                self.main_menu_frame.after(0, self.enable_buttons)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while transferring files: {e}")
            finally:
                self.main_menu_frame.after(0, hide_loading_bar)



        def show_loading_bar():
            self.loading_bar = tk.Label(self.main_menu_frame, text="Loading...", font=("Segoe UI", 10))
            self.loading_bar.grid(row=3, column=0, pady=10)  

        def hide_loading_bar():
            if hasattr(self, 'loading_bar'):
                self.loading_bar.destroy()

        dialog.destroy()

        self.disable_buttons()
        show_loading_bar()

        selected_folder = select_and_validate_folder()
        if not selected_folder:
            hide_loading_bar() 
            self.enable_buttons()  
            return

        target_folder = BLENDER_PATH

        threading.Thread(target=transfer_files, args=(selected_folder, target_folder), daemon=True).start()









    def check_for_updates(self):
        from packaging.version import Version, InvalidVersion
        """Checks for Blender updates and installs if a new version is available."""

        self.disable_buttons()
    
        def update_process():
            try:
                blender_exe = os.path.join(self.blender_install_dir, 'blender.exe')
                if not os.path.isfile(blender_exe):
                    messagebox.showwarning("Blender Not Installed", "Blender is not installed.")
                    return

                installed_version_str = self.get_installed_blender_version()
                latest_version_str, download_url = self.get_latest_blender_version()
                

                if not latest_version_str or not download_url:
                    messagebox.showerror("Error", "Failed to check for the latest version.")
                    return

                if not installed_version_str:
                    messagebox.showerror("Error", "Failed to retrieve the installed Blender version.")
                    return

                try:
                    installed_version = Version(installed_version_str)
                    latest_version = Version(latest_version_str)
                except InvalidVersion:
                    messagebox.showerror("Error", "Invalid version format detected.")
                    return
                version_text = f"Blender Version: {installed_version}"
                print(f"Installed Version: {installed_version}")
                print(f"Latest Version: {latest_version}")
                self.blender_version_label.config(text=version_text)

                force_install_latest = False

                blender_dir = os.path.join(os.path.expanduser("~"), ".BlenderManager", "blender")
                if os.path.exists(blender_dir):
                    for entry in os.listdir(blender_dir):
                        entry_path = os.path.join(blender_dir, entry)
                        if os.path.isdir(entry_path):  
                            try:
                                entry_version = Version(entry)
                                print(f"Found Version Directory: {entry_version}")
                                if entry_version > latest_version:
                                    print("Unstable version detected!")
                                    user_response = messagebox.askyesno(
                                        "Unstable Version Detected",
                                        "You are using an unstable version of Blender, which cannot be updated from here.\n"
                                        "Do you want to install the latest stable version?"
                                    )
                                    if user_response:
                                        force_install_latest = True  
                                    else:
                                        return  
                                    break  
                            except InvalidVersion:
                                print(f"Skipping non-version directory: {entry}")
                                continue  

                if installed_version >= latest_version and not force_install_latest:
                    messagebox.showinfo("No Updates", "Blender is already up-to-date.")
                else:
                    self.show_progress_bar_threadsafe()
                
                    temp_zip_path = self.download_blender_zip(download_url)
                    if temp_zip_path:
                        self.update_blender_files(temp_zip_path)
                        self.run_automatic_addon_setup
                        messagebox.showinfo("Update Complete", "Blender has been updated successfully.")
                    self.hide_progress_bar_threadsafe()
            except Exception as e:
                print(f"Error during update check: {e}")
            finally:
                self.enable_buttons()

        threading.Thread(target=update_process, daemon=True).start()




        


    def auto_update(self):
        from packaging.version import Version, InvalidVersion
        """Checks for Blender updates and installs if a new version is available."""

        def update_process():
            blender_exe = os.path.join(self.blender_install_dir, 'blender.exe')
            if not os.path.isfile(blender_exe):
                print("Blender is not installed")
                return

            installed_version_str = self.get_installed_blender_version()
            latest_version_str, download_url = self.get_latest_blender_version()

            if not latest_version_str or not download_url:
                print("Error", "Failed to check for the latest version.")
                return

            try:
                installed_version = Version(installed_version_str)
                latest_version = Version(latest_version_str)
                version_text = f"Blender Version: {installed_version}"
                self.blender_version_label.config(text=version_text)
            except InvalidVersion:
                print("Invalid version format detected.")
                return

            print("Checking for updates...")
            if installed_version > latest_version:
                print("You are using an unstable version, which cannot be updated from here.")

                return  

            if installed_version == latest_version:
                print("No new updates.")
                return 

            self.after(0, self.show_progress_bar_threadsafe) 

            temp_zip_path = self.download_blender_zip(download_url)
            if temp_zip_path:
                self.update_blender_files(temp_zip_path)
                self.run_automatic_addon_setup
                self.after(0, lambda: messagebox.showinfo("Update Complete", "Blender has been updated successfully.")) 

            self.after(0, self.hide_progress_bar_threadsafe) 

        threading.Thread(target=update_process, daemon=True).start()





    def load_main_menu_project(self):
        """Loads the selected project from the recent projects list and runs it using the specified Blender executable."""
        selected_item = self.recent_projects_tree.focus()
        settings_file = os.path.join(os.path.expanduser('~'), '.BlenderManager', 'mngaddon', 'settings.json')
        if selected_item:
            project_path = self.get_selected_project_path()  
            if project_path and project_path.endswith('.blend'):
                blender_exe = os.path.join(self.blender_install_dir, 'blender.exe')  
            
               
                if os.path.isfile(blender_exe):
                    try:
                        
                        self.launch_button.config(text="Running", state='disabled')
                        self.update_button.config(text="Check Updates", state='disabled')
                        process = subprocess.Popen([blender_exe, project_path], creationflags=subprocess.CREATE_NO_WINDOW)
                        
                        def monitor_process():
                            
                            process.wait()

                            self.main_menu_frame.after(0, self.update_project_times)
                            self.main_menu_frame.after(0, self.refresh_recent_projects)
                            self.main_menu_frame.after(0, lambda: self.launch_button.config(text="Launch Blender", state='normal'))
                            self.main_menu_frame.after(0, lambda: self.update_button.config(text="Check Updates", state='normal'))                           
                            if os.path.exists(settings_file):
                                os.remove(settings_file)
                                print("settings.json deleted after Blender closed.")
                        threading.Thread(target=monitor_process, daemon=True).start()
                        

                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to load project:\n{e}")
                else:
                    messagebox.showwarning("Blender Not Found", "Blender executable not found. Please install or configure Blender.")
            else:
                messagebox.showwarning("Invalid Selection", "Please select a valid .blend file.")
        else:
            messagebox.showwarning("No Selection", "Please select a project to load.")



    def on_project_double_click(self, event):
        """Handles double-click event on a recent project to load it."""
        self.load_main_menu_project()
        

    def get_installed_blender_version(self):
        """Retrieves the version of the currently installed Blender, if available."""
        blender_exe = os.path.join(self.blender_install_dir, 'blender.exe')
    
        if os.path.isfile(blender_exe):
            try:
                result = subprocess.run([blender_exe, '--version'], stdout=subprocess.PIPE, text=True)
                version_line = result.stdout.splitlines()[0]
                version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', version_line)
                if version_match:
                    return version_match.group(1) 
            except Exception as e:
                print(f"Failed to get installed Blender version: {e}")

        try:
            for filename in os.listdir(self.blender_install_dir):
                if filename.lower().startswith("release") and filename.endswith(".txt"):
                    release_file_path = os.path.join(self.blender_install_dir, filename)
                    print(f"Checking release file: {release_file_path}")  

                    with open(release_file_path, 'r', encoding='utf-8') as file:
                        for line in file:
                            print(f"Reading line: {line.strip()}")  
                            version_match = re.search(r'Blender (\d+\.\d+(?:\.\d+)?)', line)
                            if version_match:
                                print(f"Version found in file: {version_match.group(1)}")  
                                return version_match.group(1)  # Returns version in format X.Y or X.Y.Z
        except Exception as e:
            print(f"Failed to get Blender version from release files: {e}")
    
        print("No version information found.")  
        return None



        #------------------------------------------------------------------#
        #------------------------------------------------------------------#
        #------------------------------------------------------------------#
        








       #------------------------------------# #------------------------------------# #------------------------------------#
       #------------------------------------# #-------------SETTINGS---------------# #------------------------------------#
       #------------------------------------# #------------------------------------# #------------------------------------#



    def open_settings_window(self):
        """Open the Settings window with all options and features."""

        # Check if the settings window already exists and bring it to focus
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel(self)
        self.settings_button.configure(state='disabled')
        self.settings_window.title("Settings")
        self.settings_window.geometry("500x400")
        self.settings_window.resizable(False, False) 
        self.center_window(self.settings_window, 500, 400)
        self.settings_window.iconbitmap(r"Assets/Images/bmng.ico")
        self.settings_window.transient(self)  
        self.settings_window.grab_set()      
       

        def on_close():
            self.settings_button.configure(state='normal')
            self.settings_window.destroy()
            del self.settings_window

        self.settings_window.protocol("WM_DELETE_WINDOW", on_close)

        notebook = ttk.Notebook(self.settings_window)
        notebook.pack(expand=1, fill='both')

        tab2 = ttk.Frame(notebook)
        settings_tab = ttk.Frame(notebook)
        blender_settings_tab = ttk.Frame(notebook)

        notebook.add(tab2, text="Preferences")
        notebook.add(settings_tab, text="Settings")
        notebook.add(blender_settings_tab, text="Blender Settings")

        theme_frame = ttk.LabelFrame(tab2, text="Appearance Settings", padding=(10, 10))
        theme_frame.pack(fill='both', expand=True, padx=10, pady=10)

        theme_label = ttk.Label(theme_frame, text="Select Theme:")
        theme_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        save_theme_button = tk.Button(
            theme_frame,
            text="Save Theme",
            command=self.save_theme_preference
        )
        save_theme_button.grid(row=0, column=2, sticky="e", padx=5, pady=5)

        theme_listbox = tk.Listbox(theme_frame, height=6, exportselection=False, width=20)
        theme_listbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        available_themes = self.style.theme_names()
        for theme in available_themes:
            theme_listbox.insert(tk.END, theme)

        ttkb.Label(theme_frame, text="Treeview Font Size:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.treeview_font_size_var = tk.IntVar(value=self.treeview_font_size)
        self.treeview_font_size_slider = ttkb.Scale(
            theme_frame,
            from_=8,
            to=20,
            variable=self.treeview_font_size_var,
            orient="horizontal",
            command=self.update_treeview_font_size,
            bootstyle="success"
        )
        self.treeview_font_size_slider.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)

        ttkb.Label(theme_frame, text="Treeview Heading Size:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.treeview_heading_font_size_var = tk.IntVar(value=self.treeview_heading_font_size)
        self.treeview_heading_font_size_slider = ttkb.Scale(
            theme_frame,
            from_=10,
            to=24,
            variable=self.treeview_heading_font_size_var,
            orient="horizontal",
            command=self.update_treeview_heading_font_size,
            bootstyle="success"
        )
        self.treeview_heading_font_size_slider.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=5)

        
        ttkb.Label(theme_frame, text="Treeview Font Family:").grid(row=3, column=0, sticky="w", padx=5, pady=5)

        available_fonts = sorted(tk.font.families())

        default_fonts = ["Segoe UI", "Arial", "Helvetica", "Times New Roman", "Courier New"]
        available_fonts = default_fonts + [font for font in available_fonts if font not in default_fonts]

        self.treeview_font_family_var = tk.StringVar(value=self.treeview_font_family)
        self.treeview_font_family_combobox = ttkb.Combobox(
            theme_frame,
            textvariable=self.treeview_font_family_var,
            values=available_fonts,
            state="readonly"
        )
        self.treeview_font_family_combobox.grid(row=3, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.treeview_font_family_combobox.bind("<<ComboboxSelected>>", self.update_treeview_font_family)


        ttkb.Label(theme_frame, text="Button Font Family:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        available_fonts = sorted(tk.font.families())
        self.button_font_family_var = tk.StringVar(value=self.button_font_family)
        self.button_font_family_combobox = ttkb.Combobox(
            theme_frame,
            textvariable=self.button_font_family_var,
            values=available_fonts,
            state="readonly"
        )
        self.button_font_family_combobox.grid(row=5, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.button_font_family_combobox.bind("<<ComboboxSelected>>", self.update_button_font_family)

        ttkb.Label(theme_frame, text="Button Font Size:").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.button_font_size_var = tk.IntVar(value=self.button_font_size)
        self.button_font_size_slider = ttkb.Scale(
            theme_frame,
            from_=8,
            to=24,
            variable=self.button_font_size_var,
            orient="horizontal",
            command=self.update_button_font_size,
            bootstyle="success"
        )
        self.button_font_size_slider.grid(row=6, column=1, columnspan=2, sticky="ew", padx=10, pady=5)




        self.alpha_var = tk.DoubleVar(value=self.window_alpha)
        self.alpha_label = ttk.Label(theme_frame, text=f"Alpha: {self.window_alpha:.2f}")
        self.alpha_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)

        self.alpha_slider = ttkb.Scale(
            theme_frame,
            from_=0.1,
            to=1.0,
            variable=self.alpha_var,
            orient="horizontal",
            command=self.update_alpha,
            bootstyle="success"
        )
        self.alpha_slider.grid(row=4, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        




        info_label = ttk.Label(
            theme_frame,
            text="You might need to restart the app to see the full changes.",
            font=("Segoe UI", 8, "italic")
        )
        info_label.grid(row=8, column=0, columnspan=3, sticky="s", padx=3, pady=3)






        def on_theme_select(event):
            selected_index = theme_listbox.curselection()
            if selected_index:
                selected_theme = theme_listbox.get(selected_index)
                self.theme_choice.set(selected_theme)
                self.change_theme()

        theme_listbox.bind("<<ListboxSelect>>", on_theme_select)

        current_theme = self.style.theme_use()
        if current_theme in available_themes:
            theme_listbox.selection_set(available_themes.index(current_theme))

        advanced_frame = ttkb.Frame(settings_tab)
        advanced_frame.pack(anchor="nw", padx=5, pady=5, expand=True, fill="both")

        left_frame = ttkb.Frame(advanced_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)




        button_font_family = self.button_font_family
        self.style.configure(
            'Small.TButton',
            font=(button_font_family, 8),  
            padding=(2, 1),  
            background='#ff4d4d',
            foreground='white',
            borderwidth=0
        )



        self.style.configure(
            'Unique.TButton',
            font=("Arial", 8), 
            padding=(2, 1), 
            borderwidth=1,
            relief="flat",
            background="#e1e1e1",  
            foreground="#000000"  
        )

        self.setup_button = ttkb.Button(
            left_frame,
            text="Setup Addon",
            takefocus=False,
            command=self.run_setup,
            width=18, 
            style="Unique.TButton"
        )
        self.setup_button.grid(row=0, column=0, sticky="w", padx=2, pady=1)

        self.question_label = ttk.Label(
            left_frame,
            text="?",
            font=("Arial", 9, "bold"),
            foreground="blue",  
            cursor="hand2"
        )
        self.question_label.grid(row=0, column=1, sticky="w", padx=3, pady=1)
        self.question_label.bind("<Button-1>", lambda e: messagebox.showinfo("Info", "Install first time or update the addon from here. Blender Manager addon is important for the app to work properly."))

        self.change_launch_blender_button = ttkb.Button(
            left_frame,
            text="Change Launch Folder",
            takefocus=False,
            command=self.change_launch_blender,
            width=18,  
            style="Unique.TButton"
        )
        self.change_launch_blender_button.grid(row=1, column=0, sticky="w", padx=2, pady=1)

        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_columnconfigure(1, weight=0)



        self.auto_update_checkbox_widget = ttkb.Checkbutton(
            left_frame,
            text="Auto Update",
            variable=self.auto_update_var,
            bootstyle="success",
            command=self.toggle_auto_update
        )
        self.auto_update_checkbox_widget.grid(row=2, column=0, sticky="w", padx=5, pady=3)


        self.bm_auto_update_checkbox_widget = ttkb.Checkbutton(
            left_frame,
            text="BM Auto Update",
            variable=self.bm_auto_update_var,
            bootstyle="success",
            command=self.toggle_bm_auto_update
        )
        self.bm_auto_update_checkbox_widget.grid(row=3, column=0, sticky="w", padx=5, pady=3)


        self.launch_on_startup_checkbox = ttkb.Checkbutton(
            left_frame,
            text="Launch on Startup",
            variable=self.launch_on_startup_var,
            bootstyle="success",
            command=self.toggle_launch_on_startup
        )
        self.launch_on_startup_checkbox.grid(row=4, column=0, sticky="w", padx=5, pady=3)

        self.run_in_background_checkbox = ttkb.Checkbutton(
            left_frame,
            text="Run in Background",
            variable=self.run_in_background_var,
            bootstyle="success",
            command=self.toggle_run_in_background
        )
        self.run_in_background_checkbox.grid(row=5, column=0, sticky="w", padx=5, pady=3)

        chunk_size_frame = ttk.LabelFrame(left_frame, text="Download Chunk Size Multiplier", padding=(5, 5))
        chunk_size_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.chunk_size_label = ttkb.Label(chunk_size_frame, text=f"Multiplier: {self.chunk_size_multiplier}x")
        self.chunk_size_label.pack(anchor="w", padx=5, pady=3)

        self.chunk_size_var = tk.IntVar(value=self.chunk_size_multiplier)
        self.chunk_size_slider = ttkb.Scale(
            chunk_size_frame,
            from_=1,
            to=10,
            variable=self.chunk_size_var,
            orient="horizontal",
            command=self.update_chunk_size_multiplier,
            bootstyle="success"
        )
        self.chunk_size_slider.pack(fill="x", padx=5, pady=3)

        right_frame = ttk.LabelFrame(advanced_frame, text="Tab Visibility Settings", padding=(5, 5))
        right_frame.grid(row=0, column=1, rowspan=6, sticky="nsew", padx=5, pady=5)

        self.tab_visibility_vars = {
            "Addon Management": tk.BooleanVar(value=self.settings.get("show_addon_management", True)),
            "Project Management": tk.BooleanVar(value=self.settings.get("show_project_management", True)),
            "Render Management": tk.BooleanVar(value=self.settings.get("show_render_management", True)),
            "Version Management": tk.BooleanVar(value=self.settings.get("show_version_management", True)),
            "Installation": tk.BooleanVar(value=self.settings.get("show_installation", True)),
        }

        row = 0
        for tab_name, var in self.tab_visibility_vars.items():
            ttkb.Checkbutton(
                right_frame,
                text=f"Show {tab_name} Tab",
                variable=var,
                bootstyle="success",
                command=lambda name=tab_name, var=var: self.toggle_tab_visibility(name, var)
            ).grid(row=row, column=0, sticky="w", padx=5, pady=3)
            row += 1

        help_icon = ttk.Label(
            right_frame,
            text="?",
            font=("Segoe UI", 10, "bold"),
            foreground="blue",
            cursor="hand2"
        )
        help_icon.grid(row=row+2, column=0, sticky="e", padx=5, pady=3)

        help_icon.bind(
            "<Button-1>",
            lambda e: messagebox.showinfo(
                "Tab Visibility Settings Info",
                "These settings allow you to toggle the visibility of specific tabs in the Blender Manager. "
                "Hiding the tabs you don't need, can speed up the application's startup."
                "To apply changes, restart the application after making adjustments."
            )
        )

        info_label = ttkb.Label(
            right_frame,
            text="You need to restart the Blender Manager to apply changes.",
            font=("Segoe UI", 7, "italic"),
            foreground="grey"
        )
        info_label.grid(row=row, column=0, sticky="w", padx=7, pady=(10, 0))


        row += 1

        restart_button = ttkb.Button(
            right_frame,
            text="Restart",
            style="Unique.TButton",
            command=self.restart_application
        )
        restart_button.grid(row=row, column=0, sticky="w", padx=7, pady=(10, 0))



        button_frame = ttkb.Frame(settings_tab)
        button_frame.pack(anchor="s", padx=5, pady=5) 

        reset_button = ttkb.Button(
            button_frame,
            text="Reset All Data",
            takefocus=False,
            command=self.reset_all_data,
            style="Small.TButton"  
        )
        reset_button.pack(side="left", padx=3)

        self.delete_all_versions_button = ttkb.Button(
            button_frame,
            text="Delete All Versions",
            takefocus=False,
            command=self.delete_all_blender_versions,
            style="Small.TButton"  
        )
        self.delete_all_versions_button.pack(side="left", padx=3)

        self.reset_defaults_button = ttkb.Button(
            button_frame,
            text="Reset Defaults",
            takefocus=False,
            command=self.reset_to_default_settings,
            style="Small.TButton"
        )
        self.reset_defaults_button.pack(side="left", padx=3)



        blender_settings_frame = ttk.Frame(blender_settings_tab, padding=(10, 10))
        blender_settings_frame.pack(expand=1, fill="both")

        left_frame = ttk.LabelFrame(blender_settings_frame, text="Transfer Settings", padding=(10, 10))
        left_frame.pack(side="left", fill="y", padx=10, pady=10)

        label_frame = ttk.Frame(left_frame)
        label_frame.pack(anchor="w", fill="x", pady=5)

        description_label = ttk.Label(
            label_frame,
            text="Transfer Blender Settings",
            font=("Segoe UI", 9, "bold")
        )
        description_label.pack(side="left", padx=5)

        question_label = ttk.Label(
            label_frame,
            text="?",
            font=("Arial", 9, "bold"),
            foreground="blue", 
            cursor="hand2"
        )
        question_label.pack(side="left", padx=5)
        question_label.bind(
            "<Button-1>",
            lambda e: messagebox.showinfo("Info", "This section allows you to transfer settings and addons between Blender versions.")
        )

        ttk.Label(left_frame, text="Source Version:", font=("Segoe UI", 8)).pack(anchor="w", padx=5, pady=2)
        self.source_version_var = tk.StringVar()
        self.source_version_combobox = ttk.Combobox(
            left_frame,
            textvariable=self.source_version_var,
            state="readonly",
            width=25
        )
        self.source_version_combobox.pack(anchor="w", padx=5, pady=5)

        ttk.Label(left_frame, text="↓", font=("Segoe UI", 10)).pack(anchor="center", pady=5)

        ttk.Label(left_frame, text="Destination Version:", font=("Segoe UI", 8)).pack(anchor="w", padx=5, pady=2)
        self.destination_version_var = tk.StringVar()
        self.destination_version_combobox = ttk.Combobox(
            left_frame,
            textvariable=self.destination_version_var,
            state="readonly",
            width=25
        )
        self.destination_version_combobox.pack(anchor="w", padx=5, pady=5)

        self.transfer_button = ttkb.Button(
            left_frame,
            text="Transfer Settings",
            bootstyle="primary",
            command=self.transfer_blender_settings
        )
        self.transfer_button.pack(anchor="w", pady=10)

        self.populate_blender_versions()









        #----------------------------------Functions ---------------------------------------------------
        


    def populate_blender_versions(self):
        """Populate Blender versions in the comboboxes."""
        base_dir = os.path.join(os.getenv("APPDATA"), "Blender Foundation", "Blender")
        if not os.path.exists(base_dir):
            messagebox.showwarning("Warning", "No Blender versions found.")
            return

        versions = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        if versions:
            self.source_version_combobox["values"] = versions
            self.destination_version_combobox["values"] = versions
        else:
            messagebox.showwarning("Warning", "No Blender versions available.")






    def transfer_blender_settings(self):
        """Transfer config and script settings between Blender versions."""
        source_version = self.source_version_var.get()
        destination_version = self.destination_version_var.get()

        if not source_version or not destination_version:
            messagebox.showerror("Error", "Please select both source and destination versions.")
            return

        base_dir = os.path.join(os.getenv("APPDATA"), "Blender Foundation", "Blender")
        source_path = os.path.join(base_dir, source_version)
        destination_path = os.path.join(base_dir, destination_version)

        if not os.path.exists(source_path):
            messagebox.showerror("Error", f"Source version {source_version} does not exist.")
            return
        if not os.path.exists(destination_path):
            messagebox.showerror("Error", f"Destination version {destination_version} does not exist.")
            return

        try:
            source_config = os.path.join(source_path, "config")
            destination_config = os.path.join(destination_path, "config")
            if os.path.exists(source_config):
                if os.path.exists(destination_config):
                    shutil.rmtree(destination_config)
                shutil.copytree(source_config, destination_config)

            source_scripts = os.path.join(source_path, "scripts")
            destination_scripts = os.path.join(destination_path, "scripts")
            if os.path.exists(source_scripts):
                if os.path.exists(destination_scripts):
                    shutil.rmtree(destination_scripts)
                shutil.copytree(source_scripts, destination_scripts)

            messagebox.showinfo("Success", f"Settings transferred from {source_version} to {destination_version}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to transfer settings: {e}")












    def toggle_tab_visibility(self, tab_name, var):
        """Toggle the visibility of a tab based on the boolean variable."""
        if var.get():  
            if tab_name == "Addon Management" and not hasattr(self, "plugins_tab"):
                self.plugins_tab = ttkb.Frame(self.notebook)
                self.notebook.add(self.plugins_tab, text="Addon Management")
                self.create_plugins_tab()
            elif tab_name == "Project Management" and not hasattr(self, "project_management_tab"):
                self.project_management_tab = ttkb.Frame(self.notebook)
                self.notebook.add(self.project_management_tab, text="Project Management")
                self.create_project_management_tab()
            elif tab_name == "Render Management" and not hasattr(self, "render_management_tab"):
                self.render_management_tab = ttkb.Frame(self.notebook)
                self.notebook.add(self.render_management_tab, text="Render Management")
                self.create_render_management_tab()
            elif tab_name == "Version Management" and not hasattr(self, "installed_tab"):
                self.installed_tab = ttkb.Frame(self.notebook)
                self.notebook.add(self.installed_tab, text="Version Management")
                self.create_installed_tab()
            elif tab_name == "Installation" and not hasattr(self, "install_tab"):
                self.install_tab = ttkb.Frame(self.notebook)
                self.notebook.add(self.install_tab, text="Installation")
                self.create_install_tab()
        else:  
            for index in range(self.notebook.index("end")):
                if self.notebook.tab(index, "text") == tab_name:
                    self.notebook.forget(index)
                    break


        setting_key = f"show_{tab_name.replace(' ', '_').lower()}"
        self.settings[setting_key] = var.get()
        save_config(self.settings)

    def toggle_bm_auto_update(self):
        """Toggle the BM Auto Update setting and save it to the config."""
        self.settings["bm_auto_update_checkbox"] = self.bm_auto_update_var.get()
        save_config(self.settings)
        print(f"BM Auto Update set to: {self.bm_auto_update_var.get()}")


    def restart_application(self):
        """Restart the application."""
        try:
            python = sys.executable  
            os.execl(python, python, *sys.argv)  
        except Exception as e:
            messagebox.showerror("Restart Error", f"Failed to restart application: {e}")






    def reset_to_default_settings(self):
        """Reset all settings to default values and save them to config.json."""
        try:
            save_config(DEFAULT_SETTINGS)
            print("Settings reset to default values.")

            self.settings = DEFAULT_SETTINGS.copy()

            self.selected_theme.set(self.settings.get("selected_theme", "darkly"))
            self.theme_choice.set(self.settings.get("selected_theme", "darkly"))
            self.change_theme()

            self.alpha_var.set(self.settings.get("window_alpha", 0.98))
            self.update_alpha()

            self.auto_update_var.set(self.settings.get("auto_update_checkbox", True))

            self.launch_on_startup_var.set(self.settings.get("launch_on_startup", False))

            self.run_in_background_var.set(self.settings.get("run_in_background", True))

            self.treeview_font_size_var.set(self.settings.get("treeview_font_size", 12))
            self.treeview_heading_font_size_var.set(self.settings.get("treeview_heading_font_size", 14))
            self.treeview_font_family_var.set(self.settings.get("treeview_font_family", "Segoe UI"))
            self.update_treeview_font_family()
            self.update_treeview_font_size()
            self.update_treeview_heading_font_size()

            self.button_font_family_var.set(self.settings.get("button_font_family", "Segoe UI"))
            self.button_font_size_var.set(self.settings.get("button_font_size", 14))
            self.update_button_font_family()
            self.update_button_font_size()

            messagebox.showinfo("Settings Reset", "All settings have been reset to default values.")
        except Exception as e:
            print(f"Error resetting settings: {e}")
            messagebox.showerror("Error", f"Failed to reset settings: {e}")





    def update_button_font_family(self, event=None):
        """Update the button font family based on user selection."""
        self.button_font_family = self.button_font_family_var.get()
        self.settings["button_font_family"] = self.button_font_family
        self.apply_custom_styles()
        save_config(self.settings)

    def update_button_font_size(self, event=None):
        """Update the button font size based on user selection."""
        self.button_font_size = self.button_font_size_var.get()
        self.settings["button_font_size"] = self.button_font_size
        self.apply_custom_styles()
        save_config(self.settings)





    def update_treeview_font_family(self, event=None):
        font_family = self.treeview_font_family_var.get()
        self.treeview_font_family = font_family
        self.settings["treeview_font_family"] = font_family
        save_config(self.settings)
        self.apply_custom_styles()
        print(f"Treeview font family updated to: {font_family}")


    def update_treeview_font_size(self, event=None):
        font_size = self.treeview_font_size_var.get()
        self.treeview_font_size = font_size
        self.settings["treeview_font_size"] = font_size
        save_config(self.settings)
        self.apply_custom_styles()
        print(f"Treeview font size updated to: {font_size}")

    def update_treeview_heading_font_size(self, event=None):
        heading_font_size = self.treeview_heading_font_size_var.get()
        self.treeview_heading_font_size = heading_font_size
        self.settings["treeview_heading_font_size"] = heading_font_size
        save_config(self.settings)
        self.apply_custom_styles()
        print(f"Treeview heading font size updated to: {heading_font_size}")


        
    def update_alpha(self, event=None):
        new_alpha = round(self.alpha_var.get(), 2)
        if new_alpha < 0.1:
            new_alpha = 0.1
            self.alpha_var.set(0.1)

        self.attributes("-alpha", new_alpha)
        self.settings["window_alpha"] = new_alpha
        save_config(self.settings)

        self.alpha_label.config(text=f"Alpha: {new_alpha:.2f}")
        print(f"Window alpha updated to: {new_alpha}")





    def update_chunk_size_multiplier(self, event=None):
        new_multiplier = self.chunk_size_var.get()
        if new_multiplier < 1:
            new_multiplier = 1
            self.chunk_size_var.set(1)

        self.settings["chunk_size_multiplier"] = new_multiplier
        save_config(self.settings)

        self.chunk_size_label.config(text=f"Multiplier: {new_multiplier}x")
        print(f"Chunk size multiplier updated to: {new_multiplier}")


        
    def toggle_run_in_background(self):
        """Toggle the 'Run in Background' setting and save to config.json."""
        is_enabled = self.run_in_background_var.get()
        self.settings["run_in_background"] = is_enabled
        save_config(self.settings)
        print(f"Run in Background set to: {is_enabled}")



    def toggle_launch_on_startup(self):
        is_enabled = self.launch_on_startup_var.get()
        self.settings["launch_on_startup"] = is_enabled
        save_config(self.settings)

        try:
            if is_enabled:
                if sys.platform.startswith("win"):
                    self.enable_startup_windows()
                elif sys.platform == "darwin":
                    self.enable_startup_mac()
                elif sys.platform.startswith("linux"):
                    self.enable_startup_linux()
                print("Blender Manager set to launch on startup.")
            else:
                if sys.platform.startswith("win"):
                    self.disable_startup_windows()
                elif sys.platform == "darwin":
                    self.disable_startup_mac()
                elif sys.platform.startswith("linux"):
                    self.disable_startup_linux()
                print("Blender Manager removed from startup.")
        except Exception as e:
            print(f"Error updating startup setting: {e}")
            messagebox.showerror("Error", "Failed to update startup setting.")



    def enable_startup_windows(self):
        
        from win32com.client import Dispatch
        startup_path = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "BlenderManager.lnk")
        script_path = sys.argv[0]
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortcut(startup_path)
        shortcut.TargetPath = script_path
        shortcut.WorkingDirectory = os.path.dirname(script_path)
        shortcut.IconLocation = script_path
        shortcut.save()

    def disable_startup_windows(self):
        startup_path = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "BlenderManager.lnk")
        if os.path.exists(startup_path):
            os.remove(startup_path)

    def enable_startup_mac(self):
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.blendermanager.plist")
        script_path = sys.argv[0]
        plist_content = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>com.blendermanager</string>
            <key>ProgramArguments</key>
            <array>
                <string>{script_path}</string>
            </array>
            <key>RunAtLoad</key>
            <true/>
        </dict>
        </plist>
        """
        with open(plist_path, 'w') as plist_file:
            plist_file.write(plist_content)
        os.system(f"launchctl load {plist_path}")

    def disable_startup_mac(self):
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.blendermanager.plist")
        if os.path.exists(plist_path):
            os.system(f"launchctl unload {plist_path}")
            os.remove(plist_path)

    def enable_startup_linux(self):
        autostart_dir = os.path.expanduser("~/.config/autostart")
        desktop_file_path = os.path.join(autostart_dir, "BlenderManager.desktop")
        script_path = sys.argv[0]
        desktop_content = f"""
        [Desktop Entry]
        Type=Application
        Exec=python3 {script_path}
        Hidden=false
        NoDisplay=false
        X-GNOME-Autostart-enabled=true
        Name=BlenderManager
        Comment=Start Blender Manager on login
        """
        if not os.path.exists(autostart_dir):
            os.makedirs(autostart_dir)
        with open(desktop_file_path, 'w') as desktop_file:
            desktop_file.write(desktop_content)

    def disable_startup_linux(self):
        desktop_file_path = os.path.expanduser("~/.config/autostart/BlenderManager.desktop")
        if os.path.exists(desktop_file_path):
            os.remove(desktop_file_path)









    def toggle_auto_update(self):
        """Toggle the auto update setting and save to config.json."""
        is_checked = self.auto_update_var.get()  
        self.settings["auto_update_checkbox"] = is_checked
        save_config(self.settings)
        print(f"Auto Update set to: {is_checked}")


    def delete_main_blender_version(self):
        
        blender_dir = BLENDER_PATH 
        
        if not os.path.exists(blender_dir):
            messagebox.showinfo("Info", "Blender is not installed" )
            return
        
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete Blender? This action cannot be undone.")

        if confirm:
            self.delete_main_blender_button.configure(state='disabled')
            
            try:
                for item in os.listdir(blender_dir):
                    item_path = os.path.join(blender_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        
                    else:
                        os.remove(item_path)
                        
                messagebox.showinfo("Success", "Blender uninstalled successfully.")
                self.delete_main_blender_button.configure(state='normal')
                
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while deleting Blender versions:\n{e}")
                self.delete_all_versions_button.configure(state='normal')




    def delete_all_blender_versions(self):
        
        blender_dir = BLENDER_DIR
        
        if not os.path.exists(blender_dir):
            messagebox.showinfo("Info", "No Blender versions found to delete.")
            return
        
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all Blender versions? This action cannot be undone.")
        
        if confirm: 
            self.delete_all_versions_button.configure(state='disabled')
            try:
                
                for item in os.listdir(blender_dir):
                    item_path = os.path.join(blender_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                        
                messagebox.showinfo("Success", "All Blender versions have been deleted.")
                self.delete_all_versions_button.configure(state='normal')
                
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while deleting Blender versions:\n{e}")
                self.delete_all_versions_button.configure(state='normal')
                



    def center_window(self, window, width, height):
        """Center the given window on the screen or parent."""
        window.update_idletasks()  
        x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")


    def change_launch_blender(self):
        """Handle the process of selecting an existing Blender installation and moving its contents."""

        def select_and_validate_folder():
            while True:
                selected_folder = filedialog.askdirectory(title="Select Blender Installation Folder")
                if not selected_folder:
                    return None  

                blender_exe_path = os.path.join(selected_folder, "blender.exe")
                if os.path.isfile(blender_exe_path):
                    return selected_folder  
                else:
                    messagebox.showerror("Invalid Folder", "The selected folder does not contain blender.exe. Please try again.")

        def transfer_files(source_folder, target_folder):
            try:
                if os.path.exists(target_folder):
                    shutil.rmtree(target_folder)
                os.makedirs(target_folder)

                for item in os.listdir(source_folder):
                    source_item = os.path.join(source_folder, item)
                    target_item = os.path.join(target_folder, item)
                    if os.path.isdir(source_item):
                        shutil.copytree(source_item, target_item)
                    else:
                        shutil.copy2(source_item, target_item)
               
                self.main_menu_frame.after(0, lambda: self.launch_button.config(text="Launch Blender", state='normal'))
                self.main_menu_frame.after(0, enable_buttons)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while transferring files: {e}")
            finally:
                self.main_menu_frame.after(0, hide_loading_bar)

        def disable_buttons_and_show_loading():
            self.launch_button.config(text="Wait Please...", state='disabled')
            self.create_project_button.config(state='disabled')
            self.update_button.config(state='disabled')
            show_loading_bar()

        def enable_buttons():
            self.launch_button.config(state='normal', text="Launch Blender")
            self.create_project_button.config(state='normal')
            self.update_button.config(state='normal')

        def show_loading_bar():
            self.loading_bar = tk.Label(self.main_menu_frame, text="Loading...", font=("Segoe UI", 10))
            self.loading_bar.grid(row=3, column=0, pady=10)  

        def hide_loading_bar():
            if hasattr(self, 'loading_bar'):
                self.loading_bar.destroy()

        disable_buttons_and_show_loading()

        selected_folder = select_and_validate_folder()
        if not selected_folder:
            hide_loading_bar() 
            enable_buttons()  
            return

        target_folder = BLENDER_PATH

        threading.Thread(target=transfer_files, args=(selected_folder, target_folder), daemon=True).start()





    def reset_all_data(self):
        """Resets all data by deleting the ~/.BlenderManager directory and restarting the app."""
        try:
            confirm = messagebox.askyesno(
                "Reset All Data",
                "Are you sure you want to reset all data? This will delete all settings (Work times, theme settings, all installed blender versions etc.) and restart the app."
            )
            if confirm:
                blender_manager_dir = BLENDER_MANAGER_DIR

                if os.path.exists(blender_manager_dir):
                    self.withdraw()

                    shutil.rmtree(blender_manager_dir)

                    messagebox.showinfo("Reset Complete", "All data has been reset. The application will restart shortly.")

                    self.quit()
                    time.sleep(2)  

                    python = sys.executable
                    os.execv(python, [python] + sys.argv)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset data: {e}")


    def run_setup(self):
        """Runs the setup process to install the addon."""

        addon_zip_names = ["BlenderManager.zip", "Blender Manager.zip", "Blender_Manager.zip", "Blender Manager Addon.zip", "Blender_Manager_Addon.zip"]

        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(__file__)

        self.addon_zip_path = None
        for zip_name in addon_zip_names:
            potential_zip_path = os.path.join(current_dir, zip_name)
            if os.path.exists(potential_zip_path):
                self.addon_zip_path = potential_zip_path
                break

        if not self.addon_zip_path:
            messagebox.showerror("Error", "Addon zip file not found in the current directory. Please ensure the addon zip file is present.")
            return

        blender_foundation_path = os.path.join(os.getenv('APPDATA'), "Blender Foundation", "Blender")

        addon_folder_names = ["Blender Manager", "BlenderManager", "Blender_Manager"]

        if os.path.exists(blender_foundation_path):
            for folder in os.listdir(blender_foundation_path):
                if os.path.isdir(os.path.join(blender_foundation_path, folder)) and folder.count(".") == 1:
                    scripts_addons_path = os.path.join(blender_foundation_path, folder, "scripts", "addons")
                    os.makedirs(scripts_addons_path, exist_ok=True)

                    addon_folder_name = addon_folder_names[0]  
                    addon_full_path = os.path.join(scripts_addons_path, addon_folder_name)

                    if os.path.exists(addon_full_path):
                        print(f"Addon already exists in: {addon_full_path}. Removing old version.")
                        shutil.rmtree(addon_full_path) 

                    self.unzip_addon(self.addon_zip_path, scripts_addons_path)
                    print(f"Addon installed in: {scripts_addons_path}")

            messagebox.showinfo("Setup Complete", "Addon has been installed successfully in all Blender versions.")
        else:
            messagebox.showerror("Error", "Blender Foundation folder not found. You need to install Blender first.")






    def run_automatic_addon_setup(self):
        """Runs the setup process to install the addon automatically."""

        addon_zip_names = ["BlenderManager.zip", "Blender Manager.zip", "Blender_Manager.zip"]

        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(__file__)

        self.addon_zip_path = None
        for zip_name in addon_zip_names:
            potential_zip_path = os.path.join(current_dir, zip_name)
            if os.path.exists(potential_zip_path):
                self.addon_zip_path = potential_zip_path
                break

        if not self.addon_zip_path:
            print("Error: Addon zip file not found in the current directory. Please ensure the addon zip file is present.")
            return

        blender_foundation_path = os.path.join(os.getenv('APPDATA'), "Blender Foundation", "Blender")

        addon_folder_names = ["Blender Manager", "BlenderManager", "Blender_Manager"]

        if os.path.exists(blender_foundation_path):
            for folder in os.listdir(blender_foundation_path):
                if os.path.isdir(os.path.join(blender_foundation_path, folder)) and folder.count(".") == 1:
                    scripts_addons_path = os.path.join(blender_foundation_path, folder, "scripts", "addons")
                    os.makedirs(scripts_addons_path, exist_ok=True)

                    addon_full_path = None
                    for name in addon_folder_names:
                        potential_path = os.path.join(scripts_addons_path, name)
                        if os.path.exists(potential_path):
                            print(f"Addon already exists in: {potential_path}, skipping installation.")
                            addon_full_path = potential_path
                            break

                    if not addon_full_path:
                        addon_folder_name = addon_folder_names[0]
                        addon_full_path = os.path.join(scripts_addons_path, addon_folder_name)

                        self.auto_unzip_addon(self.addon_zip_path, scripts_addons_path)
                        print(f"Addon installed in: {scripts_addons_path}")

            print("Setup Complete: Addon has been installed successfully in all Blender versions. Please launch Blender and activate the addon.")
        else:
            print("Error: Blender Foundation folder not found. Please install Blender or manually set up the addon.")



    def auto_unzip_addon(self, zip_path, extract_to):
        """Unzips the addon to the specified directory."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            print(f"Addon extracted to: {extract_to}")
        except Exception as e:
            print(f"Error extracting addon: {e}")




    def unzip_addon(self, zip_path, extract_to):
        """Unzips the addon to the specified directory."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            print(f"Addon extracted to: {extract_to}")
        except Exception as e:
            print(f"Error extracting addon: {e}")
            messagebox.showerror("Error", f"Failed to extract addon: {e}")



    def save_theme_preference(self):
        """Save the selected theme to the config.json file."""
        selected_theme = self.theme_choice.get()

        try:
            self.settings["selected_theme"] = selected_theme

            save_config(self.settings)

            print(f"Theme '{selected_theme}' saved successfully!")
            messagebox.showinfo("Success", "Theme saved successfully!")
        except Exception as e:
            print(f"Failed to save theme: {e}")
            messagebox.showerror("Error", f"Failed to save theme: {e}")
            


    def change_theme(self, event=None):
        selected_theme = self.theme_choice.get()

        if selected_theme in self.style.theme_names():
            try:
                self.style.theme_use(selected_theme)
                print(f"Theme changed to {selected_theme}")

                self.apply_custom_styles()

            except tk.TclError as e:
                if "bad window path name" in str(e):
                    print(f"Window path error: {e}. The widget may have been destroyed.")
                    self.apply_custom_styles()
                else:
                    messagebox.showerror("Error", f"Failed to apply theme: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def apply_custom_styles(self):
        """Reapply custom styles to maintain consistency after theme change."""
        font_family = self.treeview_font_family
        font_size = self.treeview_font_size
        heading_font_size = self.treeview_heading_font_size
        button_font_family = self.button_font_family
        button_font_size = self.button_font_size
        
        default_button_style = {
            'font': (button_font_family, button_font_size),
            'padding': (10, 5)
        }
        self.style.configure(
            'Custom.Large.TButton',
            font=(button_font_family, button_font_size),
            padding=(10, 5)
        )
        self.style.configure(
            'TButton', 
            font=(button_font_family, min(button_font_size, 11)), 
            padding= (5, 2)
        )


        self.style.configure(
            'Small.TButton',
            font=(button_font_family, 8),  
            padding=(2, 1),  
            background='#ff4d4d',
            foreground='white',
            borderwidth=0
        )



       
        self.style.configure(
            'Unique.TButton',
            font=("Arial", 8),  
            padding=(2, 1),  
            borderwidth=1,
            relief="flat",
            background="#e1e1e1", 
            foreground="#000000"  
        )


        self.style.configure(
            'Green.TButton',
            font=(button_font_family, button_font_size),
            padding=(10, 5),
            background='#28a745',
            foreground='white',
            borderwidth=0,
            focuscolor='none'
        )

        self.style.configure(
            'Custom.Large.TLabel',
            font=('Segoe UI', 14),
            padding=(5, 2)
        )

        self.style.configure(
            'Custom.Small.TButton',
            font=('Segoe UI', 10),
            padding=(5, 2),
            borderwidth=0
        )

        self.style.configure("ProjectManagement.Treeview", font=(font_family, font_size), rowheight=30)
        self.style.configure("ProjectManagement.Treeview.Heading", font=(font_family, heading_font_size, 'bold'))
        self.style.configure("InstalledVersions.Treeview", font=(font_family, font_size), rowheight=30)
        self.style.configure("InstalledVersions.Treeview.Heading", font=(font_family, heading_font_size, 'bold'))
        self.style.configure("PluginManagement.Treeview", font=(font_family, font_size), rowheight=30)
        self.style.configure("PluginManagement.Treeview.Heading", font=(font_family, heading_font_size, 'bold'))
        self.style.configure("Custom.Treeview", font=(font_family, font_size), rowheight=30)
        self.style.configure("Custom.Treeview.Heading", font=(font_family, heading_font_size, 'bold'))


                        #----------------------------------#
                        #------------LOGS TAB--------------#
                        #----------------------------------#



    def create_logs_tab(self):
        self.logs_text = tk.Text(self.logs_tab, wrap='word', state='disabled',
                                 bg=self.style.lookup('TFrame', 'background'),
                                 fg=self.style.lookup('TLabel', 'foreground'),
                                 font=('Consolas', 10))
        self.logs_text.pack(expand=1, fill='both', padx=10, pady=10)

    def redirect_output(self):
        sys.stdout = Redirector(self.logs_text)
        sys.stderr = Redirector(self.logs_text)
        



        #------------------------------------------------------------------#
        #------------------------------------------------------------------#
        #------------------------------------------------------------------#









      
                
                #------------------------------------------#
                #------------ADDON MANAGEMENT--------------#
                #------------------------------------------#

    def create_plugins_tab(self):
        """Creates the plugins management tab and its widgets."""
        plugins_frame = ttk.Frame(self.plugins_tab, padding=(10, 10, 10, 10))
        plugins_frame.pack(expand=1, fill='both')

        self.directory_path = tk.StringVar(value=self.load_plugin_directory())
        directory_frame = ttk.Frame(plugins_frame)
        directory_frame.pack(anchor='w', padx=10, pady=(0, 5))

        self.directory_entry = ttk.Entry(directory_frame, textvariable=self.directory_path, width=50)
        self.directory_entry.pack(side='left', padx=(0, 5))

        self.browse_button = ttk.Button(
            directory_frame,
            text="Browse",
            command=self.browse_directory,
            style='Custom.TButton'
        )
        self.browse_button.pack(side='left', padx=(0, 5))

        self.go_to_button = ttk.Button(
            directory_frame,
            text="Go to File Path",
            takefocus=False,
            command=self.go_to_file_path,
            style='Custom.TButton'
        )
        self.go_to_button.pack(side='left', padx=(0, 5))

        self.add_plugin_button = ttk.Button(
            directory_frame,
            text="Add Addon",
            takefocus=False,
            command=self.add_plugin,
            style='Custom.TButton'
        )
        self.add_plugin_button.pack(side='left', padx=(0, 5))

        self.refresh_plugins_button = ttk.Button(
            directory_frame,
            text="Refresh",
            takefocus=False,
            command=self.refresh_plugins_list,
            style='Custom.TButton'
        )
        self.refresh_plugins_button.pack(side='left', padx=(0, 5))

        self.plugin_search_var = tk.StringVar()
        self.plugin_search_var.trace("w", lambda *args: self.on_plugin_search_change())

        search_bar_frame = ttk.Frame(plugins_frame)
        search_bar_frame.pack(anchor='w', padx=10, pady=(0, 10))

        self.plugin_search_entry = ttk.Entry(
            search_bar_frame,
            textvariable=self.plugin_search_var,
            width=50
        )
        self.plugin_search_entry.pack(side='left', padx=(0, 5))

        self.plugin_placeholder_text = "Search Addons"
        self.plugin_search_entry.insert(0, self.plugin_placeholder_text)
        self.plugin_search_entry.configure(foreground="grey")

        self.plugin_search_entry.bind("<FocusIn>", self.on_plugin_entry_click)
        self.plugin_search_entry.bind("<FocusOut>", self.on_plugin_focus_out)



        self.blender_versions = self.get_blender_versions_for_plugins()
        self.version_var = tk.StringVar()
        self.version_combobox = ttk.Combobox(
            search_bar_frame,
            textvariable=self.version_var,
            values=self.blender_versions,
            state='readonly'
        )
        self.version_combobox.set("Select Blender Version")
        self.version_combobox.pack(side='left', padx=(0, 5))
        self.version_combobox.bind("<<ComboboxSelected>>", self.on_blender_for_plugins_version_selected)

        # Plugins Treeview
        style = ttk.Style()
        self.style.configure("PluginManagement.Treeview", font=('Segoe UI', 12), rowheight=30)
        self.style.configure("PluginManagement.Treeview.Heading", font=('Segoe UI', 14, 'bold'))

        self.plugins_tree = ttk.Treeview(
            plugins_frame,
            columns=('Name', 'Version', 'Compatible'),
            show='headings',
            selectmode='browse',
            style='PluginManagement.Treeview'
        )
        self.plugins_tree.heading('Name', text='Plugin Name')
        self.plugins_tree.heading('Version', text='Version')
        self.plugins_tree.heading('Compatible', text='Compatible with')
        self.plugins_tree.column('Name', width=300, anchor='center')
        self.plugins_tree.column('Version', width=150, anchor='center')
        self.plugins_tree.column('Compatible', width=150, anchor='center')
        self.plugins_tree.pack(side='right', fill='both', expand=1)

        scrollbar = ttk.Scrollbar(plugins_frame, orient="vertical", command=self.plugins_tree.yview)
        self.plugins_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.plugins_tree.drop_target_register(DND_FILES)
        self.plugins_tree.dnd_bind('<<Drop>>', self.handle_treeview_drop)

        self.plugin_context_menu = tk.Menu(self.plugins_tree, tearoff=0)
        self.plugin_context_menu.add_command(label="Delete", command=self.remove_plugin)
        self.plugin_context_menu.add_command(label="Info", command=self.view_plugin_content)
        self.plugin_context_menu.add_command(label="View Documentation", command=self.view_plugin_document)
        self.duplicate_menu = tk.Menu(self.plugin_context_menu, tearoff=0)
        self.plugin_context_menu.add_cascade(label="Duplicate to...", menu=self.duplicate_menu)
        self.plugins_tree.bind("<Button-3>", self.show_plugin_context_menu)

        self.refresh_plugins_list()

    def show_plugin_context_menu(self, event):
        """Displays the context menu for the selected plugin."""
        item_id = self.plugins_tree.identify_row(event.y)
        if item_id:
            self.plugins_tree.selection_set(item_id)
            self.plugin_context_menu.tk_popup(event.x_root, event.y_root)

    def delete_selected_plugin(self):
        """Deletes the selected plugin."""
        selected_item = self.plugins_tree.selection()
        if selected_item:
            plugin_name = self.plugins_tree.item(selected_item, "values")[0]
            print(f"Deleting plugin: {plugin_name}")
            self.plugins_tree.delete(selected_item) 

    def show_plugin_info(self):
        """Shows information about the selected plugin."""
        selected_item = self.plugins_tree.selection()
        if selected_item:
            plugin_info = self.plugins_tree.item(selected_item, "values")
            print(f"Plugin Info: {plugin_info}")

        



        #-----------Functions----------#




    def update_duplicate_menu(self):
        """Updates the 'Duplicate to...' submenu with available Blender versions."""
        self.duplicate_menu.delete(0, "end")  # Clear existing items

        blender_versions = self.get_blender_versions_for_plugins()
        if not blender_versions:
            self.duplicate_menu.add_command(label="No versions found", state="disabled")
            return

        for version in blender_versions:
            self.duplicate_menu.add_command(
                label=version,
                command=lambda v=version: self.duplicate_addon_to_version(v)
            )

    def show_plugin_context_menu(self, event):
        """Displays the context menu for the selected plugin."""
        item_id = self.plugins_tree.identify_row(event.y)
        if item_id:
            self.plugins_tree.selection_set(item_id)
            self.update_duplicate_menu()  
            self.plugin_context_menu.tk_popup(event.x_root, event.y_root)

    def duplicate_addon_to_version(self, target_version):
        """Duplicate the selected addon to the specified Blender version."""
        selected_item = self.plugins_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "No addon selected.")
            return

        addon_name = self.plugins_tree.item(selected_item, "values")[0]
        current_addon_path = os.path.join(self.directory_path.get(), addon_name)

        if not os.path.exists(current_addon_path):
            messagebox.showerror("Error", "The selected addon does not exist.")
            return

        target_addon_path = os.path.join(
            os.getenv('APPDATA'),
            "Blender Foundation",
            "Blender",
            target_version,
            "scripts",
            "addons",
            addon_name
        )

        os.makedirs(os.path.dirname(target_addon_path), exist_ok=True)

        try:
            if os.path.isdir(current_addon_path):
                shutil.copytree(current_addon_path, target_addon_path)
            elif os.path.isfile(current_addon_path):
                shutil.copy2(current_addon_path, target_addon_path)
            messagebox.showinfo(
                "Success", f"Addon '{addon_name}' has been duplicated to Blender {target_version}."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to duplicate addon: {e}")





    
    def view_plugin_document(self):
        """Open the documentation link for the selected plugin."""
        import webview
        selected_item = self.plugins_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "No addon selected.")
            return

        plugin_name = self.plugins_tree.item(selected_item)['values'][0]
        plugin_folder_path = os.path.join(self.directory_path.get(), plugin_name)

        if os.path.isfile(plugin_folder_path + ".py"):
            addon_file = plugin_folder_path + ".py"
        else:
            addon_file = os.path.join(plugin_folder_path, "__init__.py")

        if not os.path.exists(addon_file):
            messagebox.showerror("Error", "The selected plugin does not have an accessible file.")
            return

        def extract_bl_info(file_path):
            """Extract the bl_info dictionary from a Python file."""
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                    bl_info_match = re.search(r"bl_info\s*=\s*\{.*?\}", content, re.DOTALL)
                    if bl_info_match:
                        try:
                            return eval(bl_info_match.group(0).split("=", 1)[1])
                        except Exception as e:
                            print(f"Failed to eval regex-extracted bl_info: {e}")

                    tree = ast.parse(content, filename=file_path)
                    for node in tree.body:
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == 'bl_info':
                                    try:
                                        return ast.literal_eval(node.value)
                                    except Exception as e:
                                        print(f"Failed to literal_eval bl_info: {e}")
            except Exception as e:
                print(f"Failed to read bl_info from {file_path}: {e}")
            return None

        bl_info = extract_bl_info(addon_file)
        if not bl_info:
            messagebox.showerror("Error", "Could not extract bl_info from the addon.")
            return

        doc_url = bl_info.get("doc_url")
        wiki_url = bl_info.get("wiki_url")
        ref_url = bl_info.get("#ref")

        url_to_open = doc_url or wiki_url or ref_url

        if url_to_open:
            try:
                webview.create_window(f"{plugin_name} Documentation", url_to_open)
                webview.start()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open the documentation: {e}")
        else:
            messagebox.showinfo("Info", "No documentation URL found for this plugin.")











    def get_blender_versions_for_plugins(self):
        """Retrieve available Blender versions from the AppData directory."""
        versions = []
        blender_foundation_path = os.path.join(os.getenv('APPDATA'), "Blender Foundation", "Blender")

        if os.path.exists(blender_foundation_path):
            for folder in os.listdir(blender_foundation_path):
                if os.path.isdir(os.path.join(blender_foundation_path, folder)) and folder.count(".") == 1:
                    versions.append(folder)

        return sorted(versions, reverse=True)  

    def on_blender_for_plugins_version_selected(self, event):
        """Handle version selection and update the plugins directory."""
        selected_version = self.version_var.get()
        if not selected_version or selected_version == "Select Blender Version":
            print("No version selected.")
            return

        appdata_dir = os.getenv('APPDATA')
        self.directory_path.set(os.path.join(appdata_dir, "Blender Foundation", "Blender", selected_version, "scripts", "addons"))
        self.refresh_plugins_list()




    def on_plugin_entry_click(self, event):
        if self.plugin_search_entry.get() == self.plugin_placeholder_text:
            self.plugin_search_entry.delete(0, "end")
            self.plugin_search_entry.configure(foreground="black")

    def on_plugin_focus_out(self, event):
        if not self.plugin_search_entry.get():
            self.plugin_search_entry.insert(0, self.plugin_placeholder_text)
            self.plugin_search_entry.configure(foreground="grey")


    def on_plugin_search_change(self, *args):
        if self.plugin_search_entry.get() != self.plugin_placeholder_text:
            self.filter_plugins_tree()

        
    def browse_directory(self):
        """Allow the user to select the directory where plugins are stored."""
        directory = filedialog.askdirectory() 
        if directory:
            self.directory_path.set(directory)
            self.save_plugin_directory(directory)
            self.refresh_plugins_list()
            

    def go_to_file_path(self):
        """Open the current plugin directory in the file explorer."""
        directory = self.directory_path.get()
        if os.path.exists(directory):
            try:
                if os.name == 'nt':
                    os.startfile(directory)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', directory])
                else:
                    subprocess.Popen(['xdg-open', directory])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open directory: {e}")
        else:
            messagebox.showwarning("Warning", "The selected directory does not exist.")

    def filter_plugins_tree(self):
        """Filters the plugin Treeview based on the search query."""
        query = self.plugin_search_var.get().lower()
        self.plugins_tree.delete(*self.plugins_tree.get_children())

        addons_dir = self.directory_path.get()
        if not os.path.exists(addons_dir):
            return

        for item in os.listdir(addons_dir):
            if query in item.lower():
                item_path = os.path.join(addons_dir, item)
                version, compatible = self.get_plugin_info(item_path)
                self.plugins_tree.insert('', 'end', values=(item, version, compatible))


    def save_plugin_directory(self, directory):
        """Save the selected plugin directory to a configuration file."""
        config_file_path = self.resource_path(os.path.join(os.path.expanduser("~"), ".BlenderManager", "paths", "plugin_directory.json"))

        config_dir = os.path.dirname(config_file_path)

        try:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir) 

            with open(config_file_path, 'w') as f:
                json.dump({'plugin_directory': directory}, f)
        except PermissionError:
            messagebox.showerror("Error", "Permission denied: Unable to save plugin directory. Please check your permissions.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save plugin directory: {e}")



    def get_default_plugin_directory(self):
        """Get the default plugin directory based on AppData."""
        appdata_dir = os.getenv('APPDATA')
        if appdata_dir:
            return os.path.join(appdata_dir, "Blender Foundation", "Blender", "4.2", "scripts", "addons")
        else:
            messagebox.showerror("Error", "AppData directory not found.")
            return None

    def load_plugin_directory(self):
        """Load the plugin directory from a configuration file."""
        default_dir = self.get_default_plugin_directory()
        if not default_dir:
            return ""  

        try:
            with open('plugin_directory.json', 'r') as f:
                data = json.load(f)
            plugin_dir = data.get('plugin_directory', default_dir)
        
            if not os.path.exists(plugin_dir):
                os.makedirs(plugin_dir)
                plugin_dir = default_dir

            return plugin_dir
        except FileNotFoundError:
            if not os.path.exists(default_dir):
                os.makedirs(default_dir)
            return default_dir
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load plugin directory: {e}")
            return default_dir


    def refresh_plugins_list(self):
        """List all installed plugins from the selected plugin directory."""
        self.plugins_tree.delete(*self.plugins_tree.get_children())

        addons_dir = self.directory_path.get()
        if not os.path.exists(addons_dir):
            print(f"Addons directory not found: {addons_dir}")
            return

        for item in os.listdir(addons_dir):
            item_path = os.path.join(addons_dir, item)

            if item == "__pycache__" or item.endswith(".pyc"):
                continue

            if os.path.isdir(item_path):
                version, compatible = self.get_plugin_info(item_path)
                self.plugins_tree.insert('', 'end', values=(item, version, compatible))
            elif item.endswith('.py'):
                version, compatible = self.get_plugin_info(item_path)
                plugin_name = os.path.splitext(item)[0]
                self.plugins_tree.insert('', 'end', values=(plugin_name, version, compatible))





    def get_plugin_info(self, addon_path):
        """Read the plugin's bl_info to extract version and compatibility information."""
        version = "Unknown"
        compatible = "Unknown"

        def extract_bl_info(file_path):
            """Extract bl_info dictionary from a Python file."""
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                    tree = ast.parse(content, filename=file_path)

                    for node in tree.body:
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == 'bl_info':
                                    return ast.literal_eval(node.value)
            except Exception as e:
                print(f"Failed to read bl_info from {file_path}: {e}")
            return None

        if addon_path.endswith('.py'):
            info_file = addon_path
        else:
            info_file = os.path.join(addon_path, "__init__.py")

        if os.path.exists(info_file):
            bl_info = extract_bl_info(info_file)
            if bl_info:
                version = ".".join(map(str, bl_info.get('version', [])))
                compatible = ", ".join(map(str, bl_info.get('blender', ["Unknown"])))
                return version, compatible

        for root, dirs, files in os.walk(addon_path):
            for file in files:
                if file == "__init__.py":
                    init_file_path = os.path.join(root, file)
                    bl_info = extract_bl_info(init_file_path)
                    if bl_info:
                        version = ".".join(map(str, bl_info.get('version', [])))
                        compatible = ", ".join(map(str, bl_info.get('blender', ["Unknown"])))
                        return version, compatible

        return version, compatible
 

    def add_plugin(self):
        """Add plugin functionality via file dialog."""
        file_paths = filedialog.askopenfilenames(
            title="Select Plugin Files",
            filetypes=[("Python Files", "*.py"), ("Zip Files", "*.zip")]
        )
        if not file_paths:
            return

        for file_path in file_paths:
            if os.path.isfile(file_path):
                if file_path.lower().endswith('.zip') or file_path.lower().endswith('.py'):
                    self.add_plugin_from_file(file_path)
                else:
                    messagebox.showerror("Invalid File", f"Unsupported file format: {file_path}\nPlease select a .zip or .py file.")
            else:
                messagebox.showerror("Invalid File", f"Not a file: {file_path}")

            

    def add_plugin_from_file(self, file_path):
        """Add a plugin from a dropped file."""
        try:
            addons_dir = self.directory_path.get()
            if not os.path.exists(addons_dir):
                os.makedirs(addons_dir)

            basename = os.path.basename(file_path)
            destination = os.path.join(addons_dir, basename)

            if os.path.exists(destination):
                overwrite = messagebox.askyesno(
                    "Overwrite", f"{basename} already exists. Do you want to overwrite it?"
                )
                if not overwrite:
                    return

            if file_path.lower().endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    namelist = zip_ref.namelist()

                    top_level_items = set()
                    for name in namelist:
                        if name.endswith('/'):
                            continue
                        top_level_dir = name.split('/')[0]
                        top_level_items.add(top_level_dir)

                    if len(top_level_items) == 1:
                        zip_ref.extractall(addons_dir)
                        print(f"Extracted {file_path} to {addons_dir}")
                    else:
                        folder_name = os.path.splitext(basename)[0]
                        extract_path = os.path.join(addons_dir, folder_name)
                        os.makedirs(extract_path, exist_ok=True)
                        zip_ref.extractall(extract_path)
                        print(f"Extracted {file_path} to {extract_path}")
            elif file_path.lower().endswith('.py'):
                shutil.copy(file_path, destination)
                print(f"Copied {file_path} to {destination}")

            self.refresh_plugins_list()
            messagebox.showinfo(
                "Success", f"Plugin '{basename}' has been added successfully!"
            )
        except zipfile.BadZipFile:
            print(f"Extraction failed: Bad zip file - {file_path}")
            messagebox.showerror(
                "Extraction Failed",
                f"Failed to extract '{basename}'. The zip file is corrupted.",
            )
        except Exception as e:
            print(f"Error adding plugin from file: {e}")
            messagebox.showerror("Error", f"Failed to add plugin: {e}")





    def handle_treeview_drop(self, event):
        """Handle files dropped into the drop area."""
        files = self.parse_drop_files(event.data)
        if not files:
            return

        for file_path in files:
            if os.path.isfile(file_path):
                if file_path.lower().endswith('.zip') or file_path.lower().endswith('.py'):
                    self.add_plugin_from_file(file_path)
                else:
                    messagebox.showerror("Invalid File", f"Unsupported file format: {file_path}\nPlease drop a .zip or .py file.")
            else:
                messagebox.showerror("Invalid File", f"Not a file: {file_path}")
                

    def parse_drop_files(self, data):
        """Parse the dropped files from the event data."""
        return self.tk.splitlist(data)
            

    def remove_plugin(self):
        """Remove the selected plugin from the Blender addons folder."""
        selected_item = self.plugins_tree.focus()
        if selected_item:
            plugin_name = self.plugins_tree.item(selected_item)['values'][0]
            addons_dir = self.directory_path.get()
        
            plugin_folder_path = os.path.join(addons_dir, plugin_name)
            plugin_file_path = os.path.join(addons_dir, plugin_name + ".py")

            if os.path.exists(plugin_folder_path):
                confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove the plugin folder '{plugin_name}'?")
                if confirm:
                    try:
                        shutil.rmtree(plugin_folder_path)
                        messagebox.showinfo("Success", f"Plugin folder '{plugin_name}' removed.")
                        self.refresh_plugins_list()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to remove plugin folder: {e}")
            elif os.path.exists(plugin_file_path):
                confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove the plugin file '{plugin_name}.py'?")
                if confirm:
                    try:
                        os.remove(plugin_file_path)
                        messagebox.showinfo("Success", f"Plugin file '{plugin_name}.py' removed.")
                        self.refresh_plugins_list()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to remove plugin file: {e}")
            else:
                messagebox.showwarning("Warning", "The selected plugin does not exist.")
               

    def view_plugin_content(self):
        """Show the content of the selected plugin's file or __init__.py file."""
        selected_item = self.plugins_tree.focus()
        if selected_item:
            plugin_name = self.plugins_tree.item(selected_item)['values'][0]
            plugin_file = os.path.join(self.directory_path.get(), plugin_name)
        
            if os.path.isfile(plugin_file + ".py"):
                file_path = plugin_file + ".py"
            else:
                file_path = os.path.join(plugin_file, "__init__.py")

            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    content_window = tk.Toplevel(self)
                    content_window.title(f" {plugin_name} Info")
                    text_widget = tk.Text(content_window, wrap='word')
                    text_widget.insert('1.0', content)
                    text_widget.pack(expand=1, fill='both')
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to read file: {e}")
            else:
                messagebox.showwarning("Warning", "The plugin file does not exist.")









                



  #------------------------------------------------------------#
  #---------------------PROJECT MANAGEMENT---------------------#
  #------------------------------------------------------------#              

                






    def create_project_management_tab(self):
        """Creates the Project Management tab and its widgets."""
        projects_frame = ttk.Frame(self.project_management_tab, padding=(10, 10, 10, 10))
        projects_frame.pack(expand=1, fill='both')

        self.project_directory_path = tk.StringVar(value=self.load_project_directory())
        project_directory_frame = ttk.Frame(projects_frame)
        project_directory_frame.pack(anchor='w', padx=10, pady=(0, 5))

        self.project_directory_entry = ttk.Entry(project_directory_frame, textvariable=self.project_directory_path, width=50)
        self.project_directory_entry.pack(side='left', padx=(0, 5))

        self.project_browse_button = ttk.Button(
            project_directory_frame,
            text="Browse",
            command=self.browse_project_directory,
            style='Custom.TButton'
        )
        self.project_browse_button.pack(side='left', padx=(0, 5))

        self.project_go_to_button = ttk.Button(
            project_directory_frame,
            text="Go to File Path",
            takefocus=False,
            command=self.go_to_project_file_path,
            style='Custom.TButton'
        )
        self.project_go_to_button.pack(side='left', padx=(0, 5))
        
        self.add_project_button = ttk.Button(
            project_directory_frame,
            text="Add Project",
            takefocus=False,
            command=self.add_project,
            style='Custom.TButton'
        )
        self.add_project_button.pack(side='left', padx=(0, 5))
        
        self.refresh_projects_button = ttk.Button(
            project_directory_frame,
            text="Refresh",
            takefocus=False,
            command=self.refresh_projects_list,
            style='Custom.TButton'
        )
        self.refresh_projects_button.pack(side='left', padx=(0, 5))


        self.project_search_var = tk.StringVar()
        self.project_search_var.trace("w", self.on_search_change)

        self.project_search_entry = ttk.Entry(
            projects_frame,
            textvariable=self.project_search_var,
            width=50
        )
        self.project_search_entry.pack(anchor='w', padx=10, pady=(0, 10))

        self.placeholder_text = "Search Projects"
        self.project_search_entry.insert(0, self.placeholder_text)
        self.project_search_entry.configure(foreground="grey")

        def on_entry_click(event):
            """Handle entry click to clear the placeholder text without resetting TreeView."""
            if self.project_search_entry.get() == self.placeholder_text:
                self.project_search_entry.delete(0, "end")
                self.project_search_entry.configure(foreground="black")


        def on_focus_out(event):
            """Handle focus out event to reset the search entry and restore TreeView content if search is empty."""
            query = self.project_search_var.get().strip()
            if not query:
                self.project_search_entry.configure(foreground="grey")
                self.project_search_entry.delete(0, "end")
                self.project_search_entry.insert(0, self.placeholder_text)
                self.refresh_projects_list()  

        self.project_search_entry.bind("<FocusIn>", on_entry_click)
        self.project_search_entry.bind("<FocusOut>", on_focus_out)



        style = ttkb.Style()
        self.style.configure("ProjectManagement.Treeview", font=('Segoe UI', 12), rowheight=30)
        self.style.configure("ProjectManagement.Treeview.Heading", font=('Segoe UI', 14, 'bold'))

        self.projects_tree = ttk.Treeview(
            projects_frame,
            columns=('Last Modified', 'Size', 'Last Blender Version'),
            show='tree headings',
            selectmode='browse',
            style='ProjectManagement.Treeview'
        )

        self.projects_tree.heading('#0', text='Project Name', command=lambda: self.sort_tree_column('#0', False))
        self.projects_tree.column('#0', width=300, anchor='w')

        self.projects_tree.heading('Last Modified', text='Last Modified', command=lambda: self.sort_tree_column('Last Modified', False))
        self.projects_tree.column('Last Modified', width=200, anchor='center')

        self.projects_tree.heading('Size', text='Size', command=lambda: self.sort_tree_column('Size', False))
        self.projects_tree.column('Size', width=100, anchor='center')

        self.projects_tree.heading('Last Blender Version', text='Blender Ver.', command=lambda: self.sort_tree_column('Last Blender Version', False))
        self.projects_tree.column('Last Blender Version', width=150, anchor='center')

        self.projects_tree.pack(side='right', fill='both', expand=1)

        scrollbar = ttk.Scrollbar(projects_frame, orient="vertical", command=self.projects_tree.yview)
        self.projects_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.projects_tree.bind("<<TreeviewOpen>>", self.on_treeview_open)
        self.projects_tree.drop_target_register(DND_FILES)
        self.projects_tree.dnd_bind('<<Drop>>', self.handle_project_treeview_drop)
        self.load_folder_into_tree(self.project_directory_path.get(), "")

        self.context_menu = tk.Menu(self.projects_tree, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_project_from_context)
        self.context_menu.add_command(label="Rename", command=self.rename_project_from_context)
        self.context_menu.add_command(label="Delete", command=self.remove_project_from_context)
        self.context_menu.add_command(label="Export", command=self.export_project_from_context)
        self.context_menu.add_command(label="Info", command=self.view_project_content_from_context)
        self.move_menu = tk.Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="Move to Folder", menu=self.move_menu)

        self.projects_tree.bind("<Button-3>", self.show_context_menu_projects)
        self.refresh_projects_list()


    def sort_tree_column(self, column, reverse):
        """Recursively sort TreeView items based on the specified column, with folders always on top."""
        def is_folder(item):
            """Check if the TreeView item is a folder."""
            full_path = self.get_item_full_path(item)
            return os.path.isdir(full_path)

        def parse_version(version_str):
            """Parse Blender version string, handling '+' correctly."""
            try:
                if '+' in version_str:
                    cleaned_version = version_str.replace('+', '').strip()
                    version_tuple = tuple(map(int, cleaned_version.split('.')))
                    return (*version_tuple, 1)
                else:
                    version_tuple = tuple(map(int, version_str.split('.')))
                    return (*version_tuple, 0)
            except ValueError:
                return (0, 0, 0)

        def sort_items(parent_item):
            """Sort items under a specific parent item."""
            if column == '#0':  
                items = [(self.projects_tree.item(item, 'text'), item) for item in self.projects_tree.get_children(parent_item)]
            else:  
                items = [(self.projects_tree.set(item, column), item) for item in self.projects_tree.get_children(parent_item)]

            folders = [(text, item) for text, item in items if is_folder(item)]
            files = [(text, item) for text, item in items if not is_folder(item)]

            if column == 'Size':
                files.sort(key=lambda x: float(x[0].replace(' MB', '')) if x[0] and ' MB' in x[0] else 0.0, reverse=reverse)
            elif column == 'Last Modified':
                files.sort(key=lambda x: x[0] if x[0] else '', reverse=reverse)
            elif column == 'Last Blender Version':
                files.sort(key=lambda x: parse_version(x[0]), reverse=reverse)
            else:  
                folders.sort(key=lambda x: x[0].lower(), reverse=reverse)
                files.sort(key=lambda x: x[0].lower(), reverse=reverse)

            sorted_items = folders + files
            for index, (text, item) in enumerate(sorted_items):
                self.projects_tree.move(item, parent_item, index)
                sort_items(item)

        sort_items('')
        self.projects_tree.heading(column, command=lambda: self.sort_tree_column(column, not reverse))









        #-----------Functions----------#
        

    def show_context_menu_projects(self, event):
        """Show context menu on right-click."""
        selected_item = self.projects_tree.identify_row(event.y)
        if selected_item:
            self.projects_tree.selection_set(selected_item)
            self.populate_move_menu(self.move_menu)
            self.context_menu.post(event.x_root, event.y_root)
    def open_project_from_context(self):
        """Open the selected project file."""
        self.open_project()
    def rename_project_from_context(self):
        """Rename the selected project file."""
        self.rename_project()
    def remove_project_from_context(self):
        """Delete the selected project file."""
        self.remove_project()
    def export_project_from_context(self):
        """Export the selected project file."""
        self.export_project()
    def view_project_content_from_context(self):
        """View the content information of the selected project file."""
        self.view_project_content()





    def populate_move_menu(self, menu):
        """Initialize the Move to Folder menu with top-level folders only."""
        menu.delete(0, 'end')
        project_root = self.project_directory_path.get()

        self.folder_list = []
        self.current_index = 0

        thread = threading.Thread(target=self.collect_folders_in_background, args=(project_root,))
        thread.start()

        self.after(100, lambda: self.load_folders_to_menu(menu))

    def collect_folders_in_background(self, folder_path):
        """Recursively collect all folders in the background."""
        try:
            items = sorted(os.listdir(folder_path))
            for item in items:
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path):
                    self.folder_list.append(item_path)
                    self.collect_folders_in_background(item_path)
        except Exception as e:
            print(f"Error in collect_folders_in_background: {e}")

    def load_folders_to_menu(self, menu, batch_size=10):
        """Load folders into the menu in small batches to avoid freezing the GUI."""
        if self.current_index >= len(self.folder_list):
            return

        end_index = min(self.current_index + batch_size, len(self.folder_list))

        for folder_path in self.folder_list[self.current_index:end_index]:
            folder_name = os.path.basename(folder_path)

            submenu = tk.Menu(menu, tearoff=0)

            submenu.add_command(
                label="Select This Folder",
                command=lambda path=folder_path: self.move_blend_file(self.get_item_full_path(self.projects_tree.focus()), path)
            )

            self.load_submenu(submenu, folder_path)

            menu.add_cascade(
                label=folder_name,
                menu=submenu
            )

        self.current_index = end_index

        if self.current_index < len(self.folder_list):
            self.after(100, lambda: self.load_folders_to_menu(menu, batch_size))

    def load_submenu(self, submenu, folder_path):
        """Load subfolders dynamically into the submenu."""
        try:
            submenu.delete(0, 'end')
        
            submenu.add_command(
                label="Select This Folder",
                command=lambda path=folder_path: self.move_blend_file(self.get_item_full_path(self.projects_tree.focus()), path)
            )

            items = sorted(os.listdir(folder_path))
            for item in items:
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path):
                    nested_submenu = tk.Menu(submenu, tearoff=0)

                    nested_submenu.add_command(
                        label="Select This Folder",
                        command=lambda path=item_path: self.move_blend_file(self.get_item_full_path(self.projects_tree.focus()), path)
                    )

                    self.load_submenu(nested_submenu, item_path)

                    submenu.add_cascade(
                        label=os.path.basename(item_path),
                        menu=nested_submenu
                    )
        except Exception as e:
            print(f"Error in load_submenu: {e}")





    def add_folders_to_menu(self, menu, parent_path, children):
        """Add folders to the move menu recursively."""
        for child in children:
            item_text = self.projects_tree.item(child, 'text')
            item_path = os.path.join(parent_path, item_text)

            if os.path.isdir(self.get_item_full_path(child)):
                submenu = tk.Menu(menu, tearoff=0)
                menu.add_cascade(label=item_text, menu=submenu)
                self.add_folders_to_menu(submenu, item_path, self.projects_tree.get_children(child))
            else:
                menu.add_command(
                    label=item_text,
                    command=lambda path=item_path: self.move_blend_file(self.get_item_full_path(self.projects_tree.focus()), path)
                )


    def move_blend_file(self, source_path, target_folder):
        """Move a .blend file or folder to the specified target folder."""
        try:
            target_path = os.path.join(target_folder, os.path.basename(source_path))
            if os.path.exists(target_path):
                confirm = messagebox.askyesno("Confirm", f"File already exists in the target folder. Overwrite?")
                if not confirm:
                    return

            shutil.move(source_path, target_path)
            messagebox.showinfo("Success", f"Moved {os.path.basename(source_path)} to {target_folder}. Refresh list to see changes.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move file: {e}")





    def export_project(self):
        """Initialize the export process in a separate thread."""
        selected_item = self.projects_tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "No item selected.")
            return

        blend_path = self.get_item_full_path(selected_item)
        if not os.path.isfile(blend_path) or not blend_path.lower().endswith(('.blend', '.blend1', '.blend2', '.blend3')):
            messagebox.showerror("Error", "Selected item is not a .blend file.")
            return

        export_format = simpledialog.askstring(
            "Export Format",
            "Enter export format (fbx, gltf, abc):",
            initialvalue="fbx"
        )
        if not export_format:
            return

        export_format = export_format.lower()
        if export_format not in ['fbx', 'obj', 'gltf', 'ply', 'stl', 'abc']:
            messagebox.showerror("Error", "Invalid export format.")
            return

        output_dir = tk.filedialog.askdirectory(title="Select Export Directory")
        if not output_dir:
            return

        output_file = os.path.splitext(os.path.basename(blend_path))[0] + f".{export_format}"
        output_path = os.path.join(output_dir, output_file)

        blender_path = os.path.expanduser("~/.blendermanager/blender/blender.exe")
        if not os.path.exists(blender_path):
            messagebox.showerror("Error", f"Blender executable not found at: {blender_path}")
            return

        self.show_exporting_message()
        threading.Thread(
            target=self.run_export_process,
            args=(blend_path, output_path, export_format, blender_path),
            daemon=True
        ).start()







    def run_export_process(self, blend_path, output_path, export_format, blender_path):
        """Run the export process in a separate thread."""
        blend_path = os.path.normpath(blend_path).encode('utf-8', errors='surrogateescape').decode('utf-8')
        output_path = os.path.normpath(output_path).encode('utf-8', errors='surrogateescape').decode('utf-8')

        temp_script_path = os.path.join(os.path.dirname(output_path), "temp_export_script.py")

        try:
            export_script = f"""
import bpy
bpy.ops.wm.open_mainfile(filepath=r'{blend_path}')

if '{export_format}' == 'fbx':
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.ops.export_scene.fbx(
        filepath=r'{output_path}',
        use_selection=False,
        embed_textures=True,
        path_mode='COPY',
        bake_space_transform=True,
        apply_scale_options='FBX_SCALE_ALL',
        mesh_smooth_type='FACE',
        use_tspace=True,
        use_mesh_modifiers=True,
        use_triangles=True
    )
elif '{export_format}' == 'gltf':
    bpy.ops.export_scene.gltf(
        filepath=r'{output_path}',
        export_format='GLTF_SEPARATE',
        export_materials='EXPORT',           
        export_apply=True,                   
        export_tangents=True,                
        use_selection=False
    )
elif '{export_format}' == 'abc':
    bpy.ops.wm.alembic_export(
        filepath=r'{output_path}',
        apply_scale=True,                     
        visible_objects_only=True,           
        flatten=False,                        
        uv_write=True                         
    )
    """

            with open(temp_script_path, 'w', encoding='utf-8') as temp_script:
                temp_script.write(export_script)

            if not os.path.exists(temp_script_path):
                self.show_error_exporting("Temporary script file could not be created.")
                return
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            subprocess.run(
                [blender_path, "--background", "--factory-startup", "--python", temp_script_path],
                check=True,
                startupinfo=startupinfo
            )
            self.show_info_exporting(f"Exported to {output_path}")

        except Exception as e:
            self.show_error_exporting(f"Failed to export: {e}")

        finally:

            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
                
            self.hide_exporting_message()

    def show_error_exporting(self, message):
        """Show error message in the main thread."""
        self.after(0, lambda: messagebox.showerror("Error", message))

    def show_info_exporting(self, message):
        """Show info message in the main thread."""
        self.after(0, lambda: messagebox.showinfo("Success", message))



    def show_exporting_message(self):
        """Show a temporary 'Exporting...' message next to the go to file path buttons."""
        if hasattr(self, 'exporting_label'):
            return  

        self.exporting_label = ttk.Label(self.project_directory_entry.master, text="Exporting...", foreground="red")
        self.exporting_label.pack(side='left', padx=(10, 0))

    def hide_exporting_message(self):
        """Hide the temporary 'Exporting...' message."""
        if hasattr(self, 'exporting_label'):
            self.exporting_label.destroy()
            del self.exporting_label




    def refresh_projects_list(self, query=None):
        """
        List all projects and their contents from the selected project directory with a maximum depth of 5.
        """
        self.projects_tree.delete(*self.projects_tree.get_children())

        project_dir = self.project_directory_path.get()
        if not os.path.exists(project_dir):
            return

        self.insert_directory('', project_dir, query, depth=0)

    def insert_directory(self, parent, path, query=None, depth=0):
        """
        Recursively add directories and .blend files within a folder to the TreeView, up to a maximum depth of 5.
        Folders without .blend files are not shown.
        """
        if depth >= 5:
            return

        try:
            items = sorted(os.listdir(path))

            for item in items:
                item_path = os.path.join(path, item)

                if os.path.isdir(item_path):
                    if self.contains_blend_files(item_path):
                        folder_id = self.projects_tree.insert(parent, 'end', text=item, values=("", "", ""), open=False)
                        self.insert_directory(folder_id, item_path, query, depth + 1)

            for item in items:
                item_path = os.path.join(path, item)

                if item.lower().endswith(('.blend', '.blend1', '.blend2', '.blend3')):
                    if query is None or query.lower() in item.lower():
                        last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(item_path)))
                        size = os.path.getsize(item_path) / (1024 * 1024)
                        blender_version = self.get_blend_version(item_path)
                        self.projects_tree.insert(parent, 'end', text=item, values=(last_modified, f"{size:.2f} MB", blender_version))
        except Exception as e:
            print(f"Error in insert_directory: {e}")

    def contains_blend_files(self, directory):
        """
        Check if a directory or its subdirectories contain any .blend files.
        """
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(('.blend', '.blend1', '.blend2', '.blend3')):
                        return True
            return False
        except Exception as e:
            print(f"Error in contains_blend_files: {e}")
            return False








    def rename_project(self):
        """Rename the selected project or folder, keeping the file extension unchanged for files."""
        selected_item = self.projects_tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "No item selected.")
            return

        project_path = self.get_item_full_path(selected_item)
        if not os.path.exists(project_path):
            messagebox.showerror("Error", "Selected item does not exist.")
            return

        current_name = os.path.basename(project_path)
        is_file = os.path.isfile(project_path)
        file_extension = os.path.splitext(current_name)[1] if is_file else ''
        initial_name = os.path.splitext(current_name)[0] if is_file else current_name

        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=initial_name)
        if new_name and new_name != initial_name:
            if is_file:
                new_name_with_ext = new_name + file_extension
            else:
                new_name_with_ext = new_name

            new_path = os.path.join(os.path.dirname(project_path), new_name_with_ext)

            if os.path.exists(new_path):
                messagebox.showerror("Error", "A file or folder with that name already exists.")
                return

            try:
                os.rename(project_path, new_path)
                messagebox.showinfo("Success", f"Renamed to '{new_name_with_ext}'.")
                self.refresh_projects_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename: {e}")
        else:
            print("Rename cancelled or name unchanged.")



    def get_item_full_path(self, item_id):
        """Get the full file path of a TreeView item."""
        parts = []
        while item_id:
            item_text = self.projects_tree.item(item_id, "text")
            parts.insert(0, item_text)
            item_id = self.projects_tree.parent(item_id)
        return os.path.join(self.project_directory_path.get(), *parts)


    def get_blend_version(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)

                if not header.startswith(b'BLENDER'):
                    return "4.2+"

                version_bytes = header[9:12]

                version_str = version_bytes.decode('ascii')

                if not version_str.isdigit():
                    return "Unknown"

                version_num = int(version_str)

                major = version_num // 100
                minor = version_num % 100

                return f"{major}.{minor}"

        except Exception as e:
            print(f"Error reading Blender version from {file_path}: {e}")
            return "Compressed Format"



    def on_search_change(self, *args):
        """Filter the TreeView based on the search query and scroll to the matching item."""
        query = self.project_search_var.get().strip().lower()
        if not query or query == self.placeholder_text:
            self.refresh_projects_list()
        else:
            self.projects_tree.delete(*self.projects_tree.get_children())
            self.expand_and_search(self.project_directory_path.get(), query)

    def expand_and_search(self, folder_path, query, parent_item=''):
        """Recursively search, expand all directories, and scroll to the matching item."""
        try:
            items = sorted(os.listdir(folder_path))
            for item in items:
                item_path = os.path.join(folder_path, item)

                if os.path.isdir(item_path):
                    folder_id = self.projects_tree.insert(parent_item, 'end', text=item, values=("", "", ""), open=True)
                    self.expand_and_search(item_path, query, folder_id)

                elif item.lower().endswith(('.blend', '.blend1', '.blend2', '.blend3')):
                    if query in item.lower():
                        last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(item_path)))
                        size = os.path.getsize(item_path) / (1024 * 1024)
                        blender_version = self.get_blend_version(item_path)
                        file_item = self.projects_tree.insert(parent_item, 'end', text=item, values=(last_modified, f"{size:.2f} MB", blender_version))

                        self.projects_tree.see(file_item)
                        self.projects_tree.focus(file_item)
                        self.projects_tree.selection_set(file_item)
                        self.scroll_to_item(file_item)
        except Exception as e:
            print(f"Error during search: {e}")

    def scroll_to_item(self, item):
        """Scroll the TreeView to make the specified item visible."""
        try:
            self.projects_tree.see(item)
            self.projects_tree.focus(item)
            self.projects_tree.selection_set(item)
        except Exception as e:
            print(f"Error scrolling to item: {e}")




    def reattach_all_items(self, item):
        """Recursively reattach all items to make them visible."""
        self.projects_tree.reattach(item, '', 'end')
        for child in self.projects_tree.get_children(item):
            self.reattach_all_items(child)




    def open_project(self):
        """Open the selected .blend file using the default application."""
        selected_item = self.projects_tree.focus()
        if selected_item:
            project_path = self.get_item_full_path(selected_item)
            if os.path.isfile(project_path) and project_path.lower().endswith(('.blend', '.blend1', '.blend2', '.blend3')):
                try:
                    os.startfile(project_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open project: {e}")
            else:
                messagebox.showwarning("Warning", "The selected item is not a .blend file.")
        else:
            messagebox.showwarning("Warning", "No project selected.")



    def handle_project_treeview_drop(self, event):
        file_path = event.data.strip().strip("{}")
        print("Dragged file path:", file_path)

        if os.path.isfile(file_path) and file_path.lower().endswith(('.blend', '.blend1', '.blend2', '.blend3')):
            print("Detected a .blend file directly.")
            self.add_project(file_path)
        elif os.path.isdir(file_path):
            print("Detected a directory.")
            if any(file.lower().endswith(('.blend', '.blend1', '.blend2', '.blend3')) for root, dirs, files in os.walk(file_path) for file in files):
                user_choice = messagebox.askyesno("Copy Options", "Do you want to copy the .blend files individually, or keep the folder structure?\n\nYes: Individually\nNo: Keep folder structure")
                self.add_project(file_path, copy_individually=user_choice)
            else:
                messagebox.showerror("Error", "The folder does not contain any .blend files.")
        elif file_path.lower().endswith('.zip'):
            print("Detected a zip file.")
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                if any(file.lower().endswith(('.blend', '.blend1', '.blend2', '.blend3')) for file in zip_ref.namelist()):
                    user_choice = messagebox.askyesno("Extraction Options", "Do you want to extract .blend files individually, or keep them inside a folder?\n\nYes: Individually\nNo: Keep in folder")
                    self.add_project(file_path, extract_individually=user_choice)
                else:
                    messagebox.showerror("Error", "The zip file does not contain any .blend files.")
        else:
            messagebox.showerror("Error", "Only .blend files, folders, or zip files containing .blend files can be added.")

    def add_project(self, project_dir=None, copy_individually=False, extract_individually=False):
        if project_dir is None:
            project_dir = tk.filedialog.askdirectory()
            if not project_dir:
                return

        try:
            destination = self.project_directory_path.get()

            if os.path.isfile(project_dir) and project_dir.lower().endswith(('.blend', '.blend1', '.blend2', '.blend3')):
                shutil.copy(project_dir, destination)
                print(f"Copied .blend file to {destination}")

            elif os.path.isdir(project_dir):
                if copy_individually:
                    self.copy_blend_files_from_directory(project_dir, destination)
                else:
                    folder_name = os.path.basename(project_dir).replace('.', '_')
                    target_folder = os.path.join(destination, folder_name)
                    os.makedirs(target_folder, exist_ok=True)
                    shutil.copytree(project_dir, target_folder, dirs_exist_ok=True)
                    print(f"Copied entire folder to {target_folder}")

            elif project_dir.lower().endswith('.zip'):
                if extract_individually:
                    self.extract_blend_files_from_zip(project_dir, destination)
                else:
                    folder_name = os.path.basename(project_dir).replace('.', '_')
                    target_folder = os.path.join(destination, folder_name)
                    os.makedirs(target_folder, exist_ok=True)
                    self.extract_blend_files_from_zip(project_dir, target_folder)
                    print(f"Extracted zip contents to {target_folder}")

            else:
                messagebox.showerror("Error", "Unsupported file type.")
                return

            messagebox.showinfo("Success", "Project added successfully!")
            self.refresh_projects_list()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add project: {e}")

    def copy_blend_files_from_directory(self, directory_path, destination):
        os.makedirs(destination, exist_ok=True)
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(('.blend', '.blend1', '.blend11')):
                    src_file = os.path.join(root, file)
                    shutil.copy(src_file, destination)
                    print(f"Copied {src_file} to {destination}")

    def extract_blend_files_from_zip(self, zip_path, destination):
        """
        Extract all .blend files from a zip archive, including nested directories.
        """
        os.makedirs(destination, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                file_name = file_info.filename
                if file_name.lower().endswith(('.blend', '.blend1', '.blend11')):
                    print(f"Found .blend file in zip: {file_name}")
                    extracted_path = os.path.join(destination, os.path.basename(file_name))
                    try:
                        with zip_ref.open(file_info) as source, open(extracted_path, "wb") as target:
                            shutil.copyfileobj(source, target)
                        print(f"Extracted {file_name} to {extracted_path}")
                    except Exception as e:
                        print(f"Failed to extract {file_name}: {e}")
            

    def remove_project(self):
        """Remove the selected project from the project directory."""
        selected_item = self.projects_tree.focus()
        if selected_item:
            project_path = self.get_item_full_path(selected_item)
            if os.path.exists(project_path):
                confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove '{project_path}'?")
                if confirm:
                    try:
                        if os.path.isdir(project_path):
                            shutil.rmtree(project_path)
                        else:
                            os.remove(project_path)
                        messagebox.showinfo("Success", f"'{project_path}' removed.")
                        self.refresh_projects_list()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to remove project: {e}")
            else:
                messagebox.showwarning("Warning", "The selected item does not exist.")
        else:
            messagebox.showwarning("Warning", "No item selected.")


    
    def browse_project_directory(self):
        """Allow the user to select the directory where projects are stored."""
        directory = tk.filedialog.askdirectory()
        if directory:
            total_files = sum([len(files) for _, _, files in os.walk(directory)])
        
            if total_files > 1000:  
                proceed = messagebox.askyesno(
                    "Large Directory Warning",
                    f"The selected directory contains {total_files} files. Loading this directory may take a long time and could freeze the application.\n\n"
                    "Do you want to continue?"
                )
                if not proceed:
                    return

            self.project_directory_path.set(directory)
            self.save_project_directory(directory)
            self.refresh_projects_list()

    def go_to_project_file_path(self):
        """Open the current project directory in the file explorer."""
        directory = self.project_directory_path.get()
        if os.path.exists(directory):
            try:
                if os.name == 'nt':
                    os.startfile(directory)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', directory])
                else:
                    subprocess.Popen(['xdg-open', directory])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open directory: {e}")
        else:
            messagebox.showwarning("Warning", "The selected directory does not exist.")

    def view_project_content(self):
        import datetime as dt
        import stat
        """Show the properties of the selected project file."""
        selected_item = self.projects_tree.focus()
        if selected_item:
            project_path = self.get_item_full_path(selected_item)
            if os.path.exists(project_path):
                try:
                    stats = os.stat(project_path)
                    size = stats.st_size
                    created_time = dt.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    modified_time = dt.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    accessed_time = dt.datetime.fromtimestamp(stats.st_atime).strftime('%Y-%m-%d %H:%M:%S')
                    is_dir = os.path.isdir(project_path)
                    permissions = stat.filemode(stats.st_mode)
                    owner_uid = stats.st_uid
                    group_gid = stats.st_gid

                    time_spent = 'Unknown'
                    json_path = os.path.expanduser(r'~\.BlenderManager\mngaddon\project_time.json')
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, 'r', encoding='utf-8') as json_file:
                                time_data = json.load(json_file)
                            project_basename = os.path.basename(project_path)
                            for file_path, time_in_seconds in time_data.items():
                                if os.path.basename(file_path) == project_basename:
                                    hours, remainder = divmod(time_in_seconds, 3600)
                                    minutes, seconds = divmod(remainder, 60)
                                    time_spent = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
                                    break
                        except Exception as e:
                            time_spent = f"Error reading time data: {e}"

                    properties = f"Name: {os.path.basename(project_path)}\n"
                    properties += f"Path: {project_path}\n"
                    properties += f"Type: {'Folder' if is_dir else 'File'}\n"
                    properties += f"Size: {size} bytes\n"
                    properties += f"Created Time: {created_time}\n"
                    properties += f"Modified Time: {modified_time}\n"
                    properties += f"Accessed Time: {accessed_time}\n"
                    properties += f"Permissions: {permissions}\n"
                    properties += f"Owner UID: {owner_uid}\n"
                    properties += f"Group GID: {group_gid}\n"
                    properties += f"Time Spent: {time_spent}\n"

                    content_window = tk.Toplevel(self)
                    content_window.title(f"Properties of {os.path.basename(project_path)}")
                    text_widget = tk.Text(content_window, wrap='word')
                    text_widget.insert('1.0', properties)
                    text_widget.pack(expand=1, fill='both')

                except Exception as e:
                    messagebox.showerror("Error", f"Failed to retrieve properties: {e}")
                    return
            else:
                messagebox.showerror("Error", "Selected project does not exist.")
        else:
            messagebox.showwarning("Warning", "No project selected.")



            

    def save_project_directory(self, directory):
        """Save the selected project directory to a configuration file."""
        config_file_path = os.path.join(os.path.expanduser("~"), ".BlenderManager", "paths", "project_directory.json")
        config_dir = os.path.dirname(config_file_path)

        try:
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)  

            with open(config_file_path, 'w') as f:
                json.dump({'project_directory': directory}, f)
        except PermissionError:
            messagebox.showerror("Error", "Permission denied: Unable to save project directory. Please check your permissions.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project directory: {e}")





    def load_folder_into_tree(self, folder_path, parent_item):
        try:
            items = sorted(os.listdir(folder_path))
            for item in items:
                item_path = os.path.join(folder_path, item)

                if os.path.isdir(item_path):
                    folder_id = self.projects_tree.insert(parent_item, 'end', text=item, values=("", "", ""), open=False)
                    self.projects_tree.insert(folder_id, 'end', text="dummy") 

                elif item.lower().endswith(('.blend', '.blend1', '.blend2', '.blend3')):
                    last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(item_path)))
                    size = os.path.getsize(item_path) / (1024 * 1024)
                    blender_version = self.get_blend_version(item_path)
                    self.projects_tree.insert(parent_item, 'end', text=item, values=(last_modified, f"{size:.2f} MB", blender_version))
        except Exception as e:
            print(f"Error loading folder into TreeView: {e}")

    def on_treeview_open(self, event):
        item_id = self.projects_tree.focus()
        children = self.projects_tree.get_children(item_id)

        if len(children) == 1 and self.projects_tree.item(children[0], 'text') == "dummy":
            self.projects_tree.delete(children[0])  
            folder_path = self.get_item_full_path(item_id)
            self.load_folder_into_tree(folder_path, item_id)



    def load_project_directory(self):
        """Load the project directory from a configuration file or return a default path."""
        config_file_path = os.path.join(os.path.expanduser("~"), ".BlenderManager", "paths", "project_directory.json")
        default_project_dir = os.path.join(os.getenv('APPDATA'), "Blender Foundation", "Blender", "Projects")
    
        try:
            with open(config_file_path, 'r') as f:
                data = json.load(f)
            return data.get('project_directory', default_project_dir)
        except FileNotFoundError:
           
            if not os.path.exists(default_project_dir):
                os.makedirs(default_project_dir)
            return default_project_dir
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project directory: {e}")
            return default_project_dir


  #------------------------------------------------------------#  
  #-------------------Installed Versions Tab-------------------#
  #------------------------------------------------------------#      


    def create_installed_tab(self):
        installed_frame = ttk.Frame(self.installed_tab, padding=(10, 10, 10, 10))
        installed_frame.pack(expand=1, fill='both')

        buttons_frame = ttk.Frame(installed_frame)
        buttons_frame.pack(side='left', padx=(10, 10), fill='y')

        self.launch_installed_button = ttk.Button(
            buttons_frame,
            text="Launch",
            takefocus=False,
            compound='left',
            padding=(15, 10),
            command=self.launch_blender,
            style='Custom.TButton'
        )
        self.launch_installed_button.pack(pady=(0, 10), fill='x')

        self.launch_factory_var = tk.BooleanVar()
        self.launch_factory_check = ttk.Checkbutton(
            buttons_frame,
            text="Launch with Factory Settings",
            variable=self.launch_factory_var
        )
        self.launch_factory_check.pack(pady=(0, 10), fill='x')

        self.create_shortcut_button = ttk.Button(
            buttons_frame,
            text="Create Shortcut",
            takefocus=False,
            command=self.create_shortcut_for_selected_version,
            padding=(15, 10),
            style='Custom.TButton'
        )
        self.create_shortcut_button.pack(pady=(0, 10), fill='x')


        # Remove Button
        self.remove_button = ttk.Button(
            buttons_frame,
            text="Remove",
            takefocus=False,
            compound='left',
            padding=(15, 10),
            command=self.remove_installed_version,
            style='Custom.TButton'
        )
        self.remove_button.pack(pady=(0, 10), fill='x')

        # Refresh Button
        self.refresh_button = ttk.Button(
            buttons_frame,
            text="Refresh",
            takefocus=False,
            command=self.refresh_installed_versions,
            padding=(15, 10),
            style='Custom.TButton'
        )
        self.refresh_button.pack(pady=(0, 10), fill='x')
        

        # Refresh Button
        self.transfer_to_menu_button = ttk.Button(
            buttons_frame,
            text="Convert To Main Launch",
            takefocus=False,
            command=self.transfer_version_to_menu,
            padding=(15, 10),
            style='Custom.TButton'
        )
        self.transfer_to_menu_button.pack(pady=(0, 10), fill='x')





        style = ttkb.Style()
        self.style.configure("InstalledVersions.Treeview", font=('Segoe UI', 12), rowheight=30)  
        self.style.configure("InstalledVersions.Treeview.Heading", font=('Segoe UI', 14, 'bold'))  


        self.installed_versions_tree = ttkb.Treeview(
            installed_frame,
            columns=('Version',),
            show='headings',
            selectmode='browse',
            height=17,
            style='InstalledVersions.Treeview'  
        )
        self.installed_versions_tree.heading('Version', text='Installed Versions')
        self.installed_versions_tree.column('Version', width=300, anchor='center')
        self.installed_versions_tree.pack(side='right', fill='both', expand=1, padx=(20, 0))


        self.installed_versions_tree.bind('<<TreeviewSelect>>', self.on_version_select)


        self.file_path_label = ttk.Label(self.installed_tab, text="", font=('Helvetica', 10))
        self.file_path_label.pack(pady=(10, 5), anchor='w', padx=20)

        self.go_to_button = ttk.Button(
            self.installed_tab,
            text="Go to File Path",
            takefocus=False,
            command=self.open_file_location,
            style='Custom.TButton',
            padding=(15, 10)
        )
        self.go_to_button.pack(pady=(0, 10))
        self.go_to_button.pack_forget() 


        self.refresh_installed_versions()



        


        #------------FUNCTİONS------------#




    def create_shortcut_for_selected_version (self):
        print("created")

    def transfer_version_to_menu(self):
    
        selected_item = self.installed_versions_tree.focus()
    
        if not selected_item:
            self.after(0, lambda: messagebox.showwarning("Warning", "Please select a Blender version to transfer."))
            return
    
        selected_version = self.installed_versions_tree.item(selected_item)['values'][0]
    
        source_folder = self.resource_path(os.path.join(BLENDER_DIR, selected_version))
        target_folder = BLENDER_PATH
    
        os.makedirs(target_folder, exist_ok=True)

        def transfer_files(source_folder, target_folder):
        
            try:
                self.main_menu_frame.after(0, self.disable_buttons)
                self.remove_button.configure(state='disabled')
                self.transfer_to_menu_button.configure(state='disabled', text='Transfering...')
                print(f"Transfering {source_folder} to {target_folder} ")
            
                if os.path.exists(target_folder):
                    shutil.rmtree(target_folder)
                os.makedirs(target_folder)

                for item in os.listdir(source_folder):
                    source_item = os.path.join(source_folder, item)
                    target_item = os.path.join(target_folder, item)
                    if os.path.isdir(source_item):
                        shutil.copytree(source_item, target_item)
                    else:
                        shutil.copy2(source_item, target_item)

                print("Transfer successfully complete.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while transferring files: {e}")
            finally:
                print("Process Finished")
                self.main_menu_frame.after(0, self.enable_buttons)
                self.transfer_to_menu_button.configure(state='disabled', text='Complete ! ')
                self.remove_button.configure(state='normal')
                time.sleep(1)
                self.transfer_to_menu_button.configure(state='normal', text='Convert To Main Launch')

        threading.Thread(target=transfer_files, args=(source_folder, target_folder), daemon=True).start()
            



    def disable_installed_tab_buttons(self):
        self.transfer_to_menu_button.configure(state='disabled')
        self.launch_installed_button.configure(state='disabled')
        self.create_shortcut_button.configure(state='disabled')
        self.remove_button.configure(state='disabled')
        self.refresh_button.configure(state='disabled')
        


    def enable_installed_tab_buttons(self):
        self.transfer_to_menu_button.configure(state='normal')
        self.launch_installed_button.configure(state='normal')
        self.create_shortcut_button.configure(state='normal')
        self.remove_button.configure(state='normal')
        self.refresh_button.configure(state='normal')
        


    def launch_blender(self):
        selected_item = self.installed_versions_tree.focus()
        if not selected_item:
            self.after(0, lambda: messagebox.showwarning("Warning", "Please select a Blender version to launch."))
            return
        selected_version = self.installed_versions_tree.item(selected_item)['values'][0]
        blender_exec = self.resource_path(os.path.join(BLENDER_DIR, selected_version, 'blender'))

        if os.name == 'nt':
            blender_exec += '.exe'

        if os.path.isfile(blender_exec):
            print(f"Launching {selected_version}...")
            self.remove_button.configure(state='disabled')
            self.launch_installed_button.configure(state='disabled')
            self.after(5000, lambda: self.launch_installed_button.configure(state='normal'))
            
            try:
                if self.launch_factory_var.get():
                    process = subprocess.Popen([blender_exec, '--factory-startup'], creationflags=subprocess.CREATE_NO_WINDOW)

                    print(f"Launching {selected_version} with factory settings...")
                else:
                    process = subprocess.Popen([blender_exec], creationflags=subprocess.CREATE_NO_WINDOW)
                    
                def monitor_process():
                    process.wait()
                    self.remove_button.configure(state='normal')
                    


                threading.Thread(target=monitor_process, daemon=True).start()


            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to launch Blender: {e}"))
                self.remove_button.configure(state='normal')
        else:
            self.after(0, lambda: messagebox.showerror("Error", "Blender executable not found."))
            self.remove_button.configure(state='normal')
            






    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            base_path = sys._MEIPASS  
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)





    def refresh_installed_versions(self):
        """Refresh the list of installed Blender versions, showing only folders with 'blender' in their names."""
    
        self.installed_versions_tree.delete(*self.installed_versions_tree.get_children())

        if not os.path.exists(BLENDER_DIR):
            os.makedirs(BLENDER_DIR)

        versions = [
            d for d in sorted(os.listdir(BLENDER_DIR))
            if os.path.isdir(os.path.join(BLENDER_DIR, d)) and 'blender' in d.lower()
        ]

        for index, version in enumerate(versions):
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.installed_versions_tree.insert('', 'end', values=(version,), tags=(tag,))

        self.change_theme()


    def on_version_select(self, event):
        selected_item = self.installed_versions_tree.focus()
        if selected_item:
            selected_version = self.installed_versions_tree.item(selected_item)['values'][0]
            path = os.path.join(BLENDER_DIR, selected_version)
            self.file_path_label.config(text=f"Path: {path}")
            self.go_to_button.pack(pady=5)
        else:
            self.file_path_label.config(text="")
            self.go_to_button.pack_forget()

    def open_file_location(self):
        selected_item = self.installed_versions_tree.focus()
        if selected_item:
            selected_version = self.installed_versions_tree.item(selected_item)['values'][0]
            path = os.path.join(BLENDER_DIR, selected_version)
            if os.path.exists(path):
                try:
                    if os.name == 'nt':
                        os.startfile(path)
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', path])
                    else:
                        subprocess.Popen(['xdg-open', path])
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open directory: {e}")
            else:
                messagebox.showerror("Error", "Path does not exist.")



    def remove_installed_version(self):
        selected_item = self.installed_versions_tree.focus()
        if not selected_item:
            self.after(0, lambda: messagebox.showwarning("Warning", "Please select a Blender version to remove."))
            return
        selected_version = self.installed_versions_tree.item(selected_item)['values'][0]
        self.disable_installed_tab_buttons()
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove {selected_version}?")
        
        if confirm:
            path_to_remove = os.path.join(BLENDER_DIR, selected_version)
            try:
                shutil.rmtree(path_to_remove)
                self.refresh_installed_versions()
                self.after(0, lambda: messagebox.showinfo("Success", f"{selected_version} has been removed."))
                self.enable_installed_tab_buttons()
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to remove {selected_version}: {e}"))
                self.enable_installed_tab_buttons()


        #--------------------------------------------------------------------------------#




    # -------------------------------------------------#
    # --------------INSTALLATION TAB-------------------#
    # -------------------------------------------------#

    def create_install_tab(self):
        install_frame = ttkb.Frame(self.install_tab, padding=(20, 20, 20, 20))
        install_frame.pack(expand=1, fill='both')

        left_frame = ttkb.Frame(install_frame)
        left_frame.pack(side='left', fill='y', padx=(0, 10), pady=(0, 10))

        right_frame = ttkb.Frame(install_frame)
        right_frame.pack(side='right', expand=1, fill='both')

        os_frame = ttkb.Frame(left_frame)
        os_frame.pack(fill='x', pady=(0, 10))

        self.os_label = ttkb.Label(
            os_frame,
            text="Select Operating System:",
            font=('Helvetica', 10, 'bold')
        )
        self.os_label.pack(side='top', padx=(0, 10))

        self.os_combobox = ttkb.Combobox(
            os_frame,
            values=["Windows", "macOS", "Linux"],
            state='readonly',
            font=('Helvetica', 10),
            bootstyle="primary"
        )
        self.os_combobox.set("Select OS")
        self.os_combobox.pack(fill='x', padx=(0, 10))
        self.os_combobox.bind("<<ComboboxSelected>>", self.on_os_selected)

        self.win_arch_combobox = ttkb.Combobox(
            os_frame,
            values=["32-bit", "64-bit"],
            state='readonly',
            font=('Helvetica', 10),
            bootstyle="primary"
        )
        self.win_arch_combobox.set("Select Architecture")
        self.win_arch_combobox.pack(fill='x', pady=(5, 10), padx=(0, 10))
        self.win_arch_combobox.pack_forget()  

        self.arch_combobox = ttkb.Combobox(
            os_frame,
            values=["Intel", "Apple Silicon"],
            state='readonly',
            font=('Helvetica', 10),
            bootstyle="primary"
        )
        self.arch_combobox.set("Select Architecture")
        self.arch_combobox.pack(fill='x', pady=(5, 10), padx=(0, 10))
        self.arch_combobox.pack_forget()  

        buttons_frame = ttkb.Frame(left_frame)
        buttons_frame.pack(fill='x', pady=(0, 10))

        self.get_stable_btn = ttkb.Button(
            buttons_frame,
            text="Get Stable Versions",
            takefocus=False,
            command=self.get_stable_versions,
            bootstyle="primary"
        )
        self.get_stable_btn.pack(fill='x', pady=(5, 5), padx=(0, 10))

        self.get_unstable_btn = ttkb.Button(
            buttons_frame,
            text="Get Unstable Versions",
            takefocus=False,
            command=self.get_unstable_versions,
            bootstyle="primary"
        )
        self.get_unstable_btn.pack(fill='x', pady=(5, 5), padx=(0, 10))

        self.install_btn = ttkb.Button(
            left_frame,
            text="Install",
            takefocus=False,
            command=self.install_version,
            bootstyle="primary"
        )
        self.install_btn.pack(fill='x', pady=(5, 10), padx=(0, 10))

        self.install_progress_frame = ttkb.Frame(left_frame)
        self.install_progress_label = ttkb.Label(
            self.install_progress_frame,
            text="Download Progress:",
            font=('Helvetica', 10)
        )
        self.install_progress_label.pack(side='top', padx=(0, 10))

        self.install_progress_var = tk.DoubleVar()
        self.install_progress_bar = ttkb.Progressbar(
            self.install_progress_frame,
            variable=self.install_progress_var,
            maximum=100,
            bootstyle="primary-striped"
        )
        self.install_progress_bar.pack(fill='x', expand=1)

        self.install_progress_frame.pack(fill='x', pady=(5, 10), padx=(0, 10))
        self.install_progress_frame.pack_forget()

        self.cancel_button = ttkb.Button(
            left_frame,
            text="Cancel",
            takefocus=False,
            command=self.cancel_installation,
            bootstyle="danger"
        )
        self.cancel_button.pack(fill='x', pady=(5, 10), padx=(0, 10))
        self.cancel_button.pack_forget()
        
        self.release_notes_btn = ttkb.Button(
            left_frame,
            text="Release Notes",
            takefocus=False,
            command=self.show_release_notes,
            bootstyle="info"
        )
        self.release_notes_btn.pack(fill='x', pady=(5, 10), padx=(0, 10))
        self.release_notes_btn.config(state='disabled')  
        
        self.tree = ttkb.Treeview(right_frame, columns=("Version", "Release Date"), show="headings", height=20, style="Custom.Treeview")
        self.tree.heading("Version", text="Blender Version", command=lambda: self.sort_treeview_column_installation_tab("Version"))
        self.tree.heading("Release Date", text="Release Date", command=lambda: self.sort_treeview_column_installation_tab("Release Date"))
        self.tree.column("Version", anchor="center")
        self.tree.column("Release Date", anchor="center")
        self.tree.pack(expand=True, fill="both")
        self.tree.bind("<<TreeviewSelect>>", self.on_treeview_select_install_tab)
        self.download_links = {}



    # ----Functions----
    


    def sort_treeview_column_installation_tab(self, column_name):
        """Sort the Treeview by the given column, prioritizing Year > Month > Day > Time."""
        data = [(self.tree.set(item, column_name), item) for item in self.tree.get_children("")]

        if column_name == "Release Date":
            def parse_date(date_str):
                try:
                    parsed_date = datetime.strptime(date_str, "%d-%b-%Y %H:%M")
                    return (parsed_date.year, parsed_date.month, parsed_date.day, parsed_date.hour, parsed_date.minute)
                except ValueError:
                    return (0, 0, 0, 0, 0)  

            data.sort(key=lambda x: parse_date(x[0]))
        else:
            data.sort(key=lambda x: x[0])

        is_currently_sorted_ascending = getattr(self, f"{column_name}_sorted_ascending", True)
        if not is_currently_sorted_ascending:
            data.reverse()

        for index, (_, item) in enumerate(data):
            self.tree.move(item, '', index)

        setattr(self, f"{column_name}_sorted_ascending", not is_currently_sorted_ascending)




    def on_treeview_select_install_tab(self, event):
        selected_item = self.tree.focus()
        if selected_item:
            self.release_notes_btn.config(state='normal')
        else:
            self.release_notes_btn.config(state='disabled')


    

    def show_release_notes(self):
        import webview
        from tkinter import Toplevel, messagebox
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "No version selected.")
            return

        version_text = self.tree.item(selected_item, "values")[0]
        version = version_text.replace("Blender", "").strip()
        version_parts = version.split('.')

        if len(version_parts) >= 2:
            major_version = version_parts[0]
            minor_version = version_parts[1]
        
            official_url = f"https://www.blender.org/download/releases/{major_version}.{minor_version}/"
            alternative_url = f"https://developer.blender.org/docs/release_notes/{major_version}.{minor_version}/"

            def check_url(url):
                try:
                    response = requests.head(url)
                    return response.status_code == 200
                except Exception as e:
                    print(f"Error checking URL: {e}")
                    return False

            if check_url(official_url):
                webview.create_window(f"Release Notes for Blender {major_version}.{minor_version}", official_url)
                webview.start()
            elif check_url(alternative_url):
                webview.create_window(f"Release Notes for Blender {major_version}.{minor_version}", alternative_url)
                webview.start()
            else:
                messagebox.showerror("Error", f"Release notes for Blender {major_version}.{minor_version} not found.")
        else:
            messagebox.showerror("Error", "Invalid version format.")
        




    def cancel_installation(self):
        if not self.is_installing:
            return
        confirm = messagebox.askyesno("Cancel Installation", "Are you sure you want to cancel the installation?")
        if confirm:
            self.cancel_event_install.set()  
            print("Installation cancelled by user.")

           



    def on_os_selected(self, event):
        selected_os = self.os_combobox.get()
        current_os = sys.platform

        if current_os.startswith('win') and selected_os != "Windows":
            messagebox.showwarning(
                "Warning",
                "You are running Windows. Selecting another OS may not work properly."
            )

        if selected_os == "Windows":
            self.win_arch_combobox.pack(side='left', padx=(0, 10))
            self.arch_combobox.pack_forget()
        elif selected_os == "macOS":
            self.win_arch_combobox.pack_forget()
            self.arch_combobox.pack(side='left', padx=(0, 10))
        else:
            self.win_arch_combobox.pack_forget()
            self.arch_combobox.pack_forget()


    def reset_get_stable_button(self):
        self.get_stable_btn.config(text="Get Stable Versions", state='normal')
        


    def get_stable_versions(self):
        self.get_stable_btn.config(text="Loading...", state='disabled')
        threading.Thread(target=self.run_async_fetch_stable_versions).start()


    def run_async_fetch_stable_versions(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.async_fetch_stable_versions())
        loop.close()
        self.install_tab.after(0, self.reset_get_stable_button)

    async def async_fetch_stable_versions(self):
        os_map = {
            "Windows": "windows",
            "macOS": "darwin",
            "Linux": "linux"
        }
        selected_os = self.os_combobox.get()
        if selected_os not in os_map:
            self.queue.put(('ERROR', "Please select a valid OS."))
            return

        platform = os_map[selected_os]
        architecture = None

        if platform == "windows":
            arch_selection = self.win_arch_combobox.get()
            if arch_selection == "64-bit":
                architecture = "x64"
            elif arch_selection == "32-bit":
                architecture = "x86"
            else:
                self.queue.put(('ERROR', "Please select 32-bit or 64-bit for Windows."))
                return
        elif platform == "darwin":
            arch_selection = self.arch_combobox.get()
            if arch_selection == "Intel":
                architecture = "x64"
            elif arch_selection == "Apple Silicon":
                architecture = "arm64"
            else:
                self.queue.put(('ERROR', "Please select a valid architecture for macOS."))
                return

        base_url = "https://download.blender.org/release/"

        ssl_context = ssl.create_default_context(cafile=certifi.where())

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, ssl=ssl_context) as response:
                    response.raise_for_status()
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    version_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith("Blender")]
                    if not version_links:
                        self.queue.put(('ERROR', "No stable versions found."))
                        return

                    versions, links, dates = await self.fetch_all_versions(version_links, platform, architecture, session, ssl_context)


                    if not versions:
                        self.queue.put(('ERROR', "No stable versions found for the selected platform."))
                        return

                    self.queue.put(('UPDATE_TREEVIEW', versions, links, dates))

        except Exception as e:
            self.queue.put(('ERROR', f"An unexpected error occurred: {str(e)}"))

    async def fetch_all_versions(self, version_links, platform, architecture, session, ssl_context):
        base_url = "https://download.blender.org/release/"
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        tasks = [
            self.fetch_version_page(session, base_url + version_link, platform, architecture, ssl_context)
            for version_link in version_links
        ]
        results = await asyncio.gather(*tasks)

        versions = []
        links = {}
        dates = {}
        for v, l, d in results:
            versions.extend(v)
            links.update(l)
            dates.update(d)

        return versions, links, dates

    async def fetch_version_page(self, session, version_url, platform, architecture, ssl_context):
        try:
            async with session.get(version_url, ssl=ssl_context) as response:
                response.raise_for_status()
                html = await response.text()
                version_soup = BeautifulSoup(html, "html.parser")

                pre_tag = version_soup.find("pre")
                if not pre_tag:
                    return [], {}, {}

                lines = pre_tag.text.splitlines()
                versions = []
                links = {}
                dates = {}

                for line in lines:
                    parts = line.split()
                    if len(parts) < 3:
                        continue

                    file_name = parts[0]
                    date_str = " ".join(parts[1:3])  

                    if file_name.endswith(".sha256") or file_name.endswith(".md5"):
                        continue

                    full_link = version_url + file_name
                    try:
                        version_name = "Blender " + file_name.split('-')[1]
                    except IndexError:
                        version_name = "Blender " + version_url.strip('/').split('/')[-1]

                    if platform == "windows":
                        is_64bit = "x64" in file_name or "windows64" in file_name
                        is_32bit = "x86" in file_name or "windows32" in file_name
                        is_generic = "windows" in file_name and not (is_64bit or is_32bit)

                        if architecture == "x64" and (is_64bit or is_generic):
                            if file_name.endswith(".zip"):
                                versions.append(version_name)
                                links[version_name] = full_link
                                dates[version_name] = date_str

                        elif architecture == "x86" and (is_32bit or is_generic):
                            if file_name.endswith(".zip"):
                                versions.append(version_name)
                                links[version_name] = full_link
                                dates[version_name] = date_str

                    elif platform == "darwin":
                        if ("darwin" in file_name or "macos" in file_name) and architecture in file_name and file_name.endswith(".dmg"):
                            versions.append(version_name)
                            links[version_name] = full_link
                            dates[version_name] = date_str

                    elif platform == "linux":
                        if "linux" in file_name and (file_name.endswith(".tar.xz") or file_name.endswith(".tar.gz")):
                            versions.append(version_name)
                            links[version_name] = full_link
                            dates[version_name] = date_str

                return versions, links, dates
        except Exception as e:
            return [], {}, {}





    def get_unstable_versions(self):
        self.get_unstable_btn.config(text="Loading...", state='disabled')
        threading.Thread(target=self.fetch_unstable_versions).start()
        


    def fetch_unstable_versions(self):
        os_map = {
            "Windows": "windows",
            "macOS": "darwin",
            "Linux": "linux"
        }
        selected_os = self.os_combobox.get()
        if selected_os not in os_map:
            messagebox.showerror("Error", "Please select a valid OS.")
            self.get_unstable_btn.config(text="Get Unstable Versions", state='normal')
            return

        platform = os_map[selected_os]
        architecture = None

        if platform == "darwin":
            arch_selection = self.arch_combobox.get()
            if arch_selection == "Intel":
                architecture = "is-arch-x86_64"
            elif arch_selection == "Apple Silicon":
                architecture = "is-arch-arm64"
            else:
                messagebox.showerror("Error", "Please select a valid architecture for macOS.")
                self.get_unstable_btn.config(text="Get Unstable Versions", state='normal')
                return
        elif platform == "windows":
            architecture = "is-arch-amd64"

        url = "https://builder.blender.org/download/daily/archive/"
        print(f"Fetching versions for platform: {platform}, architecture: {architecture}")

        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            versions = []
            links = {}
            dates = {}

            builds = soup.select(f'div.builds-list-container[data-platform="{platform}"] li.t-row.build')

            if not builds:
                print("No builds found. The HTML structure may have changed.")
                self.get_unstable_btn.config(text="Get Unstable Versions", state='normal')
                messagebox.showerror("Error", "No versions found. The site structure may have changed.")
                return

            for build in builds:
                classes = build.get("class", [])
                if architecture and architecture not in classes:
                    continue

                version_element = build.select_one(".t-cell.b-version")
                download_element = build.select_one(".t-cell.b-down a")

                release_date = "Unknown Date"

                if version_element and download_element:
                    version = version_element.text.strip()
                    download_link = download_element["href"]

                    if download_link.endswith(".sha256"):
                        download_link = download_link.replace(".sha256", "")

                    if platform == "windows" and not download_link.endswith(".zip"):
                        continue

                    if version not in versions:
                        versions.append(version)
                        links[version] = download_link
                        dates[version] = release_date

            if not versions:
                messagebox.showerror("Error", "No versions found.")
                return

            self.queue.put(('UPDATE_TREEVIEW', versions, links, dates))
            self.get_unstable_btn.config(text="Get Unstable Versions", state='normal')
            print("Versions successfully fetched and listed.")

        except Exception as e:
            print("Error fetching versions:", str(e))
            self.get_unstable_btn.config(text="Get Unstable Versions", state='normal')
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")


    def install_version(self):
        if self.is_installing:
            messagebox.showwarning("Warning", "Another installation is in progress.")
            return

        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a version to install.")
            return

        version = self.tree.item(selected_item, "values")[0]
        download_url = self.download_links.get(version)

        if not download_url:
            messagebox.showerror("Error", "Download URL not found.")
            return

        self.cancel_button.pack(pady=(0, 15), fill='x')
        self.is_installing = True
        self.install_progress_var.set(0)
        self.install_progress_frame.pack(fill='x', pady=(0, 10))
        self.install_btn.configure(text='Installing', state='disabled')
        

        threading.Thread(target=self.download_and_install, args=(version, download_url)).start()



    def download_and_install(self, version, download_url):
        import shutil
        file_name = os.path.basename(download_url)
        file_path = os.path.join(BLENDER_MANAGER_DIR, file_name)

        session = requests.Session()
        chunk_size = self.chunk_size_multiplier * 1024 * 1024  # 3 MB

        try:
            response = session.get(download_url, stream=True, timeout=10)
            response.raise_for_status()

            total_length = int(response.headers.get('content-length', 0))
            downloaded = 0
            self.install_progress_frame.pack(fill='x', pady=(0, 10))

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.cancel_event_install.is_set():
                        self.queue.put('INSTALLATION_CANCELED')
                        return

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = (downloaded / total_length) * 100
                        self.install_progress_var.set(percent)
                        self.queue.put(percent)

            extracted_path = os.path.join(BLENDER_DIR, version)

            if not os.path.exists(extracted_path):
                os.makedirs(extracted_path)

            if file_name.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    root_items = zip_ref.namelist()
                    top_level_dirs = set(item.split('/')[0] for item in root_items if item.strip())
                    if len(top_level_dirs) == 1:
                        root_folder = list(top_level_dirs)[0]
                        for member in zip_ref.infolist():
                            member_path = member.filename
                            if member_path.startswith(root_folder + '/'):
                                relative_path = member_path[len(root_folder) + 1:]  
                                if relative_path:
                                    target_path = os.path.join(extracted_path, relative_path)
                                    if member.is_dir():
                                        os.makedirs(target_path, exist_ok=True)
                                    else:
                                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                                        with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                                            shutil.copyfileobj(source, target)
                    else:
                        zip_ref.extractall(extracted_path)
            elif file_name.endswith(('.tar.gz', '.tar.xz')):
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    root_items = tar_ref.getnames()
                    top_level_dirs = set(item.split('/')[0] for item in root_items if item.strip())
                    if len(top_level_dirs) == 1:
                        root_folder = list(top_level_dirs)[0]
                        for member in tar_ref.getmembers():
                            if member.name.startswith(root_folder + '/'):
                                relative_path = member.name[len(root_folder) + 1:]
                                if relative_path:
                                    member.name = relative_path 
                                    tar_ref.extract(member, extracted_path)
                    else:
                        tar_ref.extractall(extracted_path)
            else:
                self.queue.put(('ERROR', "Unsupported file format."))
                return

            self.queue.put(('INSTALLATION_SUCCESS', version, extracted_path))

        except requests.exceptions.RequestException as e:
            print("Download error:", str(e))
            self.queue.put('INSTALLATION_FAILED')
        finally:
            self.is_installing = False
            self.cancel_event_install.clear()
            session.close()
            self.queue.put('DOWNLOAD_COMPLETE')





    # ----------------CHECK QUEUE----------------#

    def check_queue(self):
        try:
            while True:
                message = self.queue.get_nowait()
                

                if isinstance(message, float):
                    self.install_progress_var.set(message)
                    
                    self.update_idletasks()

                elif message == 'DOWNLOAD_COMPLETE':
                    self.install_progress_var.set(100)
                    self.install_progress_frame.pack_forget()
                    self.cancel_button.pack_forget()
                    self.install_btn.configure(text='Install', state='normal')
                    self.is_installing = False
                     
                    file_name = os.path.basename(self.download_links.get(self.tree.item(self.tree.selection(), "values")[0]))
                    file_path = os.path.join(BLENDER_MANAGER_DIR, file_name)
                    if os.path.exists(file_path):
                        try:
                            time.sleep(5)
                            os.remove(file_path)
                            print(f"Removed Archive: {file_path}")
                        except Exception as e:
                            print(f"Error removing Archive: {e}")
                            

                elif message == 'INSTALLATION_CANCELED':
                    self.install_progress_frame.pack_forget()
                    self.cancel_button.pack_forget()
                    self.is_installing = False
                    self.install_btn.configure(text='Install', state='normal')
                    self.cancel_event_install.clear()  
                    self.install_progress_var.set(0)
                    self.update_idletasks()
                    self.queue.task_done()
                    self.after(0, lambda: messagebox.showinfo("Canceled", "Installation has been canceled."))


                    file_name = os.path.basename(self.download_links.get(self.tree.item(self.tree.selection(), "values")[0]))
                    file_path = os.path.join(BLENDER_MANAGER_DIR, file_name)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            print(f"Removed incomplete download: {file_path}")
                        except Exception as e:
                            print(f"Error removing incomplete download: {e}")

                elif message == 'INSTALLATION_FAILED':
                    self.install_progress_frame.pack_forget()
                    self.cancel_button.pack_forget()
                    self.is_installing = False
                    self.cancel_event.clear()
                    self.install_btn.configure(text='Install', state='normal')
                    self.install_progress_var.set(0)
                    self.update_idletasks()
                    self.queue.task_done()
                    self.after(0, lambda: messagebox.showerror("Error", "Installation failed."))
                    file_name = os.path.basename(self.download_links.get(self.tree.item(self.tree.selection(), "values")[0]))
                    file_path = os.path.join(BLENDER_MANAGER_DIR, file_name)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            print(f"Removed incomplete download: {file_path}")
                        except Exception as e:
                            print(f"Error removing incomplete download: {e}")




                elif isinstance(message, tuple) and message[0] == 'INSTALLATION_SUCCESS':
                    version = message[1]
                    extracted_path = message[2]
                    self.install_progress_frame.pack_forget()
                    self.cancel_button.pack_forget()
                    self.is_installing = False
                    self.install_btn.configure(text='Install', state='normal')
                    self.cancel_event.clear()
                    self.install_progress_var.set(0)
                    self.update_idletasks()
                    self.queue.task_done()
                    self.after(0, lambda: messagebox.showinfo("Success", f"Successfully installed Blender {version}."))




                elif isinstance(message, tuple) and message[0] == 'UPDATE_TREEVIEW':
                    versions = message[1]
                    links = message[2]
                    dates = message[3]

                    def parse_version(version):
                        try:
                            version_number = version.split(" ")[1]
                            if all(part.isdigit() for part in version_number.split(".")):
                                return list(map(int, version_number.split(".")))
                            else:
                                return [0]
                        except (IndexError, ValueError):
                            return [0]

                    sorted_versions = sorted(versions, key=parse_version, reverse=True)

                    self.tree.delete(*self.tree.get_children())
                    for version in sorted_versions:
                        release_date = dates.get(version, "Unknown Date")
                        self.tree.insert("", "end", values=(version, release_date))
                        self.download_links[version] = links[version]

                    self.queue.task_done()



                    
                elif isinstance(message, tuple):
                    if message[0] == 'ERROR':
                        error_msg = message[1]
                        messagebox.showerror("Error", error_msg)
                    elif message[0] == 'UPDATE_TREEVIEW':
                        versions = message[1]
                        links = message[2]
                        self.tree.delete(*self.tree.get_children())
                        for version in versions:
                            self.tree.insert("", "end", values=(version,))
                            self.download_links[version] = links[version]


                    


        except queue.Empty:
            pass
        self.after(100, self.check_queue)

        #-----------------------------------------------------------------------------------------#


def log_error_to_file(error_message):
    
    if getattr(sys, 'frozen', False):  
        log_file_path = os.path.join(os.path.dirname(sys.executable), "log.txt")
    else:
       
        log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.txt")
    
    try:
        with open(log_file_path, "a") as f:  
            f.write(error_message + "\n")
    except Exception as e:
        print(f"Log file write error: {e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()

    try:
        app = BlenderManagerApp()
        app.mainloop()
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}\n"
        error_message += traceback.format_exc()  
        log_error_to_file(error_message) 
        print("An error occurred. Check log.txt for more details.")
