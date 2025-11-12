"""
Simple Build Script for Competitor Interface
Creates a standalone executable with all dependencies in a folder
"""
import os
import sys

def build_competitor():
    """Build the competitor interface executable"""
    
    print("=" * 60)
    print("Building Competitor Interface Executable")
    print("=" * 60)
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a launcher script
    launcher_content = """import tkinter as tk
from competitor_interface import ImprovedCompetitorApp
from data_manager import create_data_manager

if __name__ == "__main__":
    root = tk.Tk()
    data_manager = create_data_manager()
    app = ImprovedCompetitorApp(root, data_manager)
    root.mainloop()
"""
    
    launcher_path = os.path.join(current_dir, "competitor_launcher.py")
    with open(launcher_path, "w") as f:
        f.write(launcher_content)
    
    print("\nBuilding executable...")
    print("This will create a folder with the .exe and all dependencies.")
    
    # Build command
    cmd = f'pyinstaller --name=CompetitorInterface --windowed --add-data="problems;problems" '
    
    # Add Firebase credentials if exist
    firebase_creds = os.path.join(current_dir, "firebase_credentials.json")
    if os.path.exists(firebase_creds):
        cmd += f'--add-data="firebase_credentials.json;." '
        print("Including Firebase credentials...")
    
    cmd += f'"{launcher_path}"'
    
    print(f"\nRunning: {cmd}\n")
    os.system(cmd)
    
    print("\n" + "=" * 60)
    print("Build Complete!")
    print("=" * 60)
    print(f"\nExecutable folder: {os.path.join(current_dir, 'dist', 'CompetitorInterface')}")
    print(f"Run: {os.path.join(current_dir, 'dist', 'CompetitorInterface', 'CompetitorInterface.exe')}")
    print("\nCopy the entire 'CompetitorInterface' folder to any Windows laptop.")
    print("No Python installation required!")
    
    # Clean up
    if os.path.exists(launcher_path):
        os.remove(launcher_path)

if __name__ == "__main__":
    build_competitor()
