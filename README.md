

# KaliTrace
**Terminal Activity Logger & Analyzer**
<img width="4608" height="3072" alt="ChatGPT Image Jan 19, 2026, 08_42_16 PM_upscayl_3x_ultrasharp-4x" src="https://github.com/user-attachments/assets/6d0cc59a-1279-413a-929a-77cdd09f5292" />
---

## 🔍 Overview

KaliTrace is a professional-grade terminal activity logging and visualization tool designed for cybersecurity practitioners, red teamers, blue team analysts, and learners.

It records terminal input/output with timestamps and provides a powerful web-based interface to analyze, search, and export session logs.

KaliTrace is ideal for:

- TryHackMe / HackTheBox documentation
- Penetration testing evidence
- Command auditing
- Learning revision
- Forensic-style terminal analysis

## 🚀 Features

### Terminal Logging
- Full command input logging
- Output capture
- Timestamped entries
- Works with Bash and Zsh
- Clean structured log format

### Web-Based Log Viewer
- Modern cyberpunk UI
- Drag & drop log loading
- Regex search support
- Case-sensitive search
- Command focus mode
- Raw view toggle
- Line numbers and timestamps toggle
- Interactive minimap navigation
- IP address extraction
- Bookmark important commands
- Fullscreen analysis mode

### Analysis & Reporting
- Session duration calculation
- Total lines count
- Command frequency estimation
- Unique IP detection
- Export to JSON
- Export to HTML report

---

## 📁 Project Structure

```
CmdScope/
├── install.sh        # Enables terminal activity logging
├── uninstall.sh      # Removes logging cleanly
├── viewer.html       # Advanced log viewer UI
└── logs/
    └── terminal.log
```

---

## 🛠 Installation

```
chmod +x install.sh
sudo ./install.sh
```

This enables automatic terminal activity logging.

### Uninstall

```
chmod +x uninstall.sh
sudo ./uninstall.sh
```

---

## 🧪 Usage

1. Open terminal
2. Perform commands normally
3. Logs are captured automatically
4. Open `viewer.html`
5. Load the generated `.log` file
6. Analyze commands visually

---

## 🎯 Use Cases

- Penetration testing documentation
- Red team operation logs
- Blue team auditing
- Learning and command review
- Certification prep (PJPT, eJPT, OSCP)

---

## 🔐 Security & Ethics

KaliTrace is intended for **educational, defensive, and authorized testing only**.

Do not use this tool on systems where logging is not permitted.

---

## 🔮 Future Enhancements

- Session-based log separation
- Automatic report generation (PDF)
- MITRE ATT&CK command mapping
- Command categorization (enum/exploit/privesc)
- Live logging dashboard
- Encrypted log storage

---

## 📜 License

MIT License

---

## 👤 Author

AkhilBangaru
