import subprocess, sys, os

def check_and_install():
    """Check and auto-install missing packages from requirements.txt."""
    req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')

    if not os.path.exists(req_path):
        print(f"  X ERROR: requirements.txt not found at {req_path}")
        return False

    with open(req_path, 'r') as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    missing = []
    for package in packages:
        # Handle version specifiers (e.g. "package>=1.0") — import name is the base
        import_name = package.split('>=')[0].split('==')[0].split('<')[0].strip()
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package)

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
