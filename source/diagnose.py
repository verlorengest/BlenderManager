# -*- coding: utf-8 -*-
"""Report why Blender Manager might refuse to open. Read-only, changes nothing.

Run from the source folder:  python diagnose.py
"""
import importlib.util
import json
import os
import sys

LINE = "-" * 62


def section(title):
    print()
    print(LINE)
    print(title)
    print(LINE)


def check_python():
    section("1. Python")
    print(f"  executable : {sys.executable}")
    print(f"  version    : {sys.version.split()[0]}")
    print(f"  cwd        : {os.getcwd()}")


def check_other_instances():
    """A leftover instance makes every new launch exit silently, by design."""
    section("2. Other Blender Manager instances (the usual silent-exit cause)")
    try:
        import psutil
    except ImportError:
        print("  psutil not installed, cannot check.")
        return

    here = os.path.dirname(os.path.abspath(__file__))
    current_pid = os.getpid()
    found = []

    for process in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            if process.pid == current_pid:
                continue
            name = (process.info.get("name") or "").lower()
            cmdline = process.info.get("cmdline") or []
            joined = " ".join(cmdline)

            if name in ("blender_manager.exe",):
                found.append((process.pid, name, joined[:110]))
                continue

            # Only a Python interpreter actually *running* the script counts. Editors
            # and tools that merely have the file open are not instances of the app.
            if name not in ("python.exe", "pythonw.exe", "python", "pythonw"):
                continue
            if any(os.path.basename(arg).lower() == "blender_manager.py" for arg in cmdline):
                found.append((process.pid, name, joined[:110]))
        except Exception:
            continue

    if found:
        print(f"  FOUND {len(found)} leftover instance(s). This is why nothing opens:")
        for pid, name, cmd in found:
            print(f"    pid {pid:<8} {name:<20} {cmd}")
        print()
        print("  Close them with:")
        for pid, _, _ in found:
            print(f"    taskkill /F /PID {pid}")
    else:
        print("  None found.")
    print(f"  (source folder: {here})")


def check_window():
    """The app exits on startup if any window is titled exactly 'Blender Manager'."""
    section("3. Window titled 'Blender Manager'")
    if os.name != "nt":
        print("  Not Windows, skipped.")
        return
    import ctypes

    titles = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
    def callback(hwnd, _lparam):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buffer = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
            if buffer.value.lower() == "blender manager":
                visible = bool(ctypes.windll.user32.IsWindowVisible(hwnd))
                titles.append((hwnd, visible))
        return True

    ctypes.windll.user32.EnumWindows(callback, None)

    if titles:
        print(f"  FOUND {len(titles)} matching window(s). The app will exit on startup:")
        for hwnd, visible in titles:
            print(f"    hwnd {hwnd}  visible={visible}")
        print("  Kill the owning process (see section 2) and try again.")
    else:
        print("  None found.")


def check_ttkbootstrap():
    section("4. ttkbootstrap")
    spec = importlib.util.find_spec("ttkbootstrap")
    if spec is None or not spec.origin:
        print("  NOT INSTALLED.")
        return

    package_dir = os.path.dirname(spec.origin)
    print(f"  location : {package_dir}")

    dialogs = os.path.join(package_dir, "dialogs", "dialogs.py")
    if os.path.isfile(dialogs):
        with open(dialogs, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        patched = "# Some system locales produce an LC_TIME string LC_ALL rejects." in content
        print(f"  locale fix applied : {patched}")
        try:
            compile(content, dialogs, "exec")
            print("  dialogs.py syntax  : OK")
        except SyntaxError as e:
            print(f"  dialogs.py syntax  : BROKEN -> {e}")
            print("  Restore it with the backup: dialogs.py.orig")

    themes = os.path.join(package_dir, "themes", "standard.py")
    if os.path.isfile(themes):
        with open(themes, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        print(f"  custom themes present : {'blender' in content and 'plasticity' in content}")

    try:
        import ttkbootstrap
        print(f"  import   : OK (version {getattr(ttkbootstrap, '__version__', 'unknown')})")
    except Exception as e:
        print(f"  import   : FAILED -> {type(e).__name__}: {e}")


def check_config():
    section("5. config.json")
    path = os.path.join(os.path.expanduser("~"), ".BlenderManager", "config.json")
    if not os.path.isfile(path):
        print(f"  Not created yet: {path}")
        return
    print(f"  {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"  UNREADABLE -> {e}")
        return
    for key in ("selected_theme", "ui_scale", "window_width", "window_height",
                "run_in_background", "show_logs"):
        print(f"    {key:<20} = {config.get(key, '<missing>')}")


def check_screen():
    section("6. Screen")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        print(f"  reported size : {root.winfo_screenwidth()}x{root.winfo_screenheight()}")
        print(f"  tk scaling    : {root.tk.call('tk', 'scaling')}")
        root.destroy()
    except Exception as e:
        print(f"  FAILED -> {type(e).__name__}: {e}")


if __name__ == "__main__":
    print("Blender Manager - startup diagnostics")
    check_python()
    check_other_instances()
    check_window()
    check_ttkbootstrap()
    check_config()
    check_screen()
    print()
    print(LINE)
    print("Done. Paste this whole output back.")
