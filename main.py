import logging
import os
import signal
import subprocess
import sys
import wave
import pyaudio
import threading
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def feedback(event: str, message: str = ""):
    """Provide audio and visual feedback to user.
    
    Args:
        event: One of 'start', 'stop', 'done', 'error'
        message: Optional message to display in notification
    """
    notifications = {
        "start": ("🎙️ Recording Started", "Speak now...", "audio-input-microphone", "device-added"),
        "stop": ("⏹️ Recording Stopped", "Transcribing...", "audio-x-generic", "device-removed"),
        "done": ("✅ Text Typed", message[:100] if message else "Done!", "dialog-ok", "message-new-instant"),
        "error": ("❌ Error", message or "Something went wrong", "dialog-error", "dialog-error"),
    }
    
    title, body, icon, sound = notifications.get(event, ("STT Typer", message, "dialog-information", "bell"))
    
    # Visual notification via notify-send
    try:
        subprocess.Popen(
            ["notify-send", "-i", icon, "-t", "2000", title, body],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        pass  # notify-send not installed, skip silently
    
    # Audio feedback via canberra-gtk-play (uses system sound theme)
    try:
        subprocess.Popen(
            ["canberra-gtk-play", "-i", sound],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        pass  # canberra-gtk-play not installed, skip silently


api_key = os.getenv("GOOGLE_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
AUDIO_FILE = "/tmp/stt_recording.wav"

# Global variables for recording control
recording = False
record_thread = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global recording
    recording = False
    feedback("stop")

def cleanup_audio_file():
    """Remove temporary audio file"""
    try:
        if os.path.exists(AUDIO_FILE):
            os.remove(AUDIO_FILE)
    except Exception as e:
        logger.error(f"Error cleaning up audio file: {e}")

def record_audio():
    """Record audio continuously until stopped"""
    global recording
    
    audio = pyaudio.PyAudio()
    
    try:
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=1024
        )
        
        frames = []
        
        while recording:
            data = stream.read(1024)
            frames.append(data)
        
        # Save recorded audio to file
        with wave.open(AUDIO_FILE, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        
    except Exception as e:
        logger.error(f"Error during recording: {e}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        audio.terminate()

def type_text_uinput(text):
    """Type text using evdev/uinput (works on Wayland)"""
    try:
        from evdev import UInput, ecodes as e
        
        # Key mapping for common characters
        KEY_MAP = {
            'a': e.KEY_A, 'b': e.KEY_B, 'c': e.KEY_C, 'd': e.KEY_D, 'e': e.KEY_E,
            'f': e.KEY_F, 'g': e.KEY_G, 'h': e.KEY_H, 'i': e.KEY_I, 'j': e.KEY_J,
            'k': e.KEY_K, 'l': e.KEY_L, 'm': e.KEY_M, 'n': e.KEY_N, 'o': e.KEY_O,
            'p': e.KEY_P, 'q': e.KEY_Q, 'r': e.KEY_R, 's': e.KEY_S, 't': e.KEY_T,
            'u': e.KEY_U, 'v': e.KEY_V, 'w': e.KEY_W, 'x': e.KEY_X, 'y': e.KEY_Y,
            'z': e.KEY_Z,
            '0': e.KEY_0, '1': e.KEY_1, '2': e.KEY_2, '3': e.KEY_3, '4': e.KEY_4,
            '5': e.KEY_5, '6': e.KEY_6, '7': e.KEY_7, '8': e.KEY_8, '9': e.KEY_9,
            ' ': e.KEY_SPACE, '.': e.KEY_DOT, ',': e.KEY_COMMA,
            '!': e.KEY_1, '@': e.KEY_2, '#': e.KEY_3, '$': e.KEY_4, '%': e.KEY_5,
            '^': e.KEY_6, '&': e.KEY_7, '*': e.KEY_8, '(': e.KEY_9, ')': e.KEY_0,
            '-': e.KEY_MINUS, '=': e.KEY_EQUAL, '[': e.KEY_LEFTBRACE, ']': e.KEY_RIGHTBRACE,
            ';': e.KEY_SEMICOLON, "'": e.KEY_APOSTROPHE, '\\': e.KEY_BACKSLASH,
            '/': e.KEY_SLASH, '?': e.KEY_SLASH, ':': e.KEY_SEMICOLON,
        }
        
        SHIFT_CHARS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+{}|:"<>?')
        
        ui = UInput()
        time.sleep(0.1)  # Give time for uinput to initialize
        
        for char in text:
            lower_char = char.lower()
            need_shift = char in SHIFT_CHARS
            
            key = KEY_MAP.get(lower_char)
            if not key:
                continue
            
            # Press shift if needed
            if need_shift:
                ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
                ui.syn()
            
            # Press and release the key
            ui.write(e.EV_KEY, key, 1)  # Key down
            ui.syn()
            ui.write(e.EV_KEY, key, 0)  # Key up
            ui.syn()
            
            # Release shift if it was pressed
            if need_shift:
                ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
                ui.syn()
            
            time.sleep(0.01)  # Small delay between characters
        
        ui.close()
        return True
        
    except ImportError:
        logger.error("evdev not installed. Install with: pip install evdev --break-system-packages")
        return False
    except PermissionError:
        logger.error("Permission denied for /dev/uinput. Run: sudo chmod 666 /dev/uinput")
        return False
    except Exception as e:
        logger.error(f"uinput error: {e}")
        return False

def type_text_wayland(text):
    """Type text using Wayland-compatible methods with fallbacks"""
    
    # Method 1: Try uinput (most reliable for Wayland)
    if type_text_uinput(text):
        return True
    
    # Method 2: Try wtype
    try:
        result = subprocess.run(
            ['wtype', text],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Method 3: Try ydotool
    try:
        result = subprocess.run(
            ['ydotool', 'type', text],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Method 4: Try wl-clipboard + paste
    try:
        subprocess.run(
            ['wl-copy'],
            input=text.encode(),
            check=True,
            timeout=2
        )
        subprocess.run(
            ['wtype', '-M', 'ctrl', '-P', 'v', '-m', 'ctrl'],
            timeout=2
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # If all methods fail
    logger.error("No typing method worked. Please ensure /dev/uinput has permissions: sudo chmod 666 /dev/uinput")
    feedback("error", "Typing failed. Check uinput permissions.")
    return False

def transcribe_audio():
    """Send audio file to Google Gemini for transcription"""
    try:
        if not os.path.exists(AUDIO_FILE):
            return
        
        client = genai.Client(api_key=api_key)
        
        myfile = client.files.upload(file=AUDIO_FILE)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=["Generate a transcript of the speech. Do not include any other text. Output only in grammatically correct english. IF YOU HEAR ANYTHING ELSE THAN ENGLISH, TRANSLATE IT TO ENGLISH.", myfile]
        )
        
        if response.text:
            # Strip any trailing whitespace/newlines that might cause Enter to be pressed
            clean_text = response.text.strip()
            
            # Use Wayland-compatible typing
            if type_text_wayland(clean_text):
                feedback("done", clean_text)
            else:
                feedback("error", "Failed to type text")
        else:
            feedback("error", "No transcription received")
            
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        feedback("error", str(e))


def main():
    global recording, record_thread
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if not api_key:
        sys.exit(1)
    
    # Clean up any existing audio file
    cleanup_audio_file()
    
    # Start recording
    recording = True
    record_thread = threading.Thread(target=record_audio)
    record_thread.start()
    feedback("start")
    
    # Wait for user to stop recording (Ctrl+C will set recording to False)
    record_thread.join()
        
    # Transcribe the recorded audio
    if os.path.exists(AUDIO_FILE):
        transcribe_audio()
        
    cleanup_audio_file()


if __name__ == "__main__":
    main()
