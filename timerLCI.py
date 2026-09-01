"""
Occlusion timer for the LCI / PORH protocol.

Timing is anchored to a monotonic deadline computed once at start, so the
end-of-occlusion alert lands within a few milliseconds of the target no
matter how loaded the machine is. Any discrepancy between this timer and
the pause length reported by PIMSoft is therefore operator/procedure
latency, not drift - use OFFSET_S (and the run log) to characterise it.
"""

import argparse
import csv
import os
import time
import tkinter as tk
from datetime import datetime
from tkinter import font

# ==================== CONFIGURATION ====================
TARGET_TIME_S   = 4.5 * 60      # nominal occlusion duration
OFFSET_S        = 0.0           # subtracted from TARGET_TIME_S (see notes)

WINDOW_X        = 920
WINDOW_Y        = 900

TOGGLE_HOTKEY   = "ctrl+shift+t"  # global: works while PIMSoft has focus
TRIGGER_KEY     = None            # e.g. "space" - key that also pauses PIMSoft.
                                  # If set, that same keypress starts the timer.

WARN_AT_S       = 10.0          # amber "get ready" alert
FINAL_AT_S      = 3.0           # red final countdown
ENABLE_BEEP     = False         # Windows-only; room sounds are normally off
LOG_RUNS        = True
LOG_FILENAME    = "timer_runs.csv"
# =======================================================

C_IDLE    = "#f0f0f0"
C_RUNNING = "#e6f7ff"
C_WARN    = "#fff2cc"
C_FINAL   = "#ffe0cc"
C_DONE    = "#ffcccc"


def beep():
    if not ENABLE_BEEP:
        return
    try:
        import winsound
        winsound.Beep(880, 250)
    except Exception:
        pass


