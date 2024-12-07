import bpy
import os
import json
import math
import re

COMM_DIR = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'mngaddon')
SETTINGS_FILE = os.path.join(COMM_DIR, 'settings.json')
AUTOSAVED_PROJECTS_FILE = os.path.join(COMM_DIR, 'autosaved_projects.json')

autosave_settings = {
    "auto_save_project": False,
    "auto_save_interval": None,
    "auto_save_style": None,
    "project_name": None,
    "project_dir": None,
    "separate_counter": 1
}


def check_for_settings_file():
    """Checks for settings.json and processes it if found, then tries to load autosave settings."""
    if os.path.exists(SETTINGS_FILE):
        print(f"[Blender Manager] settings.json found at {SETTINGS_FILE}")
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print("[Blender Manager] Settings loaded:", data)
            apply_settings(data)
            print("[Blender Manager] settings.json processed.")
            os.remove(SETTINGS_FILE)  # Delete settings.json after processing
        except Exception as e:
            print(f"[Blender Manager] Error reading settings.json: {e}")
    else:
        print("[Blender Manager] No settings.json found.")

    # After attempting to process settings.json, load autosave if available
    bpy.app.timers.register(load_autosave_settings, first_interval=2.0)
    return None


def apply_settings(data):
    """Applies the settings in Blender"""
    print("[Blender Manager] Applying settings...")

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    def clear_scene():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            obj.select_set(True)
        bpy.ops.object.delete()
        bpy.ops.outliner.orphans_purge(do_recursive=True)

    clear_scene()

    project_name = data.get('project_name', None)
    project_dir = data.get('project_dir', None)

    # Attempt initial save if project_name and project_dir provided
    if project_name and project_dir:
        save_project(project_name, project_dir)
    else:
        print("[Blender Manager] Project name or directory missing, skipping initial save.")

    # Handle base mesh
    base_mesh = data.get('base_mesh', {})
    base_mesh_path = base_mesh.get('path', '')
    if base_mesh_path and os.path.exists(base_mesh_path):
        print(f"[Blender Manager] Importing base mesh from {base_mesh_path}")
        import_mesh(base_mesh_path)
    else:
        print(f"[Blender Manager] Base mesh not found or path is empty: {base_mesh_path}")

    # Handle reference images
    reference_images = data.get('reference_images', {})
    add_reference_images(reference_images)

    # Handle light and camera
    if data.get('add_light', False):
        add_light()

    if data.get('add_camera', False):
        add_camera()

    # Handle autosave
    auto_save_project_flag = data.get('auto_save_project', False)
    auto_save_interval = data.get('auto_save_interval', None)
    auto_save_style = data.get('auto_save_style', None)

    if auto_save_project_flag and project_name and project_dir and auto_save_interval and auto_save_style:
        setup_autosave(project_name, project_dir, auto_save_interval, auto_save_style)
    else:
        print("[Blender Manager] Autosave not started. Conditions not met.")


def save_project(name, directory):
    """Saves the project with the given name and directory after a delay"""
    save_path = os.path.join(directory, f"{name}.blend")
    os.makedirs(directory, exist_ok=True)  # Ensure the directory exists

    def delayed_save():
        print(f"[Blender Manager] Saving project as {save_path}...")
        bpy.ops.wm.save_as_mainfile(filepath=save_path)
        print(f"[Blender Manager] Project saved successfully: {save_path}")

    bpy.app.timers.register(lambda: delayed_save() or None, first_interval=1.0)


def import_mesh(mesh_path):
    """Imports a mesh file into the scene"""
    ext = os.path.splitext(mesh_path)[1].lower()
    if ext == '.obj':
        bpy.ops.import_scene.obj(filepath=mesh_path)
    elif ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=mesh_path)
    elif ext == '.stl':
        bpy.ops.import_mesh.stl(filepath=mesh_path)
    else:
        print(f"[Blender Manager] Unsupported mesh format: {ext}")


def add_reference_images(images):
    """Adds reference images to the scene"""
    for position, image_path in images.items():
        if os.path.exists(image_path):
            print(f"[Blender Manager] Adding reference image for {position} from {image_path}")
            create_background_image(image_path, position)
        else:
            print(f"[Blender Manager] Image not found: {image_path}")


def create_background_image(image_path, position):
    """Creates a background image aligned to the specified view."""
    bpy.ops.object.empty_add(type='IMAGE', align='WORLD', location=(0, 0, 0))
    empty = bpy.context.active_object
    empty.name = f"Ref_{position.capitalize()}"

    try:
        img = bpy.data.images.load(filepath=image_path)
        empty.data = img
        print(f"[Blender Manager] Image loaded successfully: {image_path}")
    except Exception as e:
        print(f"[Blender Manager] Error loading image {image_path}: {e}")
        bpy.data.objects.remove(empty, do_unlink=True)
        return

    empty.scale = (5, 5, 5)
    empty.empty_display_type = 'IMAGE'

    if position == 'front':
        empty.rotation_euler = (math.radians(90), 0, 0)
    elif position == 'back':
        empty.rotation_euler = (math.radians(90), 0, math.radians(180))
    elif position == 'right':
        empty.rotation_euler = (math.radians(90), 0, math.radians(-90))
    elif position == 'left':
        empty.rotation_euler = (math.radians(90), 0, math.radians(90))
    elif position == 'top':
        empty.rotation_euler = (0, 0, 0)
    elif position == 'bottom':
        empty.rotation_euler = (math.radians(180), 0, 0)
    else:
        print(f"[Blender Manager] Unknown position: {position}. Image placed without rotation.")

    for obj in bpy.context.scene.objects:
        if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
            obj.empty_image_side = 'FRONT'
            print(f"Side settings changed to Front for {obj.name}.")


