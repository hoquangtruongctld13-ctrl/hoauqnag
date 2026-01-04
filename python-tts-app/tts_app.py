#!/usr/bin/env python3
"""
Python Desktop GUI Text-to-Speech Application
==============================================

Ứng dụng này mô phỏng chức năng TTS từ mã nguồn free-tts-main,
sử dụng Google Labs Little Language Lessons API.

Cơ chế hoạt động:
1. Người dùng nhập văn bản và chọn ngôn ngữ/giọng nói
2. Ứng dụng gửi POST request đến Google Labs API
3. API trả về audio dạng base64
4. Ứng dụng decode và lưu file MP3 để phát

API Endpoint: https://labs.google/lll/api/text-to-speech
Voice Name Format: {languageCode}-Chirp3-HD-{voiceName}
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import base64
import os
import tempfile
import time
from typing import Optional

# Try to import required libraries
try:
    import requests
except ImportError:
    requests = None

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None

# Initialize pygame mixer lazily when needed
_pygame_initialized = False

def _init_pygame():
    """Initialize pygame mixer lazily to avoid issues on systems without audio"""
    global _pygame_initialized
    if PYGAME_AVAILABLE and not _pygame_initialized:
        try:
            pygame.mixer.init()
            _pygame_initialized = True
        except Exception:
            pass


# Constants - matching the original source code
GOOGLE_LABS_API_URL = "https://labs.google/lll/api/text-to-speech"
MAX_CHARACTERS = 600
API_TIMEOUT = 30  # seconds - reasonable timeout for user experience

# Languages - from text-to-speech.tsx
LANGUAGES = [
    ("en-US", "English (US)"),
    ("en-GB", "English (UK)"),
    ("vi-VN", "Vietnamese (Vietnam)"),
    ("es-ES", "Spanish (Spain)"),
    ("fr-FR", "French (France)"),
    ("de-DE", "German (Germany)"),
    ("it-IT", "Italian (Italy)"),
]

# Voice Styles - from text-to-speech.tsx
VOICE_STYLES = [
    ("Puck", "Puck"),
    ("Charon", "Charon"),
    ("Kore", "Kore"),
    ("Fenrir", "Fenrir"),
    ("Aoede", "Aoede"),
    ("Leda", "Leda"),
    ("Orus", "Orus"),
    ("Zephyr", "Zephyr"),
]

# Quick Presets - from text-to-speech.tsx
QUICK_PRESETS = [
    {
        "label": "Product teaser",
        "description": "Warm & inviting",
        "text": "Introducing Luma Desk – the adjustable workstation that remembers your perfect posture. Tap the preset, stand tall, and keep your focus locked on what matters most.",
        "voice": "Aoede",
        "language": "en-US",
    },
    {
        "label": "Learning module",
        "description": "Crisp & clear",
        "text": "In this lesson, we will explore the building blocks of narrative writing. You'll learn how conflict drives a story forward and how to balance pacing with vivid detail.",
        "voice": "Orus",
        "language": "en-US",
    },
    {
        "label": "Customer support",
        "description": "Friendly & reassuring",
        "text": "Thanks for reaching out! I can see that your order shipped this morning. I'll keep an eye on tracking and send an update as soon as it lands on your doorstep.",
        "voice": "Leda",
        "language": "en-US",
    },
    {
        "label": "Global greeting",
        "description": "en Español",
        "text": "Bienvenido a nuestra demo interactiva. Explora las funciones, escucha las voces disponibles y comparte tus comentarios con el equipo en cualquier momento.",
        "voice": "Zephyr",
        "language": "es-ES",
    },
    {
        "label": "Tiếng Việt",
        "description": "Vietnamese demo",
        "text": "Xin chào! Đây là ứng dụng chuyển văn bản thành giọng nói. Hãy nhập văn bản của bạn và chọn giọng đọc phù hợp.",
        "voice": "Orus",
        "language": "vi-VN",
    },
]


class TextToSpeechApp:
    """
    Main Application Class for Text-to-Speech GUI
    
    This class implements the same functionality as the Next.js web app:
    - Text input with character limit
    - Language selection
    - Voice style selection
    - Generate speech via Google Labs API
    - Play and download audio
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Python Text-to-Speech App")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Variables
        self.text_var = tk.StringVar()
        self.language_var = tk.StringVar(value="en-US")
        self.voice_var = tk.StringVar(value="Orus")
        self.is_generating = False
        self.current_audio_path: Optional[str] = None
        self.temp_dir = tempfile.mkdtemp()
        
        # Configure style
        self.setup_styles()
        
        # Build UI
        self.create_widgets()
        
        # Check dependencies
        self.check_dependencies()
        
    def setup_styles(self):
        """Configure ttk styles for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Helvetica', 18, 'bold'))
        style.configure('Subtitle.TLabel', font=('Helvetica', 10), foreground='gray')
        style.configure('Section.TLabel', font=('Helvetica', 11, 'bold'))
        style.configure('Counter.TLabel', font=('Helvetica', 9))
        
        # Configure buttons
        style.configure('Generate.TButton', font=('Helvetica', 10, 'bold'))
        style.configure('Preset.TButton', font=('Helvetica', 9))
        
    def create_widgets(self):
        """Create all UI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(main_frame)
        
        # Script input section
        self.create_script_section(main_frame)
        
        # Controls section (Language & Voice)
        self.create_controls_section(main_frame)
        
        # Preview and Actions section
        self.create_preview_section(main_frame)
        
        # Footer with status
        self.create_footer(main_frame)
        
    def create_header(self, parent):
        """Create header with title and description"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(
            header_frame,
            text="🎙️ Python Text-to-Speech Lab",
            style='Title.TLabel'
        )
        title_label.pack(anchor=tk.W)
        
        desc_label = ttk.Label(
            header_frame,
            text="Chuyển đổi văn bản thành giọng nói tự nhiên sử dụng Google Labs API.\n"
                 "Paste your script, choose a voice vibe, and generate natural audio.",
            style='Subtitle.TLabel',
            wraplength=800
        )
        desc_label.pack(anchor=tk.W, pady=(5, 0))
        
    def create_script_section(self, parent):
        """Create script input section with presets"""
        script_frame = ttk.LabelFrame(parent, text="📝 Script", padding="10")
        script_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Character counter
        counter_frame = ttk.Frame(script_frame)
        counter_frame.pack(fill=tk.X)
        
        self.char_counter = ttk.Label(
            counter_frame,
            text=f"0 / {MAX_CHARACTERS} chars",
            style='Counter.TLabel'
        )
        self.char_counter.pack(side=tk.RIGHT)
        
        # Text area
        text_frame = ttk.Frame(script_frame)
        text_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.text_input = tk.Text(
            text_frame,
            height=8,
            wrap=tk.WORD,
            font=('Helvetica', 11)
        )
        self.text_input.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_input.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_input.configure(yscrollcommand=scrollbar.set)
        
        # Bind text change event
        self.text_input.bind('<KeyRelease>', self.on_text_change)
        
        # Quick presets
        preset_label = ttk.Label(script_frame, text="Quick Presets:", style='Section.TLabel')
        preset_label.pack(anchor=tk.W, pady=(5, 5))
        
        preset_frame = ttk.Frame(script_frame)
        preset_frame.pack(fill=tk.X)
        
        for preset in QUICK_PRESETS:
            btn = ttk.Button(
                preset_frame,
                text=f"{preset['label']}",
                style='Preset.TButton',
                command=lambda p=preset: self.apply_preset(p)
            )
            btn.pack(side=tk.LEFT, padx=(0, 5), pady=2)
            
    def create_controls_section(self, parent):
        """Create voice control section"""
        controls_frame = ttk.LabelFrame(parent, text="🎛️ Voice Control", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Two columns for Language and Voice
        left_frame = ttk.Frame(controls_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(controls_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Language selection
        lang_label = ttk.Label(left_frame, text="Language:", style='Section.TLabel')
        lang_label.pack(anchor=tk.W)
        
        lang_desc = ttk.Label(
            left_frame,
            text="Align the delivery with your audience.",
            style='Subtitle.TLabel'
        )
        lang_desc.pack(anchor=tk.W, pady=(0, 5))
        
        self.language_combo = ttk.Combobox(
            left_frame,
            textvariable=self.language_var,
            values=[f"{name} ({code})" for code, name in LANGUAGES],
            state='readonly',
            width=30
        )
        self.language_combo.pack(fill=tk.X)
        self.language_combo.set("English (US) (en-US)")
        self.language_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        
        # Voice selection
        voice_label = ttk.Label(right_frame, text="Voice:", style='Section.TLabel')
        voice_label.pack(anchor=tk.W)
        
        voice_desc = ttk.Label(
            right_frame,
            text="Choose the personality of the narrator.",
            style='Subtitle.TLabel'
        )
        voice_desc.pack(anchor=tk.W, pady=(0, 5))
        
        self.voice_combo = ttk.Combobox(
            right_frame,
            textvariable=self.voice_var,
            values=[name for _, name in VOICE_STYLES],
            state='readonly',
            width=30
        )
        self.voice_combo.pack(fill=tk.X)
        self.voice_combo.set("Orus")
        
    def create_preview_section(self, parent):
        """Create preview and action buttons section"""
        preview_frame = ttk.LabelFrame(parent, text="🔊 Preview & Actions", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Status label
        self.status_label = ttk.Label(
            preview_frame,
            text="No audio yet. Generate speech to hear your script.",
            style='Subtitle.TLabel'
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Progress bar (hidden initially)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            preview_frame,
            mode='indeterminate',
            variable=self.progress_var
        )
        
        # Action buttons
        button_frame = ttk.Frame(preview_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.generate_btn = ttk.Button(
            button_frame,
            text="▶️ Generate Speech",
            style='Generate.TButton',
            command=self.generate_speech
        )
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.play_btn = ttk.Button(
            button_frame,
            text="🔊 Play",
            command=self.play_audio,
            state=tk.DISABLED
        )
        self.play_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="⏹️ Stop",
            command=self.stop_audio,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.download_btn = ttk.Button(
            button_frame,
            text="💾 Download MP3",
            command=self.download_audio,
            state=tk.DISABLED
        )
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_btn = ttk.Button(
            button_frame,
            text="🔄 Reset",
            command=self.reset_session
        )
        self.reset_btn.pack(side=tk.RIGHT)
        
    def create_footer(self, parent):
        """Create footer with API info"""
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(fill=tk.X, pady=(0, 0))
        
        info_label = ttk.Label(
            footer_frame,
            text="Powered by Google Labs Little Language Lessons API (https://labs.google/lll/en)",
            style='Subtitle.TLabel'
        )
        info_label.pack(anchor=tk.W)
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        missing = []
        if requests is None:
            missing.append("requests")
        if not PYGAME_AVAILABLE:
            missing.append("pygame")
            
        if missing:
            msg = f"Missing dependencies: {', '.join(missing)}\n\n"
            msg += "Install with:\n"
            msg += f"pip install {' '.join(missing)}"
            messagebox.showwarning("Missing Dependencies", msg)
            
    def on_text_change(self, event=None):
        """Handle text change event - update character counter"""
        text = self.text_input.get("1.0", tk.END).strip()
        char_count = len(text)
        
        # Enforce character limit with notification
        if char_count > MAX_CHARACTERS:
            # Truncate text and notify user
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", text[:MAX_CHARACTERS])
            char_count = MAX_CHARACTERS
            self.status_label.config(text=f"⚠️ Text truncated to {MAX_CHARACTERS} characters limit.")
            
        # Update counter with color indication
        self.char_counter.config(text=f"{char_count} / {MAX_CHARACTERS} chars")
        
        if char_count >= MAX_CHARACTERS - 40:
            self.char_counter.config(foreground='red')
        else:
            self.char_counter.config(foreground='gray')
            
    def on_language_change(self, event=None):
        """Handle language selection change"""
        selected = self.language_combo.get()
        # Extract language code from selection
        for code, name in LANGUAGES:
            if f"{name} ({code})" == selected:
                self.language_var.set(code)
                break
                
    def apply_preset(self, preset: dict):
        """Apply a quick preset"""
        # Set text
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert("1.0", preset['text'][:MAX_CHARACTERS])
        
        # Set language
        lang_code = preset.get('language', 'en-US')
        for code, name in LANGUAGES:
            if code == lang_code:
                self.language_combo.set(f"{name} ({code})")
                self.language_var.set(code)
                break
                
        # Set voice
        voice = preset.get('voice', 'Orus')
        self.voice_combo.set(voice)
        self.voice_var.set(voice)
        
        # Update counter
        self.on_text_change()
        
        # Clear audio
        self.current_audio_path = None
        self.update_button_states()
        self.status_label.config(text="Preset loaded. Click Generate to create speech.")
        
    def get_voice_name(self) -> str:
        """
        Construct voice name in the format expected by Google Labs API
        
        Format: {languageCode}-Chirp3-HD-{voiceName}
        Example: en-US-Chirp3-HD-Orus
        
        This matches the logic in lib/google-lll-tts.ts:
        voiceName: languageCode + "-Chirp3-HD-" + voiceName
        """
        language_code = self.language_var.get()
        voice_name = self.voice_var.get()
        return f"{language_code}-Chirp3-HD-{voice_name}"
        
    def generate_speech(self):
        """
        Generate speech using Google Labs API
        
        This method implements the same logic as the Next.js API route:
        1. Send POST request to https://labs.google/lll/api/text-to-speech
        2. With JSON body: {text, languageCode, voiceName}
        3. Receive base64 encoded audio
        4. Decode and save as MP3
        """
        if requests is None:
            messagebox.showerror(
                "Error",
                "requests library is required.\nInstall with: pip install requests"
            )
            return
            
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text first.")
            return
            
        if self.is_generating:
            return
            
        self.is_generating = True
        self.generate_btn.config(state=tk.DISABLED, text="⏳ Generating...")
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        self.progress_bar.start(10)
        self.status_label.config(text="Generating speech... Please wait.")
        
        # Run in thread to prevent UI freeze
        thread = threading.Thread(target=self._generate_speech_thread, args=(text,))
        thread.daemon = True
        thread.start()
        
    def _generate_speech_thread(self, text: str):
        """Background thread for speech generation"""
        try:
            # Prepare request data (matching route.ts logic)
            language_code = self.language_var.get()
            voice_name = self.get_voice_name()
            
            payload = {
                "text": text,
                "languageCode": language_code,
                "voiceName": voice_name
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Make API request (same as route.ts)
            response = requests.post(
                GOOGLE_LABS_API_URL,
                headers=headers,
                json=payload,
                timeout=API_TIMEOUT
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
                
            # Get base64 audio data
            # The API returns the base64 string directly as JSON
            data_base64 = response.json()
            
            # Decode base64 to audio bytes
            if isinstance(data_base64, str):
                audio_bytes = base64.b64decode(data_base64)
            else:
                raise Exception("Unexpected response format from API")
                
            # Save to temp file with timestamp for unique filename
            timestamp = int(time.time() * 1000)
            audio_path = os.path.join(self.temp_dir, f"speech_{timestamp}.mp3")
            with open(audio_path, 'wb') as f:
                f.write(audio_bytes)
                
            self.current_audio_path = audio_path
            
            # Update UI on main thread
            self.root.after(0, self._on_generation_success)
            
        except Exception as e:
            self.root.after(0, lambda: self._on_generation_error(str(e)))
            
    def _on_generation_success(self):
        """Handle successful speech generation"""
        self.is_generating = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.generate_btn.config(state=tk.NORMAL, text="▶️ Generate Speech")
        self.status_label.config(text="✅ Audio generated successfully! Click Play to listen.")
        self.update_button_states()
        
    def _on_generation_error(self, error_msg: str):
        """Handle speech generation error"""
        self.is_generating = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.generate_btn.config(state=tk.NORMAL, text="▶️ Generate Speech")
        self.status_label.config(text=f"❌ Error: {error_msg[:50]}...")
        messagebox.showerror("Generation Error", error_msg)
        
    def update_button_states(self):
        """Update button enabled/disabled states"""
        has_audio = self.current_audio_path is not None and os.path.exists(self.current_audio_path)
        
        if has_audio:
            self.play_btn.config(state=tk.NORMAL)
            self.download_btn.config(state=tk.NORMAL)
            if PYGAME_AVAILABLE:
                self.stop_btn.config(state=tk.NORMAL)
        else:
            self.play_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            self.download_btn.config(state=tk.DISABLED)
            
    def play_audio(self):
        """Play the generated audio"""
        if not self.current_audio_path or not os.path.exists(self.current_audio_path):
            messagebox.showwarning("Warning", "No audio to play. Generate speech first.")
            return
            
        if not PYGAME_AVAILABLE:
            messagebox.showinfo(
                "Info",
                f"Audio saved to: {self.current_audio_path}\n\n"
                "Install pygame to enable playback:\npip install pygame"
            )
            return
            
        try:
            # Initialize pygame mixer lazily
            _init_pygame()
            pygame.mixer.music.load(self.current_audio_path)
            pygame.mixer.music.play()
            self.status_label.config(text="🔊 Playing audio...")
        except Exception as e:
            messagebox.showerror("Playback Error", str(e))
            
    def stop_audio(self):
        """Stop audio playback"""
        if PYGAME_AVAILABLE:
            pygame.mixer.music.stop()
            self.status_label.config(text="⏹️ Playback stopped.")
            
    def download_audio(self):
        """Save audio to user-selected location"""
        if not self.current_audio_path or not os.path.exists(self.current_audio_path):
            messagebox.showwarning("Warning", "No audio to download. Generate speech first.")
            return
            
        # Generate user-friendly filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_filename = f"generated_speech_{timestamp}.mp3"
        
        # Open save dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy2(self.current_audio_path, file_path)
                messagebox.showinfo("Success", f"Audio saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))
                
    def reset_session(self):
        """Reset all inputs and audio"""
        # Stop any playing audio
        if PYGAME_AVAILABLE:
            pygame.mixer.music.stop()
            
        # Clear text
        self.text_input.delete("1.0", tk.END)
        
        # Reset selections
        self.language_combo.set("English (US) (en-US)")
        self.language_var.set("en-US")
        self.voice_combo.set("Orus")
        self.voice_var.set("Orus")
        
        # Clear audio
        self.current_audio_path = None
        
        # Update UI
        self.on_text_change()
        self.update_button_states()
        self.status_label.config(text="Session reset. Enter new text to generate speech.")
        
    def cleanup(self):
        """Cleanup temp files on exit"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception:
            pass
            
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """Handle window close event"""
        self.cleanup()
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = TextToSpeechApp(root)
    app.run()


if __name__ == "__main__":
    main()