class TimerApp:
    def __init__(self, root, x_pos, y_pos, target_time, offset=0.0):
        self.root = root
        self.root.title("LCI")
        self.root.geometry(f"240x86+{x_pos}+{y_pos}")
        self.root.resizable(False, False)

        self.timer_font = font.Font(family="Calibri", size=20, weight="bold")
        self.small_font = font.Font(family="Calibri", size=8)

        self.timer_display = tk.Label(root, text="04:30.00", font=self.timer_font)
        self.timer_display.pack(pady=0)

        self.status_label = tk.Label(root, fg="#808080", font=self.small_font,
                                     text=f"{TOGGLE_HOTKEY} or Ctrl+C to start")
        self.status_label.pack(pady=0)

        self.detail_label = tk.Label(root, fg="#a0a0a0", font=self.small_font, text="")
        self.detail_label.pack(pady=0)

        # Timing state - perf_counter is monotonic, immune to clock changes
        self.is_running   = False
        self.target_time  = max(0.0, target_time - offset)
        self.nominal      = target_time
        self.offset       = offset
        self.t0           = None      # perf_counter at start
        self.deadline     = None      # perf_counter at which occlusion ends
        self.wall_start   = None
        self.completed_at = None
        self._after_id    = None
        self._stage       = None      # None | "warn" | "final" | "done"

        # A hotkey thread stamps this the instant the key goes down; the UI
        # thread picks it up on the next tick. Keeps start precision off the
        # Tk event loop entirely.
        self._pending_start = None
        self._pending_stop  = False

        self.root.bind("<Control-c>", self.toggle_timer)
        self._install_global_hotkeys()

        self.set_bg(C_IDLE)
        self.timer_display.config(text=self.format_time(self.target_time))
        self._tick()

    # -- Input -------------------------------------------------------

    def _install_global_hotkeys(self):
        """Global hooks so the operator never has to leave the PIMSoft window."""
        self.hotkeys_active = False
        try:
            import keyboard
        except ImportError:
            self.detail_label.config(text="keyboard module missing - focus window for Ctrl+C")
            return

        try:
            keyboard.add_hotkey(TOGGLE_HOTKEY, self._hotkey_toggle)
            if TRIGGER_KEY:
                keyboard.on_press_key(TRIGGER_KEY, lambda e: self._hotkey_start_only())
            self.hotkeys_active = True
        except Exception as e:
            self.detail_label.config(text=f"hotkey unavailable ({e}) - use Ctrl+C")

    def _hotkey_toggle(self):
        if self.is_running:
            self._pending_stop = True
        else:
            self._pending_start = time.perf_counter()

    def _hotkey_start_only(self):
        if not self.is_running:
            self._pending_start = time.perf_counter()

    def toggle_timer(self, event=None):
        if self.is_running:
            self.stop_timer()
        else:
            self.start_timer()

    # -- Control -----------------------------------------------------

    def start_timer(self, t0=None):
        self.t0 = t0 if t0 is not None else time.perf_counter()
        self.wall_start = datetime.now()
        self.deadline = self.t0 + self.target_time
        self.is_running = True
        self.completed_at = None
        self._stage = None
        self.set_bg(C_RUNNING)
        self.status_label.config(text="Occlusion running", fg="#606060")
        self.detail_label.config(text=self.wall_start.strftime("started %H:%M:%S"))

    def stop_timer(self):
        if self.is_running:
            elapsed = time.perf_counter() - self.t0
            self._log_run(elapsed, aborted=True)
            self.status_label.config(
                text=f"Aborted at {self.format_time(elapsed)}", fg="#808080")
        self.is_running = False
        self.set_bg(C_IDLE)
        self.timer_display.config(text=self.format_time(self.target_time))

    def complete(self):
        overshoot = (time.perf_counter() - self.deadline) * 1000.0
        self.is_running = False
        self._stage = "done"
        self.completed_at = datetime.now()
        self.timer_display.config(text="00:00.00")
        self.status_label.config(text="RELEASE CUFF / RESUME", fg="red")
        self.detail_label.config(
            text=f"{self.completed_at.strftime('%H:%M:%S')} (alert {overshoot:+.0f} ms)")
        self._log_run(time.perf_counter() - self.t0, aborted=False)
        beep()
        self.flash_window(8)

    # -- Main loop ---------------------------------------------------

    def _tick(self):
        # Pick up anything the hotkey thread stamped
        if self._pending_start is not None:
            t0, self._pending_start = self._pending_start, None
            if not self.is_running:
                self.start_timer(t0)
        if self._pending_stop:
            self._pending_stop = False
            if self.is_running:
                self.stop_timer()

        interval = 20
        if self.is_running:
            remaining = self.deadline - time.perf_counter()

            if remaining <= 0:
                self.complete()
            else:
                self.timer_display.config(text=self.format_time(remaining))

                if remaining <= FINAL_AT_S and self._stage != "final":
                    self._stage = "final"
                    self.set_bg(C_FINAL)
                    self.status_label.config(text="Stand by", fg="#cc4400")
                elif FINAL_AT_S < remaining <= WARN_AT_S and self._stage != "warn":
                    self._stage = "warn"
                    self.set_bg(C_WARN)
                    self.status_label.config(text="Get ready to resume", fg="#996600")

                # Tighten the polling interval as the deadline approaches so the
                # alert never lands more than a few ms late.
                if remaining < 0.1:
                    interval = 1
                elif remaining < 2.0:
                    interval = 5

        self._after_id = self.root.after(interval, self._tick)

    # -- Logging -----------------------------------------------------

    def _log_run(self, elapsed, aborted):
        if not LOG_RUNS or self.wall_start is None:
            return
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), LOG_FILENAME)
        new = not os.path.exists(path)
        try:
            with open(path, 'a', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                if new:
                    w.writerow(["start_wallclock", "end_wallclock", "nominal_s",
                                "offset_s", "target_s", "measured_s", "aborted"])
                w.writerow([self.wall_start.isoformat(timespec='milliseconds'),
                            datetime.now().isoformat(timespec='milliseconds'),
                            f"{self.nominal:.3f}", f"{self.offset:.3f}",
                            f"{self.target_time:.3f}", f"{elapsed:.3f}",
                            int(aborted)])
        except Exception as e:
            self.detail_label.config(text=f"log write failed: {e}")

    # -- Presentation ------------------------------------------------

    def format_time(self, seconds):
        """Format as MM:SS.CC, rounding up so the display never reads 00:00
        while time still remains."""
        total_cs = int(seconds * 100 + 0.999)
        minutes, rem_cs = divmod(max(0, total_cs), 6000)
        secs, cs = divmod(rem_cs, 100)
        return f"{minutes:02d}:{secs:02d}.{cs:02d}"

    def set_bg(self, color):
        self.root.configure(background=color)
        for widget in (self.timer_display, self.status_label, self.detail_label):
            widget.configure(background=color)

    def flash_window(self, remaining):
        if remaining <= 0:
            self.set_bg(C_IDLE)
            self.status_label.config(
                text=f"Done. {TOGGLE_HOTKEY} to run again", fg="#808080")
            return
        self.set_bg(C_DONE if remaining % 2 == 0 else C_IDLE)
        self.root.after(500, self.flash_window, remaining - 1)


def main():
    parser = argparse.ArgumentParser(description="LCI occlusion timer")
    parser.add_argument('--target', type=float, default=TARGET_TIME_S,
                        help="occlusion duration in seconds (default 270)")
    parser.add_argument('--offset', type=float, default=OFFSET_S,
                        help="seconds to subtract, compensating for lead-in "
                             "before the timer is triggered")
    args = parser.parse_args()

    root = tk.Tk()
    root.attributes('-topmost', True)
    TimerApp(root, WINDOW_X, WINDOW_Y, args.target, args.offset)
    root.mainloop()


if __name__ == "__main__":
    main()
