#!/usr/bin/env python3
"""
Build script for creating executable from Financial Report application
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean .spec files
    for spec_file in Path('.').glob('*.spec'):
        print(f"Removing {spec_file}...")
        spec_file.unlink()

def create_executable():
    """Create the executable using PyInstaller"""
    
    # PyInstaller command with optimized settings for PySide6
    cmd = [
        'pyinstaller',
        '--onefile',                    # Single executable file
        '--windowed',                   # No console window (GUI app)
        '--name=FinancialReport',       # Name of the executable
        '--icon=assets/icon.png',       # Application icon
        '--add-data=assets/icon.png;assets',  # Include assets
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=peewee',
        '--hidden-import=requests',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=matplotlib',
        '--hidden-import=plotly',
        '--hidden-import=twelvedata',
        '--collect-all=PySide6',
        '--collect-all=peewee',
        'main.py'
    ]
    
    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        print("Starting PyInstaller build process...")
        print("This may take 5-15 minutes depending on your system.")
        print("PyInstaller is analyzing dependencies and creating the executable...")
        
        # Run with real-time output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        if process.stdout:
            for line in process.stdout:
                print(line.rstrip())
        
        process.wait()
        
        if process.returncode == 0:
            print("\n✅ Build completed successfully!")
            return True
        else:
            print(f"\n❌ Build failed with error code {process.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Build failed with exception: {e}")
        return False

def main():
    """Main build process"""
    print("=== Financial Report Executable Builder ===")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Please install it first:")
        print("pip install PyInstaller")
        return False
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create executable
    if create_executable():
        print("\n=== Build Successful! ===")
        print("Executable created: dist/FinancialReport.exe")
        print("\nYou can now distribute the executable file.")
        return True
    else:
        print("\n=== Build Failed! ===")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
