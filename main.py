import logging
import os
import random
import signal
import subprocess
import sys
import time
import wave
from typing import List, Optional
import pyaudio
import threading
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Configure logger before any class that uses it
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages multiple API keys with rotation and retry logic."""

    def __init__(self):
        self.api_keys: List[str] = []
        self.failed_keys: set = set()
        self.current_key: Optional[str] = None
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from environment variables."""
        # Support multiple keys: GOOGLE_API_KEY, GOOGLE_API_KEY_2, GOOGLE_API_KEY_3, etc.
        primary_key = os.getenv("GOOGLE_API_KEY")
        if primary_key:
            self.api_keys.append(primary_key)

        # Load additional keys
        index = 2
        while True:
            key = os.getenv(f"GOOGLE_API_KEY_{index}")
            if not key:
                break
            if key not in self.api_keys:
                self.api_keys.append(key)
            index += 1

        # Also support comma-separated list in GOOGLE_API_KEYS (plural)
        keys_list = os.getenv("GOOGLE_API_KEYS", "")
        if keys_list:
            for key in keys_list.split(','):
                key = key.strip()
                if key and key not in self.api_keys:
                    self.api_keys.append(key)

        logger.info(f"Loaded {len(self.api_keys)} API key(s)")

    def get_key(self) -> Optional[str]:
        """Get a random API key that hasn't failed recently."""
        if not self.api_keys:
            return None

        # Filter out recently failed keys
        available_keys = [k for k in self.api_keys if k not in self.failed_keys]

        if not available_keys:
            # All keys failed, reset and try again
            logger.warning("All API keys failed recently, resetting failed status")
            self.failed_keys.clear()
            available_keys = self.api_keys

        # Random selection for load balancing
        self.current_key = random.choice(available_keys)
        return self.current_key

    def mark_failed(self, key: str):
        """Mark a key as failed."""
        if key in self.api_keys:
            self.failed_keys.add(key)
            logger.warning(f"Marked API key as failed ({len(self.failed_keys)}/{len(self.api_keys)} failed)")

    def mark_success(self, key: str):
        """Mark a key as successful (remove from failed set)."""
        self.failed_keys.discard(key)

    def get_remaining_count(self) -> int:
        """Get count of available (non-failed) keys."""
        return len([k for k in self.api_keys if k not in self.failed_keys])


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


