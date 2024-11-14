bl_info = {
    "name": "Blender Manager",
    "description": "Essential Blender addon for Blender Manager.",
    "author": "verlorengest",
    "version": (1, 0, 10),
    "blender": (4, 2, 0),  # Minimum Blender version required
    "location": "File > External Tools > Blender Manager",
    "category": "System",
}

import bpy
import json
import os
import time
from bpy.app.handlers import persistent
from . import blender_manager_operator

COMM_DIR = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'mngaddon')
PROJECT_TIME_FILE = os.path.join(COMM_DIR, 'project_time.json')
SETTINGS_FILE = os.path.join(COMM_DIR, 'settings.json')

project_open_time = None
project_path = None

def load_project_time_data():
    """Load project time data from JSON file."""
    if os.path.exists(PROJECT_TIME_FILE):
        try:
            with open(PROJECT_TIME_FILE, 'r') as file:
                data = json.load(file)
                print("[Blender Manager] Loaded project time data:", data)
                return data
        except json.JSONDecodeError:
            print("[Blender Manager] Invalid JSON format in project_time.json.")
    return {}

def save_project_time_data(data):
    """Save project time data to JSON file with error checking."""
    os.makedirs(COMM_DIR, exist_ok=True)
    try:
        with open(PROJECT_TIME_FILE, 'w') as file:
            json.dump(data, file, indent=4)
            print("[Blender Manager] Successfully saved project time data:", data)
    except Exception as e:
        print(f"[Blender Manager] Error saving project time data: {e}")

@persistent
def on_save_post_handler(dummy):
    """Handler called after saving the blend file."""
    global project_open_time, project_path
    print("[Blender Manager] Save event triggered.")
    try:
        filepath = getattr(bpy.data, 'filepath', None)
        if filepath:
            current_time = time.time()  
            if project_path == filepath and project_open_time is not None:
                elapsed_time = current_time - project_open_time 
                print(f"[Blender Manager] Elapsed time for {project_path}: {elapsed_time:.2f} seconds.")
                
                project_time_data = load_project_time_data()
                
                if project_path in project_time_data:
                    project_time_data[project_path] += elapsed_time
                else:
                    project_time_data[project_path] = elapsed_time

                save_project_time_data(project_time_data)
                
                project_open_time = current_time
            elif project_path is None:
                elapsed_time = current_time - project_open_time  
                print(f"[Blender Manager] First save. Elapsed time for {filepath}: {elapsed_time:.2f} seconds.")
                
                project_time_data = load_project_time_data()
                
                project_time_data[filepath] = elapsed_time
                
                save_project_time_data(project_time_data)
                
                project_path = filepath
                project_open_time = current_time
            else:
                elapsed_time = current_time - project_open_time  
                print(f"[Blender Manager] Elapsed time for {project_path}: {elapsed_time:.2f} seconds.")

                project_time_data = load_project_time_data()

                if project_path in project_time_data:
                    project_time_data[project_path] += elapsed_time
                else:
                    project_time_data[project_path] = elapsed_time

                save_project_time_data(project_time_data)

                project_path = filepath
                project_open_time = current_time
                print(f"[Blender Manager] Project switched to: {project_path} at {time.ctime(project_open_time)}")
            
            if project_path == filepath:
                project_open_time = current_time
        else:
            print("[Blender Manager] No project path; not saving time.")
    except AttributeError:
        print("[Blender Manager] bpy.data.filepath not accessible in on_save_post_handler")

