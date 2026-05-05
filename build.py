import os
import subprocess
import sys

def main():
    print("=========================================")
    print(" Building Blackbird OSINT Executable...")
    print("=========================================")
    
    # Use the current python executable's pyinstaller module
    cmd = [sys.executable, "-m", "pyinstaller", "blackbird.spec"]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n=========================================")
        print(" Build Successful!")
        print(" The executable is located in the dist/ folder.")
        print("=========================================")
    except subprocess.CalledProcessError:
        print("\n=========================================")
        print(" Build Failed!")
        print(" Please check the error messages above.")
        print("=========================================")
    except FileNotFoundError:
        print("\n=========================================")
        print(" Build Failed!")
        print(" PyInstaller is not installed or not found.")
        print(" Run: pip install pyinstaller")
        print("=========================================")
        
    input("Press Enter to continue...")

if __name__ == "__main__":
    main()
