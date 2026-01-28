#!/bin/bash

# STT Typer Unified Installation Script
# Works on Linux (Wayland & X11) and macOS
# Automatically detects session type and installs appropriate dependencies
# Usage: curl -sSL https://raw.githubusercontent.com/yourusername/stt_typer/master/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project info
PROJECT_NAME="stt_typer"
PROJECT_URL="https://github.com/vertuzz/stt-typer.git"
INSTALL_DIR="$HOME/$PROJECT_NAME"

# Session type (will be detected)
SESSION_TYPE=""

# Utility functions
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        print_error "Unsupported operating system: $OSTYPE"
    fi
    print_success "Detected OS: $OS"
}

# Detect session type (Wayland or X11)
detect_session_type() {
    print_step "Detecting display session type..."

    if [[ -n "$WAYLAND_DISPLAY" ]]; then
        SESSION_TYPE="wayland"
    elif [[ -n "$XDG_SESSION_TYPE" ]]; then
        SESSION_TYPE="$XDG_SESSION_TYPE"
    elif [[ -n "$DISPLAY" ]]; then
        SESSION_TYPE="x11"
    else
        # Fallback: check loginctl
        local session_id=$(loginctl | grep "$(whoami)" | head -n1 | awk '{print $1}')
        if [[ -n "$session_id" ]]; then
            SESSION_TYPE=$(loginctl show-session "$session_id" -p Type 2>/dev/null | cut -d= -f2)
        else
            SESSION_TYPE="unknown"
        fi
    fi

    if [[ "$SESSION_TYPE" == "wayland" ]]; then
        print_success "Detected Wayland session - will install Wayland-specific dependencies"
    elif [[ "$SESSION_TYPE" == "x11" ]]; then
        print_success "Detected X11 session - will install X11-compatible dependencies"
    else
        print_warning "Could not detect session type (guessed: $SESSION_TYPE) - installing with Wayland support"
        SESSION_TYPE="wayland"  # Default to Wayland
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install system dependencies
install_system_deps() {
    print_step "Installing system dependencies..."

    if [[ "$OS" == "linux" ]]; then
        # Detect Linux distribution
        if command_exists apt-get; then
            # Ubuntu/Debian
            print_step "Installing dependencies for Ubuntu/Debian..."
            sudo apt update
            # Common dependencies
            sudo apt install -y python3-tk python3-dev alsa-utils pulseaudio-utils scrot xclip git curl portaudio19-dev

            # Session-specific dependencies
            if [[ "$SESSION_TYPE" == "wayland" ]]; then
                print_step "Installing Wayland-specific dependencies..."
                sudo apt install -y libnotify-bin libcanberra-gtk3-module
            else
                print_step "Installing X11-compatible dependencies..."
                sudo apt install -y libnotify-bin libcanberra-gtk3-module
            fi
        elif command_exists dnf; then
            # Fedora/RHEL
            print_step "Installing dependencies for Fedora/RHEL..."
            # Common dependencies
            sudo dnf install -y tkinter python3-devel alsa-utils pulseaudio-utils scrot xclip git curl portaudio-devel

            # Session-specific dependencies
            if [[ "$SESSION_TYPE" == "wayland" ]]; then
                print_step "Installing Wayland-specific dependencies..."
                sudo dnf install -y libnotify libcanberra-gtk3
            else
                print_step "Installing X11-compatible dependencies..."
                sudo dnf install -y libnotify libcanberra-gtk3
            fi
        elif command_exists pacman; then
            # Arch Linux
            print_step "Installing dependencies for Arch Linux..."
            # Common dependencies
            sudo pacman -S --noconfirm tk python alsa-utils pulseaudio scrot xclip git curl portaudio

            # Session-specific dependencies
            if [[ "$SESSION_TYPE" == "wayland" ]]; then
                print_step "Installing Wayland-specific dependencies..."
                sudo pacman -S --noconfirm libnotify libcanberra
            else
                print_step "Installing X11-compatible dependencies..."
                sudo pacman -S --noconfirm libnotify libcanberra
            fi
        else
            print_warning "Unknown Linux distribution. Please install the following packages manually:"
            echo "  - Python 3.13+ with tkinter"
            echo "  - python3-dev (development headers)"
            echo "  - alsa-utils, pulseaudio-utils"
            echo "  - scrot, xclip"
            echo "  - git, curl"
            echo "  - libnotify, libcanberra"
        fi
    elif [[ "$OS" == "macos" ]]; then
        print_step "Installing dependencies for macOS..."
        # Check for Xcode command line tools
        if ! xcode-select -p &>/dev/null; then
            print_step "Installing Xcode command line tools..."
            xcode-select --install
            print_warning "Please complete the Xcode installation and run this script again."
            exit 0
        fi

        # Install Homebrew if not present
        if ! command_exists brew; then
            print_step "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi

        # Install git if not present
        if ! command_exists git; then
            brew install git
        fi
    fi

    print_success "System dependencies installed"
}

# Install uv package manager
install_uv() {
    print_step "Checking for uv package manager..."
    
    if command_exists uv; then
        print_success "uv is already installed"
        uv --version
    else
        print_step "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # Add uv to PATH for current session
        export PATH="$HOME/.cargo/bin:$PATH"
        
        if command_exists uv; then
            print_success "uv installed successfully"
            uv --version
        else
            print_error "Failed to install uv. Please install manually from https://docs.astral.sh/uv/"
        fi
    fi
}

# Clone or update project
setup_project() {
    print_step "Setting up project..."
    
    if [[ -d "$INSTALL_DIR" ]]; then
        print_step "Project directory exists. Updating..."
        cd "$INSTALL_DIR"
        git pull origin master
    else
        print_step "Cloning project..."
        git clone "$PROJECT_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    
    print_success "Project setup complete"
}

# Install Python dependencies
install_python_deps() {
    print_step "Installing Python dependencies..."
    cd "$INSTALL_DIR"
    
    # Install dependencies with uv
    uv sync
    
    print_success "Python dependencies installed"
}

# Create environment file
setup_env() {
    print_step "Setting up environment configuration..."
    cd "$INSTALL_DIR"

    if [[ ! -f ".env" ]]; then
        cat > .env << EOF
# AssemblyAI API Key
# Get your API key from: https://www.assemblyai.com/
ASSEMBLYAI_API_KEY=your_api_key_here
EOF
        print_warning "Created .env file. You need to add your AssemblyAI API key!"
    else
        print_success "Environment file already exists"
    fi
}

# Detect session type and swap files accordingly
setup_session_files() {
    print_step "Detecting display session type..."

    cd "$INSTALL_DIR"

    # Detect session type
    if [[ -n "$WAYLAND_DISPLAY" ]]; then
        SESSION_TYPE="wayland"
    elif [[ -n "$XDG_SESSION_TYPE" ]]; then
        SESSION_TYPE="$XDG_SESSION_TYPE"
    elif [[ -n "$DISPLAY" ]]; then
        SESSION_TYPE="x11"
    else
        # Fallback: check loginctl
        local session_id=$(loginctl | grep "$(whoami)" | head -n1 | awk '{print $1}')
        if [[ -n "$session_id" ]]; then
            SESSION_TYPE=$(loginctl show-session "$session_id" -p Type 2>/dev/null | cut -d= -f2)
        else
            SESSION_TYPE="unknown"
        fi
    fi

    print_success "Detected session type: $SESSION_TYPE"

    # Swap files based on session type
    if [[ "$SESSION_TYPE" == "x11" ]]; then
        if [[ -f "main.py.backup" ]]; then
            print_step "X11 detected - swapping to X11 version of main.py..."
            mv main.py main.py.wayland
            mv main.py.backup main.py
            mv main.py.wayland main.py.backup
            print_success "Swapped: main.py is now X11 version, main.py.backup is Wayland version"
        fi
    elif [[ "$SESSION_TYPE" == "wayland" ]]; then
        # Check if main.py is actually the X11 version
        if [[ -f "main.py.backup" ]] && ! grep -q "type_text_wayland\|type_text_uinput" main.py 2>/dev/null; then
            print_step "Wayland detected - swapping to Wayland version of main.py..."
            mv main.py main.py.x11
            mv main.py.backup main.py
            mv main.py.x11 main.py.backup
            print_success "Swapped: main.py is now Wayland version, main.py.backup is X11 version"
        else
            print_success "Wayland detected - main.py is already the Wayland version"
        fi
    else
        print_warning "Unknown session type. Keeping current main.py as-is."
    fi
}

# Make toggle script executable
setup_toggle_script() {
    print_step "Setting up toggle script..."
    cd "$INSTALL_DIR"
    
    chmod +x toggle_stt.sh
    print_success "Toggle script is ready"
}

# Add to PATH (optional)
setup_global_access() {
    print_step "Setting up global access..."
    
    # Create symlink in /usr/local/bin if it doesn't exist
    if [[ ! -L "/usr/local/bin/toggle-stt" ]]; then
        echo "Creating global 'toggle-stt' command..."
        if sudo ln -sf "$INSTALL_DIR/toggle_stt.sh" /usr/local/bin/toggle-stt 2>/dev/null; then
            print_success "Global command 'toggle-stt' created"
        else
            print_warning "Could not create global command. You can run: $INSTALL_DIR/toggle_stt.sh"
        fi
    else
        print_success "Global command 'toggle-stt' already exists"
    fi
}

# Show usage instructions
show_usage() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎤 STT Typer Installed! 🎤                ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}📋 NEXT STEPS:${NC}"
    echo ""
    echo -e "${BLUE}1. Set up your API key:${NC}"
    echo "   Edit: $INSTALL_DIR/.env"
    echo "   Add your AssemblyAI API key from: https://www.assemblyai.com/"
    echo ""
    echo -e "${BLUE}2. Usage options:${NC}"
    echo ""
    echo -e "${GREEN}   • Toggle script (recommended):${NC}"
    echo "     $INSTALL_DIR/toggle_stt.sh"
    if [[ -L "/usr/local/bin/toggle-stt" ]]; then
        echo "     OR: toggle-stt"
    fi
    echo ""
    echo -e "${GREEN}   • Direct execution:${NC}"
    echo "     cd $INSTALL_DIR && uv run main.py"
    echo ""
    echo -e "${BLUE}3. How it works:${NC}"
    echo "   • First run of toggle script: starts speech-to-text"
    echo "   • Second run: stops the application"
    echo "   • Speaks into microphone → text appears where you type"
    echo "   • Logs saved to: /tmp/stt_typer.log"
    echo ""
    echo -e "${BLUE}4. System Requirements:${NC}"
    echo "   • Working microphone with system permissions"
    echo "   • AssemblyAI API key (free tier available)"
    echo ""
    echo -e "${BLUE}5. Session Type:${NC}"
    if [[ "$SESSION_TYPE" == "wayland" ]]; then
        echo "   • Detected: Wayland (main.py configured for Wayland)"
    elif [[ "$SESSION_TYPE" == "x11" ]]; then
        echo "   • Detected: X11 (main.py configured for X11)"
    else
        echo "   • Detected: Unknown (defaulted to Wayland configuration)"
    fi
    echo "   • To switch session types, re-run: ./install.sh"
    echo ""
    echo -e "${YELLOW}💡 TIP: Add toggle_stt.sh to keyboard shortcuts for quick access!${NC}"
    echo ""
    
    if [[ ! -f "$INSTALL_DIR/.env" ]] || grep -q "your_api_key_here" "$INSTALL_DIR/.env"; then
        echo -e "${RED}⚠️  IMPORTANT: Don't forget to set your API key in .env file!${NC}"
        echo ""
    fi
}

# Main installation flow
main() {
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║            🎤 STT Typer Unified Installation 🎤               ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    detect_os
    detect_session_type
    install_system_deps
    install_uv
    setup_project
    install_python_deps
    setup_env
    setup_session_files
    setup_toggle_script
    setup_global_access
    show_usage

    print_success "Installation completed successfully!"
}

# Run main function
main "$@"
