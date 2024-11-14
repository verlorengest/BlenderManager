import bpy
import os
import json
import math
import time
import uuid

COMM_DIR = os.path.join(os.path.expanduser("~"), '.BlenderManager', 'mngaddon')
SETTINGS_FILE = os.path.join(COMM_DIR, 'settings.json')

def check_for_settings_file():
    """Checks for settings.json and processes it if found"""
    if os.path.exists(SETTINGS_FILE):
        print(f"[Blender Manager] settings.json found at {SETTINGS_FILE}")
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
            print("[Blender Manager] Settings loaded:", data)
            apply_settings(data)
            print("[Blender Manager] settings.json processed.")
        except Exception as e:
            print(f"[Blender Manager] Error reading settings.json: {e}")
        return None
    else:
        
        return 1.0  

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


    # Add base mesh if provided
    base_mesh = data.get('base_mesh', {})
    base_mesh_path = base_mesh.get('path', '')
    if base_mesh_path and os.path.exists(base_mesh_path):
        print(f"[Blender Manager] Importing base mesh from {base_mesh_path}")
        import_mesh(base_mesh_path)
    else:
        print(f"[Blender Manager] Base mesh not found or path is empty: {base_mesh_path}")

    reference_images = data.get('reference_images', {})
    add_reference_images(reference_images)

    if data.get('add_light', False):
        add_light()

    if data.get('add_camera', False):
        add_camera()
        
    if data.get('activate_autosave', False):
        activate_autosave(data)

def activate_autosave(data):
    """Activates the AutoSaver feature based on JSON settings."""
    print("[Blender Manager] Activating AutoSaver...")

    interval = data.get('autosave_interval', 300)
    bpy.context.scene.auto_saver_interval = interval

    directory = data.get('autosave_directory', "")
    if directory:
        bpy.context.scene.auto_saver_directory = directory

    unique_names = data.get('autosave_unique_names', False)
    bpy.context.scene.auto_saver_unique_names = unique_names

    if not bpy.context.scene.auto_saver_running:
        try:
            bpy.ops.wm.auto_saver_operator()
            print(f"[Blender Manager] AutoSaver started with interval: {interval} seconds, "
                  f"directory: {directory}, unique names: {unique_names}")
        except Exception as e:
            print(f"[Blender Manager] Failed to start AutoSaver: {e}")





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

def register():
    bpy.utils.register_class(AutoSaverOperator)
    bpy.types.Scene.auto_saver_interval = bpy.props.IntProperty(
        name="Interval (seconds)",
        description="Time interval between autosaves",
        default=300,
        min=10,
    )
    bpy.types.Scene.auto_saver_running = bpy.props.BoolProperty(
        name="AutoSaver Running",
        description="Indicates if AutoSaver is running",
        default=False,
    )
    bpy.types.Scene.auto_saver_directory = bpy.props.StringProperty(
        name="Autosave Directory",
        description="Directory where to save autosaves if the file hasn't been saved yet",
        subtype='DIR_PATH',
        default=""
    )
    bpy.types.Scene.auto_saver_unique_names = bpy.props.BoolProperty(
        name="Save as Different Files",
        description="Save as different files each time",
        default=False
    )
    bpy.app.timers.register(check_for_settings_file)


def unregister():
    bpy.utils.unregister_class(AutoSaverOperator)
    del bpy.types.Scene.auto_saver_interval
    del bpy.types.Scene.auto_saver_running
    del bpy.types.Scene.auto_saver_directory
    del bpy.types.Scene.auto_saver_unique_names








class AutoSaverOperator(bpy.types.Operator):
    """Operator that autosaves the file at set intervals"""
    bl_idname = "wm.auto_saver_operator"
    bl_label = "Start AutoSaver"

    _timer = None
    _last_save_time = 0

    def modal(self, context, event):
        if not context.scene.auto_saver_running:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            current_time = time.time()
            interval = context.scene.auto_saver_interval

            if current_time - self._last_save_time >= interval:
                directory = context.scene.auto_saver_directory
                unique_names = context.scene.auto_saver_unique_names

                if bpy.data.is_saved:
                    if unique_names:
                        file_path = bpy.data.filepath
                        dir_name = os.path.dirname(file_path)
                        base_name = os.path.basename(file_path)
                        name, ext = os.path.splitext(base_name)
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        new_name = f"{name}_{timestamp}{ext}"
                        new_path = os.path.join(dir_name, new_name)
                        bpy.ops.wm.save_as_mainfile(filepath=new_path, copy=True)
                    else:
                        bpy.ops.wm.save_mainfile()
                    self._last_save_time = current_time
                    print("[Blender Manager] File autosaved.")

                else:
                    if directory:
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        random_name = f"autosave_{uuid.uuid4().hex[:8]}.blend"
                        save_path = os.path.join(directory, random_name)
                        bpy.ops.wm.save_as_mainfile(filepath=save_path, copy=False)
                        self._last_save_time = current_time
                        print(f"[Blender Manager] File autosaved as {random_name}.")
            return {'PASS_THROUGH'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        context.scene.auto_saver_running = True
        wm = context.window_manager
        self._timer = wm.event_timer_add(1.0, window=context.window)
        self._last_save_time = time.time()
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        context.scene.auto_saver_running = False
        print("[Blender Manager] AutoSaver stopped.")



















if __name__ == "__main__":
    register()
