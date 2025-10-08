import pyautogui
import subprocess
import time
import keyboard
import pyperclip
import os

# ==================== CONFIGURATION ====================
PROGRAM_PATH       = r"C:\Program Files\Perimed\PIMSoft\PIMSoft.exe"
PYTHON_SCRIPT_PATH = 'timerLCI.py'
CSV_SAVE_FOLDER    = r"C:\Projects\NRA\LCI"
CSV_FILENAME       = "fallback.csv"
HOTKEY_COMBINATION = "ctrl+shift+s"
# =======================================================

def automation_sequence(user_input):
    #Wait for PIMSoft to open
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
    time.sleep(0.1)
    pyautogui.press('down')
    time.sleep(0.1)
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.press('enter')
    time.sleep(0.1)
    pyautogui.write(user_input)
    time.sleep(0.1)
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

def open_program(program_path, is_pyscript=False):
    print(f"Opening program: {PROGRAM_PATH}...")
    try:
        if is_pyscript:
            subprocess.run(['python', PYTHON_SCRIPT_PATH], check=True)
        else:
            subprocess.Popen(program_path)
        return True
    except FileNotFoundError:
        print(f"Error: Program not found at {PROGRAM_PATH}")
        return False
    except Exception as e:
        print(f"Error opening program: {e}")
        return False


def save_clipboard_to_csv(user_input):
    try:
        clipboard_content = pyperclip.paste()
        
        os.makedirs(CSV_SAVE_FOLDER, exist_ok=True)
        csv_path = os.path.join(CSV_SAVE_FOLDER, user_input + '_LCI.csv')
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(clipboard_content)
        
        print(f"  Recording data saved to: {csv_path}")
    except Exception as e:
        print(f"Error saving clipboard: {e}")


def main():
    pyautogui.FAILSAFE = True
    
    print("=" * 50)
    print("Laser Speckle Contrast Imaging Setup Toolkit")
    print("  Developed by ZK @ OU/gerolab (2025)")
    print("=" * 50)
    
    user_input = input("\nEnter subject ID (e.g.: TTE017_V1): ").strip()
    if not user_input:
        return
    
    print("\n[1/3] Opening the PeriCam Software suit ...", end='')
    if open_program(PROGRAM_PATH):
        print(' DONE.')
    else:
        print('\nERROR: Could not start recording software.')
        return
    
    print("\n[2/3] Running automated setup sequence ...", end='')
    if automation_sequence(user_input):
        print(' DONE.')
    else:
        print('\nWARNING: Could not run setup automatically.')

    
    print("\n[3/3] Staring timer ...", end='')
    if open_program(PYTHON_SCRIPT_PATH, is_pyscript=True):
        print(' DONE.')
    else:
        print('\nWARNING: Could not start timer')
    
    print(f"\nPress {HOTKEY_COMBINATION} to save clipboard output.")
    print("Press 'ESC' to exit the script.\n")
    keyboard.add_hotkey(HOTKEY_COMBINATION, save_clipboard_to_csv)
    keyboard.wait('esc')
    print("\nExiting...")


if __name__ == "__main__":
    main()
