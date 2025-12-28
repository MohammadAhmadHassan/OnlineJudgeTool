"""
Build Competitor Interface Executable
Creates a distributable folder with the executable
"""
import PyInstaller.__main__
import os
import shutil
import sys
from datetime import datetime

print("=" * 60)
print("Building Competitor Interface Executable")
print("=" * 60)

# Clean previous builds
try:
    if os.path.exists('build'):
        shutil.rmtree('build')
except Exception as e:
    print(f"Warning: Could not clean 'build' folder: {e}")

try:
    if os.path.exists('dist/CompetitorInterface'):
        shutil.rmtree('dist/CompetitorInterface')
except Exception as e:
    print(f"Warning: Could not clean 'dist/CompetitorInterface' folder: {e}")
    print("This is OK - PyInstaller will overwrite files.")

# All Firebase-related hidden imports
hidden_imports = [
    'firebase_admin',
    'firebase_admin.credentials',
    'firebase_admin.firestore',
    'firebase_admin.db',
    'firebase_admin._sseclient',
    'firebase_admin._http_client',
    'google.cloud',
    'google.cloud.firestore',
    'google.cloud.firestore_v1',
    'google.auth',
    'google.auth.transport',
    'grpc',
    'google.api_core',
]

# Build hidden import arguments
hidden_import_args = []
for module in hidden_imports:
    hidden_import_args.extend(['--hidden-import', module])

# Get Python DLL path
python_dll = None
if sys.platform == 'win32':
    python_version = f"python{sys.version_info.major}{sys.version_info.minor}.dll"
    python_base = os.path.dirname(sys.executable)
    
    # Check common locations
    dll_locations = [
        os.path.join(python_base, python_version),
        os.path.join(os.path.dirname(python_base), python_version),
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32', python_version),
    ]
    
    for loc in dll_locations:
        if os.path.exists(loc):
            python_dll = loc
            print(f"Found Python DLL: {python_dll}")
            break

# PyInstaller command
pyinstaller_args = [
    'competitor_interface.py',
    '--name=CompetitorInterface',
    '--windowed',
    '--icon=NONE',
    '--add-data=problems;problems',
    '--add-data=firebase_credentials.json;.',
    '--clean',
    '--noconfirm',
    '--noupx',  # Disable UPX compression (can cause DLL issues)
    '--onedir',  # Create a directory (more reliable than onefile)
] + hidden_import_args

# Add Python DLL explicitly if found
if python_dll:
    pyinstaller_args.extend(['--add-binary', f'{python_dll};.'])

print("\nRunning PyInstaller with arguments:")
for arg in pyinstaller_args:
    print(f"  {arg}")
print()

PyInstaller.__main__.run(pyinstaller_args)

# Copy additional files
dist_dir = 'dist/CompetitorInterface'
if os.path.exists(dist_dir):
    # Copy README
    readme_content = """# Competition Problem Solving Tool - Competitor Interface

## Quick Start

1. Double-click `CompetitorInterface.exe` to launch
2. Enter your name to register
3. Start solving problems!

## Features

- Select and solve programming problems
- Write and test your code in real-time
- Submit solutions when all tests pass
- Multi-device support with Firebase sync

## System Requirements

- Windows 10/11
- No Python installation required
- Internet connection for Firebase sync

## Important Notes

- Keep all files in this folder together
- Do not move the .exe file separately
- Make sure firebase_credentials.json is present

## Troubleshooting

If you encounter "Python DLL not found":
1. Make sure you're running the .exe from this folder
2. Check that all _internal files are present
3. Try running as Administrator

If you encounter other issues:
1. Check your internet connection
2. Verify firebase_credentials.json exists
3. Contact the competition organizers

Build Date: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + f"""
Python Version: {sys.version}
"""

    with open(os.path.join(dist_dir, 'README.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    exe_path = os.path.join(dist_dir, 'CompetitorInterface.exe')
    if os.path.exists(exe_path):
        print("\n" + "=" * 60)
        print(f"✓ Build complete!")
        print(f"✓ Executable: {exe_path}")
        print(f"✓ Size: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
        print(f"✓ Total folder size: ~{sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, dirnames, filenames in os.walk(dist_dir) for filename in filenames) / (1024*1024):.2f} MB")
        print("\n⚠ IMPORTANT: Distribute the ENTIRE 'CompetitorInterface' folder!")
        print("  Do not copy just the .exe file - it needs the _internal folder!")
        print("=" * 60)
    else:
        print("\n❌ Build failed! Executable not found.")
else:
    print("\n❌ Build failed! Check the output above for errors.")