# Initialize API key manager
api_key_manager = APIKeyManager()

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

        # Comprehensive key mapping for all common characters
        KEY_MAP = {
            # Letters
            'a': e.KEY_A, 'b': e.KEY_B, 'c': e.KEY_C, 'd': e.KEY_D, 'e': e.KEY_E,
            'f': e.KEY_F, 'g': e.KEY_G, 'h': e.KEY_H, 'i': e.KEY_I, 'j': e.KEY_J,
            'k': e.KEY_K, 'l': e.KEY_L, 'm': e.KEY_M, 'n': e.KEY_N, 'o': e.KEY_O,
            'p': e.KEY_P, 'q': e.KEY_Q, 'r': e.KEY_R, 's': e.KEY_S, 't': e.KEY_T,
            'u': e.KEY_U, 'v': e.KEY_V, 'w': e.KEY_W, 'x': e.KEY_X, 'y': e.KEY_Y,
            'z': e.KEY_Z,
            # Numbers
            '0': e.KEY_0, '1': e.KEY_1, '2': e.KEY_2, '3': e.KEY_3, '4': e.KEY_4,
            '5': e.KEY_5, '6': e.KEY_6, '7': e.KEY_7, '8': e.KEY_8, '9': e.KEY_9,
            # Basic punctuation (no shift)
            ' ': e.KEY_SPACE, '.': e.KEY_DOT, ',': e.KEY_COMMA,
            '-': e.KEY_MINUS, '=': e.KEY_EQUAL,
            '[': e.KEY_LEFTBRACE, ']': e.KEY_RIGHTBRACE,
            ';': e.KEY_SEMICOLON, "'": e.KEY_APOSTROPHE,
            '\\': e.KEY_BACKSLASH, '/': e.KEY_SLASH,
            '`': e.KEY_GRAVE,
        }

        # Characters that require shift key (base key mapping)
        SHIFT_KEY_MAP = {
            '!': e.KEY_1, '@': e.KEY_2, '#': e.KEY_3, '$': e.KEY_4, '%': e.KEY_5,
            '^': e.KEY_6, '&': e.KEY_7, '*': e.KEY_8, '(': e.KEY_9, ')': e.KEY_0,
            '_': e.KEY_MINUS, '+': e.KEY_EQUAL,
            '{': e.KEY_LEFTBRACE, '}': e.KEY_RIGHTBRACE,
            ':': e.KEY_SEMICOLON, '"': e.KEY_APOSTROPHE,
            '|': e.KEY_BACKSLASH, '?': e.KEY_SLASH,
            '~': e.KEY_GRAVE,
            '<': e.KEY_COMMA, '>': e.KEY_DOT,
        }

        SHIFT_CHARS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+{}|:"<>?')

        ui = UInput()
        time.sleep(0.1)  # Give time for uinput to initialize

        typed_count = 0
        skipped_count = 0

        for char in text:
            lower_char = char.lower()
            need_shift = char in SHIFT_CHARS

            # Check shift characters first
            if char in SHIFT_KEY_MAP:
                key = SHIFT_KEY_MAP[char]
                need_shift = True
            else:
                key = KEY_MAP.get(lower_char)
                if not key:
                    skipped_count += 1
                    logger.debug(f"Skipped character: {char!r} (ord: {ord(char)})")
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

            typed_count += 1
            time.sleep(0.01)  # Small delay between characters

        ui.close()

        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} unsupported characters, typed {typed_count}")

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
    """Send audio file to Google Gemini for transcription with API key rotation and retry."""
    if not os.path.exists(AUDIO_FILE):
        return

    if api_key_manager.get_remaining_count() == 0:
        feedback("error", "All API keys failed. Please check your configuration.")
        logger.error("All API keys have failed. Cannot proceed with transcription.")
        return

    # Retry with different API keys on failure
    max_retries = api_key_manager.get_remaining_count()
    last_error = None

    for attempt in range(max_retries):
        current_key = api_key_manager.get_key()
        if not current_key:
            logger.error("No API key available")
            feedback("error", "No API key configured")
            return

        logger.info(f"Transcription attempt {attempt + 1}/{max_retries}")

        try:
            client = genai.Client(api_key=current_key)

            myfile = client.files.upload(file=AUDIO_FILE)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=["Generate a transcript of the speech. Do not include any other text. Output only in grammatically correct english. IF YOU HEAR ANYTHING ELSE THAN ENGLISH, TRANSLATE IT TO ENGLISH.", myfile]
            )

            # Mark the key as successful
            api_key_manager.mark_success(current_key)

            if response.text:
                # Strip any trailing whitespace/newlines that might cause Enter to be pressed
                clean_text = response.text.strip()

                logger.info(f"Transcription successful, text length: {len(clean_text)} characters")

                # Use Wayland-compatible typing
                if type_text_wayland(clean_text):
                    feedback("done", clean_text)
                else:
                    feedback("error", "Failed to type text")
            else:
                feedback("error", "No transcription received")
            return  # Success, exit the retry loop

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            # Check for rate limit or server errors (5xx, 502, 529, etc.)
            is_retryable = any(code in error_str for code in ['500', '502', '503', '504', '529', '599', 'rate limit', 'quota', 'overloaded', 'timeout'])

            if is_retryable:
                api_key_manager.mark_failed(current_key)
                remaining = api_key_manager.get_remaining_count()
                logger.warning(f"API error (retryable): {e}. Remaining keys: {remaining}")

                if remaining > 0:
                    time.sleep(0.5)  # Brief pause before retrying with next key
                    continue
                else:
                    feedback("error", "All API keys failed or rate limited")
                    break
            else:
                # Non-retryable error (auth, invalid request, etc.)
                logger.error(f"Non-retryable API error: {e}")
                feedback("error", f"API Error: {str(e)[:100]}")
                return

    # All retries exhausted
    logger.error(f"Transcription failed after {max_retries} attempts. Last error: {last_error}")
    feedback("error", f"Failed after {max_retries} attempts")


def main():
    global recording, record_thread

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Check if at least one API key is configured
    if api_key_manager.get_remaining_count() == 0:
        logger.error("No API key configured. Please set GOOGLE_API_KEY in .env file")
        feedback("error", "No API key configured")
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
