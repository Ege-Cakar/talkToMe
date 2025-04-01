import tkinter as tk
from tkinter import ttk, messagebox
import shutil
import os

class SettingsTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        
        # Create settings tab contents
        self.setup_settings_tab()
    
    def setup_settings_tab(self):
        settings_inner_frame = ttk.Frame(self.parent)
        settings_inner_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for settings categories
        self.settings_notebook = ttk.Notebook(settings_inner_frame)
        self.settings_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # General settings tab
        general_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(general_frame, text="General")
        
        # Ollama models tab
        models_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(models_frame, text="Ollama Models")

        # API settings tab
        api_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(api_frame, text="API Settings")
        
        # Setup general settings
        self.setup_general_settings(general_frame)
        
        # Setup models settings
        self.setup_models_settings(models_frame)

        # Setup API settings
        self.setup_api_settings(api_frame)
        
        # Save settings button
        ttk.Button(settings_inner_frame, text="Save Settings", command=self.app.save_settings).pack(pady=10)
    
    def setup_general_settings(self, parent_frame):
        # Whisper model selection
        ttk.Label(parent_frame, text="Whisper Model:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.whisper_model_var = tk.StringVar(value=self.app.settings.whisper_model_name)
        whisper_models = ["tiny", "base", "small", "medium", "large"]
        whisper_dropdown = ttk.Combobox(parent_frame, textvariable=self.whisper_model_var, 
                                       values=whisper_models, state="readonly")
        whisper_dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        whisper_dropdown.bind("<<ComboboxSelected>>", self.app.change_whisper_model)
        
        # Ollama settings
        ttk.Label(parent_frame, text="Ollama Server URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.ollama_url_var = tk.StringVar(value=self.app.settings.ollama_base_url)
        ollama_url_entry = ttk.Entry(parent_frame, textvariable=self.ollama_url_var)
        ollama_url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Button(parent_frame, text="Connect", command=self.app.connect_to_ollama).grid(
            row=1, column=2, padx=5, pady=5)
        
        # Auto-start Ollama checkbox
        self.auto_start_ollama_var = tk.BooleanVar(value=self.app.settings.auto_start_ollama)
        auto_start_check = ttk.Checkbutton(parent_frame, text="Auto-start Ollama on launch", 
                                          variable=self.auto_start_ollama_var)
        auto_start_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Audio settings
        ttk.Label(parent_frame, text="Sample Rate:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.sample_rate_var = tk.IntVar(value=self.app.settings.sample_rate)
        sample_rates = [8000, 16000, 22050, 44100, 48000]
        sample_rate_combo = ttk.Combobox(parent_frame, textvariable=self.sample_rate_var, 
                                       values=sample_rates, state="readonly")
        sample_rate_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # ffmpeg note for audio import
        ffmpeg_note = ttk.Label(parent_frame, text="Note: ffmpeg is required for importing non-WAV audio files.", 
                               font=("", 9, "italic"))
        ffmpeg_note.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Check if ffmpeg is available
        ffmpeg_available = shutil.which('ffmpeg') is not None
        ffmpeg_status = ttk.Label(parent_frame, 
                                text=f"ffmpeg status: {'Available' if ffmpeg_available else 'Not found - only WAV imports will work'}", 
                                font=("", 9))
        ffmpeg_status.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Ollama installation status and controls
        ollama_status_frame = ttk.LabelFrame(parent_frame, text="Ollama Status")
        ollama_status_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=10)
        
        self.ollama_status_var = tk.StringVar(value="Checking...")
        ttk.Label(ollama_status_frame, textvariable=self.ollama_status_var).pack(pady=5)
        
        ollama_control_frame = ttk.Frame(ollama_status_frame)
        ollama_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(ollama_control_frame, text="Check Status", command=self.app.check_ollama_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(ollama_control_frame, text="Start Ollama", command=self.app.start_ollama).pack(side=tk.LEFT, padx=5)
        ttk.Button(ollama_control_frame, text="Stop Ollama", command=self.app.stop_ollama).pack(side=tk.LEFT, padx=5)
        
        # Download Ollama if not installed
        if not shutil.which('ollama'):
            ttk.Button(ollama_control_frame, text="Download Ollama", 
                       command=self.app.download_ollama).pack(side=tk.LEFT, padx=5)
        
        # System prompt for Ollama
        ttk.Label(parent_frame, text="System Prompt for Ollama:").grid(row=7, column=0, sticky=tk.W, pady=5)
        
        self.system_prompt_var = tk.StringVar(value=self.app.settings.system_prompt)
        system_prompt_entry = ttk.Entry(parent_frame, textvariable=self.system_prompt_var, width=50)
        system_prompt_entry.grid(row=7, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Configure grid
        parent_frame.columnconfigure(1, weight=1)
    
    def setup_models_settings(self, parent_frame):
        # Installed models section
        ttk.Label(parent_frame, text="Installed Models:", font=("", 10, "bold")).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        # Model listbox with scrollbar
        model_frame = ttk.Frame(parent_frame)
        model_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(model_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.model_listbox = tk.Listbox(model_frame, height=8, width=40, yscrollcommand=scrollbar.set)
        self.model_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.model_listbox.yview)
        
        # Bind selection event
        self.model_listbox.bind('<<ListboxSelect>>', self.on_model_select)
        
        # Model controls
        model_control_frame = ttk.Frame(parent_frame)
        model_control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(model_control_frame, text="Refresh Models", command=self.app.refresh_models).pack(side=tk.LEFT, padx=5)
        ttk.Button(model_control_frame, text="Select for Use", command=self.app.select_model).pack(side=tk.LEFT, padx=5)
        
        # Selected model
        ttk.Label(parent_frame, text="Currently Selected Model:").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        self.ollama_model_var = tk.StringVar(value=self.app.settings.ollama_model_name)
        selected_model_label = ttk.Label(parent_frame, textvariable=self.ollama_model_var, font=("", 10, "bold"))
        selected_model_label.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        # Download new models section
        ttk.Separator(parent_frame, orient='horizontal').grid(
            row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(parent_frame, text="Download New Model:", font=("", 10, "bold")).grid(
            row=5, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        # Popular models
        ttk.Label(parent_frame, text="Popular Models:").grid(row=6, column=0, sticky=tk.W, pady=5)
        
        popular_models = ["llama3", "llama3:8b", "llama3:70b", "mistral", "mixtral", "gemma:7b", "phi3:mini"]
        self.download_model_var = tk.StringVar()
        download_model_combo = ttk.Combobox(parent_frame, textvariable=self.download_model_var, 
                                          values=popular_models)
        download_model_combo.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Custom model name
        ttk.Label(parent_frame, text="Or Custom Model:").grid(row=7, column=0, sticky=tk.W, pady=5)
        
        self.custom_model_var = tk.StringVar()
        custom_model_entry = ttk.Entry(parent_frame, textvariable=self.custom_model_var)
        custom_model_entry.grid(row=7, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Download button
        ttk.Button(parent_frame, text="Download Model", command=self.app.download_model).grid(
            row=8, column=0, columnspan=3, pady=10)
        
        # Progress bar for downloads
        self.download_progress_var = tk.DoubleVar()
        self.download_progress = ttk.Progressbar(parent_frame, variable=self.download_progress_var, maximum=100)
        self.download_progress.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Download status
        self.download_status_var = tk.StringVar(value="")
        download_status_label = ttk.Label(parent_frame, textvariable=self.download_status_var)
        download_status_label.grid(row=10, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Configure grid
        parent_frame.columnconfigure(1, weight=1)
        parent_frame.rowconfigure(1, weight=1)
    
    def setup_api_settings(self, parent_frame):
        """Setup API settings tab with provider selection, model selection, and API keys"""
        # API provider selection
        ttk.Label(parent_frame, text="API Provider:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.api_provider_var = tk.StringVar(value=self.app.settings.selected_provider)
        api_provider_combo = ttk.Combobox(parent_frame, textvariable=self.api_provider_var, 
                                      values=self.app.settings.api_providers)
        api_provider_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        api_provider_combo.bind("<<ComboboxSelected>>", self.on_provider_change)
        
        # Create a frame for model selection
        model_frame = ttk.LabelFrame(parent_frame, text="Model Selection")
        model_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=10)
        
        # OpenAI model selection
        self.openai_model_label = ttk.Label(model_frame, text="OpenAI Model:")
        self.openai_model_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.selected_openai_model = tk.StringVar(value=self.app.settings.selected_openai_model)
        self.openai_model_combo = ttk.Combobox(model_frame, 
                                          textvariable=self.selected_openai_model,
                                          values=list(self.app.settings.openai_models.keys()),
                                          state="readonly")
        self.openai_model_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Update UI based on current provider
        self.update_model_selection_ui()
        
        # API keys section
        api_keys_frame = ttk.LabelFrame(parent_frame, text="API Keys")
        api_keys_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=10)
        
        # Create a dictionary to hold the StringVar variables for API keys
        self.api_key_vars = {}
        
        for i, (provider, key) in enumerate(self.app.settings.api_keys.items()):
            ttk.Label(api_keys_frame, text=f"{provider} API Key:").grid(row=i, column=0, sticky=tk.W, pady=5)
            
            # Create a StringVar for each API key
            key_var = tk.StringVar(value=key)
            self.api_key_vars[provider] = key_var
                
            key_entry = ttk.Entry(api_keys_frame, textvariable=key_var, width=50, show="*")
            key_entry.grid(row=i, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Configure the grid to expand properly
        parent_frame.columnconfigure(1, weight=1)
        model_frame.columnconfigure(1, weight=1)
        api_keys_frame.columnconfigure(1, weight=1)
    
    def on_provider_change(self, event=None):
        """Handle API provider change"""
        self.update_model_selection_ui()
    
    def update_model_selection_ui(self):
        """Show/hide model selection based on selected provider"""
        provider = self.api_provider_var.get()
        
        # Show/hide model selection based on provider
        if provider == "OpenAI":
            self.openai_model_label.grid()
            self.openai_model_combo.grid()
        else:
            self.openai_model_label.grid_remove()
            self.openai_model_combo.grid_remove()
    
    def on_model_select(self, event=None):
        """Handle model selection from listbox"""
        if not self.model_listbox.curselection():
            return
        
        selected_index = self.model_listbox.curselection()[0]
        selected_model = self.model_listbox.get(selected_index)
        
        # Just highlight the selection, don't set it as active model yet
        self.model_listbox.selection_set(selected_index)
    
    def update_ollama_status(self, status_text):
        """Update Ollama status text"""
        self.ollama_status_var.set(status_text)
    
    def update_download_status(self, status_text):
        """Update download status text"""
        self.download_status_var.set(status_text)
    
    def update_download_progress(self, value):
        """Update download progress bar value"""
        self.download_progress_var.set(value)
    
    def get_model_selection(self):
        """Get currently selected model from listbox"""
        if not self.model_listbox.curselection():
            return None
        
        selected_index = self.model_listbox.curselection()[0]
        return self.model_listbox.get(selected_index)
    
    def populate_model_listbox(self, models):
        """Populate the model listbox with a list of models"""
        self.model_listbox.delete(0, tk.END)
        for model in models:
            self.model_listbox.insert(tk.END, model)
    
    def get_download_model(self):
        """Get model name for download (from dropdown or custom entry)"""
        return self.download_model_var.get() or self.custom_model_var.get()