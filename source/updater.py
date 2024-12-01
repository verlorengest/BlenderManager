# -*- coding: utf-8 -*-
import argparse
import os
import zipfile
import shutil
import platform
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description='Updater script for BlenderManager.')
    parser.add_argument('--zip-path', required=True, help='Path to the downloaded zip file.')

    args = parser.parse_args()
    zip_path = args.zip_path
    app_dir = os.getcwd()  
    extract_dir = os.path.join(app_dir, "blender_manager_update")


    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except zipfile.BadZipFile as e:
        print(f"Error: Failed to extract zip file {zip_path}. Error: {e}")
        sys.exit(1)

    try:
        extracted_folders = [
            name for name in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, name))
        ]

        if len(extracted_folders) != 1:
            print(f"Error: Expected one top-level folder in zip, found {len(extracted_folders)}.")
            sys.exit(1)

        top_level_folder = os.path.join(extract_dir, extracted_folders[0])

        for root, dirs, files in os.walk(top_level_folder):
            rel_path = os.path.relpath(root, top_level_folder)
            dest_dir = os.path.join(app_dir, rel_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                shutil.move(src_file, dest_file)
    except Exception as e:
        print(f"Error: Failed to move files from {top_level_folder} to {app_dir}. Error: {e}")
        sys.exit(1)

    try:
        shutil.rmtree(extract_dir)
    except Exception as e:
        print(f"Error: Failed to delete temporary directory {extract_dir}. Error: {e}")

    try:
        if os.path.exists(zip_path):
            os.remove(zip_path)
    except Exception as e:
        print(f"Error: Failed to delete zip file {zip_path}. Error: {e}")

    current_os = platform.system().lower()
    try:
        if current_os == 'windows':
            app_executable = os.path.join(app_dir, 'blender_manager.exe')
            if os.path.exists(app_executable):
                subprocess.Popen([app_executable])
            else:
                app_script = os.path.join(app_dir, 'blender_manager.py')
                subprocess.Popen(['python', app_script])
        elif current_os in ['darwin', 'linux']:
            app_script = os.path.join(app_dir, 'blender_manager.py')
            subprocess.Popen(['python3', app_script])
        else:
            print(f"Error: Unsupported operating system {current_os}.")
    except Exception as e:
        print(f"Error: Failed to restart application. Error: {e}")

if __name__ == '__main__':
    main()

