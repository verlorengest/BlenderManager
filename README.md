# Blender Manager

![bmanager1](https://github.com/user-attachments/assets/8f9f6104-29c1-405b-b0f4-9516470f7231)


**Blender Manager includes several powerful features designed to streamline project setup and tracking, all without the need to open Blender initially. Here’s a closer look at some of its standout functionalities:**


<details>
<summary>📋 <strong>Screenshots</strong></summary>

   
![900x](https://github.com/user-attachments/assets/899f9f7a-251e-4e2e-90fd-59d319db9449)

Selected Font: SimHei


**the following are old version of gui**

![Screenshot 1](https://github.com/user-attachments/assets/2b12f8dd-0f75-4cbc-9e41-2e06c2e4d84f)

![Screenshot 2](https://github.com/user-attachments/assets/858fc794-03aa-4eb5-ad2a-1b7cf37e190d)

![Screenshot 3](https://github.com/user-attachments/assets/de9b55eb-8168-42fa-8e6b-e411814e5df4)

![Screenshot 4](https://github.com/user-attachments/assets/f7a2702f-5fc5-4342-9177-0732b2542ecf)

![Screenshot 5](https://github.com/user-attachments/assets/ac5dc13a-f6f0-4ef5-be29-7ee10942ed65)

![Screenshot 6](https://github.com/user-attachments/assets/6044471e-f884-4889-8bbc-8685516d2387)

![Screenshot 7](https://github.com/user-attachments/assets/3cbeb936-7237-4627-a2f5-aca87b28ba60)

![Screenshot 8](https://github.com/user-attachments/assets/dd77a7f1-e258-4784-9ae8-8adb5716a658)

![Screenshot 9](https://github.com/user-attachments/assets/26b5529a-b66a-4f06-bdf6-0dfd153ab3ae)

</details>

<details>
<summary>📋 <strong>Features</strong></summary>

### 1. **Project Time Tracking**
Blender Manager automatically tracks the time spent on each project, giving users a clear view of their work hours. This feature is integrated directly into the **Recent Projects** section, displaying the total time spent on a project. Users can monitor their productivity and get a detailed breakdown of working hours for each project, making it an excellent tool for both personal time management and client billing.

### 2. **Recent Projects Overview**
The **Recent Projects** feature provides a convenient list of previously opened Blender files, showing key details such as the project name, last opened date, and file path. Users can easily access their most recent work without manually searching through directories, enhancing workflow efficiency by allowing them to quickly resume their work from where they left off.

### 3. **Comprehensive Project Creation**
Blender Manager offers an advanced **Create Project** tool that allows users to set up their project environment without launching Blender. This includes:

- **Reference Images Setup**: Import reference images for multiple views (front, back, left, right, top, and bottom) to ensure all necessary reference materials are organized and ready for modeling.
- **Base Mesh Selection**: Choose a base mesh from a predefined list or add your own custom base meshes for a quick start with pre-configured models.
- **Scene Configuration**: Predefine scene elements such as adding a camera and lights, and configure autosave options for immediate work upon opening the project in Blender.

### 4. **Auto Update**
Includes an **Auto Update** feature, ensuring both the Blender application and Blender Manager itself are always up to date. The app automatically checks for the latest releases and offers a simple one-click update option.

### 5. **Customizable GUI**
The user interface is highly customizable. Users can choose from a variety of themes, adjust font sizes, and control the transparency of the app, allowing for a personalized and comfortable experience.

### 6. **Seamless Version Control**
Manage multiple Blender versions effortlessly. Install any version you need, switch between them, or set a specific version as the **Main Launch Version**.

### 7. **Multi-Platform Support (In Progress)**
Currently optimized for Windows, with plans to expand full compatibility to macOS and Linux in future releases.

### 8. **Addon Management**
Provides an intuitive **Addon Management** tab to handle Blender addons efficiently. Key features include:

- **Addon List Display**
- **Addon Installation and Removal**
- **Compatibility Check**
- **Search Functionality**
- **File Path Access**

### 9. **Project Management**
Offers comprehensive tools for organizing and handling Blender projects:

- **Project List Overview**
- **Quick Actions**
- **File Path Navigation**
- **Search Bar**

### 10. **Render Management**
Makes it easy to handle rendered files directly within the app:

- **Render List**
- **Preview Capability**
- **File Operations**
- **Render Notes**

### 11. **Logs Tab**
Provides real-time feedback and diagnostic information:

- **Initialization Feedback**
- **Process Tracking**
- **Error and Warning Reporting**
- **Success Messages**

### 12. **Settings Tab**
Gives users full control over the application's appearance and behavior:

- **Appearance Settings**: Themes, font customization, transparency control.
- **General Settings**: Auto update, launch on startup, run in background, addon setup, change launch folder, download chunk size multiplier.
- **Reset and Maintenance Options**: Reset all data, delete Blender versions, reset to defaults.

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
- For further assistance or issues, please open a ticket on the [GitHub Issues Page](https://github.com/verlorengest/BlenderManager/issues).

---



</details>




**⚠️ Note: This is a pre-release version.**

This version may contain bugs and issues as it is still in pre-release. Your feedback is crucial in helping us improve the application. If you encounter any problems, please don’t hesitate to open an issue and let us know!


## ❣️ Show Some Love

Blender Manager is free and open-source. If you find it helpful, consider supporting the project:

- [**Donate on Gumroad**](https://verlorengest.gumroad.com/l/blendermanager)  
- [**Buy Me a Coffee**](https://buymeacoffee.com/verlorengest) ☕


---
