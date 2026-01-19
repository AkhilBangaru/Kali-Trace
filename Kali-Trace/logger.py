import os
import sys
import pty
import tty
import termios
import select
import time
import datetime
import re
import signal
import struct
import fcntl
import argparse

# Configuration
LOG_DIR = os.path.expanduser("~/.kali-logs")
SHELL = os.environ.get("SHELL", "/bin/bash")

def get_session_filename():
    """Generates a timestamped filename."""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")

def resize_pty(master_fd):
    """Resizes the PTY to match the current terminal window size."""
    try:
        # Get the size of the current terminal
        size = fcntl.ioctl(sys.stdin, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))
        # Set the size of the pty
        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, size)
    except Exception:
        pass

class VT100Lite:
    """
    A robust terminal emulator to reconstruct the visible screen buffer.
    Handles cursor, clearing, and special Zsh/Kali escape sequences.
    """
        self.cursor_x = 0
        self.buffer = [] 
        self.in_alt_screen = False
        self.bracketed_paste_mode = False
        self.last_logged_line = None

    def process(self, chunk):
        # Improved Regex for better tokenization
        # 1. CSI: \x1b [ ...
        # 2. OSC: \x1b ] ... \x07|\x1b\\
        # 3. Two-char escapes: \x1b [=@>78()EHM] (Covering Keypad, Charset, Headers)
        token_pattern = re.compile(
            r'(\x1b\[[0-9;?]*[\x40-\x7e])|'       # CSI
            r'(\x1b][0-9]*;.*?(?:\x07|\x1b\\))|'  # OSC
            r'(\x1b[=@>78()EHM])'                 # Special 2-char Escapes (Fixes "==" issue)
        )
        
        completed_lines = []
        parts = token_pattern.split(chunk)
        
        for part in parts:
            if not part: continue
            
            if part.startswith('\x1b['):
                self._handle_csi(part, completed_lines)
            elif part.startswith('\x1b]'):
                pass # Ignore OSC (Window Titles)
            elif part.startswith('\x1b'):
                # Handle special 2-char escapes (DECKPAM, etc) allow us to ignore them silently
                pass 
            else:
                lines = self._handle_text(part)
                completed_lines.extend(lines)
                
        return completed_lines

    def _handle_csi(self, seq, out_list):
        # Alt Screen Detection (Support both ?1049 and ?47)
        if seq in ('\x1b[?1049h', '\x1b[?47h'):
            self.in_alt_screen = True
            out_list.append("\n[LOG: Entered Interactive Mode]")
        elif seq in ('\x1b[?1049l', '\x1b[?47l'):
            self.in_alt_screen = False
            out_list.append("\n[LOG: Exited Interactive Mode]")
        
        # Bracketed Paste
        elif seq == '\x1b[?2004h': self.bracketed_paste_mode = True
        elif seq == '\x1b[?2004l': self.bracketed_paste_mode = False
            
        # Handle Erase Line
        elif seq.endswith('K'):
            mode = 0
            if len(seq) > 3:
                try: mode = int(seq[2:-1])
                except: pass
            
            if mode == 0: self.buffer = self.buffer[:self.cursor_x]
            elif mode == 2: 
                self.buffer = []
                self.cursor_x = 0
                
        # Cursor Horizontal 
        elif seq.endswith('G') or seq.endswith('`'):
            try:
                col = int(seq[2:-1])
                self.cursor_x = max(0, col - 1)
            except: pass
            
        # Cursor Vertical (A=Up, B=Down) OR Absolute Position (H, f) - Important for Nano
        elif (seq.endswith('A') or seq.endswith('B') or seq.endswith('H') or seq.endswith('f')) and self.in_alt_screen:
            # Whenever the cursor jumps around in an editor, we assume the previous line is "done" enough to log
            line_str = "".join(self.buffer).rstrip()
            if line_str:
                out_list.append(line_str)
            self.buffer = []
            self.cursor_x = 0

    def _handle_text(self, text):
        lines_out = []
        for char in text:
            # In Interactive Mode (Nano), CR (\r) usually acts as a Line Break.
            # In Shell, CR (\r) moves cursor to start (no newline).
            if char == '\r':
                if self.in_alt_screen:
                    # Flush as a newline
                    line_str = "".join(self.buffer).rstrip()
                    if line_str:
                        lines_out.append(line_str)
                    self.buffer = []
                    self.cursor_x = 0
                else:
                    self.cursor_x = 0
            elif char == '\n':
                line_str = "".join(self.buffer).rstrip()
                if line_str:
                    lines_out.append(line_str)
                self.buffer = []
                self.cursor_x = 0
            elif char == '\x08': # Backspace
                self.cursor_x = max(0, self.cursor_x - 1)
            elif char == '\x07': # Bell
                pass
            else:
                if len(self.buffer) <= self.cursor_x:
                     self.buffer.extend([' '] * (self.cursor_x - len(self.buffer) + 1))
                self.buffer[self.cursor_x] = char
                self.cursor_x += 1
        return lines_out

    def flush(self):
        """Force flush current buffer (e.g. on exit)"""
        if self.buffer:
           return ["".join(self.buffer).rstrip()]
        return []

