import os
import subprocess
import shutil
import tkinter as tk
from tkinter import messagebox, simpledialog
import sys

def run_command(command, cwd=None, shell=True):
    print(f"Executing: {command}")
    process = subprocess.Popen(command, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        raise Exception(f"Command failed with return code {process.returncode}: {command}")

def create_builder_ui():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    app_name = simpledialog.askstring("MIACT Builder", "Enter Application Name:", initialvalue="MIACT")
    if not app_name:
        return None, None

    version = simpledialog.askstring("MIACT Builder", "Enter Version:", initialvalue="1.0.0")
    if not version:
        return None, None

    return app_name, version

def generate_inno_script(app_name, version, output_dir):
    iss_content = f"""
[Setup]
AppName={app_name}
AppVersion={version}
DefaultDirName={{autopf}}\\{app_name}
DefaultGroupName={app_name}
OutputDir=..\\installers
OutputBaseFilename={app_name}_v{version}_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "{output_dir}\\{app_name}\*"; DestDir: "{{app}}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{app_name}"; Filename: "{{app}}\\{app_name}.exe"
Name: "{{commondesktop}}\\{app_name}"; Filename: "{{app}}\\{app_name}.exe"

[Run]
Filename: "{{app}}\\{app_name}.exe"; Description: "Launch {app_name}"; Flags: nowait postinstall skipifsilent
"""
    with open("setup_script.iss", "w") as f:
        f.write(iss_content)
    print("Inno Setup script generated: setup_script.iss")

def main():
    app_name, version = create_builder_ui()
    if not app_name:
        print("Build cancelled.")
        return

    print(f"Starting build for {app_name} v{version}...")

    try:
        # 1. Build Frontend
        print("--- Building Frontend ---")
        if not os.path.exists("frontend"):
             raise Exception("Frontend directory not found!")
             
        run_command("npm install", cwd="frontend")
        run_command("npm run build", cwd="frontend")
        
        if not os.path.exists("frontend/dist"):
             raise Exception("Frontend build failed: frontend/dist not found!")

        # 2. Build Backend with PyInstaller
        print("--- Freezing Backend ---")
        # Ensure we have pyinstaller
        run_command("pip install pyinstaller uvicorn")

        # Construct PyInstaller command
        # Use python -m PyInstaller to avoid launcher issues
        pyinstaller_cmd = (
            f'python -m PyInstaller --noconfirm --name "{app_name}" --onedir --windowed '
            f'--add-data "frontend/dist;frontend" '
            f'run_packaged.py'
        )

        run_command(pyinstaller_cmd)

        # 3. Generate Inno Setup Script
        print("--- Generating Installer Script ---")
        generate_inno_script(app_name, version, "dist")

        messagebox.showinfo("Success", f"Build complete! Executable is in dist/{app_name}.\nInno Setup script 'setup_script.iss' is ready.")
        
        # Optional: Try to run ISCC (Inno Setup Compiler) if it's in PATH
        print("Looking for Inno Setup Compiler (ISCC.exe)...")
        iscc_path = shutil.which("iscc")
        if iscc_path:
            print("ISCC found. Compiling installer...")
            run_command(f'"{iscc_path}" setup_script.iss')
            messagebox.showinfo("Success", "Installer (.exe) has been generated in the 'installers' folder.")
        else:
            print("ISCC.exe not found in PATH. Please compile 'setup_script.iss' manually using Inno Setup.")

    except Exception as e:
        print(f"Error during build: {e}")
        messagebox.showerror("Build Error", str(e))

if __name__ == "__main__":
    main()
