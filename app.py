import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import time
import shutil

# Import custom modules
from config.settings import Settings
from audio.recorder import AudioRecorder
from audio.transcriber import Transcriber
from api.api_handler import APIHandler
from utils.ollama_manager import OllamaManager
from ui.recording_tab import RecordingTab
from ui.settings_tab import SettingsTab

class SpeechToLatexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech-to-LaTeX Transcription Tool")
        self.root.geometry("1000x800")
        
        # Load settings
        self.settings = Settings()
        
        # Initialize components
        self.recorder = AudioRecorder(sample_rate=self.settings.sample_rate)
        self.transcriber = Transcriber(model_name=self.settings.whisper_model_name)
        self.api_handler = APIHandler(self.settings)
        self.ollama_manager = OllamaManager(base_url=self.settings.ollama_base_url)
        
        # Set up variables
        self.is_recording = False
        self.audio_thread = None
        self.timer_id = None
        self.ollama_models = []
        
        # Create StringVar for UI components
        self.status_var = tk.StringVar(value="Ready")
        self.selected_prompt_mode = tk.StringVar(value=self.settings.selected_prompt_mode)
        
        # Create application folders
        os.makedirs(self.settings.app_dir, exist_ok=True)
        
        # Create GUI
        self.create_gui()
        
        # Check Ollama status
        self.check_ollama_status()
        
        # Auto-start Ollama if enabled
        if self.settings.auto_start_ollama:
            self.start_ollama()
        
        # Load available Ollama models (on a delay to allow server to start)
        self.root.after(3000, self.load_ollama_models)
        
        # Load whisper model in a separate thread to avoid blocking the GUI
        self.root.after(500, lambda: threading.Thread(
            target=self.load_whisper_model, 
            args=(self.settings.whisper_model_name,), 
            daemon=True
        ).start())
        
        # Register window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_gui(self):
        # Create a notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Recording tab
        self.recording_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.recording_frame, text="Recording")
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        
        # Setup recording tab
        self.recording_tab = RecordingTab(self.recording_frame, self)
        
        # Setup settings tab
        self.settings_tab = SettingsTab(self.settings_frame, self)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Audio Recording Functions
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.is_recording = True
        self.recording_tab.update_recording_button(True)
        self.recording_tab.update_transcribe_button(tk.DISABLED)
        
        self.status_var.set("Recording...")
        
        # Start recording using the recorder
        self.recorder.start_recording()
    
    def stop_recording(self):
        self.is_recording = False
        self.recording_tab.update_recording_button(False)
        self.status_var.set("Recording stopping...")
        
        # Stop recording
        self.recorder.stop_recording()
        
        # Periodically check if recording has stopped
        self.root.after(100, self._check_recording_stopped)
    
    def _check_recording_stopped(self):
        """Periodically check if recording has stopped and update UI accordingly"""
        if hasattr(self.recorder, 'recording_completed') and self.recorder.recording_completed:
            # Recording has completed
            self.status_var.set("Recording stopped")
            
            # Enable the transcribe button if we have audio
            if os.path.exists(self.recorder.temp_audio_file):
                self.recording_tab.update_transcribe_button(tk.NORMAL)
        else:
            # Still waiting for recording to complete
            self.root.after(100, self._check_recording_stopped)
    
    # Whisper Transcription Functions
    def transcribe_audio(self):
        if not os.path.exists(self.recorder.temp_audio_file):
            messagebox.showerror("Error", "No recording found to transcribe")
            return
        
        if self.transcriber.whisper_model is None:
            messagebox.showerror("Error", "Whisper model not loaded yet")
            return
        
        self.status_var.set("Transcribing audio...")
        self.recording_tab.update_progress(0)
        
        # Define callback for transcription updates
        def transcription_callback(success, message, text):
            if success:
                self.recording_tab.set_transcribed_text(text)
                self.recording_tab.update_progress(100)
                self.recording_tab.convert_button.config(state=tk.NORMAL)
                self.status_var.set(message)
            else:
                self.status_var.set(message)
                messagebox.showerror("Transcription Error", message)
        
        # Run transcription asynchronously with callback
        self.transcriber.transcribe_async(transcription_callback)
    
    def load_whisper_model(self, model_name):
        success, message = self.transcriber.load_model(model_name)
        self.root.after(0, lambda: self.status_var.set(message))
        if not success:
            self.root.after(0, lambda: messagebox.showerror("Whisper Error", message))
    
    def change_whisper_model(self, event=None):
        model_name = self.settings_tab.whisper_model_var.get()
        threading.Thread(target=self.load_whisper_model, args=(model_name,), daemon=True).start()
    
    # LaTeX Conversion Functions
    def convert_to_latex(self):
        text = self.recording_tab.get_transcribed_text()
        
        if not text:
            messagebox.showerror("Error", "No text to convert to LaTeX")
            return
        
        # Get the current provider
        provider = self.settings_tab.api_provider_var.get()
        
        # Check provider-specific requirements
        if provider == "Ollama (Local)":
            if not self.ollama_models:
                messagebox.showerror("Error", "No Ollama models available")
                return
            
            model = self.settings_tab.ollama_model_var.get()
            if not model:
                messagebox.showerror("Error", "Please select an Ollama model")
                return
                
            self.status_var.set(f"Converting to LaTeX using Ollama model: {model}...")
        else:
            # Check API key for cloud providers
            api_key = self.settings_tab.api_key_vars[provider].get() if provider in self.settings_tab.api_key_vars else ""
            if not api_key:
                messagebox.showerror("Error", f"No API key configured for {provider}. Please add your API key in the settings.")
                return
                
            self.status_var.set(f"Converting to LaTeX using {provider} API...")
        
        self.recording_tab.update_progress(0)
        
        # Start timer to show elapsed time
        start_time = time.time()
        def update_timer():
            elapsed = int(time.time() - start_time)
            self.recording_tab.update_loading_label(f"Processing... {elapsed}s")
            self.timer_id = self.root.after(1000, update_timer)
        update_timer()
        
        # Define callback for conversion updates
        def conversion_callback(success, message, text, progress=None):
            if success:
                if text is not None:
                    self.recording_tab.set_latex_text(text)
                
                if progress is not None:
                    self.recording_tab.update_progress(progress)
                
                if progress == 100 or "complete" in message.lower():
                    # Conversion complete
                    self.recording_tab.save_button.config(state=tk.NORMAL)
                    self.status_var.set(message)
                    # Stop timer
                    if self.timer_id:
                        self.root.after_cancel(self.timer_id)
                        self.recording_tab.update_loading_label("")
                else:
                    # Still in progress
                    self.status_var.set(message)
            else:
                self.status_var.set(message)
                messagebox.showerror("Conversion Error", message)
                # Stop timer
                if self.timer_id:
                    self.root.after_cancel(self.timer_id)
                    self.recording_tab.update_loading_label("")
        
        # Save current settings to API handler
        self.update_settings_from_ui()
        
        # Run conversion asynchronously with callback
        self.api_handler.convert_text(text, conversion_callback)
    
    def save_latex(self):
        latex_text = self.recording_tab.get_latex_text()
        
        if not latex_text:
            messagebox.showerror("Error", "No LaTeX content to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".tex",
            filetypes=[("LaTeX files", "*.tex"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(latex_text)
                self.status_var.set(f"LaTeX saved to {file_path}")
            except Exception as e:
                self.status_var.set(f"Error saving file: {str(e)}")
                messagebox.showerror("Save Error", str(e))
    
    def clear_all(self):
        self.recording_tab.clear_text_areas()
        self.recording_tab.update_progress(0)
        self.recording_tab.update_transcribe_button(tk.DISABLED)
        self.recording_tab.convert_button.config(state=tk.DISABLED)
        self.recording_tab.save_button.config(state=tk.DISABLED)
        
        # Delete temporary audio file if it exists
        self.recorder.clean_up()
        
        self.status_var.set("Ready")
    
    def import_audio_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.ogg"), ("WAV files", "*.wav"), ("All files", "*.*")]
        )
        
        if file_path:
            # Update sample rate from UI
            self.recorder.sample_rate = self.settings_tab.sample_rate_var.get()
            
            # Import the file
            success, message = self.recorder.import_audio_file(file_path)
            
            if success:
                self.status_var.set(message)
                self.recording_tab.update_transcribe_button(tk.NORMAL)
            else:
                self.status_var.set(message)
                messagebox.showerror("Import Error", message)
    
    # Ollama Management Functions
    def check_ollama_status(self):
        """Check Ollama installation and server status"""
        is_installed = self.ollama_manager.is_ollama_installed()
        is_running = self.ollama_manager.is_ollama_running()
        
        if is_installed:
            if is_running:
                status = "Ollama is installed and running"
            else:
                status = "Ollama is installed but not running"
        else:
            status = "Ollama command not found. Please install Ollama from ollama.ai"
            messagebox.showwarning("Ollama Not Found", 
                                 "The ollama command was not found in your PATH.\n\n"
                                 "Please install Ollama from https://ollama.ai and complete the setup.")
        
        self.status_var.set(status)
        self.settings_tab.update_ollama_status(status)
    
    def start_ollama(self):
        """Start Ollama server"""
        def ollama_callback(success, message, in_progress=False):
            self.status_var.set(message)
            self.settings_tab.update_ollama_status(message)
            
            if success and not in_progress:
                # Load models after successful start
                self.load_ollama_models()
        
        self.ollama_manager.start_ollama(ollama_callback)
    
    def stop_ollama(self):
        """Stop Ollama server"""
        def ollama_callback(success, message):
            self.status_var.set(message)
            self.settings_tab.update_ollama_status(message)
        
        self.ollama_manager.stop_ollama(ollama_callback)
    
    def download_ollama(self):
        """Download and install Ollama"""
        messagebox.showinfo("Ollama Download", 
                         "Please visit https://ollama.ai to download and install Ollama for your platform.")
    
    def load_ollama_models(self):
        """Load available Ollama models"""
        def callback(success, message, models=None):
            self.status_var.set(message)
            
            if success and models:
                self.ollama_models = models
                
                # Populate the model listbox
                self.settings_tab.populate_model_listbox(models)
                
                # Set the first model as default if none is selected and models are available
                if not self.settings_tab.ollama_model_var.get() and models:
                    self.settings_tab.ollama_model_var.set(models[0])
        
        # Update Ollama base URL from settings
        self.ollama_manager.ollama_base_url = self.settings_tab.ollama_url_var.get()
        
        # Load models
        self.ollama_manager.load_ollama_models(callback)
    
    def connect_to_ollama(self):
        """Test connection to Ollama server and refresh models"""
        # Update base URL from UI
        new_url = self.settings_tab.ollama_url_var.get()
        self.ollama_manager.ollama_base_url = new_url
        self.settings.ollama_base_url = new_url
        
        def callback(success, message, models=None):
            self.status_var.set(message)
            
            if not success:
                messagebox.showerror("Connection Error", message)
                
                # If not running, offer to start Ollama
                if "Connection refused" in message:
                    if messagebox.askyesno("Ollama Not Running", 
                                         "Ollama server is not running. Would you like to start it?"):
                        self.start_ollama()
            elif models:
                self.ollama_models = models
                self.settings_tab.populate_model_listbox(models)
        
        self.ollama_manager.load_ollama_models(callback)
    
    def refresh_models(self):
        """Refresh the list of available Ollama models"""
        self.load_ollama_models()
    
    def select_model(self):
        """Set the selected model as the active model"""
        selected_model = self.settings_tab.get_model_selection()
        
        if not selected_model:
            messagebox.showinfo("Model Selection", "Please select a model first")
            return
        
        self.settings_tab.ollama_model_var.set(selected_model)
        messagebox.showinfo("Model Selection", f"Model '{selected_model}' selected for use")
    
    def download_model(self):
        """Download a new Ollama model"""
        # Get the model name from the settings tab
        model = self.settings_tab.get_download_model()
        
        if not model:
            messagebox.showerror("Download Error", "Please select or enter a model name")
            return
        
        # Confirm download
        if not messagebox.askyesno("Confirm Download", 
                                  f"Do you want to download the model '{model}'?\n\n"
                                  "This may take a while depending on the model size and your internet connection."):
            return
        
        # Check if Ollama is running
        if not self.ollama_manager.is_ollama_running():
            if messagebox.askyesno("Ollama Not Running", 
                                 "Ollama needs to be running to download models. Start Ollama now?"):
                # Start Ollama and then download the model
                def start_callback(success, message, in_progress=False):
                    self.status_var.set(message)
                    self.settings_tab.update_ollama_status(message)
                    
                    if success and not in_progress:
                        # Ollama started, now download the model
                        self._start_model_download(model)
                
                self.ollama_manager.start_ollama(start_callback)
            return
                
        # Start download directly if Ollama is already running
        self._start_model_download(model)
    
    def _start_model_download(self, model):
        """Start the model download process"""
        # Clear previous download status
        self.settings_tab.update_download_status("Starting download...")
        self.settings_tab.update_download_progress(0)
        
        # Define callback for download updates
        def download_callback(success, message, progress=None, in_progress=False):
            self.settings_tab.update_download_status(message)
            
            if progress is not None:
                self.settings_tab.update_download_progress(progress)
            
            if success and not in_progress and progress == 100:
                # Download complete, refresh models
                self.load_ollama_models()
                
                # Set as current model
                self.settings_tab.ollama_model_var.set(model)
            
            if not success:
                messagebox.showerror("Download Error", message)
        
        # Start download
        self.ollama_manager.download_model(model, download_callback)
    
    # Settings Functions
    def update_settings_from_ui(self):
        """Update settings object from UI values"""
        # General settings
        self.settings.whisper_model_name = self.settings_tab.whisper_model_var.get()
        self.settings.ollama_base_url = self.settings_tab.ollama_url_var.get()
        self.settings.auto_start_ollama = self.settings_tab.auto_start_ollama_var.get()
        self.settings.sample_rate = self.settings_tab.sample_rate_var.get()
        self.settings.system_prompt = self.settings_tab.system_prompt_var.get()
        
        # Update API settings
        self.settings.selected_provider = self.settings_tab.api_provider_var.get()
        self.settings.selected_prompt_mode = self.selected_prompt_mode.get()
        
        # Update component settings
        self.recorder.sample_rate = self.settings.sample_rate
        self.ollama_manager.ollama_base_url = self.settings.ollama_base_url
        
        # Update API keys
        for provider, key_var in self.settings_tab.api_key_vars.items():
            self.settings.api_keys[provider] = key_var.get()
        
        # Update OpenAI model
        if hasattr(self.settings_tab, 'selected_openai_model'):
            self.settings.selected_openai_model = self.settings_tab.selected_openai_model.get()
        
        # Update Ollama model
        if self.settings_tab.ollama_model_var.get():
            self.settings.ollama_model_name = self.settings_tab.ollama_model_var.get()
    
    def save_settings(self):
        """Save settings to config file"""
        self.update_settings_from_ui()
        
        success, message = self.settings.save_settings(
            self.settings_tab.whisper_model_var,
            self.settings_tab.ollama_url_var,
            self.settings_tab.auto_start_ollama_var,
            self.settings_tab.ollama_model_var,
            self.settings_tab.system_prompt_var,
            self.settings_tab.sample_rate_var,
            self.settings_tab.api_provider_var,
            self.settings_tab.selected_openai_model,
            self.settings_tab.api_key_vars
        )
        
        self.status_var.set(message)
        
        if not success:
            messagebox.showerror("Settings Error", message)
    
    def on_closing(self):
        """Handle window closing event"""
        # Stop ollama if it was started by the app
        self.ollama_manager.stop_ollama()
        
        # Clean up audio recorder
        self.recorder.clean_up()
        
        self.root.destroy()