def main():
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except OSError as e:
            print(f"Error creating log directory {LOG_DIR}: {e}")
            return

    session_name = get_session_filename()
    raw_log_path = os.path.join(LOG_DIR, f"{session_name}.raw")
    clean_log_path = os.path.join(LOG_DIR, f"{session_name}.log")

    print(f"[*] Starting Terminal Logger... ")
    print(f"[*] Raw Log: {raw_log_path}")
    print(f"[*] Clean Log: {clean_log_path}")
    print(f"[*] Type 'exit' or Ctrl+D to stop.")

    try:
        raw_file = open(raw_log_path, 'wb')
        clean_file = open(clean_log_path, 'w', encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"Error opening log files: {e}")
        return

    # Use master fd to avoid pty.fork logic complexity in signal handler?
    # We stick to the existing structure.
    
    # Save original tty settings
    try:
        old_tty = termios.tcgetattr(sys.stdin)
    except:
        old_tty = None
    
    pid, master_fd = pty.fork()

    if pid == 0:
        # Child process: executes the shell
        os.execv(SHELL, [SHELL])
    else:
        # Parent process
        
        # State
        vt = VT100Lite()
        
        # Signal handler
        def curried_resize(signum, frame):
            resize_pty(master_fd)
        signal.signal(signal.SIGWINCH, curried_resize)
        resize_pty(master_fd)

        try:
            tty.setraw(sys.stdin.fileno())
            
            clean_log_buffer = "" # For grouping ANSI tokens
            
            while True:
                r, w, x = select.select([sys.stdin, master_fd], [], [])
                
                if sys.stdin in r:
                    try:
                        d = os.read(sys.stdin.fileno(), 1024)
                    except OSError:
                        d = b""
                    if not d:
                        break
                    os.write(master_fd, d)

                if master_fd in r:
                    try:
                        o = os.read(master_fd, 10240)
                    except OSError:
                        o = b""
                    if not o:
                        break
                    
                    try:
                        os.write(sys.stdout.fileno(), o)
                    except OSError:
                         pass

                    raw_file.write(o)
                    raw_file.flush()

                    # VT100 Logging Logic
                    # 1. Accumulate text to safe-parse ANSI
                    text = o.decode('utf-8', errors='replace')
                    clean_log_buffer += text
                    
                    # 2. Heuristic: Wait for complete ANSI sequences
                    # If end matches incomplete escape, wait.
                    # Simple check: If \x1B is present near end.
                    to_process = ""
                    last_esc = clean_log_buffer.rfind('\x1B')
                    if last_esc == -1:
                        to_process = clean_log_buffer
                        clean_log_buffer = ""
                    elif (len(clean_log_buffer) - last_esc) > 256: 
                        # Timeout logic (too long, assume text)
                        to_process = clean_log_buffer
                        clean_log_buffer = ""
                    else:
                        # Keep potential sequence
                        to_process = clean_log_buffer[:last_esc]
                        clean_log_buffer = clean_log_buffer[last_esc:]
                    
                    if to_process:
                        # 3. Feed to VT100 Emulator
                        lines = vt.process(to_process)
                        
                        # 4. Write completed lines with Timestamp
                        for line in lines:
                             # Deduplication Logic: Ignore if identical to last line (fixes prompt double-echo)
                             if line == vt.last_logged_line:
                                 continue
                                 
                             vt.last_logged_line = line
                             timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
                             clean_file.write(f"{timestamp}{line}\n")
                             clean_file.flush()

        except OSError as e:
            pass
            
        finally:
            if old_tty:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
            
            # Flush trailing
            trailing_lines = vt.flush() # + maybe clean_log_buffer content if any text left?
            if clean_log_buffer:
                trailing_lines += vt.process(clean_log_buffer) # Process remainder
            
            for line in trailing_lines + vt.flush(): # Flush final buffer
                 timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
                 clean_file.write(f"{timestamp}{line}\n")
            
            raw_file.close()
            clean_file.close()
            
            print(f"\n[*] Session capture ended.")
            print(f"[*] Default Filename: {session_name}")
            
            try:
                choice = input(f"[?] Rename log files? (Leave empty to keep default): ").strip()
                if choice:
                    new_name = "".join(c for c in choice if c.isalnum() or c in ('-', '_', '.'))
                    if not new_name:
                         print("[!] Invalid name using default.")
                    else:
                        new_raw = os.path.join(LOG_DIR, f"{new_name}.raw")
                        new_clean = os.path.join(LOG_DIR, f"{new_name}.log")
                        
                        if os.path.exists(new_raw) or os.path.exists(new_clean):
                            print(f"[!] File {new_name} already exists. Keeping timestamped default.")
                        else:
                            os.rename(raw_log_path, new_raw)
                            os.rename(clean_log_path, new_clean)
                            print(f"[+] Renamed to: {new_clean}")
                            clean_log_path = new_clean
            except: pass
            
            print(f"[*] Clean Log Saved: {clean_log_path}")

if __name__ == "__main__":
    main()
