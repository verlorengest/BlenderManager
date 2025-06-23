# -*- coding: utf-8 -*-

import time
import os
start_time = time.time()




def get_blender_config_path():
    """Determine Blender configuration path based on the operating system."""
    import platform
    system = platform.system()
    if system == "Windows":
        appdata = os.getenv("APPDATA")
        if appdata:
            return os.path.join(appdata, "Blender Foundation", "Blender")
        else:
            raise EnvironmentError("APPDATA environment variable is not set.")
    elif system == "Darwin": 
        paths_to_check = [
            os.path.expanduser("~/Library/Application Support/Blender"),
            "/Applications/Blender.app/Contents/Resources/config",
            os.path.expanduser("~/.blender")  
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                return path

        raise EnvironmentError("Blender configuration path not found on MacOS.")

    elif system == "Linux":

        paths_to_check = [
            os.path.expanduser("~/.config/blender"),
            os.path.expanduser("~/.blender"),  
            "/usr/share/blender/config"  
        ]

        for path in paths_to_check:
            if os.path.exists(path):
                return path

        raise EnvironmentError("Blender configuration path not found on Linux.")

    else:
        raise EnvironmentError(f"Unsupported operating system: {system}")






import sys
import tkinter as tk
from tkinter import Button, ttk, messagebox, filedialog
import tkinter.simpledialog as simpledialog
from tkinterdnd2 import TkinterDnD, DND_FILES
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import pystray
import tarfile
from datetime import datetime
import shutil
import subprocess
import zipfile 
import threading
import queue 
import json
import re
import multiprocessing
import tempfile
import platform
import ctypes
from ctypes import wintypes

class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("Flags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int),
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t),
    ]

def enable_dark_mode(hwnd):
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20  
    dark_mode = ctypes.c_int(1)  
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_USE_IMMERSIVE_DARK_MODE,
        ctypes.byref(dark_mode),
        ctypes.sizeof(dark_mode)
    )




CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), ".BlenderManager", "config.json")
DEFAULT_SETTINGS = {
    "version": "1.0.2",
    "selected_theme": "darkly",
    "auto_update_checkbox": True,
    "bm_auto_update_checkbox": False,
    "launch_on_startup":False,
    "run_in_background": True,
    "chunk_size_multiplier": 3,
    "window_alpha": 0.98,
    "treeview_font_size": 12,
    "treeview_heading_font_size": 10,
    "treeview_font_family": "Segoe UI",
    "button_font_family": "Segoe UI",
    "button_font_size": 11,
    "show_addon_management": True,
    "show_project_management": True,
    "show_render_management": True,
    "show_version_management": True,
    "show_worktime_label": True,
    "auto_activate_plugin": True
}

BLENDER_MANAGER_DIR = os.path.join(os.path.expanduser("~"), ".BlenderManager")
BLENDER_DIR = os.path.join(os.path.expanduser("~"), ".BlenderManager", 'BlenderVersions')
NOTES_FILE_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'paths', "render_notes.json")
APPDATA_RENDER_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'renders')
RENDERFOLDER_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'paths', 'renderfolderpath.json')
PROJECT_RUNTIME_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'mngaddon', 'project_time.json')
BASE_MESH_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'paths', 'base_mesh_path.json')
BLENDER_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'blender')
BLENDER_ABSOLUTE_PATH = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'blender', 'blender.exe')




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

print(f"classes loaded in {time.time() - start_time:.2f} seconds.")
class BlenderManagerApp(TkinterDnD.Tk):
    
    def __init__(self):
        
        super().__init__()
        
       
        self.tray_name = "Blender Manager"
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.check_existing_window_and_tray()
        self.title("Blender Manager")  
        self.geometry("800x550")              
        self.minsize(800, 550)
        self.maxsize(1920, 1080)
        self.style = ttkb.Style() 
        self.load_settings_on_begining()
        self.iconbitmap(r"Assets/Images/bmng.ico")
        self.attributes('-fullscreen', False) 
        if platform.system() == "Windows":
            hwnd = ctypes.windll.user32.FindWindowW(None, "Blender Manager")
        else:
            hwnd=None
        if os.name == 'nt':
            enable_dark_mode(hwnd)
        self.schedule_tray_icon_creation()
        self.after(100, self.check_queue)
        self.base_install_dir = os.path.join(os.path.expanduser("~"), '.BlenderManager')
        self.blender_install_dir = os.path.join(self.base_install_dir, 'blender')
        self.style = ttkb.Style() 
        self.current_folder = self.get_render_folder_path()      
    








        def load_heavy_components(self):
            self.create_widgets()
            self.notes_data = self._load_notes()
            self.menu_cache = {}
            self.load_menu_cache()
            self.redirect_output()

            with open(BASE_MESH_PATH, 'r') as file:
                self.base_meshes = json.load(file)



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
            'Zephyr': 'zephyr',
            'Disgusting': 'disgusting',
            'Modern': 'modern',
            'Neon Glow':'neon_glow',
            'Retro Wave': 'retro_wave',
            'Pastel Dream': 'pastel_dream',
            'Minimal Modern': 'minimal_modern',
            'pure_black':'pure_black',
            'midnight_blue':'midnight_blue',
            'baby_blue': 'baby_blue',
            'Blender': 'blender',
            'plasticity':'plasticity',
            'clown_fiesta':'clown_fiesta',
            'vomit_vibes': 'vomit_vibes',
            'radioactive_swamp': 'radioactive_swamp',
            'painful_pink': 'painful_pink',
            'toxic_circus': 'toxic_circus',
            'rainbow': 'rainbow',
            'smoothie': 'smoothie',
            'cream_pastel': 'cream_pastel'


        }
        threading.Thread(target=load_heavy_components, args=(self,), daemon=True).start()
        self.is_installing = False
        self.cancel_event_main = threading.Event() 
        self.cancel_event = threading.Event()
        self.cancel_event_install = threading.Event()
        self.queue = queue.Queue()
        
        self.check_queue()


        

    def bind_right_click(self, widget, callback):
        """Bind right-click events for cross-platform compatibility."""
        widget.bind("<Button-3>", callback)  # Windows/Linux
        if platform.system() == "Darwin":  # macOS
            widget.bind("<Button-2>", callback)  # Middle click on macOS
            widget.bind("<Control-Button-1>", callback)  # Ctrl+Click on macOS


        
     
        
    def get_blender_executable_path(self):
        """
        Determine the path to the Blender executable based on the operating system.
        If the executable is not found, prompt the user to install Blender.
        Returns:
            str: Full path to the Blender executable, or None if not found and user cancels installation.
        """
        import platform
        import os

        system = platform.system()
        base_blender_dir = os.path.join(os.path.expanduser("~"), ".BlenderManager", "blender")

        if system == "Windows":
            blender_exe = os.path.join(base_blender_dir, "blender.exe")
        elif system == "Darwin":  
            blender_exe = os.path.join(base_blender_dir, "Blender.app", "Contents", "MacOS", "Blender")
        elif system == "Linux":
            blender_exe = os.path.join(base_blender_dir, "blender")
        else:
            print(f"Unsupported operating system: {system}")
            return None

        if os.path.isfile(blender_exe):
            return blender_exe
        else:
            print(f"Blender executable not found at expected path: {blender_exe}")
            self.show_install_dialog()
            return None