def add_light():
    """Adds a light to the scene"""
    bpy.ops.object.light_add(type='POINT', align='WORLD', location=(5, 5, 5))
    light = bpy.context.active_object
    light.data.energy = 1000
    print("[Blender Manager] Added light to the scene.")


def add_camera():
    """Adds a camera to the scene"""
    bpy.ops.object.camera_add(align='VIEW', location=(0, -10, 0), rotation=(1.5708, 0, 0))
    camera = bpy.context.active_object
    bpy.context.scene.camera = camera
    print("[Blender Manager] Added camera to the scene.")


def setup_autosave(project_name, project_dir, interval, style):
    """Setup autosave for the given project."""
    autosave_settings["auto_save_project"] = True
    autosave_settings["auto_save_interval"] = interval
    autosave_settings["auto_save_style"] = style
    autosave_settings["project_name"] = project_name
    autosave_settings["project_dir"] = project_dir
    autosave_settings["separate_counter"] = 1

    # Write settings to AUTOSAVED_PROJECTS_FILE
    write_autosaved_project(project_name, project_dir, interval, style)

    # Start autosave timer
    start_autosave_timer()


def write_autosaved_project(project_name, project_dir, interval, style):
    """Write current autosave settings to AUTOSAVED_PROJECTS_FILE keyed by project_name."""
    data = {}
    if os.path.exists(AUTOSAVED_PROJECTS_FILE):
        try:
            with open(AUTOSAVED_PROJECTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}

    if "projects" not in data:
        data["projects"] = {}

    data["projects"][project_name] = {
        "auto_save_project": True,
        "auto_save_interval": interval,
        "auto_save_style": style,
        "project_name": project_name,
        "project_dir": project_dir
    }

    with open(AUTOSAVED_PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("[Blender Manager] Autosave settings written to autosaved_projects.json.")


def extract_base_project_name(filename):
    """
    Extracts the base project name from a given filename.
    If filename is like 'NewProject_4.blend', it should return 'NewProject'.
    If filename is 'NewProject.blend', it returns 'NewProject'.
    """
    name, ext = os.path.splitext(filename)
    # Remove trailing underscores and digits
    # We'll match a pattern: (BaseName)_(Number)?
    # If there's a trailing underscore + digits, remove them.
    match = re.match(r'^(.*?)(_\d+)?$', name)
    if match:
        return match.group(1)
    return name


def load_autosave_settings():
    """Load autosave settings from AUTOSAVED_PROJECTS_FILE if current project (or its variants) matches one with autosave enabled."""
    current_path = bpy.data.filepath
    if not current_path:
        # No project loaded yet
        return None

    current_filename = os.path.basename(current_path)
    guessed_project_name = extract_base_project_name(current_filename)

    if os.path.exists(AUTOSAVED_PROJECTS_FILE):
        try:
            with open(AUTOSAVED_PROJECTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {}

        projects = data.get("projects", {})
        if guessed_project_name in projects:
            project_data = projects[guessed_project_name]
            if (project_data.get("auto_save_project", False) and
                    project_data.get("project_name") and
                    project_data.get("project_dir") and
                    project_data.get("auto_save_interval") and
                    project_data.get("auto_save_style")):
                # Setup autosave again with these settings
                autosave_settings["auto_save_project"] = True
                autosave_settings["auto_save_interval"] = project_data["auto_save_interval"]
                autosave_settings["auto_save_style"] = project_data["auto_save_style"]
                autosave_settings["project_name"] = project_data["project_name"]
                autosave_settings["project_dir"] = project_data["project_dir"]
                autosave_settings["separate_counter"] = 1  # reset counter or could load from file if needed
                print("[Blender Manager] Resuming autosave from stored settings for project:", guessed_project_name)
                start_autosave_timer()
            else:
                print("[Blender Manager] Autosave settings found but incomplete or disabled for:", guessed_project_name)
        else:
            print("[Blender Manager] No autosave settings found for:", guessed_project_name)
    return None


def start_autosave_timer():
    """Start the autosave timer based on the autosave_settings."""
    interval = autosave_settings["auto_save_interval"]
    if interval is None:
        return

    def autosave():
        if not autosave_settings["auto_save_project"]:
            return None

        project_name = autosave_settings["project_name"]
        project_dir = autosave_settings["project_dir"]
        style = autosave_settings["auto_save_style"]
        base_path = os.path.join(project_dir, f"{project_name}.blend")

        if style == "overwrite":
            print("[Blender Manager] Autosaving (overwrite)...")
            bpy.ops.wm.save_as_mainfile(filepath=base_path)
        elif style == "separate":
            counter = autosave_settings["separate_counter"]
            save_path = os.path.join(project_dir, f"{project_name}_{counter}.blend")
            print(f"[Blender Manager] Autosaving (separate) to {save_path}...")
            bpy.ops.wm.save_as_mainfile(filepath=save_path)
            autosave_settings["separate_counter"] += 1

        # Schedule the next autosave
        return interval

    bpy.app.timers.register(autosave, first_interval=autosave_settings["auto_save_interval"])


def register():
    bpy.app.timers.register(check_for_settings_file)


if __name__ == "__main__":
    register()
