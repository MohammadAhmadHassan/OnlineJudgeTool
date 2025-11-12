"""
Build Competitor Interface Executable
Creates a standalone .exe file that includes Python and all dependencies
"""
import PyInstaller.__main__
import os
import shutil
import sys

def build_competitor_exe():
    """Build the competitor interface as a standalone executable"""
    
    print("=" * 60)
    print("Building Competitor Interface Executable")
    print("=" * 60)
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a launcher script for competitor interface
    launcher_content = """
import tkinter as tk
from competitor_interface import ImprovedCompetitorApp
from data_manager import create_data_manager
import sys
import os

if __name__ == "__main__":
    root = tk.Tk()
    
    # Create data manager
    data_manager = create_data_manager()
    
    # Create competitor interface
    app = ImprovedCompetitorApp(root, data_manager)
    
    root.mainloop()
"""
    
    # Write the launcher script
    launcher_path = os.path.join(current_dir, "competitor_launcher.py")
    with open(launcher_path, "w") as f:
        f.write(launcher_content)
    
    print("\n1. Creating standalone executable...")
    print("   - Including Python interpreter")
    print("   - Including all dependencies")
    print("   - Including Firebase support")
    
    # PyInstaller arguments
    args = [
        launcher_path,
        '--name=CompetitorInterface',
        '--onefile',  # Single executable file
        '--windowed',  # No console window
        '--icon=NONE',  # No icon (you can add one if you have it)
        f'--distpath={os.path.join(current_dir, "dist")}',
        f'--workpath={os.path.join(current_dir, "build")}',
        f'--specpath={current_dir}',
        
        # Add hidden imports
        '--hidden-import=firebase_admin',
        '--hidden-import=google.cloud',
        '--hidden-import=google.cloud.firestore',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.scrolledtext',
        
        # Add data files
        f'--add-data={os.path.join(current_dir, "problems")};problems',
        
        # Collect all submodules
        '--collect-all=firebase_admin',
        '--collect-all=google.cloud.firestore',
    ]
    
    # Add Firebase credentials if they exist
    firebase_creds = os.path.join(current_dir, "firebase_credentials.json")
    if os.path.exists(firebase_creds):
        args.append(f'--add-data={firebase_creds};.')
        print("   - Including Firebase credentials")
    
    try:
        # Run PyInstaller
        PyInstaller.__main__.run(args)
        
        print("\n" + "=" * 60)
        print("✓ Build Complete!")
        print("=" * 60)
        print(f"\nExecutable location: {os.path.join(current_dir, 'dist', 'CompetitorInterface.exe')}")
        print("\nThe executable includes:")
        print("  ✓ Python interpreter")
        print("  ✓ All required libraries")
        print("  ✓ Firebase support")
        print("  ✓ Problem files")
        print("  ✓ All dependencies")
        print("\nYou can copy this .exe file to any Windows laptop and run it directly!")
        print("No Python installation required on the target machine.")
        
        # Clean up temporary launcher
        if os.path.exists(launcher_path):
            os.remove(launcher_path)
            
    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        print("\nMake sure PyInstaller is installed:")
        print("  pip install pyinstaller")
        sys.exit(1)

if __name__ == "__main__":
    build_competitor_exe()
