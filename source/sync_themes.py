# -*- coding: utf-8 -*-
"""Install Blender Manager's extra ttkbootstrap themes into the installed ttkbootstrap package.

The app offers themes (blender, plasticity, pure_black, neon_glow, ...) that stock
ttkbootstrap does not ship. They live in source/themes and have to replace the
package's own theme modules, otherwise those names are missing from
Style.theme_names() both when running from source and inside a frozen build.

Each replaced file is backed up once as <name>.orig next to the original, so a
`pip install --force-reinstall ttkbootstrap` is never needed to get back to stock.
"""
import importlib.util
import os
import shutil
import sys


def main():
    # find_spec locates the package without executing it, so a broken import-time
    # side effect inside ttkbootstrap cannot take this script down with it.
    spec = importlib.util.find_spec("ttkbootstrap")
    if spec is None or not spec.origin:
        print("ttkbootstrap is not installed. Run: pip install -r requirements.txt")
        return 1

    source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "themes")
    target_dir = os.path.join(os.path.dirname(spec.origin), "themes")

    if not os.path.isdir(source_dir):
        print(f"No themes folder next to this script: {source_dir}")
        return 1
    if not os.path.isdir(target_dir):
        print(f"ttkbootstrap themes folder not found: {target_dir}")
        return 1

    installed = 0
    for name in sorted(os.listdir(source_dir)):
        if not name.endswith(".py"):
            continue

        source_file = os.path.join(source_dir, name)
        target_file = os.path.join(target_dir, name)
        backup_file = target_file + ".orig"

        try:
            if os.path.exists(target_file) and not os.path.exists(backup_file):
                shutil.copy2(target_file, backup_file)
                print(f"  backed up {name} -> {name}.orig")
            shutil.copy2(source_file, target_file)
            print(f"  installed {name}")
            installed += 1
        except OSError as e:
            print(f"  FAILED {name}: {e}")
            print("  Hint: run this from an elevated prompt, or use a virtual environment.")
            return 1

    # Stale bytecode would keep shadowing the modules that were just replaced.
    cache_dir = os.path.join(target_dir, "__pycache__")
    if os.path.isdir(cache_dir):
        shutil.rmtree(cache_dir, ignore_errors=True)

    print(f"Synced {installed} theme module(s) into {target_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
