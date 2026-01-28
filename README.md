# STT Typer - Wayland Edition

> **Fork of [vertuzz/stt-typer](https://github.com/vertuzz/stt-typer) with full Wayland support**

A Python application that captures speech from your microphone and automatically types the transcribed text using Google Gemini API.

---

## 🖥️ Choose Your Display Server

**Select your display server to see tailored installation instructions:**

| [**🟦 Wayland Users**](#wayland-installation) | [**🪟 X11 Users**](#x11-installation) |
|:---:|:---:|
| For GNOME, KDE Plasma, Sway, Hyprland, etc. | For Xfce, LXQt, i3, Openbox, etc. |

---

## Credits

This is a fork of the original [stt-typer](https://github.com/vertuzz/stt-typer) by [vertuzz](https://github.com/vertuzz).

### What's Changed in This Fork

The original version was designed for X11. This fork adds **full Wayland support** with:

- **uinput-based typing** - Direct kernel input for Wayland compatibility
- **Multiple fallback methods** - wtype, ydotool, and clipboard-based typing
- **Unified installation script** - `install.sh` auto-detects Wayland/X11 and installs accordingly
- **Auto-detection & file swapping** - Installation script detects your session (Wayland/X11) once and swaps files accordingly
- Original file preserved as `main.py.backup` (X11 version)
- Modified `main.py` for Wayland (includes typing fallbacks)

---

## Features

- Record audio from microphone with manual control (Ctrl+C to stop)
- Transcribe recorded audio using Google Gemini API
- Automatic typing of transcribed text
- **Full Wayland support** with multiple input methods
- **One-time session detection** during installation - swaps files automatically
- Multi-language support with automatic translation to English
- Toggle script for easy start/stop control
- Background operation with logging

---

<a name="wayland-installation"></a>
## 🟦 Wayland Installation

> **For:** GNOME, KDE Plasma, Sway, Hyprland, Wayfire, River, etc.

### Quick Install (Recommended)

The installation script automatically detects Wayland and configures everything:

```bash
chmod +x install.sh
./install.sh
```

**What the script does for Wayland:**
- Detects your Wayland session
- Installs Wayland-specific dependencies
- Sets up uinput permissions for typing
- Prompts for your Google API key
- Configures `main.py` with Wayland support
- Sets up the toggle script

### Manual Wayland Setup

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-tk python3-dev alsa-utils pulseaudio-utils scrot xclip git curl portaudio19-dev libnotify-bin libcanberra-gtk3-module
```

**Fedora/RHEL:**
```bash
sudo dnf install tkinter python3-devel alsa-utils pulseaudio-utils scrot xclip git curl portaudio-devel libnotify libcanberra-gtk3
```

**Arch Linux:**
```bash
sudo pacman -S --noconfirm tk python alsa-utils pulseaudio scrot xclip git curl portaudio libnotify libcanberra
```

#### 2. Install Optional Wayland Typing Tools

The app includes uinput-based typing by default. You can also install these optional tools for additional fallback methods:

```bash
# wtype - recommended Wayland typing tool
sudo apt install wtype  # Ubuntu/Debian
sudo dnf install wtype  # Fedora
yay -S wtype            # Arch (AUR)

# ydotool - alternative Wayland input tool
sudo apt install ydotool  # Ubuntu/Debian
sudo dnf install ydotool  # Fedora
yay -S ydotool           # Arch (AUR)
```

#### 3. Setup uinput Permissions

> **Note:** The `install.sh` script does this automatically.

**Quick (temporary, lost on reboot):**
```bash
sudo chmod 666 /dev/uinput
```

**Permanent (recommended):**
```bash
# Add user to input group
sudo usermod -aG input $USER

# Create udev rule
echo 'KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-uinput.rules

# Log out and back in for group changes to take effect
```

#### 4. Install Python Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

#### 5. Configure API Key

```bash
cp .env.example .env
nano .env  # or your preferred editor
```

Add your Google API key:
```
GOOGLE_API_KEY=your_actual_api_key_here
```

Get your key from: https://aistudio.google.com/app/apikey

#### 6. Ensure Correct main.py

The installation script should have already configured this. Verify `main.py` contains Wayland typing functions (check for `type_text_uinput` or `type_text_wayland`).

If needed, swap files manually:
```bash
# If main.py.backup has the Wayland version:
mv main.py main.py.x11
mv main.py.backup main.py
mv main.py.x11 main.py.backup
```

### Wayland Typing Methods

The app tries multiple typing methods in order:

1. **uinput (evdev)** - Primary method, works at kernel level
2. **wtype** - Command-line Wayland typing tool
3. **ydotool** - Alternative Wayland input tool
4. **Clipboard** - Copy-paste fallback using wl-clipboard

[↑ Back to top](#-choose-your-display-server)

---

<a name="x11-installation"></a>
## 🪟 X11 Installation

> **For:** Xfce, LXQt, i3, Openbox, KDE (X11 session), etc.

### Quick Install (Recommended)

The installation script automatically detects X11 and configures everything:

```bash
chmod +x install.sh
./install.sh
```

**What the script does for X11:**
- Detects your X11 session
- Installs X11-compatible dependencies
- Swaps `main.py.backup` to `main.py` (original X11 version)
- Prompts for your Google API key
- Sets up the toggle script

### Manual X11 Setup

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-tk python3-dev alsa-utils pulseaudio-utils scrot xclip git curl portaudio19-dev libnotify-bin libcanberra-gtk3-module
```

**Fedora/RHEL:**
```bash
sudo dnf install tkinter python3-devel alsa-utils pulseaudio-utils scrot xclip git curl portaudio-devel libnotify libcanberra-gtk3
```

**Arch Linux:**
```bash
sudo pacman -S --noconfirm tk python alsa-utils pulseaudio scrot xclip git curl portaudio libnotify libcanberra
```

#### 2. Install Python Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

#### 3. Configure API Key

```bash
cp .env.example .env
nano .env  # or your preferred editor
```

Add your Google API key:
```
GOOGLE_API_KEY=your_actual_api_key_here
```

Get your key from: https://aistudio.google.com/app/apikey

#### 4. Ensure Correct main.py

The installation script should have already configured this. For X11, you want the original `main.py` (without Wayland typing functions).

If `main.py` contains Wayland functions (`type_text_uinput`, `type_text_wayland`), swap it:
```bash
# Swap to use the X11 version from backup
mv main.py main.py.wayland
mv main.py.backup main.py
mv main.py.wayland main.py.backup
```

[↑ Back to top](#-choose-your-display-server)

---

## Usage (Both Wayland & X11)

### Toggle Script (Recommended)

```bash
./toggle_stt.sh
```

- **First run:** Starts the application in background
- **Second run:** Stops the application
- Logs are saved to `/tmp/stt_typer.log`

### Direct Execution

```bash
uv run main.py
```

Recording will start immediately. Stop recording with `Ctrl+C` to transcribe and type the audio.

### System-wide Access

```bash
sudo ln -s $(pwd)/toggle_stt.sh /usr/local/bin/toggle-stt
toggle-stt
```

### Keyboard Shortcut

Add to your desktop environment's keyboard shortcuts:

| Setting | Value |
|---------|-------|
| **Command** | `/full/path/to/your/project/toggle_stt.sh` |
| **Key combination** | Your choice (e.g., `Super+S`) |

### Switching Between Wayland & X11

If you switch display servers, re-run the installation:
```bash
./install.sh
```

The script will detect your new session type and swap files accordingly.

---

## How It Works

The application records audio from your microphone until you stop it with Ctrl+C. It then uploads the audio file to Google Gemini API for transcription and automatically types the transcribed text. The system supports multiple languages and automatically translates non-English speech to English.

### How File Swapping Works

**During installation** (`./install.sh`):

| Session Type | Action |
|-------------|--------|
| **Wayland detected** | Ensures `main.py` is the Wayland version (swaps if needed) |
| **X11 detected** | Swaps `main.py.backup` → `main.py` (puts Wayland version as backup) |

The session check happens **once during installation** - no need to detect every time you run the app. The files remain swapped appropriately.

---

## System Requirements

- **Python**: 3.13 or higher
- **Microphone**: Working microphone with proper system permissions
- **Display Server**: Wayland or X11
- **API Key**: Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

---

## Troubleshooting

### Wayland Issues

**Typing doesn't work:**
1. Check uinput permissions: `ls -l /dev/uinput`
2. Ensure user is in `input` group: `groups`
3. Try installing `wtype` as fallback
4. Check logs: `tail -f /tmp/stt_typer.log`

**Permission denied on /dev/uinput:**
```bash
sudo chmod 666 /dev/uinput
# For permanent fix, see the uinput setup section above
```

### X11 Issues

**Typing doesn't work:**
- Ensure you're using the original `main.py` (not the Wayland version)
- Check that X11 automation libraries are working
- Check logs: `tail -f /tmp/stt_typer.log`

### General Issues

**Python module not found:**
```bash
uv sync
```

**API key errors:**
- Verify `.env` file contains valid key
- Get a new key from: https://aistudio.google.com/app/apikey

---

## License

This fork maintains the same license as the original [stt-typer](https://github.com/vertuzz/stt-typer) project.

## Links

- **Original Repository**: https://github.com/vertuzz/stt-typer
- **Google AI Studio**: https://aistudio.google.com/

---

[↑ Back to top](#-choose-your-display-server)