#------------------------UPDATE CONTROL-----------------------------------------------

    def schedule_tray_icon_creation(self):
        """Schedules the creation of the tray icon after a 5-second delay."""
        self.after(3000, self.create_tray_icon)  








    def bm_show_loading_screen(self):
        """Show a loading screen during the update process."""
        self.loading_window = tk.Toplevel(self)
        self.loading_window.title("Updating Blender Manager")
        self.loading_window.geometry("300x150")
        self.loading_window.resizable(False, False)
        self.loading_window.iconbitmap(r"Assets/Images/bmng.ico")

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
        import requests

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
        import requests
        """Download and install the update."""
        current_os = platform.system().lower()
        supported_systems = {
            'windows': 'windows',
            'darwin': 'macos',
            'linux': 'linux'
        }

        if current_os not in supported_systems:
            print(f"Update Error: Unsupported operating system: {current_os}")
            messagebox.showerror("Error", f"Unsupported operating system: {current_os}")
            return

        os_suffix = supported_systems[current_os]
        download_url = f"https://github.com/verlorengest/BlenderManager/releases/download/v{version}/blender_manager_v{version}_{os_suffix}.zip"

        app_dir = os.getcwd()
        zip_path = os.path.join(app_dir, f"blender_manager_v{version}.zip")

        try:
            self.bm_show_loading_screen()

            try:
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Update Error: Failed to download update. Error: {e}")
                messagebox.showerror("Error", f"Failed to download update: {e}")
                return

            try:
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                with open(zip_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                self.loading_progress_var.set(progress)
                                self.loading_window.update_idletasks()
            except Exception as e:
                print(f"Update Error: Failed to save update file. Error: {e}")
                messagebox.showerror("Error", f"Failed to save update file: {e}")
                return

            try:
                python_executable = sys.executable
                updater_exe = os.path.join(app_dir, 'updater.exe')
                updater_script = os.path.join(app_dir, 'updater.py')

                if os.path.exists(updater_exe):
                    cmd = [updater_exe, '--zip-path', zip_path]
                elif os.path.exists(updater_script):
                    cmd = [python_executable, updater_script, '--zip-path', zip_path]
                else:
                    print("Update Error: No updater file found (updater.exe or updater.py).")
                    messagebox.showerror("Error", "No updater file found (updater.exe or updater.py).")
                    return

                subprocess.Popen(cmd)
            except Exception as e:
                print(f"Update Error: Failed to run update script. Error: {e}")
                messagebox.showerror("Error", f"Failed to run update script: {e}")
                return

            os._exit(0)

        except Exception as e:
            print(f"Update Error: Unexpected error occurred. Error: {e}")
            messagebox.showerror("Error", f"Unexpected error occurred: {e}")
        finally:
            self.bm_close_loading_screen()





#--------------------------------------------------------------------------------------------------




    def initialize_app(self):
        """Initialize the application."""
        print("Initializing app in thread:", threading.current_thread().name)
        self.task_queue = queue.Queue()  

        def background_task():
            """Runs heavy initialization tasks in a background thread."""
            print("Background task running in thread:", threading.current_thread().name)


            try:
                setup_complete_file = os.path.join(os.path.expanduser("~"), ".BlenderManager", "setup_complete")
                if os.path.exists(setup_complete_file):
                    print("Setup already complete. Skipping initialization.")
                    self.task_queue.put(self.finalize_initialization)
                    return

                base_dir = BLENDER_MANAGER_DIR
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir)

                required_dirs = [
                    "BlenderVersions", "mngaddon",
                    "paths"
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
                self.task_queue.put(self.finalize_initialization) 

        threading.Thread(target=background_task, daemon=True).start()

        self.check_task_queue()

    def check_task_queue(self):
        """Periodically checks the task queue and executes tasks in the main thread."""
        try:
            while not self.task_queue.empty():
                task = self.task_queue.get_nowait() 
                task()  
        except queue.Empty:
            pass
        self.after(100, self.check_task_queue)  

    def finalize_initialization(self):
        """Finalize the initialization by showing the main window."""
        print("Finalizing initialization...")
        self.deiconify()  
        self.show_window()  

    def load_menu_cache(self):
        try:
            try:
                self.menu_cache['plugins'] = self.refresh_plugins_list()
            except Exception as e:
                print(f"Error loading plugins: {e}")
                self.menu_cache['plugins'] = []

            try:
                self.menu_cache['projects'] = self.refresh_projects_list()
            except Exception as e:
                print(f"Error loading projects: {e}")
                self.menu_cache['projects'] = []
                
            try:
                self.menu_cache['installed_versions'] = self.get_installed_versions()
            except Exception as e:
                print(f"Error loading installed versions: {e}")
                self.menu_cache['installed_versions'] = []

        except Exception as e:
            print(f"Unexpected error while loading menu cache: {e}")

                    

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
        self.show_worktime_label_var = tk.BooleanVar(value=self.settings.get("show_worktime_label", True))
        self.auto_activate_plugin_var = tk.BooleanVar(value=self.settings.get("auto_activate_plugin", True))
        self.chunk_size_multiplier = self.settings.get("chunk_size_multiplier", 3)
        self.window_alpha = self.settings.get("window_alpha", 0.98)
        self.attributes("-alpha", self.window_alpha)
        self.treeview_font_family = self.settings.get("treeview_font_family", "Segoe UI")
        self.treeview_font_size = self.settings.get("treeview_font_size", 12)
        self.treeview_heading_font_size = self.settings.get("treeview_heading_font_size", 14)
        self.button_font_family = self.settings.get("button_font_family", "Segoe UI")
        self.button_font_size = self.settings.get("button_font_size", 14)

        self.apply_custom_styles()


    def main_menu_loader_thread(self):
        """Arka planda Main Menu tabını yükle."""
        self.main_menu_tab = ttk.Frame(self.notebook)
        self.after(0, lambda: self.notebook.insert(0, self.main_menu_tab, text="Main Menu"))
    
        thread = threading.Thread(target=self.main_menu_loader, daemon=True)
        thread.start()

        self.after(0, lambda: self.notebook.select(self.main_menu_tab))

    def main_menu_loader(self):
        """Main Menu'nun içeriğini yükle."""
        start_time = time.time()

        self.create_main_menu()
    
        if os.path.exists(BLENDER_ABSOLUTE_PATH):
            self.update_blender_version_label()
    
        print(f"Main menu loaded in {time.time() - start_time:.2f} seconds.")

    def get_installed_versions(self):
        versions = []
        if os.path.exists(BLENDER_DIR):
            versions = [d for d in sorted(os.listdir(BLENDER_DIR)) if os.path.isdir(os.path.join(BLENDER_DIR, d))]
        return versions
    

    def create_widgets(self):
        """Create the GUI layout."""
        main_frame = ttkb.Frame(self, padding=(0, 0, 0, 0))
        main_frame.pack(expand=1, fill="both")
        
        self.style.configure("TNotebook.Tab", font=(self.button_font_family, 10))
        self.notebook = ttkb.Notebook(main_frame)
        self.notebook.pack(expand=1, fill="both")

        threading.Thread(target=self.main_menu_loader_thread, daemon=True).start()

        start_time = time.time()
        threads = []
        for tab_name, is_visible in self.tab_visibility_settings.items():
            if is_visible:
                thread = threading.Thread(
                    target=self.toggle_tab_visibility_thread_safe,
                    args=(tab_name, tk.BooleanVar(value=True)),  
                    daemon=True
                )
                thread.start()
                threads.append(thread)

        for thread in threads:
            thread.join()


        self.logs_tab = ttkb.Frame(self.notebook)
        self.notebook.add(self.logs_tab, text="Logs")
        self.create_logs_tab()

        print(f"All tabs loaded in {time.time() - start_time:.2f} seconds.")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.current_version = self.bm_load_current_version()
        self.latest_version = None
        threading.Thread(target=self.after_widget_check_bm_updates, daemon=True).start()


    def toggle_tab_visibility_thread_safe(self, tab_name, var):
        """Wrapper to call toggle_tab_visibility in a thread-safe manner."""
        self.after(0, lambda: self.toggle_tab_visibility(tab_name, var))




    def after_widget_check_bm_updates(self):
        """Check for updates in a background thread."""
        if self.settings.get("bm_auto_update_checkbox", True):
            print("Checking Blender Manager updates...")
            self.bm_check_for_updates_threaded()

        if self.auto_update_var.get():
            print(f"Auto Update: {self.auto_update_var.get()}")
            self.auto_update()
        else:
            print(f"Auto Update: {self.auto_update_var.get()}")




    def find_window_with_tray_name(self, tray_name):
        import ctypes

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
        
        import platform

        try:
            
            if platform.system() == "Windows":
                import win32gui
                import win32con

                if hwnd:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                else:
                    hwnd = win32gui.FindWindow(None, self.tray_name)
                    if hwnd:
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                    else:
                        print("Window not found.")
            else:
                if platform.system() == "Darwin":  
                    from AppKit import NSApplication, NSRunningApplication, NSApplicationActivateIgnoringOtherApps
                    from Foundation import NSBundle

                    bundle = NSBundle.mainBundle()
                    app = NSRunningApplication.runningApplicationWithProcessIdentifier_(os.getpid())
                    app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                    print("Window brought to front on macOS.")
                else:
                    print("Bringing window to front is not supported on this platform.")
        except Exception as e:
            print(f"Error bringing window to front: {e}")





    def check_existing_window_and_tray(self):
        import psutil
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
        from PIL import Image, ImageTk
        image = Image.open(r"Assets/Images/bmng.ico")
        self.tray_icon = pystray.Icon(
            "BlenderManager", image, "Blender Manager", self.create_tray_menu()
        )
        self.tray_icon.on_click = self.show_window  
        self.tray_icon.run_detached()

    def create_tray_menu(self):
        project_menu_items = []
        for item in self.recent_projects_tree.get_children():
            project_name = self.recent_projects_tree.item(item, "values")[0]
            project_menu_items.append(pystray.MenuItem(project_name, self.show_project_info))

        return pystray.Menu(
            pystray.MenuItem("Show Blender Manager", self.show_window, default=True),
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
        self.deiconify()




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
        button_font_family = self.button_font_family
        treeview_font_family = self.treeview_font_family

        style = ttk.Style()
        style.configure(
            "custom_render_treeview",
            font=(treeview_font_family, 12), 
            rowheight=25  
        )
        style.configure(
            "custom_render_treeview.Heading",
            font=(treeview_font_family, 14, "bold") 
        )

        render_list_label = ttk.Label(render_list_frame, text="Render List", font=(button_font_family, 14, "bold"))
        render_list_label.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))

       
        self.render_tree = ttk.Treeview(
            render_list_frame,
            columns=("File Size", "Resolution", "File Date"),
            show="tree headings",
            selectmode='browse',
            style="custom_render_treeview"  
        )

        self.render_tree.heading("#0", text="Name", anchor="w") 
        self.render_tree.column("#0", anchor="w", stretch=True, minwidth=150)

        self.render_tree.heading("File Size", text="File Size", anchor="center")
        self.render_tree.column("File Size", anchor="center", stretch=True, minwidth=100)

        self.render_tree.heading("Resolution", text="Resolution", anchor="center")
        self.render_tree.column("Resolution", anchor="center", stretch=True, minwidth=100)

        self.render_tree.heading("File Date", text="File Date", anchor="center")
        self.render_tree.column("File Date", anchor="center", stretch=True, minwidth=150)

        self.render_tree.grid(row=1, column=0, sticky="nsew", padx=3, pady=(0, 0))

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

        preview_label = ttk.Label(right_frame, text="Render Preview", font=(button_font_family, 14, "bold"))
        preview_label.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))

        self.preview_frame = ttk.Frame(right_frame, relief="solid", borderwidth=0, width=1200, height=1000)
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 0))
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.rowconfigure(0, weight=1)

        self.preview_label = ttk.Label(self.preview_frame, text="No Preview Available", anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        buttons_frame = ttk.Frame(right_frame) 
        buttons_frame.grid(row=2, column=0, sticky="ew", padx=3, pady=(0, 0))
        buttons_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="button")

        open_button = ttk.Button(buttons_frame, text="Open", takefocus=False, command=self.open_render)
        open_button.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        refresh_button = ttk.Button(buttons_frame, text="Refresh", takefocus=False, command=self.refresh_render_list)
        refresh_button.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        browse_button = ttk.Button(buttons_frame, text="Browse", takefocus=False, command=self.browse_render_directory)
        browse_button.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        delete_button = ttk.Button(buttons_frame, text="Delete", takefocus=False, command=self.delete_render)
        delete_button.grid(row=0, column=3, sticky="nsew", padx=5, pady=5)

        # ====== Render Notes Section (Bottom) ======
        notes_frame = ttk.Frame(render_frame)
        notes_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=(10, 0))
        notes_frame.columnconfigure(0, weight=1)
        notes_frame.rowconfigure(1, weight=1)

        notes_label = ttk.Label(notes_frame, text="Render Notes", font=(button_font_family, 14, "bold"))
        notes_label.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))

        self.notes_text = tk.Text(notes_frame, height=5, wrap="word", font=(button_font_family, 10))
        self.notes_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))

        notes_scrollbar = ttk.Scrollbar(notes_frame, orient="vertical", command=self.notes_text.yview)
        self.notes_text.configure(yscrollcommand=notes_scrollbar.set)
        notes_scrollbar.grid(row=1, column=1, sticky="ns", pady=(0,5))

        save_note_button = ttk.Button(notes_frame, text="Save Note", takefocus=False, command=self.save_current_note)
        save_note_button.grid(row=2, column=0, sticky="ew", padx=5, pady=(5, 0))

        render_frame.grid_propagate(True)
        self.render_file_paths = {}
        self.refresh_render_list()

        self.render_tree.bind("<<TreeviewSelect>>", self.display_selected_render)

        self.notes_data = self._load_notes()



        #--------------Render Menu Methods--------------
        



    def refresh_render_list(self):
        """Refresh the Render List by reloading the current directory files and folders in a parent-child hierarchy."""
        from PIL import Image

        if not hasattr(self, 'current_folder') or not self.current_folder:
            messagebox.showwarning("No Folder Loaded", "Please select a folder to load renders first.")
            return

        if not os.path.exists(self.current_folder):
            os.makedirs(self.current_folder, exist_ok=True)

        self.render_tree.delete(*self.render_tree.get_children())
        self.render_file_paths.clear()
        print(f"Cleared Treeview and reset file paths for folder: {self.current_folder}")

        def add_items_to_treeview(parent_item, current_path):
            """Recursive function to add items (folders and files) to the Treeview."""
            for item_name in sorted(os.listdir(current_path)):
                item_path = os.path.join(current_path, item_name)

                if os.path.isdir(item_path): 
                    folder_id = self.render_tree.insert(
                        parent_item,
                        "end",
                        text=item_name,
                        values=("", "", ""),  
                        tags=('folder',)
                    )
                    add_items_to_treeview(folder_id, item_path)

                elif os.path.isfile(item_path) and item_name.lower().endswith(('.png', '.jpeg', '.jpg', '.mp4')):
                    try:
                        file_stats = os.stat(item_path)
                        file_date = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                        file_size = f"{file_stats.st_size / (1024 * 1024):.2f} MB"
                        file_extension = os.path.splitext(item_name)[1].lower()

                        if file_extension in ['.png', '.jpeg', '.jpg']:
                            with Image.open(item_path) as img:
                                resolution = f"{img.width}x{img.height}"
                        elif file_extension == '.mp4':
                            resolution = "N/A"
                        else:
                            resolution = "N/A"

                        file_id = self.render_tree.insert(
                            parent_item,
                            "end",
                            text=item_name,
                            values=(file_size, resolution, file_date),
                            tags=('file',)
                        )
                        self.render_file_paths[file_id] = item_path

                    except Exception as e:
                        print(f"Error processing file: {item_name}, {e}")
                        messagebox.showerror("Error", f"Error processing file {item_name}: {e}")
                        continue

        root_item = self.render_tree.insert("", "end", text=os.path.basename(self.current_folder), open=True, tags=('folder',))
        add_items_to_treeview(root_item, self.current_folder)

        first_item = self.render_tree.get_children()
        if first_item:
            self.render_tree.selection_set(first_item[0])
            self.render_tree.focus(first_item[0])
            self.render_tree.event_generate("<<TreeviewSelect>>")






    def sort_treeview(self, column, reverse):
        """Sort TreeView items based on the specified column, keeping folders at the top."""
        def is_folder(item):
            """Check if a Treeview item is a folder."""
            return self.render_tree.item(item, "values") == ("", "", "")

        def sort_items(parent_item):
            """Sort items under a specific parent item."""
            items = [
                (self.render_tree.item(item, "text" if column == "#0" else "values")[0], item)
                for item in self.render_tree.get_children(parent_item)
            ]

            folders = [(text, item) for text, item in items if is_folder(item)]
            files = [(text, item) for text, item in items if not is_folder(item)]

            if column == "File Size":
                files.sort(key=lambda x: float(x[0].replace(" MB", "")) if x[0] and " MB" in x[0] else 0, reverse=reverse)
            elif column == "File Date":
                files.sort(key=lambda x: x[0], reverse=reverse)
            elif column == "Resolution":
                files.sort(key=lambda x: x[0], reverse=reverse)
            else:  
                folders.sort(key=lambda x: x[0].lower(), reverse=reverse)
                files.sort(key=lambda x: x[0].lower(), reverse=reverse)

            sorted_items = folders + files
            for index, (_, item) in enumerate(sorted_items):
                self.render_tree.move(item, parent_item, index)
                sort_items(item)

        sort_items("")
        self.render_tree.heading(column, command=lambda: self.sort_treeview(column, not reverse))

  

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
        """Open a dialog to select a folder and display files and folders in a parent-child relationship."""
        from PIL import Image, ImageTk

        folder_path = filedialog.askdirectory(initialdir=APPDATA_RENDER_PATH, title="Select Render Folder")
        if not folder_path:
            return

        self.current_folder = folder_path
        self.save_render_folder_path(folder_path)

        self.render_tree.delete(*self.render_tree.get_children())
        self.render_file_paths.clear()

        def add_items(parent_item, path):
            """Recursive function to add files and folders to the Treeview."""
            for item_name in sorted(os.listdir(path)):
                item_path = os.path.join(path, item_name)
                if os.path.isdir(item_path):  
                    folder_id = self.render_tree.insert(
                        parent_item, "end", text=item_name, values=("", "", ""), tags=('folder',)
                    )
                    add_items(folder_id, item_path)  
                elif os.path.isfile(item_path) and item_name.lower().endswith(('.png', '.jpeg', '.jpg', '.mp4')):
                    try:
                        file_stats = os.stat(item_path)
                        file_date = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                        file_size = f"{file_stats.st_size / (1024 * 1024):.2f} MB"
                        file_extension = os.path.splitext(item_name)[1].lower()

                        if file_extension in ['.png', '.jpeg', '.jpg']:
                            with Image.open(item_path) as img:
                                resolution = f"{img.width}x{img.height}"
                        elif file_extension == '.mp4':
                            resolution = "N/A"
                        else:
                            resolution = "N/A"

                        file_id = self.render_tree.insert(
                            parent_item,
                            "end",
                            text=item_name,
                            values=(file_size, resolution, file_date),
                            tags=('file',)
                        )
                        self.render_file_paths[file_id] = item_path

                    except PermissionError:
                        messagebox.showwarning("Permission Denied", f"Cannot access file: {item_name}")
                        continue
                    except Exception as e:
                        messagebox.showerror("Error", f"Error processing file {item_name}: {e}")
                        continue

        root_item = self.render_tree.insert("", "end", text=os.path.basename(folder_path), open=True, tags=('folder',))
        add_items(root_item, folder_path)

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
            messagebox.showwarning("No Selection", "Please select a render to preview.")
            return

        file_path = self.render_file_paths.get(selected_item)
        if not file_path or not os.path.exists(file_path):
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
        from PIL import Image, ImageTk

        try:
            img = Image.open(file_path)
            frame_width = self.preview_frame.winfo_width() or 500
            frame_height = self.preview_frame.winfo_height() or 500
            img.thumbnail((frame_width, frame_height), Image.Resampling.LANCZOS)

            self.render_image = ImageTk.PhotoImage(img)

            self.preview_label.config(image=self.render_image, text="")
            print("Image displayed successfully.")

            if hasattr(self, 'video_player') and self.video_player:
                self.video_player.destroy()

        except Exception as e:
            print(f"Error displaying image: {e}")
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
            else:
                messagebox.showerror("Video Playback Error", "Unsupported operating system for video playback.")

        except FileNotFoundError:
            messagebox.showerror("Video Playback Error", "The video file could not be found.")
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
            render_name = self.render_tree.item(selected_item, 'text')  
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
            font=(button_font_family, 14),
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
            font=(button_font_family, 10),
            padding=(5, 2),
            borderwidth=0  
        )

        self.buttons_frame = ttkb.Frame(self.main_menu_frame)
        self.buttons_frame.grid(row=0, column=0, sticky="n", padx=(0, 10), pady=(5, 0))  
        

        self.launch_button = ttkb.Button(
            self.buttons_frame,
            text="Launch Blender",
            takefocus=False,
            command=self.launch_latest_blender,
            style='Green.TButton',
            bootstyle=SUCCESS,
            width=15
        )
        self.launch_button.grid(row=1, column=0, pady=(30, 5), sticky="ew", ipady=5)  
        self.bind_right_click(self.launch_button, self.launch_right_click_menu)



        self.create_project_button = ttkb.Button(
            self.buttons_frame,
            text="Create Project",
            takefocus=False,
            command=self.open_create_project_window,
            style='Custom.Large.TButton',
            bootstyle=SUCCESS,
            width=15
        )
        self.create_project_button.grid(row=2, column=0, pady=(10, 5), sticky="ew")

  
        self.update_button = ttkb.Button(
            self.buttons_frame,
            text="Check Updates",
            takefocus=False,
            command=self.check_for_updates,
            style='Custom.Large.TButton',
            bootstyle=PRIMARY,  
            width=15 
        )
        self.update_button.grid(row=3, column=0, pady=(10, 5), sticky="ew")

       
        self.cancel_button_main = ttkb.Button(
            self.buttons_frame,
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
            self.buttons_frame,
            orient="horizontal",
            length=100,  
            mode="determinate",
            variable=self.progress_var,
            bootstyle=WARNING
        )
        self.progress_bar.grid(row=8, column=0, pady=(4, 0), sticky="ew")  
        self.progress_bar.grid_remove() 
        
        self.progress_label = ttkb.Label(
            self.buttons_frame,
            text="Updating",
            anchor="center",
            style="Custom.Large.TLabel",
            font=(button_font_family, 10)
        )
        self.progress_label.grid(row=9, column=0, sticky="ew", pady=(0, 3))
        self.progress_label.grid_remove()



        self.settings_button = ttkb.Button(
            self.buttons_frame,
            text="⚙️",
            takefocus=False,
            command=self.open_settings_window,
            style='Custom.Large.TButton',
            width=5  
        )
        self.settings_button.grid(row=5, column=0, pady=(10, 5), sticky="w") 
        
        self.help_button = ttkb.Button(
            self.buttons_frame,
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
            font=(button_font_family, 12)
        )
        projects_label.pack(side="left")

        self.work_hours_label = ttkb.Label(
            projects_label_frame,
            text="  ",
            style='Custom.Large.TLabel',
            font=(button_font_family, 12)
        )
        self.work_hours_label.pack(side="left", padx=(10, 0))  
        
        if not self.show_worktime_label_var.get(): 
            self.work_hours_label.pack_forget()
        

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

        projects_frame.grid_columnconfigure(0, weight=1)
        projects_frame.grid_rowconfigure(0, weight=1)

        self.bind_right_click(self.recent_projects_tree, self.show_context_menu)


        recent_projects = self.load_recent_projects()
        for project in recent_projects:
            project_name, last_opened, project_path = project
            self.recent_projects_tree.insert("", "end", values=(project_name, last_opened, project_path))

        self.recent_projects_tree.bind("<Double-1>", self.on_project_double_click)


        self.release_notes_label = ttkb.Label(
            self.buttons_frame,
            text="See Release Notes",
            cursor="hand2",  
            style="Custom.Large.TLabel",
            font=(self.button_font_family, 10, "underline"),  
            foreground="blue"  
        )

        self.release_notes_label.grid(row=10, column=0, pady=(10, 0), sticky="ew")
        self.release_notes_label.bind("<Button-1>", self.show_main_update_release_notes)
        self.release_notes_label.grid_remove()  
        self.progress_label.grid_forget()


        self.bm_version_frame = ttkb.Frame(self.buttons_frame)
        self.bm_version_frame.place(relx=0.01, rely=2.0, anchor="s")  

        self.bm_version_label = ttkb.Label(
            self.main_menu_frame,
            text=f"BManager v{DEFAULT_SETTINGS['version']}",
            style='Custom.Large.TLabel',
            font=(self.button_font_family, 8)
        )
        self.bm_version_label.place(relx=0.00005, rely=0.98, anchor="sw")

        self.blender_version_label = ttkb.Label(
            self.main_menu_frame,
            text="Blender Not Installed",
            cursor="hand2",
            style='Custom.Large.TLabel',
            font=(self.button_font_family, 8)
        )
        self.blender_version_label.place(relx=0.00005, rely=0.94, anchor="sw") 
        self.blender_version_label.bind("<Button-1>", self.show_main_release_notes)
        self.update_bm_version_label()


    def update_blender_version_label(self):
        """Updates the Blender version label with the installed version."""
        blender_version = self.get_installed_blender_version()
        if blender_version:
            blender_text_label = f"Blender {blender_version}"
        else:
            blender_text_label = "Blender Not Installed" 

        self.blender_version_label.config(text=blender_text_label)



    def update_bm_version_label(self):
        """Update the Blender Manager version label based on the current and latest versions."""
        current_version = self.settings.get("version", "0.0.0")
        latest_version = self.bm_get_latest_version()

        version_text = f"BManager v{current_version}"
    
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
        self.update_idletasks()  

    def on_version_label_click(self, event):
        """Handle click event on version label."""
        self.bm_check_for_updates_threaded()
        self.update_bm_version_label()  

    # --------Create Project Menu-----------






    def open_create_project_window(self):
        """Opens a new window for creating a project."""
        self.create_project_button.config(state='disabled')
    
        user_input_data = self.load_user_input_data()

        self.create_project_window = tk.Toplevel(self)
        self.create_project_window.title("Create Project")
        self.create_project_window.geometry("700x500")
        self.create_project_window.resizable(False, False)
        self.center_window(self.create_project_window, 700, 500)
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

        # --- Reference Images ---
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
            entry_value = user_input_data.get('reference_images', {}).get(position.lower(), '')
            entry.insert(0, entry_value)
            entry.grid(row=idx * 2, column=1, pady=5, sticky='w')
            self.reference_images[position.lower()] = entry
            browse_button = ttkb.Button(images_frame, text="Browse", command=lambda pos=position.lower(): self.browse_image(pos))
            browse_button.grid(row=idx * 2, column=2, padx=5, pady=5)

        # --- Base Mesh ---
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

        base_mesh_saved = user_input_data.get('base_mesh', '')
        if base_mesh_saved in self.base_meshes:
            self.base_mesh_var.set(base_mesh_saved)

        add_base_mesh_button = ttkb.Button(base_mesh_frame, text="Add Base Mesh", takefocus=False, command=self.open_add_base_mesh_window)
        add_base_mesh_button.grid(row=1, column=1, pady=10, sticky='w')

        # --- Settings ---
        settings_label = ttkb.Label(settings_tab, text="Settings", font=('Segoe UI', 14, 'bold'))
        settings_label.pack(pady=(10, 10))

        settings_frame = ttkb.LabelFrame(settings_tab, text="Project Settings", padding=10)
        settings_frame.pack(fill='both', expand=True, padx=20)

        self.add_light_var = tk.BooleanVar(value=user_input_data.get('add_light', False))
        add_light_checkbox = ttkb.Checkbutton(settings_frame, text="Add Light", variable=self.add_light_var)
        add_light_checkbox.grid(row=0, column=0, sticky='w', padx=10, pady=5)

        self.add_camera_var = tk.BooleanVar(value=user_input_data.get('add_camera', False))
        add_camera_checkbox = ttkb.Checkbutton(settings_frame, text="Add Camera", variable=self.add_camera_var)
        add_camera_checkbox.grid(row=1, column=0, sticky='w', padx=10, pady=5)

        project_name_label = ttkb.Label(settings_frame, text="Project Name:")
        project_name_label.grid(row=6, column=0, sticky='w', padx=10, pady=5)

        self.project_name_var = tk.StringVar(value=user_input_data.get('project_name', ''))
        self.project_name_entry = ttkb.Entry(settings_frame, textvariable=self.project_name_var, width=30)
        self.project_name_entry.grid(row=6, column=1, sticky='w', padx=10, pady=5)

        project_directory_label = ttkb.Label(settings_frame, text="Project Directory:")
        project_directory_label.grid(row=7, column=0, sticky='w', padx=10, pady=5)

        self.project_directory_var = tk.StringVar(value=user_input_data.get('project_dir', ''))
        self.project_directory_entry = ttkb.Entry(settings_frame, textvariable=self.project_directory_var, width=30, state='disabled')
        self.project_directory_entry.grid(row=7, column=1, sticky='w', padx=10, pady=5)

        browse_button = ttkb.Button(settings_frame, text="Browse", takefocus=False, command=self.browse_setproject_directory)
        browse_button.grid(row=7, column=2, sticky='w', padx=5, pady=5)
    
        self.auto_save_project_var = tk.BooleanVar(value=user_input_data.get('auto_save_project', False))
        auto_save_project_checkbox = ttkb.Checkbutton(settings_frame, text="Auto Save", variable=self.auto_save_project_var, command=self.toggle_autosave_settings)
        auto_save_project_checkbox.grid(row=2, column=0, sticky='w', padx=10, pady=5)

        autosave_style_label = ttkb.Label(settings_frame, text="Autosave Style:")
        autosave_style_label.grid(row=3, column=0, sticky='w', padx=10, pady=5)

        self.auto_save_style_var = tk.StringVar(value=user_input_data.get('auto_save_style', 'overwrite'))
        self.autosave_style_combobox = ttkb.Combobox(settings_frame, textvariable=self.auto_save_style_var, values=["overwrite", "separate"], state='disabled')
        self.autosave_style_combobox.grid(row=3, column=1, sticky='w', padx=10, pady=5)

        autosave_interval_label = ttkb.Label(settings_frame, text="Autosave Interval:")
        autosave_interval_label.grid(row=4, column=0, sticky='w', padx=10, pady=5)

        saved_interval = user_input_data.get('auto_save_interval', '5 minutes')
        self.auto_save_interval_var = tk.StringVar(value=saved_interval)
        self.autosave_interval_combobox = ttkb.Combobox(
            settings_frame,
            textvariable=self.auto_save_interval_var,
            values=["5 minutes", "15 minutes", "30 minutes", "1 hour", "2 hours", "3 hours", "6 hours", "12 hours", "24 hours"],
            state='disabled'
        )
        self.autosave_interval_combobox.grid(row=4, column=1, sticky='w', padx=10, pady=5)

        self.toggle_autosave_settings()

        self.create_button = ttkb.Button(self.create_project_window, text="Create Project", takefocus=False, command=self.create_project)
        self.create_button.pack(pady=10)

        self.create_project_window.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def browse_setproject_directory(self):
        directory = filedialog.askdirectory(title="Select Project Directory")
        if directory:
            self.project_directory_var.set(directory)

    def toggle_autosave_settings(self):
        """Enables or disables autosave-related settings based on the checkbox state."""
        state = 'normal' if self.auto_save_project_var.get() else 'disabled'
        self.autosave_style_combobox.config(state=state)
        self.autosave_interval_combobox.config(state=state)
        

    def convert_interval_to_seconds(self, interval_str):
        """Converts interval string like '5 minutes' to seconds."""
        if "minute" in interval_str:
            return int(interval_str.split()[0]) * 60
        elif "hour" in interval_str:
            return int(interval_str.split()[0]) * 3600
        else:
            return 300  


    def on_window_close(self):
        self.save_user_input_data()
        self.create_project_button.config(state='normal')
        self.create_project_window.destroy()


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
        self.create_button.config(state="disabled", text="Loading...")

        def perform_project_creation():
            try:
                images = {position: entry.get() for position, entry in self.reference_images.items() if entry.get()}
                base_mesh_name = self.base_mesh_var.get()
                base_mesh_path = self.base_meshes.get(base_mesh_name, '')
                add_light = self.add_light_var.get()
                add_camera = self.add_camera_var.get()
                project_name = self.project_name_var.get()
                project_dir = self.project_directory_var.get()
                auto_save_project = self.auto_save_project_var.get()
                auto_save_interval = self.auto_save_interval_var.get()
                auto_save_style = self.auto_save_style_var.get()

                interval_in_seconds = self.convert_interval_to_seconds(auto_save_interval) if auto_save_project else None

                data = {
                    'reference_images': images,
                    'base_mesh': {'name': base_mesh_name, 'path': base_mesh_path},
                    'add_light': add_light,
                    'add_camera': add_camera,
                    'project_name': project_name,
                    'project_dir': project_dir,
                    'auto_save_project': auto_save_project,
                    'auto_save_interval': interval_in_seconds,
                    'auto_save_style': auto_save_style
                }

                settings_dir = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'mngaddon')
                settings_file = os.path.join(settings_dir, 'settings.json')
                os.makedirs(settings_dir, exist_ok=True)

                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)

                self.save_user_input_data()

                time.sleep(2)
                self.launch_latest_blender()
            finally:
                self.create_button.config(state="normal", text="Create Project")
                self.create_project_window.destroy()
                self.create_project_button.config(state='normal')

        threading.Thread(target=perform_project_creation, daemon=True).start()


    def save_user_input_data(self):
        """Saves the user input fields to a JSON file so they can be remembered next time."""
        settings_dir = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'mngaddon')
        user_input_file = os.path.join(settings_dir, 'user_input.json')
        os.makedirs(settings_dir, exist_ok=True)

        data = {
            'reference_images': {pos: entry.get() for pos, entry in self.reference_images.items()},
            'base_mesh': self.base_mesh_var.get(),
            'add_light': self.add_light_var.get(),
            'add_camera': self.add_camera_var.get(),
            'project_name': self.project_name_var.get(),
            'project_dir': self.project_directory_var.get(),
            'auto_save_project': self.auto_save_project_var.get(),
            'auto_save_interval': self.auto_save_interval_var.get(),
            'auto_save_style': self.auto_save_style_var.get(),
        }

        with open(user_input_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)


    def load_user_input_data(self):
        """Loads previously saved user inputs from a JSON file."""
        settings_dir = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'mngaddon')
        user_input_file = os.path.join(settings_dir, 'user_input.json')

        if os.path.exists(user_input_file):
            try:
                with open(user_input_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            except:
                return {}
        return {}



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
        button_font_family = self.button_font_family
        button_font_size = self.button_font_size

        frame = ttkb.Frame(self.help_window, padding=0)
        frame.pack(fill='both', expand=True)

        notebook = ttkb.Notebook(frame)
        notebook.pack(fill='both', expand=True)

        doc_tab = ttkb.Frame(notebook)
        notebook.add(doc_tab, text="Documentation")

        doc_label = ttkb.Label(doc_tab, text="Blender Manager Documentation", font=(button_font_family, 10, 'bold'))
        doc_label.pack(pady=(10, 0))

        doc_frame = ttkb.Frame(doc_tab)
        doc_frame.pack(fill='both', expand=True)

        doc_scrollbar = ttkb.Scrollbar(doc_frame, orient="vertical")
        doc_scrollbar.pack(side="right", fill="y")

        doc_text = tk.Text(
            doc_frame,
            wrap='word',
            padx=10,
            pady=10,
            yscrollcommand=doc_scrollbar.set
        )
        doc_text.insert('1.0', """
Overview:

Blender Manager is a comprehensive desktop application that allows users to:

- Manage multiple Blender versions and installations.
- Simplify project creation and organization.
- Automatically track project working times.
- Manage reference images and base meshes for streamlined modeling.
- Provide a UI for managing renders with notes and previews.
- Utilize an autosave feature to prevent data loss.
- Integrate with Blender through a custom addon for enhanced features.
- Manage addons for every different Blender versions easily.

Additional Features:

- Automatically detects new versions of Blender and installs them.
- Cloud-based feature synchronization is planned.
- Supports both amateur and professional workflows.
- Includes advanced rendering management tools.
- Collaborate and share project resources with a team.
- Marketplace support for external assets.
        """)
        doc_text.config(state='disabled', font=(button_font_family, 9))
        doc_text.pack(side="left", fill='both', expand=True)

        doc_scrollbar.config(command=doc_text.yview)

        detailed_doc_label = ttkb.Label(
            doc_tab,
            text="Detailed Documentation",
            font=(button_font_family, 10, 'underline'),
            foreground="blue",
            cursor="hand2"
        )
        detailed_doc_label.pack(pady=(5, 0))
        detailed_doc_label.bind("<Button-1>", lambda e: self.open_url("https://github.com/verlorengest/BlenderManager"))

        feedback_label = ttkb.Label(
            doc_tab,
            text="For Feedbacks and error logs: majinkaji@proton.me",
            font=(button_font_family, 9, 'italic'),
            foreground="gray"
        )
        feedback_label.pack(pady=(5, 0))


        credits_tab = ttkb.Frame(notebook)
        notebook.add(credits_tab, text="Credits")

        credits_label = ttkb.Label(
            credits_tab,
            text="Developed by verlorengest",
            font=(button_font_family, 10, 'underline'),
            foreground="blue",
            cursor="hand2"
        )
        credits_label.pack(pady=(150, 10))
        credits_label.bind("<Button-1>", lambda e: self.open_url("https://github.com/verlorengest"))

        # Donate Tab
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
            anchor="center",
            wraplength=500,
            font=(button_font_family, 9)
        )
        donate_label.pack(pady=(10, 20))

        donate_link = ttkb.Label(
            donate_frame,
            text="Donate Now",
            font=(button_font_family, 10, 'underline'),
            foreground="blue",
            cursor="hand2"
        )
        donate_link.pack()
        donate_link.bind("<Button-1>", lambda e: self.open_url("https://verlorengest.gumroad.com/l/blendermanager"))

        def on_close():
            self.help_button.configure(state='normal')
            self.help_window.destroy()
            del self.help_window

        self.help_window.protocol("WM_DELETE_WINDOW", on_close)

        self.wait_window(self.help_window)

    def open_url(self, url):
        """Opens the given URL in the default web browser."""
        import webbrowser
        webbrowser.open(url)


        #-----------------------------------------------------------------------------------------------------------------------------------


            # -------- Main Menu Functions -----------





    def show_main_update_release_notes(self, event=None):
        import webview
        import requests
        import webbrowser

        """Handles the release notes opening process when the label is clicked."""
        version, _ = self.get_latest_blender_version() 

        if not version:
            messagebox.showerror("Error", "No valid Blender version found.")
            return

       
        try:
            major_version, minor_version, *_ = map(int, version.split('.'))
        except ValueError:
            messagebox.showerror("Error", "Invalid version format.")
            return

        
        official_url = f"https://www.blender.org/download/releases/{major_version}.{minor_version}/"
        alternative_url = f"https://developer.blender.org/docs/release_notes/{major_version}.{minor_version}/"

        def check_url(url):
            """Check if the given URL is accessible."""
            try:
                response = requests.head(url, timeout=5)
                return response.status_code == 200
            except Exception as e:
                print(f"Error checking URL: {e}")
                return False

      
        try:
            if check_url(official_url):
                
                try:
                    webview.create_window(f"Release Notes for Blender {major_version}.{minor_version}", official_url)
                    webview.start()
                except Exception as e:
                    print(f"Error opening with webview: {e}. Falling back to webbrowser.")
                    webbrowser.open(official_url)
            elif check_url(alternative_url):
                
                try:
                    webview.create_window(f"Release Notes for Blender {major_version}.{minor_version}", alternative_url)
                    webview.start()
                except Exception as e:
                    print(f"Error opening with webview: {e}. Falling back to webbrowser.")
                    webbrowser.open(alternative_url)
            else:
                
                messagebox.showerror("Error", f"Release notes for Blender {major_version}.{minor_version} not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
           
            webbrowser.open(official_url)
















    def show_main_release_notes(self, event):
        import webbrowser
        import requests
        try:
            import webview
        except ImportError:
            webview = None
            print("Webview library not found, trying to open in browser...")

        label_text = self.blender_version_label.cget("text")
        version_match = re.search(r'\b(\d+\.\d+)(?:\.\d+)?\b', label_text)

        if not version_match:
            messagebox.showerror("Error", "No valid Blender version found.")
            return

        version = version_match.group(1)
        major_version, minor_version = version.split(".")

        official_url = f"https://www.blender.org/download/releases/{major_version}.{minor_version}/"
        alternative_url = f"https://developer.blender.org/docs/release_notes/{major_version}.{minor_version}/"

        def check_url(url):
            try:
                response = requests.head(url, timeout=5)
                return response.status_code == 200
            except Exception as e:
                print(f"Error checking URL: {e}")
                return False

        try:
            if check_url(official_url):
                if webview:
                    try:
                        webview.create_window(f"Release Notes for Blender {major_version}.{minor_version}", official_url)
                        webview.start()
                    except Exception as e:
                        print(f"Error opening with webview: {e}")
                        webbrowser.open(official_url)
                else:
                    webbrowser.open(official_url)
            elif check_url(alternative_url):
                if webview:
                    try:
                        webview.create_window(f"Release Notes for Blender {major_version}.{minor_version}", alternative_url)
                        webview.start()
                    except Exception as e:
                        print(f"Error opening with webview: {e}")
                        webbrowser.open(alternative_url)
                else:
                    webbrowser.open(alternative_url)
            else:
                messagebox.showerror("Error", f"Release notes for Blender {major_version}.{minor_version} not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            if webview and check_url(official_url):
                webbrowser.open(official_url)









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
        if not self.show_worktime_label_var.get():
            return



        selected_item = self.recent_projects_tree.selection()
        if selected_item:
            project_name = self.recent_projects_tree.item(selected_item[0], "values")[0]  
            work_hours = self.project_times.get(project_name, " ")
            self.work_hours_label.config(text=f"Work Time: {work_hours}")
        else:
            self.work_hours_label.config(text="Work Time: ")




    def show_progress_bar_for_installing(self):
        
        self.progress_bar.grid()  
        self.launch_button.state(['disabled'])  
        self.update_button.state(['disabled']) 
        self.progress_label.grid()
        self.progress_label.config(
            text=f"Installing Latest \n Blender Version.."
        )




    def hide_progress_bar_for_installing(self):
        
        self.progress_bar.grid_remove() 
        self.launch_button.state(['!disabled'])  
        self.update_button.state(['!disabled'])
        self.progress_label.grid_remove()
        self.progress_label.grid_forget


    def show_progress_bar(self):
        """Show progress bar and disable buttons."""
        installed_version = self.get_installed_blender_version()
        latest_version, _ = self.get_latest_blender_version()
    
        self.progress_bar.grid()  
        self.progress_label.grid()

        if installed_version and latest_version:
           
            self.progress_label.config(
                text=f"Updating Blender\n{installed_version} to {latest_version}"
            )



        else:
            self.progress_label.config(
                text="Unable to retrieve version information."
            )
        self.release_notes_label.grid()
        self.launch_button.state(['disabled'])  
        self.update_button.state(['disabled']) 


    def hide_progress_bar(self):
        """Hide progress bar and enable buttons."""
        self.progress_bar.grid_remove()
        self.release_notes_label.grid_remove()
        self.progress_label.grid_remove()
        self.progress_label.grid_forget
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




    def on_right_click(self, event):
        """Handle right-click on the Launch button."""
        print(f"Widget clicked: {event.widget}")

        if event.widget != self.launch_button:
            print("Not the target widget. Ignoring.")
            return "break"

        if self.launch_button["state"] == "disabled":
            print("Button is disabled. Ignoring right-click.")
            return "break" 

        print("Right-click detected. Showing context menu.")
        self.launch_right_click_menu(event)



    def launch_right_click_menu(self, event):
        """Display a context menu for the Launch button if it is active."""


        menu = tk.Menu(self.launch_button, tearoff=0)

        menu.add_command(label="Launch With Arguments", command=self.launch_with_arguments)
        menu.add_command(label="Export Blender", command=lambda: self.export_main_blender())
        menu.add_command(label="Delete Blender", command=self.delete_main_blender)

        menu.post(event.x_root, event.y_root)

    def launch_with_arguments(self):
        """Launch Blender with user-provided arguments, ensuring compatibility and error handling."""
        import platform

        def launch_with_args():
            blender_exe = self.get_blender_executable_path()
            if not blender_exe:
                
                return

            argument_window = tk.Toplevel(self)
            argument_window.title("Launch Blender with Arguments")
            argument_window.geometry("400x200")
            argument_window.resizable(False, False)
            argument_window.transient(self)
            argument_window.grab_set()
            argument_window.iconbitmap(r"Assets/Images/bmng.ico")

            main_x = self.winfo_x()
            main_y = self.winfo_y()
            main_width = self.winfo_width()
            main_height = self.winfo_height()

            x = main_x + (main_width // 2) - (400 // 2)
            y = main_y + (main_height // 2) - (200 // 2)
            argument_window.geometry(f"+{x}+{y}")

            tk.Label(argument_window, text="Enter Blender arguments:", font=("Segoe UI", 12)).pack(pady=10)

            arg_entry = tk.Entry(argument_window, width=50)
            arg_entry.pack(pady=5)

            def show_help():
                messagebox.showinfo(
                    "Usage Information",
                    "Enter only the arguments starting with '--'.\n\n"
                    "Example: --factory-startup\n            --open project.blend"
                    "\nYou can use plural arguments like: \n--factory-startup --open project.blend"
                    
                )

            help_label = tk.Label(
                argument_window, 
                text="?", 
                font=("Segoe UI", 10, "bold"), 
                fg="yellow", 
                cursor="hand2"
            )
            help_label.pack(pady=5)

            help_label.bind("<Button-1>", lambda event: show_help())

            def validate_and_launch():
                args = arg_entry.get().strip()

                if not args.startswith("--"):
                    messagebox.showerror("Invalid Argument", "Unknown Arguments. Please try again.")
                    return

                try:
                    self.disable_buttons(launch_button_text="Running")

                    command = [blender_exe] + args.split()
                    if platform.system() == "Windows":
                        process = subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        process = subprocess.Popen(command)

                    def monitor_process():
                        process.wait() 

                        self.main_menu_frame.after(0, self.update_project_times)
                        self.main_menu_frame.after(0, self.refresh_recent_projects)
                        self.enable_buttons()

                        print("Blender closed. All processes cleaned.")

                    threading.Thread(target=monitor_process, daemon=True).start()
                    argument_window.destroy()

                except FileNotFoundError:
                    messagebox.showerror("Launch Error", "Blender executable not found. Please ensure Blender is installed.")
                except ValueError as ve:
                    messagebox.showerror("Argument Error", f"Invalid argument: {ve}")
                except Exception as e:
                    messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")

            launch_button = tk.Button(argument_window, text="Launch", command=validate_and_launch, font=("Segoe UI", 12), fg="green")
            launch_button.pack(pady=10)

        threading.Thread(target=launch_with_args, daemon=True).start()



    def export_main_blender(self):
        """Export the BLENDER_PATH directory to a user-chosen location with optional compression."""
        import threading

        def perform_export():
            try:
                self.disable_buttons(launch_button_text="Exporting...")

                if not os.path.exists(BLENDER_PATH):
                    self.main_menu_frame.after(0, lambda: messagebox.showerror("Error", "The Blender directory does not exist."))
                    return

                destination_dir = filedialog.askdirectory(title="Select Destination Directory")
                if not destination_dir:
                    self.main_menu_frame.after(0, lambda: messagebox.showinfo("Export Cancelled", "No directory selected. Export operation cancelled."))
                    return

                compress = messagebox.askyesno("Compress Directory", "Would you like to compress the Blender directory into a ZIP archive?")

                if compress:
                    zip_file_name = "blender_export.zip"
                    destination_path = os.path.join(destination_dir, zip_file_name)

                    try:
                        with zipfile.ZipFile(destination_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for root, dirs, files in os.walk(BLENDER_PATH):
                                for file in files:
                                    full_path = os.path.join(root, file)
                                    arcname = os.path.relpath(full_path, BLENDER_PATH)
                                    zipf.write(full_path, arcname=arcname)
                        self.main_menu_frame.after(0, lambda: messagebox.showinfo("Export Successful", f"The Blender directory was successfully compressed and exported to:\n{destination_path}"))
                    except Exception as e:
                        self.main_menu_frame.after(0, lambda: messagebox.showerror("Compression Error", f"An error occurred while compressing the directory:\n{e}"))
                else:
                    destination_path = os.path.join(destination_dir, os.path.basename(BLENDER_PATH))

                    try:
                        shutil.copytree(BLENDER_PATH, destination_path)
                        self.main_menu_frame.after(0, lambda: messagebox.showinfo("Export Successful", f"The Blender directory was successfully exported to:\n{destination_path}"))
                    except FileExistsError:
                        self.main_menu_frame.after(0, lambda: messagebox.showerror("Export Error", "The directory already exists at the selected location."))
                    except PermissionError:
                        self.main_menu_frame.after(0, lambda: messagebox.showerror("Permission Denied", "You do not have permission to write to the selected location."))
                    except Exception as e:
                        self.main_menu_frame.after(0, lambda: messagebox.showerror("Export Error", f"An error occurred while exporting the directory:\n{e}"))

            except Exception as e:
                self.main_menu_frame.after(0, lambda: messagebox.showerror("Unexpected Error", f"An unexpected error occurred during export:\n{e}"))
            finally:
                self.enable_buttons()

        threading.Thread(target=perform_export, daemon=True).start()










    def delete_main_blender(self):
        """Deletes the Blender directory after confirmation, with button state updates."""
        import threading

        def perform_deletion():
            try:
                self.disable_buttons(launch_button_text="Deleting...")

                if not os.path.exists(BLENDER_PATH):
                    self.main_menu_frame.after(0, lambda: messagebox.showerror("Error", "Blender directory not found."))
                    return

                confirmation = messagebox.askyesno(
                    "Confirm Deletion",
                    "Are you sure you want to delete the Blender directory?"
                )

                if not confirmation:
                    return

                try:
                    shutil.rmtree(BLENDER_PATH)
                    self.main_menu_frame.after(0, lambda: messagebox.showinfo("Success", "Blender directory deleted successfully."))
                    self.main_menu_frame.after(0, self.refresh_recent_projects)
                except PermissionError:
                    self.main_menu_frame.after(0, lambda: messagebox.showerror("Permission Denied", "You do not have permission to delete this directory."))
                except FileNotFoundError:
                    self.main_menu_frame.after(0, lambda: messagebox.showerror("Error", "Blender directory not found."))
                except Exception as e:
                    self.main_menu_frame.after(0, lambda: messagebox.showerror("Unexpected Error", f"An error occurred: {e}"))
            finally:
                self.enable_buttons()

        threading.Thread(target=perform_deletion, daemon=True).start()










        



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
        start_time = time.time()

        blender_foundation_path = get_blender_config_path()
        blender_version = self.get_blender_folder()

        if platform.system() == "Darwin" and blender_version:
            blender_version = ".".join(blender_version.split(".")[:2])

        if not blender_version:
            print("No Blender version detected for loading recent files.")
            return []

        recent_files_path = os.path.join(blender_foundation_path, blender_version, "config", "recent-files.txt")

        if not os.path.exists(recent_files_path):
            print(f"recent-files.txt not found at expected path: {recent_files_path}")
            return []

        print(f"Found recent-files.txt at: {recent_files_path}")

        try:
            with open(recent_files_path, 'r', encoding='utf-8') as file:
                recent_projects = [
                    (os.path.basename(line.strip()), 
                     datetime.fromtimestamp(os.path.getmtime(line.strip())).strftime('%Y-%m-%d'), 
                     line.strip())
                    for line in file if os.path.exists(line.strip())
                ]
        except Exception as e:
            print(f"Error loading recent projects: {e}")
            return []

        print(f"Recent Projects Loaded in {time.time() - start_time:.2f} seconds.")
        return recent_projects




    def get_blender_folder(self):
        """
        Finds the latest Blender version installed in .BlenderManager/blender directory.
        On macOS, uses the get_installed_blender_version method to retrieve the version if necessary.
        """
        import re
        import platform

        blender_base_path = os.path.join(os.path.expanduser("~"), ".BlenderManager", "blender")
        latest_version = None

        if not os.path.exists(blender_base_path):
            print("Blender directory not found.")
            return None

        system = platform.system()

        if system == "Darwin": 
            print("Using get_installed_blender_version for macOS.")
            installed_version = self.get_installed_blender_version()
            if installed_version:
                print(f"Installed Blender version detected: {installed_version}")
                return installed_version
            else:
                print("Failed to detect installed Blender version on macOS.")

        for entry in os.listdir(blender_base_path):
            entry_path = os.path.join(blender_base_path, entry)

            if os.path.isdir(entry_path):
                match = re.match(r"(\d+\.\d+)", entry) 
                if match:
                    folder_version = match.group(1)
                    if not latest_version or list(map(int, folder_version.split('.'))) > list(map(int, latest_version.split('.'))):
                        latest_version = folder_version
                        print(f"Detected Blender version from folder: {latest_version}")

        if latest_version:
            print(f"Latest Blender version detected: {latest_version}")
        else:
            print("No Blender version detected.")

        return latest_version






    def get_latest_blender_version(self):
        from bs4 import BeautifulSoup
        import requests
        import platform
        import re

        """Finds the latest Blender version in X.Y.Z format from the release page."""
        base_url = "https://download.blender.org/release/"

        def get_macos_architecture():
            machine = platform.machine()
            if machine == "arm64":
                return "macos-arm64.dmg" 
            elif machine == "x86_64":
                return "macos-x64.dmg"  
            return None

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

            system = platform.system()
            if system == "Windows":
                file_suffix = "windows-x64.zip"
            elif system == "Darwin":  
                file_suffix = get_macos_architecture()
                if not file_suffix:
                    print("Unsupported MacOS architecture.")
                    messagebox.showerror("Unsupported System", "Your Mac architecture is not supported.")
                    return None, None
            else:
                print(f"Unsupported operating system: {system}")
                messagebox.showerror("Unsupported System", "Your operating system is not supported.")
                return None, None

            minor_versions = []
            for link in soup.find_all('a', href=True):
                href = link['href'].strip('/')
                match = re.match(rf'blender-(\d+)\.(\d+)\.(\d+)-{file_suffix}', href)
                if match and int(match.group(1)) == x and int(match.group(2)) == y:
                    z_version = int(match.group(3))
                    minor_versions.append(z_version)

            if not minor_versions:
                print("No minor Blender versions found in the specified major version directory.")
                messagebox.showerror("Version Error", "No specific Blender version found in the major directory.")
                return None, None

            latest_minor_version = max(minor_versions)
            version_number = f"{x}.{y}.{latest_minor_version}"
            download_url = f"{major_version_url}blender-{version_number}-{file_suffix}"

            return version_number, download_url

        except requests.RequestException as e:
            print(f"Network error while fetching latest Blender version: {e}")
            messagebox.showerror("Network Error", "Failed to connect to the Blender release page.")
            return None, None


    def download_blender_zip(self, download_url):
        import requests
        import tempfile
        import shutil

        """Downloads the Blender installer (zip or dmg) to a temporary location with progress."""
        self.show_progress_bar_for_installing_threadsafe()
        self.cancel_button_main.grid()
        temp_dir = tempfile.mkdtemp() 
        file_extension = download_url.split('.')[-1]  
        temp_file_path = os.path.join(temp_dir, f'blender_latest.{file_extension}')
        self.cancel_event_main.clear()  
    
        try:
            response = requests.get(download_url, stream=True, timeout=10) 
            response.raise_for_status() 

            total_length = response.headers.get('content-length')
            if total_length is None:
                self.progress_var.set(100)  
            else:
                downloaded = 0
                total_length = int(total_length)
                with open(temp_file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=4096): 
                        if self.cancel_event_main.is_set():  
                            raise Exception("Download cancelled by user.")
                    
                        downloaded += len(chunk)
                        f.write(chunk)
                        self.progress_var.set((downloaded / total_length) * 100) 

            return temp_file_path  
        except requests.RequestException as e:
            print(f"Network error while downloading Blender: {e}")
            messagebox.showerror("Download Error", "Failed to download Blender. Please check your internet connection.")
            shutil.rmtree(temp_dir) 
            return None
        except Exception as e:
            print(f"Error downloading Blender update: {e}")
            shutil.rmtree(temp_dir)  
            return None
        finally:
            self.hide_progress_bar_for_installing_threadsafe()  
            self.cancel_button_main.grid_remove()  



    

    def update_blender_files(self, temp_file_path):
        import platform
        import zipfile
        import tempfile
        import subprocess

        self.disable_buttons()
        """Extracts Blender files from the downloaded zip/dmg to the install directory, replacing old files."""
    
        system = platform.system()
        if system == "Windows" or system == "Linux":
            if temp_file_path.endswith('.zip'):
                with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
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
                os.remove(temp_file_path)
            else:
                print("Unsupported file format for Windows/Linux. Only .zip is supported.")
        elif system == "Darwin":  
            if temp_file_path.endswith('.dmg'):
                mount_point = tempfile.mkdtemp()
                try:
                    subprocess.run(["hdiutil", "attach", temp_file_path, "-mountpoint", mount_point], check=True)
                    blender_app_path = os.path.join(mount_point, "Blender.app")
                    if os.path.exists(blender_app_path):
                        if os.path.exists(self.blender_install_dir):
                            shutil.rmtree(self.blender_install_dir)
                        os.makedirs(self.blender_install_dir, exist_ok=True)
                    
                        shutil.copytree(blender_app_path, os.path.join(self.blender_install_dir, "Blender.app"))
                    else:
                        raise Exception("Blender.app not found in mounted .dmg.")
                finally:
                    subprocess.run(["hdiutil", "detach", mount_point], check=True)
                    shutil.rmtree(mount_point)
                    os.remove(temp_file_path)
            else:
                print("Unsupported file format for MacOS. Only .dmg is supported.")
        else:
            print(f"Unsupported operating system: {system}")
            raise EnvironmentError(f"Unsupported operating system: {system}")
    
        self.enable_buttons()


    def show_progress_bar_threadsafe(self):
        self.main_menu_frame.after(0, self.show_progress_bar)

    def hide_progress_bar_threadsafe(self):
        self.main_menu_frame.after(0, self.hide_progress_bar)
        
    def show_progress_bar_for_installing_threadsafe(self):
        self.main_menu_frame.after(0, self.show_progress_bar_for_installing)

    def hide_progress_bar_for_installing_threadsafe(self):
        self.main_menu_frame.after(0, self.hide_progress_bar_for_installing)
        


    def show_handle_existing_bar_threadsafe(self):
        self.main_menu_frame.after(0, self.show_handle_existing_bar)

    def hide_handle_existing_bar_threadsafe(self):
        self.main_menu_frame.after(0, self.show_done_text)
        


    def show_handle_existing_bar(self):
        self.progress_label.grid() 
        self.progress_label.config(
            text=f"Transfering Your \n  Blender.."       
            )
        
    def hide_handle_existing_bar(self):
        self.progress_label.grid_remove()
        self.progress_label.grid_forget

    def show_done_text(self):
         
        self.progress_label.config(
            text="Done!"      
        )
        self.progress_label.update_idletasks() 
        self.main_menu_frame.after(2000, self.hide_handle_existing_bar)
        if os.path.exists(BLENDER_ABSOLUTE_PATH):
            self.update_blender_version_label()
            self.refresh_recent_projects()
            self.run_automatic_addon_setup()
        



    def disable_buttons(self, launch_button_text="Wait Please..."):
        """Disable buttons and update the Launch button text dynamically."""
        self.launch_button.config(text=launch_button_text, state='disabled')
        self.launch_button.unbind("<Button-3>")  
        self.create_project_button.config(state='disabled')
        self.update_button.config(state='disabled')

    def enable_buttons(self):
        self.launch_button.config(state='normal', text="Launch Blender")
        self.bind_right_click(self.launch_button, self.on_right_click)

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
        import platform

        def launch():
            blender_exe = self.get_blender_executable_path()
            if not blender_exe:  
                print("Blender is not installed.")
                return

            settings_file = os.path.join(os.path.expanduser('~'), '.BlenderManager', 'mngaddon', 'settings.json')

            if os.path.isfile(blender_exe):
                try:
                    self.disable_buttons(launch_button_text="Running")

                    if platform.system() == "Windows":
                        process = subprocess.Popen([blender_exe],creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        process = subprocess.Popen([blender_exe])

                    def monitor_process():
                        process.wait()  

                        self.main_menu_frame.after(0, self.update_project_times)
                        self.main_menu_frame.after(0, self.refresh_recent_projects)
                        self.enable_buttons()
                        self.main_menu_frame.after(0, self.load_project_times)
                        if os.path.exists(settings_file):
                            os.remove(settings_file)
                            print("settings.json deleted after Blender closed.")

                    threading.Thread(target=monitor_process, daemon=True).start()

                except Exception as e:
                    self.main_menu_frame.after(0, lambda: messagebox.showerror("Launch Error", f"Failed to launch Blender:\n{e}"))
            else:
                print("Blender executable path is invalid.")

        threading.Thread(target=launch, daemon=True).start()




    def show_install_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Blender Not Installed")
        dialog.geometry("320x180")
        dialog.resizable(False, False)
        dialog.iconbitmap(r"Assets/Images/bmng.ico")
        dialog.transient(self)
        dialog.grab_set()
        dialog.update_idletasks()

        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        style = ttk.Style(dialog)
        style.configure(
            "Unique.TButton",
            font=("Segoe UI", 10),
            padding=5,
            background="#0078D7",
            foreground="white",
            relief="flat"
        )
        style.map(
            "Unique.TButton",
            background=[("active", "#005a9e")],
            foreground=[("active", "white")]
        )

        main_frame = ttk.Frame(dialog, padding=(20, 10))
        main_frame.pack(fill="both", expand=True)

        label = ttk.Label(
            main_frame,
            text="Blender is not installed.\nWould you like to install it?",
            font=("Segoe UI", 11, "bold"),
            anchor="center",
            justify="center",
            wraplength=280
        )
        label.pack(pady=(0, 15))

        button_frame_top = ttk.Frame(main_frame)
        button_frame_top.pack(pady=(0, 10))

        yes_button = ttk.Button(
            button_frame_top,
            text="Yes",
            style="Unique.TButton",
            takefocus=False,
            command=lambda: self.install_blender(dialog),
            width=14
        )
        no_button = ttk.Button(
            button_frame_top,
            text="No",
            style="Unique.TButton",
            takefocus=False,
            command=dialog.destroy,
            width=14
        )

        yes_button.grid(row=0, column=0, padx=5, pady=5)
        no_button.grid(row=0, column=1, padx=5, pady=5)

        already_installed_button = ttk.Button(
            main_frame,
            text="Already Installed",
            style="Unique.TButton",
            takefocus=False,
            command=lambda: self.handle_existing_blender(dialog),
            width=30
        )
        already_installed_button.pack(pady=(0, 10))

        dialog.focus_set()
        dialog.wait_window()




    def install_blender(self, dialog):
        """Handle the installation of Blender."""
        dialog.destroy()  

        def install():
            latest_version, download_url = self.get_latest_blender_version()
            if latest_version and download_url:
                self.disable_buttons()
                self.show_progress_bar_for_installing_threadsafe()
                temp_zip_path = self.download_blender_zip(download_url)
                if temp_zip_path:
                    self.update_blender_files(temp_zip_path)
                    self.main_menu_frame.after(0, lambda: messagebox.showinfo("Installation Complete", "Blender has been installed successfully."))
                    if os.path.exists(BLENDER_ABSOLUTE_PATH):
                        self.update_blender_version_label()
                        self.refresh_recent_projects()
                        self.run_automatic_addon_setup()
                self.hide_progress_bar_for_installing_threadsafe()
                self.enable_buttons()

        threading.Thread(target=install, daemon=True).start()




    def handle_existing_blender(self, dialog):
        """Handle the process of selecting an existing Blender installation and moving its contents."""

        def select_and_validate_folder():
            """Prompt the user to select a folder and validate it contains a valid Blender executable."""
            while True:
                selected_folder = filedialog.askdirectory(title="Select Blender Installation Folder")
                if not selected_folder:
                    return None  

                import platform
                system = platform.system()
                if system == "Windows":
                    blender_exe_path = os.path.join(selected_folder, "blender.exe")
                elif system == "Darwin":  
                    blender_exe_path = os.path.join(selected_folder, "Blender.app", "Contents", "MacOS", "Blender")
                elif system == "Linux":
                    blender_exe_path = os.path.join(selected_folder, "blender")
                else:
                    messagebox.showerror("Unsupported OS", "Your operating system is not supported.")
                    return None

                if os.path.isfile(blender_exe_path):
                    return selected_folder  
                else:
                    messagebox.showerror(
                        "Invalid Folder",
                        "The selected folder does not contain a valid Blender executable. Please try again."
                    )

        def transfer_files(source_folder, target_folder):
            """Transfer Blender files from the source to the target folder."""
            
            try:
                show_loading_bar()
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
                hide_loading_bar()
                print("Blender Successfully Loaded !")

        def show_loading_bar():
            """Show a loading bar on the main menu frame."""
            self.show_handle_existing_bar_threadsafe()

        def hide_loading_bar():
            """Hide the loading bar."""
            self.hide_handle_existing_bar_threadsafe()

        dialog.destroy()
        
        self.disable_buttons()

        selected_folder = select_and_validate_folder()
        if not selected_folder:
            
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
                blender_exe = self.get_blender_executable_path()
                

                if blender_exe is None or not isinstance(blender_exe, (str, bytes, os.PathLike)):
                    return
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
                print(f"Installed Version: {installed_version}")
                print(f"Latest Version: {latest_version}")

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
            blender_exe = self.get_blender_executable_path()

            
            if blender_exe is None or not isinstance(blender_exe, (str, bytes, os.PathLike)):
                return
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
                blender_exe = self.get_blender_executable_path()  
            
               
                if os.path.isfile(blender_exe):
                    try:
                        
                        self.disable_buttons(launch_button_text="Running")
                        process = subprocess.Popen([blender_exe, project_path], creationflags=subprocess.CREATE_NO_WINDOW)
                        
                        def monitor_process():
                            
                            process.wait()

                            self.main_menu_frame.after(0, self.update_project_times)
                            self.main_menu_frame.after(0, self.refresh_recent_projects)
                            self.enable_buttons()
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
        blender_exe = self.get_blender_executable_path()

        if os.path.isfile(blender_exe):
            try:
                startupinfo = None
                if os.name == 'nt':  
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
            
                result = subprocess.run(
                    [blender_exe, '--version'],
                    stdout=subprocess.PIPE,
                    text=True,
                    startupinfo=startupinfo
                )
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
                                return version_match.group(1)
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

        self.theme_choice = tk.StringVar()  
        theme_combobox = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_choice,
            state="readonly",  
            width=20
        )
        theme_combobox.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        available_themes = self.style.theme_names()
        theme_combobox['values'] = available_themes

        theme_combobox.set("Default")  

        theme_combobox.bind("<<ComboboxSelected>>", self.change_theme)

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
            selected_theme = theme_combobox.get()
            if selected_theme in available_themes:
                self.theme_choice.set(selected_theme)
                self.change_theme()

        self.theme_choice = tk.StringVar()
        theme_combobox = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_choice,
            state="readonly",
            width=20
        )
        theme_combobox.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        available_themes = self.style.theme_names()
        theme_combobox['values'] = available_themes

        theme_combobox.bind("<<ComboboxSelected>>", on_theme_select)

        current_theme = self.style.theme_use()
        if current_theme in available_themes:
            theme_combobox.set(current_theme)

        advanced_frame = ttkb.Frame(settings_tab)
        advanced_frame.pack(fill="both", expand=True, padx=10, pady=10)

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
        self.setup_button.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.question_label = ttk.Label(
            left_frame,
            text="?",
            font=("Arial", 9, "bold"),
            foreground="blue",
            cursor="hand2"
        )
        self.question_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.question_label.bind("<Button-1>", lambda e: messagebox.showinfo(
            "Info",
            "Install first time or update the addon from here. Blender Manager addon is important for the app to work properly."
        ))

        self.change_launch_blender_button = ttkb.Button(
            left_frame,
            text="Change Launch Folder",
            takefocus=False,
            command=self.change_launch_blender,
            width=18,
            style="Unique.TButton"
        )
        self.change_launch_blender_button.grid(row=1, column=0, sticky="w", padx=5, pady=5, columnspan=2)

        self.auto_update_checkbox_widget = ttkb.Checkbutton(
            left_frame,
            text="Auto Update",
            variable=self.auto_update_var,
            bootstyle="success",
            command=self.toggle_auto_update
        )
        self.auto_update_checkbox_widget.grid(row=2, column=0, sticky="w", padx=5, pady=3, columnspan=2)

        self.bm_auto_update_checkbox_widget = ttkb.Checkbutton(
            left_frame,
            text="BM Auto Update",
            variable=self.bm_auto_update_var,
            bootstyle="success",
            command=self.toggle_bm_auto_update
        )
        self.bm_auto_update_checkbox_widget.grid(row=3, column=0, sticky="w", padx=5, pady=3, columnspan=2)
        

        
        
        self.auto_activate_added_plugin_checkbox = ttkb.Checkbutton(
            left_frame,
            text="Auto Activate Addon After Adding",
            variable=self.auto_activate_plugin_var,
            bootstyle="success",
            command=self.toggle_auto_activate_plugin
        )
        self.auto_activate_added_plugin_checkbox.grid(row=4, column=0, sticky="w", padx=5, pady=3, columnspan=2)


        self.launch_on_startup_checkbox = ttkb.Checkbutton(
            left_frame,
            text="Launch on Startup",
            variable=self.launch_on_startup_var,
            bootstyle="success",
            command=self.toggle_launch_on_startup
        )
        self.launch_on_startup_checkbox.grid(row=5, column=0, sticky="w", padx=5, pady=3, columnspan=2)

        self.run_in_background_checkbox = ttkb.Checkbutton(
            left_frame,
            text="Run in Background",
            variable=self.run_in_background_var,
            bootstyle="success",
            command=self.toggle_run_in_background
        )
        self.run_in_background_checkbox.grid(row=6, column=0, sticky="w", padx=5, pady=3, columnspan=2)

        chunk_size_frame = ttk.LabelFrame(left_frame, text="Download Chunk Size Multiplier", padding=(5, 5))
        chunk_size_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

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
        right_frame.grid(row=0, column=1, sticky="n", padx=5, pady=5)

        self.tab_visibility_vars = {
            "Addon Management": tk.BooleanVar(value=self.settings.get("show_addon_management", True)),
            "Project Management": tk.BooleanVar(value=self.settings.get("show_project_management", True)),
            "Render Management": tk.BooleanVar(value=self.settings.get("show_render_management", True)),
            "Version Management": tk.BooleanVar(value=self.settings.get("show_version_management", True)),
        }

        row = 0
        for tab_name, var in self.tab_visibility_vars.items():
            ttkb.Checkbutton(
                right_frame,
                text=f"Show {tab_name} Tab",
                variable=var,
                bootstyle="success",
                command=lambda name=tab_name, var=var: self.toggle_tab_visibility(name, var)
            ).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            row += 1









        self.show_worktime_label_checkbox = ttkb.Checkbutton(
            right_frame,
            text="Show Worktime Label",
            variable=self.show_worktime_label_var,
            bootstyle="success",
            command=self.toggle_show_worktime_label
        )
        self.show_worktime_label_checkbox.grid(row=row, column=0, sticky='w', padx=5, pady=2)
        row += 1

        info_label = ttkb.Label(
            right_frame,
            text="You need to restart the Blender Manager to apply changes.",
            font=("Segoe UI", 7, "italic"),
            foreground="grey"
        )
        info_label.grid(row=row, column=0, sticky="w", padx=5, pady=(5, 0))
        row += 1



        restart_button = ttkb.Button(
            right_frame,
            text="Restart",
            style="Unique.TButton",
            command=self.restart_application
        )
        restart_button.grid(row=row, column=0, sticky="w", padx=5, pady=(5, 0))

        help_icon = ttk.Label(
            right_frame,
            text="?",
            font=("Segoe UI", 10, "bold"),
            foreground="blue",
            cursor="hand2"
        )
        help_icon.grid(row=row, column=1, sticky="e", padx=5, pady=3)
        help_icon.bind(
            "<Button-1>",
            lambda e: messagebox.showinfo(
                "Tab Visibility Settings Info",
                "These settings allow you to toggle the visibility of specific tabs in the Blender Manager. "
                "Hiding the tabs you don't need can speed up the application's startup. "
                "To apply changes, restart the application after making adjustments."
            )
        )
        


        reset_config_frame = ttk.LabelFrame(right_frame, text="Reset Blender Config", padding=(5, 5))
        reset_config_frame.grid(row=row + 1, column=0, sticky="ew", padx=5, pady=5)

        self.config_versions = self.get_blender_config_versions()
        self.selected_config_version = tk.StringVar()

        self.config_combobox = ttk.Combobox(
            reset_config_frame,
            textvariable=self.selected_config_version,
            values=self.config_versions,
            state='readonly',
            width=20
        )
        self.config_combobox.set("Select Blender Version")
        self.config_combobox.pack(pady=(5, 2)) 

        self.reset_config_button = ttkb.Button(
            reset_config_frame,
            text="Reset Config",
            command=self.reset_blender_config,
            style="Small.TButton"
        )
        self.reset_config_button.pack(pady=(2, 5))

        reset_frame = ttk.Frame(settings_tab)
        reset_frame.pack(fill="x", padx=5, pady=5)
        reset_buttons_frame = ttk.Frame(reset_frame)
        reset_buttons_frame.pack(side='left', padx=5, pady=5)

        reset_button = ttkb.Button(
            reset_buttons_frame,
            text="Reset All Data",
            takefocus=False,
            command=self.reset_all_data,
            style="Small.TButton"
        )
        reset_button.pack(side="left", padx=3)

        self.delete_all_versions_button = ttkb.Button(
            reset_buttons_frame,
            text="Delete All Versions",
            takefocus=False,
            command=self.delete_all_blender_versions,
            style="Small.TButton"
        )
        self.delete_all_versions_button.pack(side="left", padx=3)

        self.reset_defaults_button = ttkb.Button(
            reset_buttons_frame,
            text="Reset Settings",
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

       
        right_frame = ttk.LabelFrame(blender_settings_frame, text="Export/Import Settings", padding=(10, 10))
        right_frame.pack(side="right", fill="y", padx=10, pady=10)

        # Export Config
        ttk.Label(right_frame, text="Select Version to Export:", font=("Segoe UI", 8)).pack(anchor="w", padx=5, pady=2)
        self.export_version_var = tk.StringVar()
        self.export_version_combobox = ttk.Combobox(
            right_frame,
            textvariable=self.export_version_var,
            state="readonly",
            width=25
        )
        self.export_version_combobox.pack(anchor="w", padx=5, pady=5)

        self.export_button = ttkb.Button(
            right_frame,
            text="Export Config",
            bootstyle="primary",
            command=self.export_blender_config
        )
        self.export_button.pack(anchor="w", pady=10)

        # Import Config
        ttk.Label(right_frame, text="Select Version to Import:", font=("Segoe UI", 8)).pack(anchor="w", padx=5, pady=2)
        self.import_version_var = tk.StringVar()
        self.import_version_combobox = ttk.Combobox(
            right_frame,
            textvariable=self.import_version_var,
            state="readonly",
            width=25
        )
        self.import_version_combobox.pack(anchor="w", padx=5, pady=5)

        self.import_button = ttkb.Button(
            right_frame,
            text="Import Config",
            bootstyle="primary",
            command=self.import_blender_config
        )
        self.import_button.pack(anchor="w", pady=10)

        self.populate_blender_versions()








        #----------------------------------Functions ---------------------------------------------------
        







    def get_blender_config_versions(self):
        """Retrieve available Blender versions from the config path."""
        try:
            config_path = get_blender_config_path()  
            if not os.path.exists(config_path):
                return []

            versions = [
                folder for folder in os.listdir(config_path)
                if os.path.isdir(os.path.join(config_path, folder))
            ]
            return sorted(versions)  
        except Exception as e:
            print(f"Failed to retrieve Blender config versions: {e}")
            return []




    def reset_blender_config(self):
        """Deletes the config folder of the selected Blender version."""
        selected_version = self.selected_config_version.get()
        if not selected_version or selected_version == "Select Blender Version":
            messagebox.showerror("Error", "No Blender version selected.")
            return

        try:
            config_path = get_blender_config_path() 
            version_path = os.path.join(config_path, selected_version)

            if not os.path.exists(version_path):
                messagebox.showinfo("Info", f"No config folder found for version {selected_version}. Nothing to reset.")
                return

            import shutil
            shutil.rmtree(version_path) 
            messagebox.showinfo("Success", f"Config for Blender version {selected_version} has been reset.")
        
            self.config_versions = self.get_blender_config_versions()
            self.config_combobox['values'] = self.config_versions
            self.config_combobox.set("Select Blender Version")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset config for version {selected_version}: {e}")




    def export_blender_config(self):
        """Export Blender settings for the selected version."""
        version = self.export_version_var.get()
        if not version:
            messagebox.showerror("Error", "Please select a version to export.")
            return

        base_dir = get_blender_config_path()
        version_path = os.path.join(base_dir, version)
        if not os.path.exists(version_path):
            messagebox.showerror("Error", f"Version {version} does not exist.")
            return

        selected_dir = filedialog.askdirectory(title="Select Export Directory")
        if not selected_dir: 
            return

        export_dir = os.path.join(selected_dir, version)

        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
        os.makedirs(export_dir)

        include_addons = messagebox.askyesno(
            "Include Add-ons?",
            "Do you want to include add-ons in the exported settings?"
        )

        try:
            source_config = os.path.join(version_path, "config")
            if os.path.exists(source_config):
                shutil.copytree(source_config, os.path.join(export_dir, "config"))

            if include_addons:
                source_scripts = os.path.join(version_path, "scripts")
                if os.path.exists(source_scripts):
                    shutil.copytree(source_scripts, os.path.join(export_dir, "scripts"))

            messagebox.showinfo("Success", f"Settings exported for version {version} to {export_dir}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export settings: {e}")





    def import_blender_config(self):
        """Import Blender settings to the selected version."""
        version = self.import_version_var.get()
        if not version:
            messagebox.showerror("Error", "Please select a version to import to.")
            return

        base_dir = get_blender_config_path()
        version_path = os.path.join(base_dir, version)
        if not os.path.exists(version_path):
            messagebox.showerror("Error", f"Version {version} does not exist.")
            return

        import_dir = filedialog.askdirectory(title="Select Import Directory")
        if not import_dir:
            return

        include_addons = messagebox.askyesno(
            "Include Add-ons?",
            "Do you want to include add-ons in the imported settings?"
        )

        try:
         
            source_config = os.path.join(import_dir, "config")
            destination_config = os.path.join(version_path, "config")
            if os.path.exists(source_config):
                if os.path.exists(destination_config):
                    shutil.rmtree(destination_config)
                shutil.copytree(source_config, destination_config)

       
            if include_addons:
                source_scripts = os.path.join(import_dir, "scripts")
                destination_scripts = os.path.join(version_path, "scripts")
                if os.path.exists(source_scripts):
                    if os.path.exists(destination_scripts):
                        shutil.rmtree(destination_scripts)
                    shutil.copytree(source_scripts, destination_scripts)

            messagebox.showinfo("Success", f"Settings imported to version {version}.")
            self.refresh_recent_projects()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import settings: {e}")



    def populate_blender_versions(self):
        """Populate Blender versions in the comboboxes."""
        base_dir = get_blender_config_path()
        if not os.path.exists(base_dir):
            messagebox.showwarning("Warning", "No Blender versions found.")
            return

        versions = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

        if versions:
            self.source_version_combobox["values"] = versions
            self.destination_version_combobox["values"] = versions
        
            self.export_version_combobox["values"] = versions
            self.import_version_combobox["values"] = versions
        else:
            messagebox.showwarning("Warning", "No Blender versions available.")



    def transfer_blender_settings(self):
        """Transfer config and script settings between Blender versions."""
        source_version = self.source_version_var.get()
        destination_version = self.destination_version_var.get()

        if not source_version or not destination_version:
            messagebox.showerror("Error", "Please select both source and destination versions.")
            return

        base_dir = get_blender_config_path()
        source_path = os.path.join(base_dir, source_version)
        destination_path = os.path.join(base_dir, destination_version)

        if not os.path.exists(source_path):
            messagebox.showerror("Error", f"Source version {source_version} does not exist.")
            return
        if not os.path.exists(destination_path):
            messagebox.showerror("Error", f"Destination version {destination_version} does not exist.")
            return

        include_addons = messagebox.askyesno(
            "Include Add-ons?",
            "Do you want to include add-ons (scripts) in the transfer?"
        )

        try:
            source_config = os.path.join(source_path, "config")
            destination_config = os.path.join(destination_path, "config")
            if os.path.exists(source_config):
                if os.path.exists(destination_config):
                    shutil.rmtree(destination_config)
                shutil.copytree(source_config, destination_config)

            if include_addons:
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
                self.projects_tree = ttk.Treeview(self)
                self.project_management_tab = ttkb.Frame(self.notebook)
                self.notebook.add(self.project_management_tab, text="Project Management")
                self.create_project_management_tab()
            elif tab_name == "Render Management" and not hasattr(self, "render_management_tab"):
                self.render_management_tab = ttkb.Frame(self.notebook)
                self.notebook.add(self.render_management_tab, text="Render Management")
                self.create_render_management_tab()
            elif tab_name == "Version Management" and not hasattr(self, "version_management_tab"):
                self.version_management_tab = ttkb.Frame(self.notebook)
                self.notebook.add(self.version_management_tab, text="Version Management")
                self.create_version_management_tab()
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



    def toggle_show_worktime_label (self):
        self.settings["show_worktime_label"] = self.show_worktime_label_var.get()
        save_config(self.settings)
        print(f"Show Worktime Label set to: {self.show_worktime_label_var.get()}")
        if not self.show_worktime_label_var.get():
            self.work_hours_label.pack_forget()
            
        if self.show_worktime_label_var.get():
            self.work_hours_label.pack()
        

    def toggle_auto_activate_plugin (self):
        self.settings["auto_activate_plugin"] = self.auto_activate_plugin_var.get()
        save_config(self.settings)
        print(f"Auto Activate Addon set to: {self.auto_activate_plugin_var.get()}")



    def restart_application(self):
        """Schedule the application to restart after 5 seconds, without showing a command prompt window."""
        try:
            python = sys.executable
            args = [python] + sys.argv

            subprocess.Popen(
                ["timeout", "/t", "3", "/nobreak", "&&"] + args,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW 
            )

            self.force_exit()
        except Exception as e:
            print(f"Failed to restart application: {e}")


    def force_exit(self):
        """Forcefully and immediately exits the application."""
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.stop()  
        except Exception as e:
            print(f"Tray icon stop failed: {e}")
        finally:
            os._exit(0)


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

                blender_exe_path = self.get_blender_executable_path()
                if os.path.isfile(blender_exe_path):
                    return selected_folder  
                else:
                    messagebox.showerror("Invalid Folder", "The selected folder does not contain Blender. Please try again.")

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
        """Runs the setup process to install and activate the addon."""
        addon_zip_names = [
            "BlenderManager.zip", "Blender Manager.zip",
            "Blender_Manager.zip", "Blender Manager Addon.zip",
            "Blender_Manager_Addon.zip"
        ]

        current_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)

        for zip_name in addon_zip_names:
            potential_zip_path = os.path.join(current_dir, zip_name)
            if os.path.exists(potential_zip_path):
                self.addon_zip_path = potential_zip_path
                break

        if not self.addon_zip_path:
            messagebox.showerror("Error", "Addon zip file not found in the current directory. Please ensure the addon zip file is present.")
            return

        blender_foundation_path = get_blender_config_path()
        if not os.path.exists(blender_foundation_path):
            messagebox.showerror("Error", "Blender Foundation folder not found. Please install Blender first.")
            return

        installed_version = self.get_installed_blender_version()
        if not installed_version:
            messagebox.showerror("Error", "Blender version not found. Please ensure Blender is installed.")
            return

        major_minor_version = ".".join(installed_version.split(".")[:2])
        version_folder_path = os.path.join(blender_foundation_path, major_minor_version)

        if not os.path.exists(version_folder_path):
            os.makedirs(version_folder_path, exist_ok=True)
            print(f"Version folder created: {version_folder_path}")

        scripts_addons_path = os.path.join(version_folder_path, "scripts", "addons")
        config_path = os.path.join(version_folder_path, "config")

        os.makedirs(scripts_addons_path, exist_ok=True)
        os.makedirs(config_path, exist_ok=True)

        print(f"Config directory ensured at: {config_path}")
        print(f"Scripts/Addons directory ensured at: {scripts_addons_path}")

        addon_folder_names = ["Blender Manager", "BlenderManager", "Blender_Manager"]
        addon_folder_name = addon_folder_names[0]
        addon_full_path = os.path.join(scripts_addons_path, addon_folder_name)

        if os.path.exists(addon_full_path):
            print(f"Addon already exists in: {addon_full_path}. Removing old version.")
            shutil.rmtree(addon_full_path)

        self.unzip_addon(self.addon_zip_path, scripts_addons_path)
        print(f"Addon installed in: {scripts_addons_path}")

        if self.activate_bm_addon(addon_folder_name):
            messagebox.showinfo("Setup Complete", "Addon has been installed and activated successfully in all Blender versions.")




    def activate_bm_addon(self, addon_name):
        """Activates the addon using Blender's Python environment."""
        blender_path = self.get_blender_executable_path()

        script_content = f"""
import bpy
bpy.ops.preferences.addon_enable(module="{addon_name}")
bpy.ops.wm.save_userpref()
print("Addon '{addon_name}' activated successfully.")
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py", encoding="utf-8") as temp_script:
            temp_script_path = temp_script.name
            temp_script.write(script_content)

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  

            subprocess.run(
                [blender_path, "--background", "--python", temp_script_path],
                check=True,
                startupinfo=startupinfo
            )
            return True  
        except subprocess.CalledProcessError as e:
            print(f"Failed to activate addon. Error: {e}")
            return False  
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)




    def run_automatic_addon_setup(self):
        """Runs the setup process to install the addon automatically."""
        addon_zip_names = [
            "BlenderManager.zip", "Blender Manager.zip",
            "Blender_Manager.zip", "Blender Manager Addon.zip",
            "Blender_Manager_Addon.zip"
        ]

        current_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)

        for zip_name in addon_zip_names:
            potential_zip_path = os.path.join(current_dir, zip_name)
            if os.path.exists(potential_zip_path):
                self.addon_zip_path = potential_zip_path
                break

        if not self.addon_zip_path:
            print("Error: Addon zip file not found in the current directory. Please ensure the addon zip file is present.")
            return

        blender_foundation_path = get_blender_config_path()
        if not os.path.exists(blender_foundation_path):
            print("Error: Blender Foundation folder not found. Please install Blender first.")
            return

        installed_version = self.get_installed_blender_version()
        if not installed_version:
            print("Error: Blender version not found. Please ensure Blender is installed.")
            return

        major_minor_version = ".".join(installed_version.split(".")[:2])
        version_folder_path = os.path.join(blender_foundation_path, major_minor_version)

        if not os.path.exists(version_folder_path):
            os.makedirs(version_folder_path, exist_ok=True)
            print(f"Version folder created: {version_folder_path}")

        scripts_addons_path = os.path.join(version_folder_path, "scripts", "addons")
        config_path = os.path.join(version_folder_path, "config")

        os.makedirs(scripts_addons_path, exist_ok=True)
        os.makedirs(config_path, exist_ok=True)

        print(f"Config directory ensured at: {config_path}")
        print(f"Scripts/Addons directory ensured at: {scripts_addons_path}")

        addon_folder_names = ["Blender Manager", "BlenderManager", "Blender_Manager"]
        addon_folder_name = addon_folder_names[0]
        addon_full_path = os.path.join(scripts_addons_path, addon_folder_name)

        if os.path.exists(addon_full_path):
            print(f"Addon already exists in: {addon_full_path}. Removing old version.")
            shutil.rmtree(addon_full_path)

        self.unzip_addon(self.addon_zip_path, scripts_addons_path)
        print(f"Addon installed in: {scripts_addons_path}")

        if self.activate_bm_addon(addon_folder_name):
            print("Setup Complete: Addon has been installed and activated successfully in all Blender versions.")




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
                print(f"An unexpected error occurred: {e}")

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

        self.style.map(
            'Green.TButton',
            background=[('active', '#34d058'), ('!active', '#28a745')],
            foreground=[('disabled', 'grey'), ('!disabled', 'white')]
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
        

        treeview_font_family = self.treeview_font_family

        style = ttk.Style()
        style.configure(
            "custom_render_treeview",
            font=(treeview_font_family, 12), 
            rowheight=25  
        )
        style.configure(
            "custom_render_treeview.Heading",
            font=(treeview_font_family, 14, "bold") 
        )



        style = ttkb.Style()
        style.configure("InstallVersions.Treeview", font=(font_family, 12), rowheight=30)  
        style.configure("InstallVersions.Treeview.Heading", font=('Segoe UI', 14, 'bold'))  
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
            columns=('Name', 'Version', 'Compatible', 'Status'),  
            show='headings',
            selectmode='browse',
            style='PluginManagement.Treeview'
        )
        self.plugins_tree.heading('Name', text='Plugin Name')
        self.plugins_tree.heading('Version', text='Version')
        self.plugins_tree.heading('Compatible', text='Compatible with')
        self.plugins_tree.heading('Status', text='Status')  
        self.plugins_tree.column('Name', width=300, anchor='center')
        self.plugins_tree.column('Version', width=150, anchor='center')
        self.plugins_tree.column('Compatible', width=150, anchor='center')
        self.plugins_tree.column('Status', width=100, anchor='center')  
        self.plugins_tree.pack(side='right', fill='both', expand=1)

        scrollbar = ttk.Scrollbar(plugins_frame, orient="vertical", command=self.plugins_tree.yview)
        self.plugins_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.plugins_tree.drop_target_register(DND_FILES)
        self.plugins_tree.dnd_bind('<<Drop>>', self.handle_treeview_drop)

        self.plugin_context_menu = tk.Menu(self.plugins_tree, tearoff=0)
        self.plugin_context_menu.add_command(label="Delete", command=self.remove_plugin)
        self.plugin_context_menu.add_command(label="Go to File Path", command=self.go_to_file_path)
        self.plugin_context_menu.add_command(label="Info", command=self.view_plugin_content)
        self.plugin_context_menu.add_command(label="View Documentation", command=self.view_plugin_document)
        
        self.duplicate_menu = tk.Menu(self.plugin_context_menu, tearoff=0)
        
        
        self.plugin_context_menu.add_cascade(label="Duplicate to...", menu=self.duplicate_menu)
        self.plugin_context_menu.add_separator()
        self.plugin_context_menu.add_command(label="Activate Addon", command=self.activate_selected_addon_in_versions)
        self.plugin_context_menu.add_command(label="Deactivate Addon", command=self.deactivate_selected_addon_in_versions)

        self.bind_right_click(self.plugins_tree, self.show_plugin_context_menu)


        self.refresh_plugins_list()

    def show_plugin_context_menu(self, event):
        """Displays the context menu for the selected plugin."""
        item_id = self.plugins_tree.identify_row(event.y)
        if item_id:
            self.plugins_tree.selection_set(item_id)
            self.plugins_tree.focus(item_id)
            self.update_duplicate_menu()
            self.plugins_tree.selection_set(item_id)
            self.plugin_context_menu.tk_popup(event.x_root, event.y_root)
        else:
            self.plugin_context_menu.unpost()



        #-----------Functions----------#



    def auto_activate_plugin (self, addon_name):
        
        activate_addon = addon_name

        self.activate_addon_in_all_versions(activate_addon)
        




    def activate_selected_addon_in_versions(self):
        """Activates the selected addon in all versions for the selected ComboBox version."""
        selected_item = self.plugins_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "No addon selected.")
            return

        selected_addon = self.plugins_tree.item(selected_item, "values")[0]

        threading.Thread(target=self.activate_addon_in_all_versions, args=(selected_addon,), daemon=True).start()

    def deactivate_selected_addon_in_versions(self):
        """Deactivates the selected addon in all versions for the selected ComboBox version."""
        selected_item = self.plugins_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "No addon selected.")
            return

        selected_addon = self.plugins_tree.item(selected_item, "values")[0]

        threading.Thread(target=self.deactivate_addon_in_all_versions, args=(selected_addon,), daemon=True).start()

    def activate_addon_in_all_versions(self, selected_addon):
        """Activates the addon in all sub-versions of the selected ComboBox version."""
        selected_version = self.version_var.get()
        self.show_addon_page_message("Activating...")
        if not selected_version or selected_version == "Select Blender Version":
            messagebox.showerror("Error", "No Blender version selected.")
            return

        
        try:
            blender_executable = self.get_blender_executable_path()
            if blender_executable and self._check_version_match(blender_executable, selected_version):
                self._run_addon_script(blender_executable, selected_addon, enable=True)
            else:
                base_version_prefix = selected_version.split('.')[0] + '.' + selected_version.split('.')[1]
                versions_to_process = self._get_matching_versions(base_version_prefix)

                for blender_executable in versions_to_process:
                    self._run_addon_script(blender_executable, selected_addon, enable=True)
        except Exception as e:
            print(f"Error activating addon: {e}")
        finally:
            self.hide_addon_page_message()
            self.update_addon_status()

    def deactivate_addon_in_all_versions(self, selected_addon):
        """Deactivates the addon in all sub-versions of the selected ComboBox version."""
        selected_version = self.version_var.get()
        self.show_addon_page_message("Deactivating...")
        if not selected_version or selected_version == "Select Blender Version":
            messagebox.showerror("Error", "No Blender version selected.")
            return

        
        try:
            blender_executable = self.get_blender_executable_path()
            if blender_executable and self._check_version_match(blender_executable, selected_version):
                self._run_addon_script(blender_executable, selected_addon, enable=False)
            else:
                base_version_prefix = selected_version.split('.')[0] + '.' + selected_version.split('.')[1]
                versions_to_process = self._get_matching_versions(base_version_prefix)

                for blender_executable in versions_to_process:
                    self._run_addon_script(blender_executable, selected_addon, enable=False)
        except Exception as e:
            print(f"Error deactivating addon: {e}")
        finally:
            self.hide_addon_page_message()
            self.update_addon_status()

    def _check_version_match(self, blender_executable, selected_version):
        """Check if the version of the given Blender executable matches the selected version."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE  

            result = subprocess.run(
                [blender_executable, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo  
            )
            if result.returncode == 0:
                version_output = result.stdout.splitlines()[0]
                blender_version = version_output.split()[-1] 
                base_version_prefix = selected_version.split('.')[0] + '.' + selected_version.split('.')[1]
                return blender_version.startswith(base_version_prefix)
        except Exception as e:
            print(f"Failed to check Blender version: {e}")
        return False

    def _get_matching_versions(self, base_version_prefix):
        """Finds all matching Blender executables based on the version prefix."""
        matching_executables = []

        for folder in os.listdir(BLENDER_DIR):
            if os.path.isdir(os.path.join(BLENDER_DIR, folder)) and folder.startswith("Blender"):
                folder_version = folder.split(" ")[-1]
                if folder_version.startswith(base_version_prefix):
                    blender_executable = os.path.join(BLENDER_DIR, folder, "blender.exe" if os.name == "nt" else "blender")
                    if os.path.exists(blender_executable):
                        matching_executables.append(blender_executable)

        return matching_executables

    def _run_addon_script(self, blender_executable, addon_name, enable=True):
        """Runs a Blender script to enable or disable an addon."""
        action = "enable" if enable else "disable"
        script_content = f"""
import bpy
bpy.ops.preferences.addon_{action}(module="{addon_name}")
bpy.ops.wm.save_userpref()
print("Addon '{addon_name}' {action}d successfully.")
        """

        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py", encoding="utf-8") as temp_script:
                temp_script_path = temp_script.name
                temp_script.write(script_content)

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  

            subprocess.run(
                [blender_executable, "--background", "--python", temp_script_path],
                check=True,
                startupinfo=startupinfo
            )
            os.remove(temp_script_path)
        except Exception as e:
            print(f"Failed to {action} addon '{addon_name}' for {blender_executable}: {e}")





    def show_addon_page_message(self, message):
        """Show a temporary message next to the go to file path buttons."""
        if hasattr(self, 'activating_label'):
            return  

        self.activating_label = ttk.Label(self.version_combobox.master, text=f"{message}", foreground="green")
        self.activating_label.pack(side='left', padx=(10, 0))

    def hide_addon_page_message(self):
        """Hide the temporary message."""
        if hasattr(self, 'activating_label'):
            self.activating_label.destroy()
            del self.activating_label

    def update_addon_status(self, event=None):
        """Update the 'Status' column based on the selected Blender version."""
        print("Starting addon status update thread...") 
        threading.Thread(target=self._update_addon_status_thread, daemon=True).start()

    def _update_addon_status_thread(self):
        selected_version = self.version_var.get()
        print(f"Selected Blender version: {selected_version}") 

        if not selected_version or selected_version == "Select Blender Version":
            print("No valid Blender version selected.")  
            return

        temp_script_path = None 

        try:
            self.show_addon_page_message("Loading...")
            blender_exe = self.get_blender_executable_path()
            if not blender_exe or not os.path.exists(blender_exe):
                print("Main Blender executable not found.")
                return

            main_blender_version = self.get_blender_version(blender_exe)
            print(f"Main Blender version: {main_blender_version}")

            if not main_blender_version.startswith(selected_version):
                print(f"Main Blender version does not match. Searching in BLENDER_DIR for version {selected_version}...")
                blender_exe = self.get_matching_blender_executable(selected_version)

            if not blender_exe or not os.path.exists(blender_exe):
                print(f"No matching Blender executable found for version {selected_version}.")
                return

            print(f"Using Blender executable: {blender_exe}")

            blender_manager_dir = BLENDER_MANAGER_DIR.replace("\\", "/")
            print(f"Formatted BLENDER_MANAGER_DIR: {blender_manager_dir}")  

            script_content = f"""
import bpy
import json
import os

BLENDER_MANAGER_DIR = r"{blender_manager_dir}"
output_file = os.path.join(BLENDER_MANAGER_DIR, "addon_status.json")

addon_status = {{}}
try:
    for addon in bpy.context.preferences.addons.values():
        module_name = getattr(addon, "module", "Unknown")
        is_enabled = True
        addon_status[module_name] = is_enabled
except Exception as e:
    addon_status["error"] = f"Error fetching addons: {{str(e)}}"

try:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(addon_status, f, indent=4)
    print(f"Addon status written to: {{output_file}}")
except Exception as e:
    print(f"Failed to write addon status JSON: {{str(e)}}")
            """
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py", encoding="utf-8") as temp_script:
                temp_script_path = temp_script.name
                temp_script.write(script_content)
            print(f"Temporary Blender script created at: {temp_script_path}") 

            print("Running Blender subprocess...")  
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE 

            process = subprocess.run(
                [blender_exe, "--background", "--python", temp_script_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo 
            )
            print("Blender subprocess completed.")  


            addon_status_file = os.path.join(blender_manager_dir, "addon_status.json")
            if not os.path.exists(addon_status_file):
                self.show_error("Addon status file not found.")
                return

            with open(addon_status_file, "r", encoding="utf-8") as f:
                addon_status = json.load(f)

            def update_treeview():
                for item in self.plugins_tree.get_children():
                    addon_name = self.plugins_tree.item(item, "values")[0]
                    status = "Active" if addon_status.get(addon_name, False) else "Inactive"
                    self.plugins_tree.set(item, 'Status', status)

            self.plugins_tree.after(0, update_treeview)

        except Exception as e:
            self.show_error(f"Failed to update addon status: {e}")
        finally:
            self.hide_addon_page_message()
            if temp_script_path and os.path.exists(temp_script_path):
                os.remove(temp_script_path)

    def get_blender_version(self, blender_executable):
        """Retrieve Blender version from the executable."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE  

            process = subprocess.run(
                [blender_executable, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo 
            )
            version_line = process.stdout.splitlines()[0]
            version = version_line.split(" ")[1] 
            return version
        except Exception as e:
            print(f"Failed to retrieve Blender version: {e}")
            return ""

    def get_matching_blender_executable(self, selected_version):
        import random
        """Find a matching Blender executable in BLENDER_DIR."""
        try:
            blender_folders = [
                folder for folder in os.listdir(BLENDER_DIR)
                if folder.startswith(f"Blender {selected_version}")
            ]

            if not blender_folders:
                print(f"No matching Blender folders found for version {selected_version}.")
                return None

            selected_folder = random.choice(blender_folders)
            blender_exe = os.path.join(BLENDER_DIR, selected_folder, "blender.exe")
            if not os.path.exists(blender_exe):
                print(f"Executable not found in: {blender_exe}")
                return None

            return blender_exe
        except Exception as e:
            print(f"Failed to find matching Blender executable: {e}")
            return None


    def show_error(self, message):
        """Show error message in the main thread."""
        def show():
            messagebox.showerror("Error", message)
        self.plugins_tree.after(0, show)







    def update_duplicate_menu(self):
        """Updates the 'Duplicate to...' submenu with available Blender versions."""
        self.duplicate_menu.delete(0, "end")  

        blender_versions = self.get_blender_versions_for_plugins()
        if not blender_versions:
            self.duplicate_menu.add_command(label="No versions found", state="disabled")
            return

        for version in blender_versions:
            self.duplicate_menu.add_command(
                label=version,
                command=lambda v=version: self.duplicate_addon_to_version(v)
            )

    def duplicate_addon_to_version(self, target_version):
        """Duplicate the selected addon to the specified Blender version."""
        import platform
        selected_item = self.plugins_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "No addon selected.")
            return

        addon_name = self.plugins_tree.item(selected_item, "values")[0]
        current_addon_path = os.path.join(self.directory_path.get(), addon_name)

        if not os.path.exists(current_addon_path):
            messagebox.showerror("Error", "The selected addon does not exist.")
            return


        try:
            blender_config_path = get_blender_config_path()
        except EnvironmentError as e:
            messagebox.showerror("Error", f"Failed to determine Blender configuration path: {e}")
            return

        target_addon_path = os.path.join(
            blender_config_path,
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
        import ast
        import webbrowser

        try:
            import webview
        except ImportError:
            webview = None
            print("Webview library not found, trying to open in browser...")

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
            if webview:
                try:
                    webview.create_window(f"{plugin_name} Documentation", url_to_open)
                    webview.start()
                except Exception as e:
                    print(f"Failed to open with webview: {e}")
                    try:
                        webbrowser.open(url_to_open)
                    except Exception as browser_error:
                        messagebox.showerror("Error", f"Failed to open the documentation in the browser: {browser_error}")
            else:
                try:
                    webbrowser.open(url_to_open)
                except Exception as browser_error:
                    messagebox.showerror("Error", f"Failed to open the documentation in the browser: {browser_error}")
        else:
            messagebox.showinfo("Info", "No documentation URL found for this plugin.")





    def get_blender_versions_for_plugins(self):
        """Retrieve available Blender versions."""
        versions = []
        blender_foundation_path = get_blender_config_path()

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

        try:
            blender_config_path = get_blender_config_path()
        except EnvironmentError as e:
            print(f"Error determining Blender config path: {e}")
            return

        self.directory_path.set(
            os.path.join(
                blender_config_path, 
                selected_version, 
                "scripts", 
                "addons"
            )
        )
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
        """Get the default plugin directory based on the platform."""
        try:
            blender_config_path = get_blender_config_path()
        except EnvironmentError as e:
            messagebox.showerror("Error", f"Failed to determine Blender configuration path: {e}")
            return None

        default_version = "4.2"  
        plugin_directory = os.path.join(
            blender_config_path, 
            default_version, 
            "scripts", 
            "addons"
        )
        return plugin_directory

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
        print("Refreshing plugins list...")  

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
                self.plugins_tree.insert('', 'end', values=(item, version, compatible, " ")) 
            elif item.endswith('.py'):
                version, compatible = self.get_plugin_info(item_path)
                plugin_name = os.path.splitext(item)[0]
                self.plugins_tree.insert('', 'end', values=(plugin_name, version, compatible, " ")) 

        self.update_addon_status()


    def update_addon_status(self, event=None):
        """
        Update the 'Status' column based on the selected Blender version.
        """
        threading.Thread(target=self._update_addon_status_thread, daemon=True).start()


    def get_plugin_info(self, addon_path):
        import ast

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

            addon_name = None
            if file_path.lower().endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    namelist = zip_ref.namelist()
                    top_level_items = set(name.split('/')[0] for name in namelist if not name.endswith('/'))

                    if len(top_level_items) == 1:
                        addon_name = list(top_level_items)[0]
                        zip_ref.extractall(addons_dir)
                        print(f"Extracted {file_path} to {addons_dir}")
                    else:
                        folder_name = os.path.splitext(basename)[0]
                        addon_name = folder_name
                        extract_path = os.path.join(addons_dir, folder_name)
                        os.makedirs(extract_path, exist_ok=True)
                        zip_ref.extractall(extract_path)
                        print(f"Extracted {file_path} to {extract_path}")
            elif file_path.lower().endswith('.py'):
                shutil.copy(file_path, destination)
                addon_name = os.path.splitext(basename)[0]
                print(f"Copied {file_path} to {destination}")

            self.refresh_plugins_list()
            messagebox.showinfo(
                "Success", f"Plugin '{basename}' has been added successfully!"
            )

            if self.auto_activate_plugin_var.get() and addon_name:
                self.auto_activate_plugin(addon_name)
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
        self.open_menu = tk.Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="Open With...", menu=self.open_menu)
        self.context_menu.add_command(label="Rename", command=self.rename_project_from_context)
        self.context_menu.add_command(label="Go to File Path", command=self.go_to_project_file_path)
        self.context_menu.add_command(label="Delete", command=self.remove_project_from_context)
        self.context_menu.add_command(label="Export", command=self.export_project_from_context)
        self.context_menu.add_command(label="Info", command=self.view_project_content_from_context)
        self.move_menu = tk.Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="Move to Folder", menu=self.move_menu)

        self.bind_right_click(self.projects_tree, self.show_context_menu_projects)

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
            self.projects_tree.focus(selected_item)
            self.populate_move_menu(self.move_menu)
            self.open_project_menu()  
            self.context_menu.post(event.x_root, event.y_root)
            
    def open_project_menu(self):
        """Populate the Open With... menu with available Blender versions."""
        blender_versions = [
            folder for folder in os.listdir(BLENDER_DIR)
            if os.path.isdir(os.path.join(BLENDER_DIR, folder))
        ]

        self.open_menu.delete(0, "end")  

        main_blender_path = self.get_blender_executable_path()
        if os.path.exists(main_blender_path):
            self.open_menu.add_command(
                label="Blender Main",
                command=lambda: self.open_project_with_blender(main_blender_path)
            )
        else:
            self.open_menu.add_command(
                label="Blender Main (Not Found)",
                state="disabled"
            )

        if not blender_versions:
            self.open_menu.add_command(label="No Blender versions found", state="disabled")
            return

        for version in sorted(blender_versions):
            version_path = os.path.join(BLENDER_DIR, version, "blender.exe")
            if os.path.exists(version_path):
                self.open_menu.add_command(
                    label=version,
                    command=lambda path=version_path: self.open_project_with_blender(path)
                )


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

        blender_path = self.get_blender_executable_path()
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
            startupinfo.wShowWindow = 0  
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
        """Show a temporary 'Exporting...' message."""
        if hasattr(self, 'exporting_label'):
            return  


        parent_widget = self  

        self.exporting_label = ttk.Label(parent_widget, text="Exporting...", foreground="red")
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
        if not hasattr(self, 'projects_tree'):
            print("Error: projects_tree is not defined yet.")
            return

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


    def open_project_with_blender(self, blender_executable_path):
        """Open the selected project with the specified Blender executable."""
        selected_item = self.projects_tree.focus()
        if selected_item:
            project_path = self.get_item_full_path(selected_item)
            if os.path.isfile(project_path) and project_path.lower().endswith(('.blend', '.blend1', '.blend11', '.blend111')):
                try:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  
                    subprocess.Popen(
                        [blender_executable_path, project_path],
                        startupinfo=startupinfo,
                        shell=False
                    )
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open project with Blender: {e}")
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

            if os.path.isfile(project_dir) and project_dir.lower().endswith(('.blend', '.blend1', '.blend2', '.blend11', '.blend3')):
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
        """Open the directory of the selected project in the file explorer."""
        selected_item = self.projects_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "No project selected.")
            return

        project_path = self.get_item_project_folder_path(selected_item[0]) 
        if os.path.exists(project_path):
            try:
                if os.name == 'nt':
                    os.startfile(project_path)
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', project_path])
                else:
                    subprocess.Popen(['xdg-open', project_path])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open directory: {e}")
        else:
            messagebox.showwarning("Warning", "The selected directory does not exist.")



    def get_item_project_folder_path(self, item_id):
        """Get the folder path of a TreeView item."""
        parts = []
        while item_id:
            item_text = self.projects_tree.item(item_id, "text")
            parts.insert(0, item_text)
            item_id = self.projects_tree.parent(item_id)
    
        full_path = os.path.join(self.project_directory_path.get(), *parts)

        if os.path.isfile(full_path):
            return os.path.dirname(full_path)
        return full_path


    def view_project_content(self):
        import datetime as dt
        import stat
        import tempfile
        import subprocess
        import json
        from PIL import Image, ImageTk
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog
        import os

        selected_item = self.projects_tree.focus()
        if selected_item:
            project_path = self.get_item_full_path(selected_item)
            if os.path.exists(project_path):
                try:
                    stats = os.stat(project_path)
                    size = stats.st_size
                    size_mb = size / (1024 * 1024)
                    size_mb_str = f"{size_mb:.2f} MB"
                    created_time = dt.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    modified_time = dt.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    accessed_time = dt.datetime.fromtimestamp(stats.st_atime).strftime('%Y-%m-%d %H:%M:%S')
                    is_dir = os.path.isdir(project_path)
                    permissions = stat.filemode(stats.st_mode)

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

                    thumbnail, meshes, total_vertex_count, materials, textures = self.get_embedded_thumbnail_meshes_and_vertex_count(project_path)

                    content_window = tk.Toplevel(self)
                    content_window.title(f"Properties of {os.path.basename(project_path)}")
                    content_window.geometry("800x600")
                    content_window.transient(self)
                    content_window.resizable(False, False)
                    content_window.iconbitmap(r"Assets/Images/bmng.ico")
                    content_window.update_idletasks()
                    x = self.winfo_rootx() + (self.winfo_width() // 2) - (content_window.winfo_width() // 2)
                    y = self.winfo_rooty() + (self.winfo_height() // 2) - (content_window.winfo_height() // 2)
                    content_window.geometry(f"+{x}+{y}")

                    main_frame = ttk.Frame(content_window, padding=(10, 10, 10, 10))
                    main_frame.pack(fill='both', expand=True)

                    properties_frame = ttk.Frame(main_frame)
                    properties_frame.pack(side='left', fill='y', padx=10, pady=10)

                    preview_frame = ttk.Frame(main_frame)
                    preview_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

                    properties = (
                        f"Name: {os.path.basename(project_path)}\n"
                        f"Path: {project_path}\n"
                        f"Type: {'Folder' if is_dir else 'File'}\n"
                        f"Size: {size_mb_str}\n"
                        f"Created Time: {created_time}\n"
                        f"Modified Time: {modified_time}\n"
                        f"Accessed Time: {accessed_time}\n"
                        f"Permissions: {permissions}\n"
                        f"Time Spent: {time_spent}\n"
                        f"Total Vertex Count: {total_vertex_count}\n"
                    )

                    properties_label = tk.Text(properties_frame, wrap='word', width=40, height=20)
                    properties_label.insert('1.0', properties)
                    properties_label.configure(state='disabled')
                    properties_label.pack(expand=1, fill='both')

                    canvas = tk.Canvas(preview_frame, width=200, height=200)
                    canvas.pack(anchor='n', padx=5, pady=5)
                    if thumbnail:
                        thumbnail = thumbnail.resize((200, 200), Image.LANCZOS)
                        thumbnail = ImageTk.PhotoImage(thumbnail)
                        canvas.create_image(100, 100, image=thumbnail)
                        canvas.image = thumbnail
                    else:
                        placeholder = Image.new("RGB", (200, 200), color=(200, 200, 200))
                        placeholder = ImageTk.PhotoImage(placeholder)
                        canvas.create_image(100, 100, image=placeholder)
                        canvas.image = placeholder

                    notebook = ttk.Notebook(preview_frame)
                    notebook.pack(expand=1, fill='both', padx=5, pady=5)

                    meshes_frame = ttk.Frame(notebook)
                    notebook.add(meshes_frame, text='Meshes')

                    meshes_listbox = tk.Listbox(meshes_frame)
                    meshes_listbox.pack(expand=1, fill='both', padx=5, pady=5)

                    if meshes:
                        for mesh_name in meshes:
                            meshes_listbox.insert(tk.END, mesh_name)
                    else:
                        meshes_listbox.insert(tk.END, "No meshes found.")
                        meshes_listbox.configure(state='disabled')

                    export_mesh_button = ttk.Button(meshes_frame, text="Export Selected Mesh", command=lambda: self.export_selected_mesh(meshes_listbox, project_path))
                    export_mesh_button.pack(pady=5)

                    materials_frame = ttk.Frame(notebook)
                    notebook.add(materials_frame, text='Materials')

                    materials_listbox = tk.Listbox(materials_frame)
                    materials_listbox.pack(expand=1, fill='both', padx=5, pady=5)

                    if materials:
                        for mat_name in materials:
                            materials_listbox.insert(tk.END, mat_name)
                    else:
                        materials_listbox.insert(tk.END, "No materials found.")
                        materials_listbox.configure(state='disabled')

                    export_material_button = ttk.Button(materials_frame, text="Export Selected Material", command=lambda: self.export_selected_material(materials_listbox, project_path))
                    export_material_button.pack(pady=5)

                    textures_frame = ttk.Frame(notebook)
                    notebook.add(textures_frame, text='Textures')

                    textures_listbox = tk.Listbox(textures_frame)
                    textures_listbox.pack(expand=1, fill='both', padx=5, pady=5)

                    if textures:
                        for tex_path in textures:
                            textures_listbox.insert(tk.END, tex_path)
                    else:
                        textures_listbox.insert(tk.END, "No textures found.")
                        textures_listbox.configure(state='disabled')

                    export_texture_button = ttk.Button(textures_frame, text="Export Selected Texture", command=lambda: self.export_selected_texture(textures_listbox))
                    export_texture_button.pack(pady=5)

                except Exception as e:
                    messagebox.showerror("Error", f"Failed to retrieve properties: {e}")
            else:
                messagebox.showerror("Error", "Selected project does not exist.")
        else:
            messagebox.showwarning("Warning", "No project selected.")

    def get_embedded_thumbnail_meshes_and_vertex_count(self, blend_file_path):
        from PIL import Image
        import struct
        import os
        import json
        import tempfile
        import subprocess

        def blend_extract_thumb(path):
            REND = b'REND'
            TEST = b'TEST'

            with open(path, 'rb') as blendfile:
                head = blendfile.read(12)

                if not head.startswith(b'BLENDER'):
                    return None, 0, 0

                is_64_bit = (head[7] == b'-'[0])
                is_big_endian = (head[8] == b'V'[0])

                sizeof_bhead = 24 if is_64_bit else 20
                int_endian = '>i' if is_big_endian else '<i'
                int_endian_pair = int_endian + 'i'

                while True:
                    bhead = blendfile.read(sizeof_bhead)

                    if len(bhead) < sizeof_bhead:
                        return None, 0, 0

                    code = bhead[:4]
                    length = struct.unpack(int_endian, bhead[4:8])[0]

                    if code == REND:
                        blendfile.seek(length, os.SEEK_CUR)
                    else:
                        break

                if code != TEST:
                    return None, 0, 0

                try:
                    x, y = struct.unpack(int_endian_pair, blendfile.read(8))
                except struct.error:
                    return None, 0, 0

                length -= 8
                if length != x * y * 4:
                    return None, 0, 0

                image_buffer = blendfile.read(length)
                if len(image_buffer) != length:
                    return None, 0, 0

                return image_buffer, x, y

        try:
            buf, width, height = blend_extract_thumb(blend_file_path)
            if buf:
                from io import BytesIO
                import zlib

                def write_png(buf, width, height):
                    width_byte_4 = width * 4
                    raw_data = b"".join(b'\x00' + buf[span:span + width_byte_4]
                                        for span in range((height - 1) * width * 4, -1, - width_byte_4))

                    def png_pack(png_tag, data):
                        chunk_head = png_tag + data
                        return struct.pack("!I", len(data)) + chunk_head + struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head))

                    return b"".join([
                        b'\x89PNG\r\n\x1a\n',
                        png_pack(b'IHDR', struct.pack("!2I5B", width, height, 8, 6, 0, 0, 0)),
                        png_pack(b'IDAT', zlib.compress(raw_data, 9)),
                        png_pack(b'IEND', b'')])

                png_data = write_png(buf, width, height)
                thumbnail_image = Image.open(BytesIO(png_data))
            else:
                thumbnail_image = None
        except Exception as e:
            print(f"Error extracting thumbnail: {e}")
            thumbnail_image = None

        blender_exe_path = self.get_blender_executable_path()
        if not blender_exe_path:
            print("Blender executable path not found.")
            return thumbnail_image, None, None, None, None

        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = os.path.join(temp_dir, 'data.json')
            script_path = os.path.join(temp_dir, 'extract_data.py')

            script_content = '''
import bpy
import os
import json
import sys

blend_file_path = sys.argv[-2]
data_path = sys.argv[-1]

bpy.ops.wm.open_mainfile(filepath=blend_file_path)

meshes = [obj.name for obj in bpy.data.objects if obj.type == 'MESH']
total_vertex_count = sum(len(obj.data.vertices) for obj in bpy.data.objects if obj.type == 'MESH')

materials = [mat.name for mat in bpy.data.materials if not mat.library]

textures = []
for image in bpy.data.images:
    if image.filepath:
        tex_path = bpy.path.abspath(image.filepath)
        if os.path.exists(tex_path):
            textures.append(tex_path)

data = {
    "meshes": meshes,
    "total_vertex_count": total_vertex_count,
    "materials": materials,
    "textures": textures
}
with open(data_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
            '''

            with open(script_path, 'w', encoding='utf-8') as script_file:
                script_file.write(script_content)

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            subprocess.run([
                blender_exe_path,
                '--background',
                '--factory-startup',
                '--python', script_path,
                '--',
                blend_file_path,
                data_path
            ], check=True, startupinfo=startupinfo)

            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            meshes = data.get('meshes', [])
            total_vertex_count = data.get('total_vertex_count', 0)
            materials = data.get('materials', [])
            textures = data.get('textures', [])

        return thumbnail_image, meshes, total_vertex_count, materials, textures

    def export_selected_material(self, materials_listbox, project_path):
        import tempfile
        import subprocess
        import os
        from tkinter import messagebox, filedialog

        selected_indices = materials_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "No material selected.")
            return
        selected_material = materials_listbox.get(selected_indices[0])

        filetypes = [
            ("Blender File", "*.blend"),
            ("FBX File", "*.fbx"),
            ("OBJ File", "*.obj"),
            ("Substance Archive", "*.sbsar"),
            ("All Files", "*.*"),
        ]

        export_path = filedialog.asksaveasfilename(
            defaultextension=".blend",
            filetypes=filetypes,
            title="Save Material As"
        )
        if not export_path:
            return

        try:
            blender_exe_path = self.get_blender_executable_path()
            if not blender_exe_path:
                messagebox.showerror("Error", "Blender executable path not found.")
                return

            with tempfile.TemporaryDirectory() as temp_dir:
                script_path = os.path.join(temp_dir, 'export_material.py')

                _, ext = os.path.splitext(export_path)
                ext = ext.lower()

                if ext == ".blend":
                    script_content = f'''
import bpy

blend_file_path = r"{project_path}"
material_name = r"{selected_material}"
export_path = r"{export_path}"

bpy.ops.wm.read_factory_settings(use_empty=True)

with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
    if material_name in data_from.materials:
        data_to.materials = [material_name]
    else:
        print(f"Material {{material_name}} not found in the blend file.")
        exit()

bpy.ops.wm.save_as_mainfile(filepath=export_path)
    '''
                elif ext == ".fbx" or ext == ".obj":
                    script_content = f'''
import bpy

blend_file_path = r"{project_path}"
material_name = r"{selected_material}"
export_path = r"{export_path}"

bpy.ops.wm.read_factory_settings(use_empty=True)

bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object

with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
    if material_name in data_from.materials:
        data_to.materials = [material_name]
    else:
        print(f"Material {{material_name}} not found in the blend file.")
        exit()

mat = bpy.data.materials.get(material_name)
if mat:
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

if export_path.lower().endswith(".fbx"):
    bpy.ops.export_scene.fbx(
        filepath=export_path,
        use_selection=True,
        embed_textures=True
    )
elif export_path.lower().endswith(".obj"):
    bpy.ops.export_scene.obj(
        filepath=export_path,
        use_selection=True,
        use_materials=True
    )
    '''
                elif ext == ".sbsar":
                    messagebox.showerror("Error", "Exporting to .sbsar format is not supported.")
                    return
                else:
                    messagebox.showerror("Error", f"Unsupported file extension: {ext}")
                    return

                with open(script_path, 'w', encoding='utf-8') as script_file:
                    script_file.write(script_content)

                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0

                subprocess.run([
                    blender_exe_path,
                    '--background',
                    '--factory-startup',
                    '--python', script_path
                ], check=True, startupinfo=startupinfo)

            messagebox.showinfo("Success", f"Material '{selected_material}' exported successfully to '{export_path}'.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to export material: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def export_selected_mesh(self, meshes_listbox, project_path):
        import tempfile
        import subprocess
        import os
        from tkinter import messagebox, filedialog

        selected_indices = meshes_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "No mesh selected.")
            return
        selected_mesh = meshes_listbox.get(selected_indices[0])

        export_path = filedialog.asksaveasfilename(
            defaultextension=".fbx",
            filetypes=[("Autodesk FBX", "*.fbx"), ("All Files", "*.*")],
            title="Save Mesh As"
        )
        if not export_path:
            return

        try:
            blender_exe_path = self.get_blender_executable_path()
            if not blender_exe_path:
                messagebox.showerror("Error", "Blender executable path not found.")
                return

            with tempfile.TemporaryDirectory() as temp_dir:
                script_path = os.path.join(temp_dir, 'export_mesh.py')

                script_content = f'''
import bpy

blend_file_path = r"{project_path}"
mesh_name = r"{selected_mesh}"
export_path = r"{export_path}"

bpy.ops.wm.open_mainfile(filepath=blend_file_path)

for obj in bpy.data.objects:
    obj.select_set(False)

obj = bpy.data.objects.get(mesh_name)
if obj:
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.export_scene.fbx(
        filepath=export_path,
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL'
    )
else:
    print(f"Mesh {{mesh_name}} not found.")
    '''

                with open(script_path, 'w', encoding='utf-8') as script_file:
                    script_file.write(script_content)

                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0

                subprocess.run([
                    blender_exe_path,
                    '--background',
                    '--factory-startup',
                    '--python', script_path
                ], check=True, startupinfo=startupinfo)

            messagebox.showinfo("Success", f"Mesh '{selected_mesh}' exported successfully to '{export_path}'.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to export mesh: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def export_selected_texture(self, textures_listbox):
        import shutil
        import os
        from tkinter import messagebox, filedialog

        selected_indices = textures_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "No texture selected.")
            return
        selected_texture_path = textures_listbox.get(selected_indices[0])

        if not os.path.exists(selected_texture_path):
            messagebox.showerror("Error", f"Texture file not found: {selected_texture_path}")
            return

        save_dir = filedialog.askdirectory(title="Select Folder to Save Texture")
        if not save_dir:
            return

        try:
            destination = os.path.join(save_dir, os.path.basename(selected_texture_path))
            shutil.copy(selected_texture_path, destination)
            messagebox.showinfo("Success", f"Texture copied to '{destination}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy texture: {e}")









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

        try:
            blender_config_path = get_blender_config_path()
        except EnvironmentError as e:
            messagebox.showerror("Error", f"Failed to determine Blender configuration path: {e}")
            return None

        default_project_dir = os.path.join(blender_config_path, "Projects")

        try:
            with open(config_file_path, 'r') as f:
                data = json.load(f)
            return data.get('project_directory', default_project_dir)
        except FileNotFoundError:
            if not os.path.exists(default_project_dir):
                os.makedirs(default_project_dir, exist_ok=True)
            return default_project_dir
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project directory: {e}")
            return default_project_dir


  #------------------------------------------------------------#  
  #-------------------Version Management------------------------#
  #------------------------------------------------------------#      


    def create_version_management_tab(self):
        
        self.versions_parent_frame = ttkb.Frame(self.version_management_tab, padding=(10, 0, 0, 0))
        self.versions_parent_frame.pack(expand=1, fill='both')
        
        self.create_install_view()
        self.create_installed_view()
 
        
        self.toggle_button_frame = ttkb.Frame(self.version_management_tab)
        self.toggle_button_frame.place(relx=0.0, rely=1.0, anchor='sw')  
    
        self.toggle_button = ttkb.Button(
            self.toggle_button_frame,
            text="Show Installed Versions",
            takefocus=False,
            command=self.toggle_views,
            bootstyle="secondary"
        )
        self.toggle_button.pack(padx=10, pady=10)

        self.show_install_view()
        self.showing_install = True
    
    def create_install_view(self):
        self.install_frame = ttkb.Frame(self.versions_parent_frame, padding=(0, 0, 0, 0))
    
        left_frame = ttkb.Frame(self.install_frame)
        left_frame.pack(side='left', fill='y', padx=(0, 10), pady=(0, 10))
    
        right_frame = ttkb.Frame(self.install_frame)
        right_frame.pack(side='right', expand=1, fill='both')
        button_font_family = self.button_font_family
        button_font_size = self.button_font_size
        font_family = self.treeview_font_family
        font_size = self.treeview_font_size
        os_frame = ttkb.Frame(left_frame)
        os_frame.pack(fill='x', pady=(0, 10))
    
        self.os_label = ttkb.Label(
            os_frame,
            text="Select Operating System:",
            font=(button_font_family, 10, 'bold')
        )
        self.os_label.pack(side='top', padx=(10, 10))
    
        self.os_combobox = ttkb.Combobox(
            os_frame,
            values=["Windows", "macOS", "Linux"],
            state='readonly',
            font=(button_font_family, 10),
            bootstyle="primary"
        )
        self.os_combobox.set("Select OS")
        self.os_combobox.pack(fill='x', padx=(10, 10))
        self.os_combobox.bind("<<ComboboxSelected>>", self.on_os_selected)
    
        self.win_arch_combobox = ttkb.Combobox(
            os_frame,
            values=["32-bit", "64-bit"],
            state='readonly',
            font=(button_font_family, 10),
            bootstyle="primary"
        )
        self.win_arch_combobox.set("Select Architecture")
        self.win_arch_combobox.pack(fill='x', padx=(10, 10))
        self.win_arch_combobox.pack_forget()  
    
        self.arch_combobox = ttkb.Combobox(
            os_frame,
            values=["Intel", "Apple Silicon"],
            state='readonly',
            font=(button_font_family, 10),
            bootstyle="primary"
        )
        self.arch_combobox.set("Select Architecture")
        self.arch_combobox.pack(fill='x', padx=(10, 10))
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
        self.get_stable_btn.pack(fill='x', pady=(5, 5), padx=(10, 10))
    
        self.get_unstable_btn = ttkb.Button(
            buttons_frame,
            text="Get Unstable Versions",
            takefocus=False,
            command=self.get_unstable_versions,
            bootstyle="primary"
        )
        self.get_unstable_btn.pack(fill='x', pady=(5, 5), padx=(10, 10))
    
        self.install_btn = ttkb.Button(
            left_frame,
            text="Install",
            takefocus=False,
            command=self.install_version,
            bootstyle="primary"
        )
        self.install_btn.pack(fill='x', pady=(5, 10), padx=(10, 10))
    
        self.install_progress_frame = ttkb.Frame(left_frame)
        self.install_progress_label = ttkb.Label(
            self.install_progress_frame,
            text="Download Progress:",
            font=('Helvetica', 10)
        )
        self.install_progress_label.pack(side='top', padx=(10, 10))
    
        self.install_progress_var = tk.DoubleVar()
        self.install_progress_bar = ttkb.Progressbar(
            self.install_progress_frame,
            variable=self.install_progress_var,
            maximum=100,
            bootstyle="primary-striped"
        )
        self.install_progress_bar.pack(fill='x', expand=1)
    
        self.install_progress_frame.pack(fill='x', pady=(5, 10), padx=(10, 10))
        self.install_progress_frame.pack_forget()
    
        self.cancel_button = ttkb.Button(
            left_frame,
            text="Cancel",
            takefocus=False,
            command=self.cancel_installation,
            bootstyle="danger"
        )
        self.cancel_button.pack(fill='x', pady=(5, 10), padx=(10, 10))
        self.cancel_button.pack_forget()
    
        self.release_notes_btn = ttkb.Button(
            left_frame,
            text="Release Notes",
            takefocus=False,
            command=self.show_release_notes,
            bootstyle="info"
        )
        self.release_notes_btn.pack(fill='x', pady=(5, 10), padx=(10, 10))
        self.release_notes_btn.config(state='disabled')  
        style = ttkb.Style()
        style.configure("InstallVersions.Treeview", font=(font_family, 12), rowheight=30)  
        style.configure("InstallVersions.Treeview.Heading", font=('Segoe UI', 14, 'bold'))  
    
        self.tree = ttkb.Treeview(right_frame, columns=("Version", "Release Date"), show="headings", height=20, style="InstallVersions.Treeview")
        self.tree.heading("Version", text="Blender Version", command=lambda: self.sort_treeview_column_installation_tab("Version"))
        self.tree.heading("Release Date", text="Release Date", command=lambda: self.sort_treeview_column_installation_tab("Release Date"))
        self.tree.column("Version", anchor="center")
        self.tree.column("Release Date", anchor="center")
        self.tree.pack(expand=1, fill='both', padx=0, pady=0)
        self.tree.bind("<<TreeviewSelect>>", self.on_treeview_select_install_tab)
        self.download_links = {}
    
        # Auto-detect OS and Architecture
        current_os = platform.system()
        if current_os == "Windows":
            self.os_combobox.set("Windows")
            arch = platform.architecture()[0]
            if arch == "64bit":
                self.win_arch_combobox.set("64-bit")
            elif arch == "32bit":
                self.win_arch_combobox.set("32-bit")
            self.on_os_selected(None)
        elif current_os == "Darwin":
            self.os_combobox.set("macOS")
            machine = platform.machine().lower()
            if "arm" in machine or "aarch64" in machine:
                self.arch_combobox.set("Apple Silicon")
            else:
                self.arch_combobox.set("Intel")
            self.on_os_selected(None)
        elif current_os == "Linux":
            self.os_combobox.set("Linux")
            self.on_os_selected(None)
    
    def create_installed_view(self):
        self.installed_frame = ttkb.Frame(self.versions_parent_frame, padding=(0, 0, 0, 0))
        self.installed_frame.pack(fill='both', expand=True)
        button_font_family = self.button_font_family
        button_font_size = self.button_font_size
        font_family = self.treeview_font_family
        font_size = self.treeview_font_size
        buttons_frame = ttkb.Frame(self.installed_frame)
        buttons_frame.pack(side='left', padx=(0, 10), pady=(0, 0), fill='y')

        self.launch_installed_button = ttkb.Button(
            buttons_frame,
            text="Launch",
            takefocus=False,
            padding=(30, 10),
            command=self.launch_blender,
            style='Custom.TButton'
        )
        self.launch_installed_button.pack(pady=(10, 10), padx=(10, 10), fill='x')

        self.launch_factory_var = tk.BooleanVar()
        self.launch_factory_check = ttk.Checkbutton(
            buttons_frame,
            text="Factory Settings",
            variable=self.launch_factory_var
        )
        self.launch_factory_check.pack(pady=(5, 5), padx=(10, 10), fill='x')

        self.refresh_button = ttkb.Button(
            buttons_frame,
            text="Refresh",
            takefocus=False,
            command=self.refresh_installed_versions,
            padding=(30, 10),
            style='Custom.TButton'
        )
        self.refresh_button.pack(pady=(10, 10), padx=(10, 10), fill='x')

        self.transfer_to_menu_button = ttkb.Button(
            buttons_frame,
            text="Convert To Main",
            takefocus=False,
            command=self.transfer_version_to_menu,
            padding=(30, 10),
            style='Custom.TButton'
        )
        self.transfer_to_menu_button.pack(pady=(10, 10), padx=(10, 10), fill='x')

        style = ttkb.Style()
        style.configure("InstalledVersions.Treeview", font=(font_family, font_size), rowheight=30)
        style.configure("InstalledVersions.Treeview.Heading", font=('Segoe UI', 14, 'bold'))

        self.installed_versions_tree = ttkb.Treeview(
            self.installed_frame,
            columns=('Version',),
            show='headings',
            selectmode='browse',
            height=17,
            style='InstalledVersions.Treeview'
        )
        self.installed_versions_tree.heading('Version', text='Installed Versions')
        self.installed_versions_tree.column('Version', width=300, anchor='center')
        self.installed_versions_tree.pack(side='right', fill='both', expand=1, padx=(0, 0))

        self.versions_context_menu = tk.Menu(self.installed_versions_tree, tearoff=0)
        self.versions_context_menu.add_command(label="Create Shortcut", command=self.create_shortcut)
        self.versions_context_menu.add_command(label="Delete", command=self.remove_installed_version)
        self.bind_right_click(self.installed_versions_tree, self.show_installed_context_menu)


        self.refresh_installed_versions()

    
    def show_install_view(self):
        self.installed_frame.pack_forget()
        self.install_frame.pack(expand=1, fill='both')
        self.toggle_button.configure(text="Installed Versions")
        self.showing_install = True
    
    def show_installed_view(self):
        self.install_frame.pack_forget()
        self.installed_frame.pack(expand=1, fill='both')
        self.toggle_button.configure(text="Install a Version")
        self.showing_install = False
    
    def toggle_views(self):
        if self.showing_install:
            self.show_installed_view()
        else:
            self.show_install_view()

        


        #------------FUNCTİONS------------#




    def show_installed_context_menu(self, event):
        """Displays the context menu for the selected item in the Treeview."""
        item_id = self.installed_versions_tree.identify_row(event.y)
    
        if item_id:  
            self.installed_versions_tree.selection_set(item_id) 
            self.installed_versions_tree.focus(item_id)
            self.versions_context_menu.post(event.x_root, event.y_root)  
            self.versions_context_menu.unpost()  





    def create_shortcut(self):
        """Create a shortcut for the selected Blender version."""
        selected_item = self.installed_versions_tree.focus()

        if not selected_item:
            self.after(0, lambda: messagebox.showwarning("Warning", "Please select a Blender version to make a shortcut."))
            return

        selected_version = self.installed_versions_tree.item(selected_item)['values'][0]

        blender_dir = os.path.join(BLENDER_DIR, selected_version)

        if platform.system() == "Darwin":  # macOS
            blender_exec = os.path.join(blender_dir, "Blender.app", "Contents", "MacOS", "Blender")
        else:
            blender_exec = os.path.join(blender_dir, "blender")
            if platform.system() == "Windows":
                blender_exec += ".exe"

        if not os.path.isfile(blender_exec):
            self.after(0, lambda: messagebox.showerror("Error", f"Blender executable not found in {blender_dir}"))
            return

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop") 

        shortcut_name = f"{selected_version}.lnk" if platform.system() == "Windows" else f"{selected_version}"
        shortcut_path = os.path.join(desktop_path, shortcut_name)

        try:
            if platform.system() == "Windows":
                self.create_windows_shortcut(shortcut_path, blender_exec, blender_dir)
            elif platform.system() == "Darwin": 
                self.create_mac_shortcut(shortcut_path, blender_exec)
            elif platform.system() == "Linux":
                self.create_linux_shortcut(shortcut_path, blender_exec)
            else:
                raise OSError("Unsupported operating system")

            self.after(0, lambda: messagebox.showinfo("Success", f"Shortcut created: {shortcut_path}"))
        except Exception as error:
            error_message = str(error) 
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to create shortcut.\n{error_message}"))


    def create_windows_shortcut(self, shortcut_path, target_path, working_directory):
        import winshell
        with winshell.shortcut(shortcut_path) as shortcut:
            shortcut.path = target_path
            shortcut.working_directory = working_directory
            shortcut.description = "Shortcut to Blender"
            shortcut.icon_location = target_path, 0

    def create_mac_shortcut(self, shortcut_path, target_path):
        os.symlink(target_path, shortcut_path) 

    def create_linux_shortcut(self, shortcut_path, target_path):
        shortcut_path += ".desktop"
        with open(shortcut_path, "w") as shortcut_file:
            shortcut_file.write(f"""
[Desktop Entry]
Type=Application
Name={os.path.basename(shortcut_path)}
Exec={target_path}
Icon={target_path}
Terminal=false
    """)
        os.chmod(shortcut_path, 0o755) 


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
                time.sleep(1)
                self.transfer_to_menu_button.configure(state='normal', text='Convert To Main')
                if os.path.exists(BLENDER_ABSOLUTE_PATH):
                    self.update_blender_version_label()
                    self.refresh_recent_projects()
                    self.run_automatic_addon_setup()

        threading.Thread(target=transfer_files, args=(source_folder, target_folder), daemon=True).start()
            



    def disable_installed_tab_buttons(self):
        self.transfer_to_menu_button.configure(state='disabled')
        self.launch_installed_button.configure(state='disabled')
        self.refresh_button.configure(state='disabled')
        


    def enable_installed_tab_buttons(self):
        self.transfer_to_menu_button.configure(state='normal')
        self.launch_installed_button.configure(state='normal')
        self.refresh_button.configure(state='normal')
        


    def launch_blender(self):
        """
        Launch the selected version of Blender. Handles .app packages for macOS.
        """
        import platform
        import subprocess
        import threading

        selected_item = self.installed_versions_tree.focus()
        if not selected_item:
            self.after(0, lambda: messagebox.showwarning("Warning", "Please select a Blender version to launch."))
            return

        selected_version = self.installed_versions_tree.item(selected_item)['values'][0]
        blender_dir = os.path.join(BLENDER_DIR, selected_version)
    
        if platform.system() == "Darwin":  
            blender_exec = os.path.join(blender_dir, "Blender.app", "Contents", "MacOS", "Blender")
        else: 
            blender_exec = os.path.join(blender_dir, "blender")
            if platform.system() == "Windows":
                blender_exec += ".exe"

        if not os.path.isfile(blender_exec):
            self.after(0, lambda: messagebox.showerror("Error", f"Blender executable not found for version {selected_version}."))
            return

        print(f"Launching Blender version {selected_version} from: {blender_exec}")

        self.launch_installed_button.configure(state='disabled')
        self.after(5000, lambda: self.launch_installed_button.configure(state='normal'))

        try:
            args = [blender_exec]
            if self.launch_factory_var.get():
                args.append('--factory-startup')
                print(f"Launching {selected_version} with factory settings...")

            process = subprocess.Popen(args)

            def monitor_process():
                process.wait()
                print(f"Blender version {selected_version} has exited.")

            threading.Thread(target=monitor_process, daemon=True).start()

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to launch Blender: {e}"))

            






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
        import webbrowser
        import requests

        try:
            import webview
        except ImportError:
            webview = None
            print("Webview library not found, trying to open in browser...")

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
                    response = requests.head(url, timeout=5)
                    return response.status_code == 200
                except Exception as e:
                    print(f"Error checking URL: {e}")
                    return False

            try:
                if check_url(official_url):
                    if webview:
                        try:
                            webview.create_window(f"Release Notes for Blender {major_version}.{minor_version}", official_url)
                            webview.start()
                        except Exception as e:
                            print(f"Error opening with webview: {e}")
                            try:
                                webbrowser.open(official_url)
                            except Exception as browser_error:
                                messagebox.showerror("Error", f"Failed to open in browser: {browser_error}")
                    else:
                        try:
                            webbrowser.open(official_url)
                        except Exception as browser_error:
                            messagebox.showerror("Error", f"Failed to open in browser: {browser_error}")
                elif check_url(alternative_url):
                    if webview:
                        try:
                            webview.create_window(f"Release Notes for Blender {major_version}.{minor_version}", alternative_url)
                            webview.start()
                        except Exception as e:
                            print(f"Error opening with webview: {e}")
                            try:
                                webbrowser.open(alternative_url)
                            except Exception as browser_error:
                                messagebox.showerror("Error", f"Failed to open in browser: {browser_error}")
                    else:
                        try:
                            webbrowser.open(alternative_url)
                        except Exception as browser_error:
                            messagebox.showerror("Error", f"Failed to open in browser: {browser_error}")
                else:
                    messagebox.showerror("Error", f"Release notes for Blender {major_version}.{minor_version} not found.")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
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
            self.win_arch_combobox.pack(fill='x',padx=(10, 10))
            self.arch_combobox.pack_forget()
        elif selected_os == "macOS":
            self.win_arch_combobox.pack_forget()
            self.arch_combobox.pack(fill='x', padx=(10, 10))
        else:
            self.win_arch_combobox.pack_forget()
            self.arch_combobox.pack_forget()


    def reset_get_stable_button(self):
        self.get_stable_btn.config(text="Get Stable Versions", state='normal')
        


    def get_stable_versions(self):
        self.get_stable_btn.config(text="Loading...", state='disabled')
        threading.Thread(target=self.run_async_fetch_stable_versions).start()


    def run_async_fetch_stable_versions(self):
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.async_fetch_stable_versions())
        loop.close()
        self.version_management_tab.after(0, self.reset_get_stable_button)

    async def async_fetch_stable_versions(self):
        import ssl
        import aiohttp
        import certifi
        from bs4 import BeautifulSoup

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
        import ssl
        import asyncio
        import certifi


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

        from bs4 import BeautifulSoup


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
        
        from bs4 import BeautifulSoup
        import requests


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
        import requests

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
                        



            elif file_name.endswith('.dmg'):
                mount_point = tempfile.mkdtemp()
                try:
                    subprocess.run(["hdiutil", "attach", file_path, "-mountpoint", mount_point], check=True)

                    blender_app_path = os.path.join(mount_point, "Blender.app")
                    if os.path.exists(blender_app_path):
                        shutil.copytree(blender_app_path, os.path.join(extracted_path, "Blender.app"))
                    else:
                        raise Exception("Blender.app not found in mounted .dmg.")

                finally:
                    subprocess.run(["hdiutil", "detach", mount_point], check=True)
                    shutil.rmtree(mount_point)
                    os.remove(file_path)





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
        app.initialize_app()
        app.mainloop()
    except Exception as e:
        import traceback

        error_message = f"An unexpected error occurred: {str(e)}\n"
        error_message += traceback.format_exc()  
        log_error_to_file(error_message) 
        print("An error occurred. Check log.txt for more details.")
