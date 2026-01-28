# STT Typer - Wayland Edition

> **Fork of [vertuzz/stt-typer](https://github.com/vertuzz/stt-typer) with full Wayland support**

A Python application that captures speech from your microphone and automatically types the transcribed text using Google Gemini API.

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

### How File Swapping Works

**During installation** (`./install.sh`):

| Session Type | Action |
|-------------|--------|
| **Wayland detected** | Ensures `main.py` is the Wayland version (swaps if needed) |
| **X11 detected** | Swaps `main.py.backup` → `main.py` (puts Wayland version as backup) |

The session check happens **once during installation** - no need to detect every time you run the app. The files remain swapped appropriately.

## Features

- Record audio from microphone with manual control (Ctrl+C to stop)
- Transcribe recorded audio using Google Gemini API
- Automatic typing of transcribed text
- **Full Wayland support** with multiple input methods
- **One-time session detection** during installation - swaps files automatically
- Multi-language support with automatic translation to English
- Toggle script for easy start/stop control
- Background operation with logging

## Installation

### Unified Installation Script (Recommended)

The installation script automatically detects your session type (Wayland or X11) and installs the appropriate dependencies:

```bash
./install.sh
```

This script will:
- Detect your session type (Wayland vs X11)
- Detect your Linux distribution
- Install system dependencies (session-specific and common packages)
- Install the `uv` package manager
- Set up Python dependencies
- Swap `main.py` files based on your session type
- Configure the toggle script
- Create optional global `toggle-stt` command

### Manual Installation

#### System Dependencies for Wayland

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-tk python3-dev alsa-utils pulseaudio-utils scrot xclip git curl libnotify-bin libcanberra-gtk3-module
```

**Fedora/RHEL:**
```bash
sudo dnf install tkinter python3-devel alsa-utils pulseaudio-utils scrot xclip git curl libnotify libcanberra-gtk3
```

**Arch Linux:**
```bash
sudo pacman -S --noconfirm tk python alsa-utils pulseaudio scrot xclip git curl libnotify libcanberra
```

#### Optional Wayland Typing Tools

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

#### uinput Permissions

For the primary uinput typing method:

```bash
# Allow current user to write to /dev/uinput
sudo chmod 666 /dev/uinput

# For permanent access, create a udev rule
echo 'KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo usermod -aG input $USER
```

### System Requirements

- **Python**: 3.13 or higher
- **Microphone**: Working microphone with proper system permissions
- **Display Server**: Wayland (this fork) or X11 (see original repo)
- **API Key**: Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

## Setup

1. Install dependencies using uv:
   ```bash
   uv sync
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Google API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

3. Get your API key from [Google AI Studio](https://aistudio.google.com/)

## Usage

### Toggle script (recommended):
Files were already configured during installation based on your session type.

```bash
./toggle_stt.sh
```
- First run: starts the application in background
- Second run: stops the application
- Logs are saved to `/tmp/stt_typer.log`
- To switch between Wayland/X11, re-run `./install.sh`

### Direct execution:
```bash
uv run main.py
```
Recording will start immediately. Stop recording with `Ctrl+C` to transcribe and type the audio.

### System-wide access:
```bash
sudo ln -s $(pwd)/toggle_stt.sh /usr/local/bin/toggle-stt
toggle-stt
```

### Keyboard shortcut:
Add to your desktop environment's keyboard shortcuts:
- Command: `/full/path/to/your/project/toggle_stt.sh`
- Key combination: your choice (e.g., `Super+S`)

## Typing Methods (Wayland)

The app tries multiple typing methods in order:

1. **uinput (evdev)** - Primary method, works at kernel level
2. **wtype** - Command-line Wayland typing tool
3. **ydotool** - Alternative Wayland input tool
4. **Clipboard** - Copy-paste fallback using wl-clipboard

## How it works

The application records audio from your microphone until you stop it with Ctrl+C. It then uploads the audio file to Google Gemini API for transcription and automatically types the transcribed text. The system supports multiple languages and automatically translates non-English speech to English.

## License

This fork maintains the same license as the original [stt-typer](https://github.com/vertuzz/stt-typer) project.

## Links

- **Original Repository**: https://github.com/vertuzz/stt-typer
- **Google AI Studio**: https://aistudio.google.com/
