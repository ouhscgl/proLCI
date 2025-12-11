import subprocess, sys

REQUIRED_PACKAGES = [
    ('pyautogui', 'pyautogui'),
    ('keyboard', 'keyboard'),
    ('pyperclip', 'pyperclip'),
    ('colorama', 'colorama'),
]

def check_and_install():
    missing = []
    
    for import_name, pip_name in REQUIRED_PACKAGES:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)
    
    if not missing:
        return True
    
    print(f"Installing missing packages: {', '.join(missing)}")
    for package in missing:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])
            print(f"  ./ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"  X Failed to install {package}: {e}")
            return False
    return True

if __name__ == "__main__":
    success = check_and_install()
    sys.exit(0 if success else 1)