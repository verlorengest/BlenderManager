# -*- coding: utf-8 -*-
"""Fix ttkbootstrap 1.x's import-time locale crash inside the installed package.

ttkbootstrap/dialogs/dialogs.py executes this at class-body level, so it runs on
plain `import ttkbootstrap`:

    locale.setlocale(locale.LC_ALL, locale.setlocale(locale.LC_TIME, ""))

On systems where LC_ALL refuses the string LC_TIME returns (Turkish Windows among
others) this raises locale.Error and the whole package fails to import. That breaks
PyInstaller's collection hooks and any tool that imports ttkbootstrap.

This rewrites that single statement into a guarded one. It is idempotent and backs
the original file up once as dialogs.py.orig.
"""
import importlib.util
import os
import shutil
import sys

TARGET = 'locale.setlocale(locale.LC_ALL, locale.setlocale(locale.LC_TIME, ""))'
MARKER = "# Some system locales produce an LC_TIME string LC_ALL rejects."


def find_dialogs_module():
    """Locate ttkbootstrap/dialogs/dialogs.py without importing the package."""
    spec = importlib.util.find_spec("ttkbootstrap")
    if spec is None or not spec.origin:
        return None
    return os.path.join(os.path.dirname(spec.origin), "dialogs", "dialogs.py")


def main():
    path = find_dialogs_module()
    if path is None:
        print("ttkbootstrap is not installed. Run: pip install -r requirements.txt")
        return 1
    if not os.path.isfile(path):
        print(f"Not found: {path}")
        print("Nothing to patch; this ttkbootstrap version may not need it.")
        return 0

    with open(path, "r", encoding="utf-8", newline="") as f:
        lines = f.readlines()

    if any(MARKER in line for line in lines):
        print("Already patched.")
        return 0

    index = None
    for i, line in enumerate(lines):
        if line.strip() == TARGET:
            index = i
            break

    if index is None:
        print("Already patched (or this version does not contain the faulty call).")
        return 0

    line = lines[index]
    indent = line[:len(line) - len(line.lstrip())]
    eol = "\r\n" if line.endswith("\r\n") else "\n"

    replacement = [
        f"{indent}try:{eol}",
        f"{indent}    {TARGET}{eol}",
        f"{indent}except locale.Error:{eol}",
        f"{indent}    {MARKER}{eol}",
        f"{indent}    pass{eol}",
    ]
    lines[index:index + 1] = replacement

    backup = path + ".orig"
    try:
        if not os.path.exists(backup):
            shutil.copy2(path, backup)
            print(f"  backed up -> {os.path.basename(backup)}")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.writelines(lines)
    except OSError as e:
        print(f"  FAILED to write {path}: {e}")
        print("  Hint: run this from an elevated prompt, or use a virtual environment.")
        return 1

    print(f"Patched the locale call in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
