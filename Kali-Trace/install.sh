#!/bin/bash

LOG_DIR="$HOME/.kali-logs"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGGER_SCRIPT="$SCRIPT_DIR/logger.py"

echo "[*] Setting up Kali Terminal Logger..."

# Create log directory
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo "[+] Created log directory: $LOG_DIR"
else
    echo "[.] Log directory exists: $LOG_DIR"
fi

# Make logger executable
chmod +x "$LOGGER_SCRIPT"

# Copy viewer to log directory
cp "$SCRIPT_DIR/viewer.html" "$LOG_DIR/viewer.html"
echo "[+] Deployed log viewer to $LOG_DIR/viewer.html"

# Add alias to .zshrc if it exists
if [ -f "$HOME/.zshrc" ]; then
    if ! grep -q "start-log" "$HOME/.zshrc"; then
        echo "" >> "$HOME/.zshrc"
        echo "# Kali Terminal Logger" >> "$HOME/.zshrc"
        echo "alias start-log='python3 $LOGGER_SCRIPT'" >> "$HOME/.zshrc"
        echo "[+] Added 'start-log' alias to ~/.zshrc"
        echo "[!] Run 'source ~/.zshrc' to use it."
    else
        echo "[.] Alias 'start-log' already in ~/.zshrc"
    fi
fi

# Add alias to .bashrc if it exists
if [ -f "$HOME/.bashrc" ]; then
    if ! grep -q "start-log" "$HOME/.bashrc"; then
        echo "" >> "$HOME/.bashrc"
        echo "# Kali Terminal Logger" >> "$HOME/.bashrc"
        echo "alias start-log='python3 $LOGGER_SCRIPT'" >> "$HOME/.bashrc"
        echo "[+] Added 'start-log' alias to ~/.bashrc"
    else
        echo "[.] Alias 'start-log' already in ~/.bashrc"
    fi
fi

echo "[*] Setup complete."
echo "[*] To start recording, restart your shell or run 'source ~/.zshrc' / 'source ~/.bashrc', then type 'start-log'."
