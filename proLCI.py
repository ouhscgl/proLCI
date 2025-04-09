import tkinter as tk
import time
from tkinter import font

class TimerApp:
    def __init__(self, root, x_pos, y_pos, target_time):
        self.root = root
        self.root.title("Timer")
        self.root.geometry(f"300x150+{x_pos}+{y_pos}")  # Set window size and position
        self.root.resizable(False, False)  # Fixed window size
        
        # Configure the font for the timer display
        self.timer_font = font.Font(family="Arial", size=24, weight="bold")
        
        # Create and set up timer display
        self.timer_display = tk.Label(root, text="00:00.00", font=self.timer_font)
        self.timer_display.pack(pady=30)
        
        # Status label for instructions and notifications
        self.status_label = tk.Label(root, text="Press Ctrl+C to start timer")
        self.status_label.pack(pady=10)
        
        # Timer variables
        self.is_running = False
        self.start_time = 0
        self.target_time = target_time
        
        # Bind keyboard shortcut (Ctrl+C)
        self.root.bind("<Control-c>", self.toggle_timer)
        
        # Update timer display periodically
        self.update_timer()
    
    def toggle_timer(self, event=None):
        if not self.is_running:
            self.start_timer()
        else:
            self.stop_timer()
    
    def start_timer(self):
        self.is_running = True
        self.start_time = time.time()
        self.status_label.config(text="Timer running...")
        
        # Change background color to indicate timer is running
        self.root.configure(background="#e6f7ff")  # Light blue
        self.timer_display.configure(background="#e6f7ff")
        self.status_label.configure(background="#e6f7ff")
    
    def stop_timer(self):
        self.is_running = False
        self.status_label.config(text="Timer stopped. Press Ctrl+C to restart")
        
        # Restore original background color
        self.root.configure(background="#f0f0f0")  # Default gray
        self.timer_display.configure(background="#f0f0f0")
        self.status_label.configure(background="#f0f0f0")
    
    def update_timer(self):
        if self.is_running:
            elapsed_time = time.time() - self.start_time
            
            if elapsed_time >= self.target_time:
                # Timer completed
                self.is_running = False
                self.timer_display.config(text=self.format_time(self.target_time))
                self.notify_completion()
            else:
                # Update timer display
                self.timer_display.config(text=self.format_time(elapsed_time))
        
        # Schedule the next update (every 10ms for smoother display)
        self.root.after(10, self.update_timer)
    
    def format_time(self, seconds):
        """Format time as MM:SS.CC (minutes, seconds, centiseconds)"""
        minutes = int(seconds // 60)
        seconds_remainder = seconds % 60
        centiseconds = int((seconds_remainder - int(seconds_remainder)) * 100)
        
        return f"{minutes:02d}:{int(seconds_remainder):02d}.{centiseconds:02d}"
    
    def notify_completion(self):
        # Visual notification since sounds are off
        self.status_label.config(text="Time's up! Please proceed.", fg="red")
        
        # Flash the window to get attention
        self.flash_window(8)  # Flash 8 times
    
    def flash_window(self, remaining):
        if remaining <= 0:
            # Reset to normal after flashing
            self.root.configure(background="#f0f0f0")
            self.timer_display.configure(background="#f0f0f0")
            self.status_label.configure(background="#f0f0f0")
            return
        
        # Toggle between colors
        if remaining % 2 == 0:
            bg_color = "#ffcccc"  # Light red
        else:
            bg_color = "#f0f0f0"  # Default gray
        
        self.root.configure(background=bg_color)
        self.timer_display.configure(background=bg_color)
        self.status_label.configure(background=bg_color)
        
        # Schedule next flash after 500ms
        self.root.after(500, self.flash_window, remaining - 1)


def main():
    x_position = 100
    y_position = 100
    target_time = 4.5 * 60

    root = tk.Tk()
    app = TimerApp(root, x_position, y_position, target_time)
    root.mainloop()

if __name__ == "__main__":
    main()