@persistent
def on_load_post_handler(dummy):
    """Handler called after loading a blend file or creating a new one."""
    global project_open_time, project_path
    print("[Blender Manager] Load event triggered.")
    try:
        filepath = getattr(bpy.data, 'filepath', None)
        current_time = time.time()
        
        if filepath:
            if project_path and project_open_time is not None:
                elapsed_time = current_time - project_open_time
                print(f"[Blender Manager] Elapsed time for {project_path}: {elapsed_time:.2f} seconds.")
                
                project_time_data = load_project_time_data()
                
                if project_path in project_time_data:
                    project_time_data[project_path] += elapsed_time
                else:
                    project_time_data[project_path] = elapsed_time

                save_project_time_data(project_time_data)
            
            project_path = filepath
            project_open_time = current_time
            print(f"[Blender Manager] Project loaded: {project_path} at {time.ctime(project_open_time)}")
        else:
            if project_path and project_open_time is not None:
                elapsed_time = current_time - project_open_time
                print(f"[Blender Manager] Elapsed time for {project_path}: {elapsed_time:.2f} seconds.")
                
                project_time_data = load_project_time_data()
                
                if project_path in project_time_data:
                    project_time_data[project_path] += elapsed_time
                else:
                    project_time_data[project_path] = elapsed_time

                save_project_time_data(project_time_data)
            
            project_path = None
            project_open_time = current_time
            print(f"[Blender Manager] New project created at {time.ctime(project_open_time)}. Timer reset.")
    except AttributeError:
        print("[Blender Manager] bpy.data.filepath not accessible in on_load_post_handler")

@persistent
def on_quit_pre_handler(dummy):
    """Handler called before Blender quits."""
    global project_open_time, project_path
    print("[Blender Manager] Blender is quitting.")
    try:
        filepath = getattr(bpy.data, 'filepath', None)
        if filepath and project_open_time is not None:
            current_time = time.time()
            elapsed_time = current_time - project_open_time
            print(f"[Blender Manager] Elapsed time for {project_path}: {elapsed_time:.2f} seconds.")
            
            project_time_data = load_project_time_data()
            
            if project_path in project_time_data:
                project_time_data[project_path] += elapsed_time
            else:
                project_time_data[project_path] = elapsed_time

            save_project_time_data(project_time_data)
        else:
            print("[Blender Manager] No project path or open time; not saving time.")
    except AttributeError:
        print("[Blender Manager] bpy.data.filepath not accessible in on_quit_pre_handler")

def register():
    """Register the addon and its handlers."""
    os.makedirs(COMM_DIR, exist_ok=True)
    print(f"[Blender Manager] Directory ensured at: {COMM_DIR}")

    global project_open_time, project_path
    filepath = getattr(bpy.data, 'filepath', None)
    if filepath:
        project_path = filepath
        project_open_time = time.time()
        print(f"[Blender Manager] Existing project detected: {project_path} at {time.ctime(project_open_time)}")
    else:
        project_path = None
        project_open_time = time.time()
        print(f"[Blender Manager] No project open at start. Timer will start when a project is created or loaded.")

    bpy.app.handlers.save_post.append(on_save_post_handler)
    bpy.app.handlers.load_post.append(on_load_post_handler)

    if hasattr(bpy.app.handlers, 'quit_pre'):
        bpy.app.handlers.quit_pre.append(on_quit_pre_handler)
        print("[Blender Manager] Quit pre handler appended.")
    else:
        print("[Blender Manager] 'quit_pre' handler not found. Quit event may not be tracked.")

    blender_manager_operator.register()

    print("[Blender Manager] Blender Manager Plugin registered.")

def unregister():
    """Unregister the addon and remove its handlers."""
    if on_save_post_handler in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(on_save_post_handler)
        print("[Blender Manager] Removed save_post handler.")
    if on_load_post_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_load_post_handler)
        print("[Blender Manager] Removed load_post handler.")
    if hasattr(bpy.app.handlers, 'quit_pre') and on_quit_pre_handler in bpy.app.handlers.quit_pre:
        bpy.app.handlers.quit_pre.remove(on_quit_pre_handler)
        print("[Blender Manager] Removed quit_pre handler.")

    blender_manager_operator.unregister()

    print("[Blender Manager] Blender Manager Plugin unregistered.")
    


if __name__ == "__main__":
    register()
