﻿# -*- coding: utf-8 -*-
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
from tkinterdnd2 import TkinterDnD, DND_FILES
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import json
import re
import multiprocessing
import traceback
import tempfile
import ast 
end_time = time.time()
print(f"imports loaded in {end_time - start_time}.") 
CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), ".BlenderManager", "config.json")

DEFAULT_SETTINGS = {
    "selected_theme": "darkly",
    "auto_update_checkbox": True,
    "launch_on_startup":False,
    "run_in_background": True,
    "chunk_size_multiplier": 3,
    "window_alpha": 0.98,
    "treeview_font_size": 12,
    "treeview_heading_font_size": 14,
    "treeview_font_family": "Segoe UI",
    "button_font_family": "Segoe UI",
    "button_font_size": 14
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
        
        self.check_existing_window()
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
        self.render_file_paths = {}
        self.notes_data = self._load_notes()
        self.current_render_name = None     
        self.menu_cache = {}  
        self.load_menu_cache()  
        self.create_main_menu()
        self.redirect_output()
        self.start_time = time.time() 
        self.refresh_render_list()
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



    def initialize_app(self):
        """Initializing the application."""
        print("Initializing app...")

        def background_task():
            """Runs heavy initialization tasks in a background thread."""
            try:
                # setup file paths
                setup_complete_file = os.path.join(os.path.expanduser("~"), ".BlenderManager", "setup_complete")
                if os.path.exists(setup_complete_file):
                    print("Setup already complete. Skipping initialization.")
                    return  

                # base directory
                base_dir = BLENDER_MANAGER_DIR
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir)

                # create required directories
                required_dirs = [
                    "BaseMeshes", "BlenderVersions", "mngaddon",
                    "paths", "Projects", "renders"
                ]
                for dir_name in required_dirs:
                    dir_path = os.path.join(base_dir, dir_name)
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path)

                # create required JSON files
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
                            json.dump({}, file)  # Write an empty JSON object

                # mark setup as complete
                with open(setup_complete_file, 'w') as file:
                    file.write("Setup complete.")
            finally:
                print("Initialization complete.")
                # schedule UI updates on the main thread
                self.after(0, self.show_window)
                self.after(0, self.deiconify)

        # start the background task in a separate thread
        threading.Thread(target=background_task, daemon=True).start()


    def load_menu_cache(self):
        
        try:
           
            self.menu_cache['plugins'] = self.refresh_plugins_list()
            self.menu_cache['projects'] = self.refresh_projects_list()
            self.menu_cache['installed_versions'] = self.get_installed_versions()
        except Exception as e:
            print(f"Error Loading: {e}")
                    


    def load_settings_on_begining(self):
        self.settings = load_config()

        
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

        # load data
        self.selected_theme = tk.StringVar(value=self.settings.get("selected_theme", "darkly"))
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
        # Main Frame
        main_frame = ttkb.Frame(self, padding=(20, 20, 20, 20))
        main_frame.pack(expand=1, fill='both')
        font_family = self.button_font_family
        self.style.configure("TNotebook.Tab", font=(font_family, 10))
        self.notebook = ttkb.Notebook(main_frame)
        self.notebook.pack(expand=1, fill='both')
        self.main_menu_tab = ttk.Frame(self.notebook)
        self.installed_tab = ttkb.Frame(self.notebook)
        self.install_tab = ttkb.Frame(self.notebook)
        self.logs_tab = ttkb.Frame(self.notebook)  # Logs tab
        self.notebook.add(self.main_menu_tab, text="Main Menu")
        self.notebook.add(self.installed_tab, text='Installed Versions')
        self.notebook.add(self.install_tab, text='Installation')
        self.plugins_tab = ttkb.Frame(self.notebook)
        self.notebook.add(self.plugins_tab, text='Addon Management')
        self.create_plugins_tab()
        self.project_management_tab = ttkb.Frame(self.notebook)
        self.notebook.add(self.project_management_tab, text='Project Management')
        self.create_project_management_tab()
        self.render_management_tab = ttkb.Frame(self.notebook)
        self.notebook.add(self.render_management_tab, text='Render Management')
        self.create_render_management_tab()
        self.create_installed_tab()
        self.create_install_tab()
        self.notebook.add(self.logs_tab, text='Logs')  # Add logs tab
        self.create_logs_tab()
        self.create_main_menu()
        

        if self.auto_update_var.get():
            print(f"Auto Update: {self.auto_update_var.get()}")
            self.auto_update()
        else:
            print(f"Auto Update: {self.auto_update_var.get()}")
        
    def check_existing_window(self):
        import psutil


        current_pid = os.getpid()
        current_path = os.path.abspath(sys.argv[0])

        possible_exe_names = ["blender_manager.exe", "Blender Manager.exe", "Blender_Manager.exe", "BlenderManager.exe"]

        try:
            tasklist_output = subprocess.check_output("tasklist", shell=True).decode()

            for exe_name in possible_exe_names:
                if exe_name in tasklist_output:
                    for process in psutil.process_iter(attrs=['pid', 'exe']):
                        if process.pid != current_pid and process.info['exe']:
                            if os.path.samefile(process.info['exe'], current_path):
                                self.bring_window_to_front()
                                sys.exit()
        except Exception as e:
            print(f"Error checking for existing window: {e}")
            

    def bring_window_to_front(self):
        """Uses Windows API to bring the existing window to the front."""
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "Blender Manager")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"Error bringing window to front: {e}")
            messagebox.showerror("Error", "Failed to bring the existing window to the front.")




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
        # Restore the window
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
        right_frame.rowconfigure(0, weight=3)  # Render Preview
        right_frame.rowconfigure(1, weight=1)  # Buttons

        
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
            # attempt to convert to appropriate type for sorting
            try:
                # remove any nonnumeric characters for numerical sorting
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
        self.recent_projects_tree.heading("Path", text="Path")  # Hidden column for project path
        self.recent_projects_tree.column("Project Name", anchor="w", width=300, minwidth=200, stretch=True)
        self.recent_projects_tree.column("Last Opened", anchor="center", width=150, minwidth=100, stretch=False)
        self.recent_projects_tree.column("Path", width=0, stretch=False)  # Hide the path column
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
                "consider supporting us! ~ ♡"
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
        webbrowser.open("https://buymeacoffee.com/verlorengest")


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
                    print(f"Checking release file: {release_file_path}")  # Debug line

                    with open(release_file_path, 'r', encoding='utf-8') as file:
                        for line in file:
                            print(f"Reading line: {line.strip()}")  # Debug line
                            version_match = re.search(r'Blender (\d+\.\d+(?:\.\d+)?)', line)
                            if version_match:
                                print(f"Version found in file: {version_match.group(1)}")  # Debug line
                                return version_match.group(1)  # Returns version in format X.Y or X.Y.Z
        except Exception as e:
            print(f"Failed to get Blender version from release files: {e}")
    
        print("No version information found.")  # Debug line
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
        tab3 = ttk.Frame(notebook)


        notebook.add(tab2, text="Preferences")
        notebook.add(tab3, text="Settings")


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

        advanced_frame = ttkb.Frame(tab3)
        advanced_frame.pack(anchor="nw", padx=10, pady=10, expand=True, fill="both")

        self.auto_update_checkbox_widget = ttkb.Checkbutton(
            advanced_frame,
            text="Auto Update",
            variable=self.auto_update_var,
            bootstyle="success",
            command=self.toggle_auto_update
        )
        self.auto_update_checkbox_widget.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.launch_on_startup_checkbox = ttkb.Checkbutton(
            advanced_frame,
            text="Launch on Startup",
            variable=self.launch_on_startup_var,
            bootstyle="success",
            command=self.toggle_launch_on_startup
        )
        self.launch_on_startup_checkbox.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.run_in_background_checkbox = ttkb.Checkbutton(
            advanced_frame,
            text="Run in Background",
            variable=self.run_in_background_var,
            bootstyle="success",
            command=self.toggle_run_in_background
        )
        self.run_in_background_checkbox.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.setup_button = ttkb.Button(
            advanced_frame,
            text="Setup Addon",
            takefocus=False,
            command=self.run_setup
        )
        self.setup_button.grid(row=3, column=0, sticky="w", padx=10, pady=5)

        self.tooltip_label = ttk.Label(
            advanced_frame,
            text="You must install the addon for the program to work properly.",
            font=("Arial", 10)
        )
        self.tooltip_label.grid(row=4, column=0, sticky="w", padx=10, pady=5)

        self.change_launch_blender_button = ttkb.Button(
            advanced_frame,
            text="Change Launch Folder",
            takefocus=False,
            command=self.change_launch_blender
        )
        self.change_launch_blender_button.grid(row=5, column=0, sticky="w", padx=10, pady=5)



        chunk_size_frame = ttkb.LabelFrame(tab3, text="Download Chunk Size Multiplier", padding=(10, 10))
        chunk_size_frame.pack(anchor="nw", padx=10, pady=10, fill="x")

        self.chunk_size_label = ttkb.Label(chunk_size_frame, text=f"Multiplier: {self.chunk_size_multiplier}x")
        self.chunk_size_label.pack(anchor="w", padx=10, pady=5)

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
        self.chunk_size_slider.pack(fill="x", padx=10, pady=5)


        button_font_family = self.button_font_family
        self.style.configure(
            'Small.TButton',
            font=(button_font_family, 8),  
            padding=(2, 1),  
            background='#ff4d4d',
            foreground='white',
            borderwidth=0
        )

        button_frame = ttkb.Frame(tab3)
        button_frame.pack(anchor="s", padx=10, pady=10) 

        reset_button = ttkb.Button(
            button_frame,
            text="Reset All Data",
            takefocus=False,
            command=self.reset_all_data,
            style="Small.TButton"  
        )
        reset_button.pack(side="left", padx=5)

        self.delete_all_versions_button = ttkb.Button(
            button_frame,
            text="Delete All Blender Versions",
            takefocus=False,
            command=self.delete_all_blender_versions,
            style="Small.TButton"  
        )
        self.delete_all_versions_button.pack(side="left", padx=5)

        self.delete_main_blender_button = ttkb.Button(
            button_frame,
            text="Delete Main Blender",
            takefocus=False,
            command=self.delete_main_blender_version,
            style="Small.TButton"  
        )
        self.delete_main_blender_button.pack(side="left", padx=5)
        
        self.reset_defaults_button = ttkb.Button(
            button_frame,
            text="Reset to Defaults",
            takefocus=False,
            command=self.reset_to_default_settings,
            style="Small.TButton"
        )
        self.reset_defaults_button.pack(side="left", padx=5)










        #----------------------------------Functions ---------------------------------------------------
        



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
            self.loading_bar.grid(row=3, column=0, pady=10)  # Use grid instead of pack

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
                    # Hide the main window before deletion
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

        # Directory Selector Frame
        directory_frame = ttk.Frame(plugins_frame)
        directory_frame.pack(fill='x', padx=10, pady=(0, 5))

        # Directory Entry
        self.directory_path = tk.StringVar(value=self.load_plugin_directory())
        self.directory_entry = ttk.Entry(directory_frame, textvariable=self.directory_path, width=50)
        self.directory_entry.grid(row=0, column=0, padx=(0, 5), sticky='w')

        # Browse Button
        self.browse_button = ttk.Button(
            directory_frame,
            text="Browse",
            takefocus=False,
            command=self.browse_directory,
            style='Custom.TButton'
        )
        self.browse_button.grid(row=0, column=1, padx=(0, 5), sticky='w')

        # Go to File Path Button
        self.go_to_button = ttk.Button(
            directory_frame,
            text="Go to File Path",
            takefocus=False,
            command=self.go_to_file_path,
            style='Custom.TButton'
        )
        self.go_to_button.grid(row=0, column=2, padx=(0, 5), sticky='e')

        # Blender Version Label
        version_label = ttk.Label(
            directory_frame,
            text="Blender Version:",
            font=('Segoe UI', 10, 'bold')
        )
        version_label.grid(row=0, column=3, padx=(10, 5), sticky='e')

        # Blender Version Selection Combobox
        self.blender_versions = self.get_blender_versions_for_plugins()
        self.version_var = tk.StringVar()
        self.version_combobox = ttk.Combobox(
            directory_frame,
            textvariable=self.version_var,
            values=self.blender_versions,
            state='readonly'
        )
        self.version_combobox.set("Select Blender Version")
        self.version_combobox.grid(row=0, column=4, padx=(0, 10), sticky='e')
        self.version_combobox.bind("<<ComboboxSelected>>", self.on_blender_for_plugins_version_selected)

        # Plugin Search
        self.plugin_search_var = tk.StringVar()
        self.plugin_search_var.trace("w", lambda *args: self.on_plugin_search_change())



        self.plugin_search_entry = ttk.Entry(
            plugins_frame,
            textvariable=self.plugin_search_var,
            width=50
        )
        self.plugin_search_entry.pack(anchor='w', padx=10, pady=(0, 10))

        # Placeholder text setup
        self.plugin_placeholder_text = "Search Addons"
        self.plugin_search_entry.insert(0, self.plugin_placeholder_text)
        self.plugin_search_entry.configure(foreground="grey")

        # Binding events for placeholder behavior
        self.plugin_search_entry.bind("<FocusIn>", self.on_plugin_entry_click)
        self.plugin_search_entry.bind("<FocusOut>", self.on_plugin_focus_out)




        # Buttons Frame on the left
        buttons_frame = ttk.Frame(plugins_frame)
        buttons_frame.pack(side='left', padx=(10, 10), fill='y')

        # Add Plugin Button
        self.add_plugin_button = ttk.Button(
            buttons_frame,
            text="Add",
            takefocus=False,
            command=self.add_plugin,
            style='Custom.TButton',
            padding=(15, 10)  
        )
        self.add_plugin_button.pack(pady=(10, 10), fill='x')

        # Remove Plugin Button
        self.remove_plugin_button = ttk.Button(
            buttons_frame,
            text="Remove",
            takefocus=False,
            command=self.remove_plugin,
            style='Custom.TButton',
            padding=(15, 10)
        )
        self.remove_plugin_button.pack(pady=(10, 10), fill='x')

        # View Plugin Content Button
        self.view_plugin_button = ttk.Button(
            buttons_frame,
            text="Info",
            takefocus=False,
            command=self.view_plugin_content,
            style='Custom.TButton',
            padding=(15, 10)
        )
        self.view_plugin_button.pack(pady=(10, 10), fill='x')

        # Refresh Plugins List Button
        self.refresh_plugins_button = ttk.Button(
            buttons_frame,
            text="Refresh",
            takefocus=False,
            command=self.refresh_plugins_list,
            style='Custom.TButton',
            padding=(15, 10)
        )
        self.refresh_plugins_button.pack(pady=(10, 10), fill='x')

        style = ttkb.Style()
        self.style.configure("PluginManagement.Treeview", font=('Segoe UI', 12), rowheight=30)  
        self.style.configure("PluginManagement.Treeview.Heading", font=('Segoe UI', 14, 'bold'))  


        # Plugins Treeview on the right
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

        # Scrollbar for the Treeview
        scrollbar = ttk.Scrollbar(plugins_frame, orient="vertical", command=self.plugins_tree.yview)
        self.plugins_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Bind Drag-and-Drop events to the Treeview
        self.plugins_tree.drop_target_register(DND_FILES)
        self.plugins_tree.dnd_bind('<<Drop>>', self.handle_treeview_drop)

        # Load initial plugin list
        self.refresh_plugins_list()


        



        #-----------Functions----------#

    
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

        # Update the plugin directory based on the selected version
        appdata_dir = os.getenv('APPDATA')
        self.directory_path.set(os.path.join(appdata_dir, "Blender Foundation", "Blender", selected_version, "scripts", "addons"))
        self.refresh_plugins_list()




    # Methods for handling plugin search placeholder
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

        if addon_path.endswith('.py'):
            info_file = addon_path
        else:
            info_file = os.path.join(addon_path, "__init__.py")

        if os.path.exists(info_file):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    bl_info = {}
                    tree = ast.parse(content, filename=info_file)

                    for node in tree.body:
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == 'bl_info':
                                    bl_info = ast.literal_eval(node.value)
                                    break

                    if bl_info:
                        version = ".".join(map(str, bl_info.get('version', [])))
                        compatible = ", ".join(map(str, bl_info.get('blender', ["Unknown"])))
            except Exception as e:
                print(f"Failed to read bl_info from {info_file}: {e}")

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

                    # Determine if the zip has a single top-level folder
                    top_level_items = set()
                    for name in namelist:
                        # Ignore directory entries
                        if name.endswith('/'):
                            continue
                        top_level_dir = name.split('/')[0]
                        top_level_items.add(top_level_dir)

                    if len(top_level_items) == 1:
                        # Zip has a single top-level folder or file, extract as is
                        zip_ref.extractall(addons_dir)
                        print(f"Extracted {file_path} to {addons_dir}")
                    else:
                        # Create a folder with the same name as the zip file
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
                    content_window.title(f"Content of {plugin_name}")
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

        # Directory Selector and Entry
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
            command=self.go_to_project_file_path,
            style='Custom.TButton'
        )
        self.project_go_to_button.pack(side='left', padx=(0, 5))

        # Project Search
        self.project_search_var = tk.StringVar()
        self.project_search_var.trace("w", self.on_search_change)


        self.project_search_entry = ttk.Entry(
            projects_frame,
            textvariable=self.project_search_var,
            width=50
        )
        self.project_search_entry.pack(anchor='w', padx=10, pady=(0, 10))

        # Placeholder text
        self.placeholder_text = "Search Projects"
        self.project_search_entry.insert(0, self.placeholder_text)
        self.project_search_entry.configure(foreground="grey")

        def on_entry_click(event):
            if self.project_search_entry.get() == self.placeholder_text:
                self.project_search_entry.delete(0, "end")
                self.project_search_entry.configure(foreground="black")

        def on_focus_out(event):
            if not self.project_search_entry.get():
                self.project_search_entry.insert(0, self.placeholder_text)
                self.project_search_entry.configure(foreground="grey")



        self.project_search_entry.bind("<FocusIn>", on_entry_click)
        self.project_search_entry.bind("<FocusOut>", on_focus_out)


        project_buttons_frame = ttk.Frame(projects_frame)
        project_buttons_frame.pack(side='left', padx=(10, 10), fill='y')

        self.add_project_button = ttk.Button(
            project_buttons_frame,
            text="Add",
            takefocus=False,
            command=self.add_project,
            style='Custom.TButton',
            padding=(15, 10)  # Larger padding for bigger buttons
        )
        self.add_project_button.pack(pady=(10, 10), fill='x')

        # Remove Project Button
        self.remove_project_button = ttk.Button(
            project_buttons_frame,
            text="Remove",
            takefocus=False,
            command=self.remove_project,
            style='Custom.TButton',
            padding=(15, 10)
        )
        self.remove_project_button.pack(pady=(10, 10), fill='x')

        # View Project Content Button
        self.view_project_button = ttk.Button(
            project_buttons_frame,
            text="Info",
            takefocus=False,
            command=self.view_project_content,
            style='Custom.TButton',
            padding=(15, 10)
        )
        self.view_project_button.pack(pady=(10, 10), fill='x')

        # Open Project Button
        self.open_project_button = ttk.Button(
            project_buttons_frame,
            text="Open",
            takefocus=False,
            command=self.open_project,
            style='Custom.TButton',
            padding=(15, 10)
        )
        self.open_project_button.pack(pady=(10, 10), fill='x')

        # Refresh List Button
        self.refresh_projects_button = ttk.Button(
            project_buttons_frame,
            text="Refresh",
            takefocus=False,
            command=self.refresh_projects_list,
            style='Custom.TButton',
            padding=(15, 10)
        )
        self.refresh_projects_button.pack(pady=(10, 10), fill='x')
        

        style = ttkb.Style()
        self.style.configure("ProjectManagement.Treeview", font=('Segoe UI', 12), rowheight=30)  
        self.style.configure("ProjectManagement.Treeview.Heading", font=('Segoe UI', 14, 'bold'))  


        self.projects_tree = ttk.Treeview(
            projects_frame,
            columns=('Project Name', 'Last Modified', 'Size'),
            show='headings',
            selectmode='browse',
            style='ProjectManagement.Treeview'
            
        )
        
        self.projects_tree.drop_target_register(DND_FILES)
        self.projects_tree.dnd_bind('<<Drop>>', self.handle_project_treeview_drop)
        self.projects_tree.heading('Project Name', text='Project Name')
        self.projects_tree.heading('Last Modified', text='Last Modified')
        self.projects_tree.heading('Size', text='Size')
        self.projects_tree.column('Project Name', width=300, anchor='center')
        self.projects_tree.column('Last Modified', width=200, anchor='center')
        self.projects_tree.column('Size', width=100, anchor='center')
        self.projects_tree.pack(side='right', fill='both', expand=1)

        scrollbar = ttk.Scrollbar(projects_frame, orient="vertical", command=self.projects_tree.yview)
        self.projects_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Load initial project list
        self.refresh_projects_list()






        #-----------Functions----------#


    def on_search_change(self, *args): 
        if self.project_search_entry.get() != self.placeholder_text:
            self.filter_projects_tree()


    def open_project(self):
        """Open the selected .blend file using the default application."""
        selected_item = self.projects_tree.focus()
        if selected_item:
            project_name = self.projects_tree.item(selected_item)['values'][0]

            config_file_path = os.path.join(os.path.expanduser("~"), ".BlenderManager","paths", "project_directory.json")
            try:
                with open(config_file_path, 'r') as config_file:
                    config_data = json.load(config_file)
                    project_directory = config_data.get('project_directory')

                    if not project_directory or not os.path.isdir(project_directory):
                        messagebox.showerror("Error", "Project directory not found or invalid. Please check the configuration.")
                        return

                    project_path = os.path.join(project_directory, project_name)

                    if project_path.endswith(('.blend', '.blend1', '.blend2', '.blend3')):
                        try:
                            os.startfile(project_path)
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to open project: {e}")
                    else:
                        messagebox.showwarning("Warning", "The selected project is not a .blend file.")
            except FileNotFoundError:
                messagebox.showerror("Error", "Project configuration file not found. Please set the project directory.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project directory from configuration: {e}")



    def filter_projects_tree(self):
        """Filters the project Treeview based on the search query."""
        query = self.project_search_var.get().lower()
        self.projects_tree.delete(*self.projects_tree.get_children())

        project_dir = self.project_directory_path.get()
        if not os.path.exists(project_dir):
            return

        for item in os.listdir(project_dir):
            if query in item.lower():
                item_path = os.path.join(project_dir, item)
                last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(item_path)))
                size = os.path.getsize(item_path) / (1024 * 1024)  
                self.projects_tree.insert('', 'end', values=(item, last_modified, f"{size:.2f} MB"))



    def handle_project_treeview_drop(self, event):
        file_path = event.data.strip().strip("{}")
        print("Dragged file path:", file_path)

        if file_path.lower().endswith(('.blend', '.blend1', '.blend11')):
            print("Detected a .blend file directly.")
            self.add_project(file_path)
        elif os.path.isdir(file_path):
            print("Detected a directory.")
            if any(file.lower().endswith(('.blend', '.blend1', '.blend11')) for root, dirs, files in os.walk(file_path) for file in files):
                user_choice = messagebox.askyesno("Copy Options", "Do you want to copy the .blend files individually, or keep the folder structure?\n\nYes: Individually\nNo: Keep folder structure")
                self.add_project(file_path, copy_individually=user_choice)
            else:
                messagebox.showerror("Error", "The folder does not contain any .blend files.")
        elif file_path.lower().endswith('.zip'):
            print("Detected a zip file.")
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                if any(file.lower().endswith(('.blend', '.blend1', '.blend11')) for file in zip_ref.namelist()):
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

            if os.path.isfile(project_dir) and project_dir.lower().endswith(('.blend', '.blend1', '.blend11')):
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
            project_name = self.projects_tree.item(selected_item)['values'][0]
            project_path = os.path.join(self.project_directory_path.get(), project_name)

            if os.path.exists(project_path):
                confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove the project '{project_name}'?")
                if confirm:
                    try:
                        
                        if os.path.isdir(project_path):
                            shutil.rmtree(project_path)
                        else:
                           
                            os.remove(project_path)
                        messagebox.showinfo("Success", f"Project '{project_name}' removed.")
                        self.refresh_projects_list()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to remove project: {e}")
            else:
                messagebox.showwarning("Warning", "The selected project does not exist.")


    
    def browse_project_directory(self):
        """Allow the user to select the directory where projects are stored."""
        directory = tk.filedialog.askdirectory()
        if directory:
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
            project_name = self.projects_tree.item(selected_item)['values'][0]
            project_path = os.path.join(self.project_directory_path.get(), project_name)

            if os.path.exists(project_path):
                # Get file properties
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
                            # Use absolute path as key
                            abs_project_path = os.path.abspath(project_path)
                            time_in_seconds = time_data.get(abs_project_path, None)
                            if time_in_seconds is not None:
                                hours, remainder = divmod(time_in_seconds, 3600)
                                minutes, seconds = divmod(remainder, 60)
                                time_spent = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
                        except Exception as e:
                            time_spent = f"Error reading time data: {e}"

                    properties = f"Name: {project_name}\n"
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

                    # Display the properties in a new window
                    content_window = tk.Toplevel(self)
                    content_window.title(f"Properties of {project_name}")
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


    def refresh_projects_list(self):
        """List all projects and their contents from the selected project directory."""
        self.projects_tree.delete(*self.projects_tree.get_children())

        project_dir = self.project_directory_path.get()
        if not os.path.exists(project_dir):
            messagebox.showerror("Error", f"Project directory not found: {project_dir}")
            return

        self.insert_directory('', project_dir)

        self.projects_tree.bind("<<TreeviewOpen>>", self.on_treeview_open)


    def insert_directory(self, parent, path):
        """Add directories and files within a folder to the Treeview."""
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folder_id = self.projects_tree.insert(parent, 'end', values=(item, "", "Folder"), open=False)
                self.projects_tree.insert(folder_id, 'end', text="dummy")  
            else:
                last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(item_path)))
                size = os.path.getsize(item_path) / (1024 * 1024) 
                self.projects_tree.insert(parent, 'end', values=(item, last_modified, f"{size:.2f} MB"), tags=("small",))


    def on_treeview_open(self, event):
        """Handle the opening of a folder in the Treeview."""
        item_id = self.projects_tree.focus()
        folder_path = self.get_folder_path_from_item(item_id)

        children = self.projects_tree.get_children(item_id)
        if len(children) == 1 and self.projects_tree.item(children[0], "text") == "dummy":
            self.projects_tree.delete(children[0])

            self.insert_directory(item_id, folder_path)


    def get_folder_path_from_item(self, item_id):
        """Construct the full folder path based on the Treeview item."""
        parts = []
        while item_id:
            item_text = self.projects_tree.item(item_id, "values")[0]
            parts.append(item_text)
            item_id = self.projects_tree.parent(item_id)
        parts.reverse()
        return os.path.join(self.project_directory_path.get(), *parts)
    



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
            
                # Clear the target directory
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
    # --------------INSTALL VERSIONS TAB---------------#
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

        self.tree = ttkb.Treeview(right_frame, columns=("Version"), show="headings", height=20, style="Custom.Treeview")
        self.tree.heading("Version", text="Blender Version")
        self.tree.column("Version", anchor="center")
        self.tree.pack(expand=True, fill="both")
        
        self.download_links = {}



    # ----Functions----
    
    

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

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url) as response:
                    response.raise_for_status()
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    version_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith("Blender")]
                    if not version_links:
                        self.queue.put(('ERROR', "No stable versions found."))
                        return

                    versions, links = await self.fetch_all_versions(version_links, platform, architecture, session)

                    if not versions:
                        self.queue.put(('ERROR', "No stable versions found for the selected platform."))
                        return

                    self.queue.put(('UPDATE_TREEVIEW', versions, links))

        except Exception as e:
            self.queue.put(('ERROR', f"An unexpected error occurred: {str(e)}"))

    async def fetch_all_versions(self, version_links, platform, architecture, session):
        base_url = "https://download.blender.org/release/"
        tasks = [
            self.fetch_version_page(session, base_url + version_link, platform, architecture)
            for version_link in version_links
        ]
        results = await asyncio.gather(*tasks)

        versions = []
        links = {}
        for v, l in results:
            versions.extend(v)
            links.update(l)

        return versions, links

    async def fetch_version_page(self, session, version_url, platform, architecture):
        try:
            async with session.get(version_url) as response:
                response.raise_for_status()
                html = await response.text()
                version_soup = BeautifulSoup(html, "html.parser")

                download_links = [a['href'] for a in version_soup.find_all('a', href=True)]
                versions = []
                links = {}

                for download_link in download_links:
                    if download_link.endswith(".sha256") or download_link.endswith(".md5"):
                        continue

                    full_link = version_url + download_link
                    try:
                        version_name = "Blender " + download_link.split('-')[1]
                    except IndexError:
                        version_name = "Blender " + version_url.strip('/').split('/')[-1]

                    if platform == "windows":
                        is_64bit = "x64" in download_link or "windows64" in download_link
                        is_32bit = "x86" in download_link or "windows32" in download_link
                        is_generic = "windows" in download_link and not (is_64bit or is_32bit)

                        if architecture == "x64" and (is_64bit or is_generic):
                            if download_link.endswith(".zip"):
                                versions.append(version_name)
                                links[version_name] = full_link

                        elif architecture == "x86" and (is_32bit or is_generic):
                            if download_link.endswith(".zip"):
                                versions.append(version_name)
                                links[version_name] = full_link

                    elif platform == "darwin":
                        if ("darwin" in download_link or "macos" in download_link) and architecture in download_link and download_link.endswith(".dmg"):
                            versions.append(version_name)
                            links[version_name] = full_link

                    elif platform == "linux":
                        if "linux" in download_link and (download_link.endswith(".tar.xz") or download_link.endswith(".tar.gz")):
                            versions.append(version_name)
                            links[version_name] = full_link

            return versions, links
        except Exception as e:
            return [], {}


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

            if not versions:
                messagebox.showerror("Error", "No versions found.")
                return

            self.queue.put(('UPDATE_TREEVIEW', versions, links))
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
                    self.tree.delete(*self.tree.get_children())
                    for version in versions:
                        self.tree.insert("", "end", values=(version,))
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
