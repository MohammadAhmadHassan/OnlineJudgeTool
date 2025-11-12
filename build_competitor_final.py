"""
Build Competitor Interface Executable
Creates a distributable folder with the executable
"""
import os
import subprocess
import sys

# Get paths
current_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(current_dir, ".venv", "Scripts", "python.exe")
pyinstaller = os.path.join(current_dir, ".venv", "Scripts", "pyinstaller.exe")

print("=" * 70)
print("Building Competitor Interface Executable")
print("=" * 70)

# Create launcher script
launcher_content = """# -*- coding: utf-8 -*-
import sys
import os
import traceback

# Force UTF-8 encoding for stdout/stderr to prevent Unicode errors on Windows
if sys.platform == 'win32':
    import io
    # In windowed mode, stdout/stderr might be None, so check first
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr is not None and hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import tkinter as tk
from tkinter import messagebox

try:
    from competitor_interface import ImprovedCompetitorApp
    from data_manager import create_data_manager
    
    if __name__ == "__main__":
        root = tk.Tk()
        root.withdraw()  # Hide root window initially
        
        try:
            data_manager = create_data_manager()
            app = ImprovedCompetitorApp(root, data_manager)
            root.deiconify()  # Show window after successful initialization
            root.mainloop()
        except Exception as e:
            error_msg = f"Failed to start application:\\n\\n{str(e)}\\n\\nPlease contact support."
            messagebox.showerror("Startup Error", error_msg)
            sys.exit(1)
            
except Exception as e:
    # Critical error before GUI starts
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Critical Error", f"Failed to load application:\\n\\n{str(e)}")
    sys.exit(1)
"""

launcher_path = os.path.join(current_dir, "competitor_launcher.py")
with open(launcher_path, "w") as f:
    f.write(launcher_content)

print("\n✓ Created launcher script")

# Build PyInstaller command
cmd = [
    pyinstaller,
    "--name=CompetitorInterface",
    "--windowed",  # No console window
    "--noconfirm",  # Overwrite existing files
    f"--add-data=problems{os.pathsep}problems",
]

# Add Firebase credentials if they exist
firebase_creds = os.path.join(current_dir, "firebase_credentials.json")
if os.path.exists(firebase_creds):
    cmd.append(f"--add-data=firebase_credentials.json{os.pathsep}.")
    print("✓ Including Firebase credentials")

# Add hidden imports for Firebase
cmd.extend([
    "--hidden-import=firebase_admin",
    "--hidden-import=google.cloud.firestore",
    "--collect-all=firebase_admin",
    "--collect-all=google.cloud.firestore",
])

cmd.append(launcher_path)

print("\n Building executable (this may take 2-3 minutes)...")
print("  - Including Python interpreter")
print("  - Including all dependencies")
print("  - Including Firebase support\n")

try:
    # Run PyInstaller
    result = subprocess.run(cmd, check=True)
    
    print("\n" + "=" * 70)
    print("✓ BUILD SUCCESSFUL!")
    print("=" * 70)
    
    dist_folder = os.path.join(current_dir, "dist", "CompetitorInterface")
    exe_path = os.path.join(dist_folder, "CompetitorInterface.exe")
    
    print(f"\nExecutable location:")
    print(f"  {exe_path}")
    print(f"\nTo distribute:")
    print(f"  1. Copy the entire 'dist/CompetitorInterface' folder")
    print(f"  2. Share it with students")
    print(f"  3. They can run CompetitorInterface.exe directly")
    print(f"\n✓ No Python installation required on student laptops!")
    print(f"✓ All dependencies included!")
    print(f"✓ Firebase support included!")
    
    # Clean up
    if os.path.exists(launcher_path):
        os.remove(launcher_path)
        
except subprocess.CalledProcessError as e:
    print(f"\n✗ Build failed with error code {e.returncode}")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Build failed: {e}")
    sys.exit(1)
