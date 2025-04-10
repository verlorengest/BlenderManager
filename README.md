# Blender Manager

![bmanager1](https://github.com/user-attachments/assets/8f9f6104-29c1-405b-b0f4-9516470f7231)


# Purpose

Blender Manager is an open-source tool for keep your Blender updated, organized and clean.


---

<details>
<summary>📋 <strong>Screenshots</strong></summary>

 ![1](https://github.com/user-attachments/assets/97cfd485-9be2-42ab-ad28-adf1b9282437)
  
![1 5](https://github.com/user-attachments/assets/f8d9634f-9d74-4317-9b28-c7606caca572)

![2](https://github.com/user-attachments/assets/f507a55a-55c9-48ed-9df9-3267f454ea41)

![3](https://github.com/user-attachments/assets/fd72d7ef-4dd0-4d69-8edf-70231bd736f2)

![4](https://github.com/user-attachments/assets/8d856750-9358-4f2b-9ed4-d9d81e0c687e)

![5](https://github.com/user-attachments/assets/7325f458-e405-41d5-a225-7df15ff6b1f1)

![6](https://github.com/user-attachments/assets/e388930a-c6df-4d6e-977b-c1509e2e734f)

![7](https://github.com/user-attachments/assets/8eb8e308-550b-490f-8195-4fc44250c4f0)

![8](https://github.com/user-attachments/assets/918379e2-f83b-44d0-bcb8-aa92d44fa13c)

![9](https://github.com/user-attachments/assets/d2133532-b858-41e9-8471-1fafbf89131f)

![10](https://github.com/user-attachments/assets/959458f4-b859-49f9-aeda-740bf227306a)

Selected Font: SimHei



</details>

<details>
<summary>📋 <strong>Core Features</strong></summary>


## **1) Main Menu**

- **Launch Blender**: Start your main Blender version, export it, or delete it with a click.  
- **Create Project**: Create a new project with reference images, a base mesh, and custom startup settings.  
- **Check Updates**: Check for the latest Blender version and update if needed.  
- **Preferences**: Customize the Blender Manager interface theme, fonts, sizes, and transparency.  
- **General Settings**: Configure general options like addon setup, auto-updates, launch behavior, and data reset.  
- **Blender Settings**: Export, import, or transfer settings between Blender versions.  
- **Recent Projects**: View, open, or delete recently accessed projects and check time spent.  
- **Help Section**: Access documentation, contributor credits, and donation options.  
- **Version Info**: View installed versions and update if an outdated version is detected.

---

## **2) Addon Management**

- **Add Addon**: Import Blender addons from your computer.  
- **Refresh**: Update the addon list after changes.  
- **Version Selection**: Choose a Blender version to view its addons.  
- **Addon List & Right-Click**: Manage addons by deleting, duplicating, activating, deactivating, or viewing info and documentation.

---

## **3) Project Management**

- **Add Project**: Import existing Blender projects into the manager.  
- **Refresh**: Refresh the project list to reflect recent changes.  
- **Project List**: Organize, drag and drop, and manage your project hierarchy.  
- **Project Info & Right-Click**: Rename, open, move, delete, export, or view project details and previews.

---

## **4) Version Management**

- **OS & Architecture**: Select your operating system and architecture for compatibility.  
- **Get Versions**: List official stable or experimental Blender releases.  
- **Install**: Download and install selected Blender versions.  
- **Release Notes**: Read about new features and updates in each release.  
- **Installed Versions**: View, refresh, create shortcuts, or delete installed Blender versions.  
- **Buttons**: Launch, open with factory settings, or set as the main version.

---

## **5) Render Management**

- **Render List**: Display renders with file size, resolution, and modification date.  
- **Browse**: Import render files from your computer.  
- **Open**: Preview selected renders.  
- **Refresh**: Update the render list after changes.  
- **Delete**: Permanently delete selected render files from your system.  
- **Render Notes**: Add personal notes or comments to your renders.

</details>



<details>
<summary>🛠️ <strong>Installation Guide</strong></summary>

Follow these steps to install and set up Blender Manager on your system.

---

### **Step 1: Download and Extract the ZIP File**

1. **Download the Blender Manager ZIP file**  
   📥 [**Download Latest Release**](https://github.com/verlorengest/BlenderManager/releases)

2. **Extract the ZIP file** to a location of your choice:
   - Right-click the ZIP file and select **"Extract All"** or use a tool like **WinRAR** or **7-Zip**.
   - After extraction, you’ll find a folder named **"BlenderManager"**.

---

### **Step 2: Launch Blender Manager**

1. Open the **BlenderManager** folder.
2. Double-click on **`blender_manager.exe`** to start the application.
   - If a security prompt appears, click **"Run Anyway"**.
3. Install Blender by clicking Launch Blender in Main Menu
4. Select the option which suits you.
5. Note: If the Blender Manager addon doesn't appear in the Preferences or Addon Management tab, go to Settings -> Setup Addon or try installing it manually.

---


### 🎉 **You're All Set!**

Blender Manager is now installed and ready to enhance your Blender workflow. Enjoy streamlined project management and efficient tool integration!

---


# How to Run BlenderManager from Source

Follow the instructions below to clone, set up, and run **BlenderManager** from the source code. Ensure you have Python installed on your system (version 3.10 or higher is recommended).

---

## Prerequisites

1. **Python Installation**: Ensure Python 3.10+ is installed and added to your system's PATH. You can download Python from the [official Python website](https://www.python.org/downloads/).

2. **Git Installation**: Ensure Git is installed on your system. You can download Git from [here](https://git-scm.com/downloads).

---

## Steps to Run the Project

### Step 1: Clone the Repository
Use the following command to clone the BlenderManager repository to your local machine:
```bash
git clone https://github.com/verlorengest/BlenderManager.git
```

Navigate to the project directory:
```bash
cd BlenderManager
```

### Step 2: Install Dependencies
Create a virtual environment (optional but recommended):
```bash
python -m venv venv
```

Activate the virtual environment:
- **Windows**:
  ```bash
  venv\Scripts\activate
  ```
- **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### Step 3: Run BlenderManager
Run the application using the following command:
```bash
python blender_manager.py
```

---

## Additional Notes
- Ensure you have **Blender** installed or configure the application to detect an existing Blender installation. If Blender is not installed, the app will prompt you to install it.
- The application may require elevated permissions to access certain directories or system settings, depending on your operating system.
- **themes** Folder should be inside of \Lib\site-packages\ttkbootstrap
- For further assistance or issues, please open a ticket on the [GitHub Issues Page](https://github.com/verlorengest/BlenderManager/issues).

---



</details>




**⚠️ Note: This is a pre-release version.**

This version may contain bugs and issues as it is still in pre-release. Your feedback is crucial in helping us improve the application. If you encounter any problems, please don’t hesitate to open an issue and let us know!


## ❣️ Show Some Love

Blender Manager is free and open-source. If you find it helpful, consider supporting the project:

- [**Gumroad**](https://verloren.gumroad.com/l/blendermanager)  
- [**Buy Me a Coffee**](https://buymeacoffee.com/verlorengest) ☕


---
