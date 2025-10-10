import pyautogui
import subprocess
import time
import keyboard
import pyperclip
import os
import re
import shutil

# ==================== CONFIGURATION ====================
PROGRAM_PATH       = r"C:\Program Files\Perimed\PIMSoft\PIMSoft.exe"
PYTHON_SCRIPT_PATH = 'timerLCI.py'
CSV_SAVE_FOLDER    = r"C:\Projects\XXX\LCI"
BACKUP_TO_ONEDRIVE = True

HOTKEY_COMBINATION = "ctrl+shift+s"

# OneDrive Project Dictionary
ONEDRIVE_DICTIONARY = {
    'NRA' : ''
    }
# =======================================================

def automation_sequence(user_input):
    # Wait for PIMSoft to open
    time.sleep(10)
    # Do not perform validation
    pyautogui.press('enter')
    # New recording
    pyautogui.keyDown('ctrl')
    pyautogui.keyDown('n')
    time.sleep(2)
    pyautogui.keyUp('n')
    pyautogui.keyUp('ctrl')
    time.sleep(4)
    
    # Set up participant
    pyautogui.leftClick(144, 154)
    time.sleep(0.5)
    pyautogui.press('down')
    time.sleep(0.5)
    pyautogui.press('tab')
    time.sleep(0.5)
    pyautogui.press('tab')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.write(user_input)
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.2)
    
    # Exit first subject selection menu
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('enter')
    time.sleep(0.2)
    
    # Exit second subject selection menu
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('enter')
    return True


def open_program(program_path, is_pyscript=False, startup_wait=3, max_retries=10):
    try:
        if is_pyscript:
            process = subprocess.Popen(['python', program_path])
            return True
        else:
            process = subprocess.Popen(program_path, shell=True)
            time.sleep(startup_wait)
            
            for attempt in range(max_retries):
                return_code = process.poll()
                if return_code is None:
                    return True
                
                if attempt < max_retries - 1:
                    time.sleep(1)
        
            return False
        
    except FileNotFoundError:
        print(f"\n  ✗ ERROR: Program not found at {program_path}")
        return False
    except PermissionError:
        print(f"\n  ✗ ERROR: Permission denied to execute {program_path}")
        return False
    except Exception as e:
        print(f"\n  ✗ ERROR: Could not open program: {e}")
        return False


def save_clipboard_to_csv(user_input):
    try:
        match = re.match(r'^([A-Za-z]+)', user_input)
        folder_name = match.group(1) if match else user_input
        save_folder = CSV_SAVE_FOLDER.replace('XXX',folder_name)
        
        clipboard_content = pyperclip.paste()
        
        os.makedirs(save_folder, exist_ok=True)
        csv_path = os.path.join(save_folder, user_input + '_LCI.csv')
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(clipboard_content)
        print(f"  ✓ Recording data saved to: {csv_path}")
        
        if BACKUP_TO_ONEDRIVE:
            dst = os.path.join(ONEDRIVE_DICTIONARY[folder_name], user_input + '_LCI.csv')
            try:
                shutil.copy(csv_path, dst)
                print( "  ✓ Recording data backed up to OneDrive.")
            except Exception as e:
                print(f"  ✗ ERROR: Failed to back up data to OneDrive: {e}")
    except Exception as e:
        print(f"  ✗ ERROR: Failed to save recording data: {e}")


def main():
    pyautogui.FAILSAFE = True
    
    print("=" * 60)
    print("Laser Speckle-contrast Imaging Setup Toolkit (LASIST)")
    print("  Developed by ZK @ OU/gerolab (2025)")
    print("  Property of The University of Oklahoma.")
    print("=" * 60)
    
    # Get subject ID
    user_input = input("\nEnter subject ID (e.g.: TTE017_V1): ").strip()
    if not user_input:
        print("  • No subject ID provided. Exiting...")
        return
    print(f"  ✓ Subject ID: {user_input}")
    
    # Check if device is connected
    print("\n[1/4] Check for PeriCam device connection...", end='')
    ans = input('  Is the device connected? [y]/n ')
    if ans.lower() in ['\r','y']:
        print('OK')
    else:
        print("\nExiting...")
        time.sleep(2)
        return
    
    # Continue with normal startup sequence
    print("\n[2/4] Opening the PeriCam Software suit ...", end='')
    if open_program(PROGRAM_PATH):
        print(' DONE')
    else:
        print('\n  ⚠ WARNING: PeriCam might not be running.')
        usrin = input('  Do you want to continue? [y]/n')
        if usrin.lower() in ['\r','y']:
            print()
        else:
            print("\nExiting...")
            time.sleep(2)
            return
    
    print("\n[3/4] Running automated setup sequence ....", end='')
    if automation_sequence(user_input):
        print(' DONE')
    else:
        print('\n  ⚠ WARNING: Could not run setup automatically.')
    
    print("\n[4/4] Starting timer ......................", end='')
    if open_program(PYTHON_SCRIPT_PATH, is_pyscript=True):
        print(' DONE')
    else:
        print('\n  ⚠ WARNING: Could not start timer')
    
    print(f"\nPress {HOTKEY_COMBINATION} to save clipboard output")
    print("Press 'ESC' to exit the script\n")
    
    keyboard.add_hotkey(HOTKEY_COMBINATION, lambda: save_clipboard_to_csv(user_input))
    keyboard.wait('esc')
    print("\nExiting...")


if __name__ == "__main__":
    main()