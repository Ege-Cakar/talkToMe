import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import pyaudio
import wave
import os
import numpy as np
import requests
import json
import time
import whisper
import configparser
import subprocess
import shutil
import platform
import zipfile
import tarfile
import tempfile
import base64
from urllib.request import urlretrieve
from pathlib import Path
from google import genai

class SpeechToLatexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech-to-LaTeX Transcription Tool")
        self.root.geometry("1000x800")
        
        # Set up variables
        self.is_recording = False
        self.audio_thread = None
        self.frames = []
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.temp_audio_file = "temp_recording.wav"
        self.ollama_models = []
        self.whisper_model = None
        self.ollama_base_url = "http://localhost:11434/api"
        self.config_file = os.path.join(os.path.expanduser("~"), ".speech2latex.ini")
        self.ollama_process = None
        
        # API provider variables
        self.api_providers = ["Ollama (Local)", "OpenAI", "Anthropic", "Perplexity", "Mistral", "Google Gemini"]
        self.selected_provider = tk.StringVar(value="Ollama (Local)")
        self.api_keys = {
            "OpenAI": "",
            "Anthropic": "",
            "Perplexity": "",
            "Mistral": "",
            "Google Gemini": ""
        }
        # LLM Prompt Modes
        self.mode_prompts = {
        "Direct Transcription": """TASK: Convert mathematical expressions in the text to LaTeX.
        
  INPUT TEXT:
  {text}
  
  CONVERSION RULES:
  - Convert ONLY mathematical expressions to LaTeX notation
  - Do NOT modify any other text
  - Use $...$ for inline math expressions
  - Use $$...$$ for displayed equations
  - Do NOT add any additional text, explanations, or commentary
  
  EXAMPLES:
  Original: "The area of a circle is given by pi r squared."
  Correct: "The area of a circle is given by $\pi r^2$."
  
  Original: "To solve for x, I use the quadratic formula x equals negative b plus or minus square root of b squared minus 4 a c all over 2a."
  Correct: "To solve for x, I use the quadratic formula $$x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$$."
  
  Original: "The derivative of x to the power of n is n times x to the power of n minus 1."
  Correct: "The derivative of $x^n$ is $n \cdot x^{{n-1}}$."
  
  IMPORTANT: Your response must contain ONLY the input text with mathematical expressions converted to LaTeX. Do not include comments, explanations, or anything else.
  
  CONVERT NOW:""",
        "Clean Transcription": """TASK: Remove filler words and convert mathematical expressions to LaTeX.
  
  INPUT TEXT:
  {text}
  
  CONVERSION RULES:
  - Remove all filler words and phrases like "um", "uh", "like", "you know", "sort of", "kind of", etc.
  - Fix grammatical errors and make the text flow naturally
  - Convert all mathematical expressions to LaTeX notation
  - Use $...$ for inline math expressions
  - Use $$...$$ for displayed equations
  - Maintain the original meaning and content
  - Do NOT add any additional information or explanations
  
  EXAMPLES:
  Original: "Um, so the area of a circle is, like, given by pi r squared, you know."
  Correct: "The area of a circle is given by $\pi r^2$."
  
  Original: "Uh, to solve for x, I use the, um, quadratic formula x equals negative b plus or minus, uh, square root of b squared minus 4 a c all over 2a."
  Correct: "To solve for x, I use the quadratic formula $$x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$$."
  
  IMPORTANT: Your response must contain ONLY the cleaned text with mathematical expressions converted to LaTeX. Do not include comments, explanations, or anything else.
  
  CLEAN AND CONVERT NOW:""",
        "Class Notes (PDF Style)": r"""TASK: Generate comprehensive, well-structured LaTeX lecture notes based on the provided transcript, mimicking the style and depth of formal academic lecture notes. 

                INPUT TEXT:
                {INPUT_TEXT}
                
                LATEX NOTE GENERATION RULES:
                1.  **Document Structure:**
                  *   Use standard LaTeX article class structure (e.g., `\documentclass{article}`).
                  *   Include necessary packages like `amsmath`, `amssymb`.
                  *   Use `\section{Section Title}` and `\subsection{Subsection Title}` for organization. Infer appropriate titles from the content.
                2.  **Content Flow & Depth:**
                  *   Reconstruct the lecture's narrative flow, including introductions, motivations, core concepts, detailed derivations (if present in the transcript), illustrative examples, and conclusions/summaries.
                  *   Do NOT just list facts. Explain concepts, define terms, and show the reasoning or steps discussed in the transcript.
                  *   The notes should be comprehensive and detailed, reflecting the depth of a university lecture.
                3.  **Mathematical Content:**
                  *   Convert ALL mathematical expressions, symbols, and variables to appropriate LaTeX notation.
                  *   Use `$ ... $` for inline mathematics.
                  *   Use `\begin{equation} ... \end{equation}` for numbered display equations. Number equations sequentially throughout the notes.
                  *   Ensure mathematical accuracy and consistency in notation.
                4.  **Formatting & Style:**
                  *   Use `\textbf{Definition:}` or similar emphasis for key definitions.
                  *   Use `itemize` or `enumerate` for lists where appropriate.
                  *   Structure examples clearly, perhaps using `\textbf{Example:}` or a dedicated subsection.
                  *   Maintain a formal, academic tone suitable for the subject matter.
                5.  **Information Integrity:**
                  *   Base the notes SOLELY on the information present in the input transcript.
                  *   Do NOT add external information, opinions, or topics not discussed. You may fill in points that you believe were not represented fully accurately in the transcript. 
                  *   Accurately represent the concepts and relationships described by the speaker.
                  *   If the transcript refers to previous material (e.g., "as we saw in Lecture 7"), include this reference in the notes.
                  *   Make sure to not miss ANYTHING being talked about in the lecture. 
                
                EXAMPLE LATEX STRUCTURE SNIPPET:
                \documentclass{article}
                \usepackage{amsmath, amssymb}
                
                \begin{document}
                
                \section{Introduction}
                % Brief overview based on transcript intro
                
                \section{Thermodynamic Potentials}
                \subsection{Internal Energy and First Law}
                The fundamental relation is given by:
                \begin{equation}
                dE = TdS - PdV + \mu dN
                \end{equation}
                where $E$ is internal energy, $T$ is temperature... % Explanation based on transcript
                
                \subsection{Helmholtz Free Energy}
                \textbf{Definition:} The Helmholtz Free Energy $F$ is defined as:
                \begin{equation}
                F = E - TS
                \end{equation}
                Taking the differential gives... % Derivation based on transcript
                \begin{equation}
                dF = -SdT - PdV + \mu dN
                \end{equation}
                This shows that $F$ is a function of $T, V, N$.
                
                \textbf{Example:} Monatomic Ideal Gas
                The entropy is $S(E, V, N) = ...$ % Content from transcript
                The free energy can be calculated as $F = -k_B T \ln Z = ...$
                \begin{equation}
                F = -Nk_B T \left[ \ln\left(\frac{V}{N}\right) + \frac{3}{2}\ln\left(\frac{2\pi mk_B T}{h^2}\right) + 1 \right]
                \end{equation}
                
                % ... further sections and subsections ...
                
                \end{document}
                
                IMPORTANT: Generate the full LaTeX document structure, starting from `\documentclass` to `\end{document}`, following all the rules above to create notes that closely resemble the style, structure, and depth of the provided PDF example. If you follow all of your tasks accurately, you will get a very large and nice reward. 
                
                GENERATE LATEX NOTES NOW:
                """}
        self.selected_prompt_mode = tk.StringVar(value="Direct Transcription")
        self.openai_models = {
        "GPT-4o": "gpt-4o",
        "GPT-4o-mini": "gpt-4o-mini",
        "o3-mini": "o3-mini",
        "o1": "o1"
    }
        self.selected_openai_model = tk.StringVar(value="o3-mini")  # Default model is cheap and smart
        
        # Create application folders
        self.app_dir = os.path.join(os.path.expanduser("~"), ".speech2latex")
        os.makedirs(self.app_dir, exist_ok=True)
        
        # Load settings from config file
        self.load_settings()
        
        # Create GUI
        self.create_gui()
        
        # Check Ollama status
        self.check_ollama_status()
        
        # Auto-start Ollama if enabled
        if self.auto_start_ollama:
            self.start_ollama()
        
        # Load available Ollama models (on a delay to allow server to start)
        self.root.after(3000, self.load_ollama_models)
        
        # Load whisper model in a separate thread to avoid blocking the GUI
        self.root.after(500, lambda: threading.Thread(target=self.load_whisper_model, 
                                                     args=(self.whisper_model_name,), 
                                                     daemon=True).start())
        
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
        self.setup_recording_tab()
        
        # Setup settings tab
        self.setup_settings_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_recording_tab(self):
        # Control frame
        control_frame = ttk.Frame(self.recording_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        # Add a frame for LLM prompt mode selection
        prompt_mode_frame = ttk.LabelFrame(self.recording_frame, text="Select LLM Prompt Mode")
        prompt_mode_frame.pack(fill=tk.X, padx=10, pady=5)
        for mode in self.mode_prompts.keys():
          rb = ttk.Radiobutton(prompt_mode_frame, text=mode, variable=self.selected_prompt_mode, value=mode)
          rb.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.record_button = ttk.Button(control_frame, text="Start Recording", command=self.toggle_recording)
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        self.import_button = ttk.Button(control_frame, text="Import Audio", command=self.import_audio_file)
        self.import_button.pack(side=tk.LEFT, padx=5)
        
        self.transcribe_button = ttk.Button(control_frame, text="Transcribe", command=self.transcribe_audio, state=tk.DISABLED)
        self.transcribe_button.pack(side=tk.LEFT, padx=5)
        
        self.convert_button = ttk.Button(control_frame, text="Convert to LaTeX", command=self.convert_to_latex, state=tk.DISABLED)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(control_frame, text="Save LaTeX", command=self.save_latex, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(control_frame, text="Clear All", command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(control_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.loading_label = ttk.Label(control_frame, text="")
        self.loading_label.pack(side=tk.LEFT, padx=5)
        
        # Text display frame
        text_frame = ttk.Frame(self.recording_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Labels and text areas
        ttk.Label(text_frame, text="Transcribed Text:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.transcribed_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10)
        self.transcribed_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.transcribed_text.bind("<<Modified>>", self.on_transcribed_text_change)
        
        ttk.Label(text_frame, text="LaTeX Output:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.latex_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=10)
        self.latex_text.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(1, weight=1)
        text_frame.rowconfigure(3, weight=1)
    
    def setup_settings_tab(self):
        settings_inner_frame = ttk.Frame(self.settings_frame)
        settings_inner_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for settings categories
        settings_notebook = ttk.Notebook(settings_inner_frame)
        settings_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # General settings tab
        general_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(general_frame, text="General")
        
        # Ollama models tab
        models_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(models_frame, text="Ollama Models")

        # API settings tab
        api_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(api_frame, text="API Settings")
        
        # Setup general settings
        self.setup_general_settings(general_frame)
        
        # Setup models settings
        self.setup_models_settings(models_frame)

        # Setup API settings
        self.setup_api_settings(api_frame)
        
        # Save settings button
        ttk.Button(settings_inner_frame, text="Save Settings", command=self.save_settings).pack(pady=10)
    
    def setup_general_settings(self, parent_frame):
        # Whisper model selection
        ttk.Label(parent_frame, text="Whisper Model:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.whisper_model_var = tk.StringVar(value=self.whisper_model_name)
        whisper_models = ["tiny", "base", "small", "medium", "large"]
        whisper_dropdown = ttk.Combobox(parent_frame, textvariable=self.whisper_model_var, 
                                         values=whisper_models, state="readonly")
        whisper_dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        whisper_dropdown.bind("<<ComboboxSelected>>", self.change_whisper_model)
        
        # Ollama settings
        ttk.Label(parent_frame, text="Ollama Server URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.ollama_url_var = tk.StringVar(value=self.ollama_base_url)
        ollama_url_entry = ttk.Entry(parent_frame, textvariable=self.ollama_url_var)
        ollama_url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Button(parent_frame, text="Connect", command=self.connect_to_ollama).grid(
            row=1, column=2, padx=5, pady=5)
        
        # Auto-start Ollama checkbox
        self.auto_start_ollama_var = tk.BooleanVar(value=self.auto_start_ollama)
        auto_start_check = ttk.Checkbutton(parent_frame, text="Auto-start Ollama on launch", 
                                          variable=self.auto_start_ollama_var)
        auto_start_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Audio settings
        ttk.Label(parent_frame, text="Sample Rate:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.sample_rate_var = tk.IntVar(value=self.sample_rate)
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
        
        ttk.Button(ollama_control_frame, text="Check Status", command=self.check_ollama_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(ollama_control_frame, text="Start Ollama", command=self.start_ollama).pack(side=tk.LEFT, padx=5)
        ttk.Button(ollama_control_frame, text="Stop Ollama", command=self.stop_ollama).pack(side=tk.LEFT, padx=5)
        
        # Download Ollama if not installed
        if not shutil.which('ollama'):
            ttk.Button(ollama_control_frame, text="Download Ollama", 
                       command=self.download_ollama).pack(side=tk.LEFT, padx=5)
        
        # Update Ollama status
        self.update_ollama_status()
        
        # System prompt for Ollama
        ttk.Label(parent_frame, text="System Prompt for Ollama:").grid(row=7, column=0, sticky=tk.W, pady=5)
        
        self.system_prompt_var = tk.StringVar(value=self.system_prompt)
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
        
        ttk.Button(model_control_frame, text="Refresh Models", command=self.refresh_models).pack(side=tk.LEFT, padx=5)
        ttk.Button(model_control_frame, text="Select for Use", command=self.select_model).pack(side=tk.LEFT, padx=5)
        
        # Selected model
        ttk.Label(parent_frame, text="Currently Selected Model:").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        self.ollama_model_var = tk.StringVar(value=self.ollama_model_name)
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
        ttk.Button(parent_frame, text="Download Model", command=self.download_model).grid(
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
        
    def on_transcribed_text_change(self, event=None):
      # Reset the modified flag so the event fires again on new changes
      self.transcribed_text.edit_modified(False)
      content = self.transcribed_text.get("1.0", tk.END).strip()
      if content:
        self.convert_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)
      else:
        self.convert_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
    
    def setup_api_settings(self, parent_frame):
        """Setup API settings tab with provider selection, model selection, and API keys"""
        # API provider selection
        ttk.Label(parent_frame, text="API Provider:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.api_provider_var = tk.StringVar(value=self.selected_provider)
        api_provider_combo = ttk.Combobox(parent_frame, textvariable=self.api_provider_var, 
                                        values=self.api_providers)
        api_provider_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        api_provider_combo.bind("<<ComboboxSelected>>", self.on_provider_change)
        
        # Create a frame for model selection
        model_frame = ttk.LabelFrame(parent_frame, text="Model Selection")
        model_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=10)
        
        # OpenAI model selection
        self.openai_model_label = ttk.Label(model_frame, text="OpenAI Model:")
        self.openai_model_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # If this is the first time using the app after adding this feature, initialize the dictionary and variable
        if not hasattr(self, 'openai_models'):
            self.openai_models = {
                "GPT-4o": "gpt-4o",
                "GPT-4o-mini": "gpt-4o-mini",
                "GPT-4 Turbo": "gpt-4-turbo",
                "GPT-3.5 Turbo": "gpt-3.5-turbo"
            }
        
        if not hasattr(self, 'selected_openai_model'):
            self.selected_openai_model = tk.StringVar(value="GPT-4o")
        
        self.openai_model_combo = ttk.Combobox(model_frame, 
                                            textvariable=self.selected_openai_model,
                                            values=list(self.openai_models.keys()),
                                            state="readonly")
        self.openai_model_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Update UI based on current provider
        self.update_model_selection_ui()
        
        # API keys section
        api_keys_frame = ttk.LabelFrame(parent_frame, text="API Keys")
        api_keys_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=10)
        
        for i, (provider, key) in enumerate(self.api_keys.items()):
            ttk.Label(api_keys_frame, text=f"{provider} API Key:").grid(row=i, column=0, sticky=tk.W, pady=5)
            
            # Handle both string and StringVar cases
            if isinstance(key, str):
                key_var = tk.StringVar(value=key)
                self.api_keys[provider] = key_var
            else:
                key_var = key
                
            key_entry = ttk.Entry(api_keys_frame, textvariable=key_var, width=50, show="*")
            key_entry.grid(row=i, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Configure the grid to expand properly
        parent_frame.columnconfigure(1, weight=1)
        model_frame.columnconfigure(1, weight=1)
        api_keys_frame.columnconfigure(1, weight=1)

    def on_provider_change(self, event=None):
        """Handle API provider change"""
        self.update_model_selection_ui()
        self.selected_provider = self.api_provider_var.get()

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

    # Modified _ method to use the selected model
    def _convert_using_openai(self, text, prompt, system_prompt):
        api_key = self.api_keys["OpenAI"].get()
        if not api_key:
            raise ValueError("OpenAI API key is not configured. Please add your API key in the settings.")
            
        # Get selected model ID
        model_name = self.selected_openai_model.get()
        
        endpoint = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model_name, 
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        
        def api_call():
            return requests.post(endpoint, headers=headers, json=payload)
        
        self.root.after(0, lambda: self.progress_var.set(40))
        
        response = self._call_api_with_retry(api_call)
        
        self.root.after(0, lambda: self.progress_var.set(80))
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            error_message = f"OpenAI API error: {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_message += f" - {error_data['error']['message']}"
            except:
                error_message += f" - {response.text}"
            raise Exception(error_message)
        
    def load_settings(self):
        """Load settings from config file"""
        config = configparser.ConfigParser()
        
        # Default settings
        self.whisper_model_name = "base"
        self.ollama_model_name = ""
        self.system_prompt = """You are an expert academic and scientific assistant specializing in mathematics, physics, and technical content. Your strengths include:

1. ACCURACY: You prioritize mathematical and scientific correctness above all else
2. PRECISION: You use exact terminology and proper notation in all contexts
3. CLARITY: You express complex ideas in clear, well-structured formats
4. THOROUGHNESS: You provide comprehensive responses that fully address the task
5. ADAPTABILITY: You adjust your output format to best serve the current needs
6. EXPLANATORY: When appropriate, you provide insightful explanations that enhance understanding
7. EDUCATIONAL: Your outputs are optimized for learning and knowledge retention

As a LaTeX expert, you understand:
- Proper mathematical notation and LaTeX syntax
- Academic writing conventions and document structures
- The importance of consistent formatting and notation
- How to represent complex mathematical expressions with precision

You follow specific instructions carefully and adapt your output to match the requested format, style, and level of detail. You maintain academic rigor while ensuring your content is accessible and useful.

When working with transcribed speech, you recognize common patterns in verbal mathematics and convert them appropriately to formal notation, accounting for the differences between spoken and written mathematical language.

Always prioritize correctness over completeness - when uncertain about a specific expression or concept, indicate this clearly rather than providing potentially incorrect information."""
        self.system_prompt_var = """You are an expert academic and scientific assistant specializing in mathematics, physics, and technical content. Your strengths include:

1. ACCURACY: You prioritize mathematical and scientific correctness above all else
2. PRECISION: You use exact terminology and proper notation in all contexts
3. CLARITY: You express complex ideas in clear, well-structured formats
4. THOROUGHNESS: You provide comprehensive responses that fully address the task
5. ADAPTABILITY: You adjust your output format to best serve the current needs
6. EXPLANATORY: When appropriate, you provide insightful explanations that enhance understanding
7. EDUCATIONAL: Your outputs are optimized for learning and knowledge retention

As a LaTeX expert, you understand:
- Proper mathematical notation and LaTeX syntax
- Academic writing conventions and document structures
- The importance of consistent formatting and notation
- How to represent complex mathematical expressions with precision

You follow specific instructions carefully and adapt your output to match the requested format, style, and level of detail. You maintain academic rigor while ensuring your content is accessible and useful.

When working with transcribed speech, you recognize common patterns in verbal mathematics and convert them appropriately to formal notation, accounting for the differences between spoken and written mathematical language.

Always prioritize correctness over completeness - when uncertain about a specific expression or concept, indicate this clearly rather than providing potentially incorrect information."""
        self.auto_start_ollama = False
        self.ollama_model_var = tk.StringVar()
        self.sample_rate_var = tk.IntVar(value=self.sample_rate)
        
        if os.path.exists(self.config_file):
            try:
                config.read(self.config_file)
                
                # Load Whisper settings
                if 'Whisper' in config:
                    self.whisper_model_name = config.get('Whisper', 'model', fallback=self.whisper_model_name)
                
                # Load Ollama settings
                if 'Ollama' in config:
                    self.ollama_base_url = config.get('Ollama', 'url', fallback=self.ollama_base_url)
                    self.auto_start_ollama = config.getboolean('Ollama', 'auto_start', fallback=False)
                    model = config.get('Ollama', 'model', fallback='')
                    if model:
                        self.ollama_model_var.set(model)
                
                # Load system prompt
                if 'Prompts' in config:
                    system_prompt = config.get('Prompts', 'system', fallback=self.system_prompt_var.get())
                    self.system_prompt_var.set(system_prompt)
                
                # Load audio settings
                if 'Audio' in config:
                    sample_rate = config.getint('Audio', 'sample_rate', fallback=self.sample_rate)
                    self.sample_rate_var.set(sample_rate)
                
                # Load API provider settings
                if 'APIProvider' in config:
                    provider = config.get('APIProvider', 'provider', fallback="Ollama (Local)")
                    self.selected_provider = provider
                
                # Load API keys
                if 'APIKeys' in config:
                    for provider in self.api_keys.keys():
                        self.api_keys[provider] = config.get('APIKeys', provider, fallback="")
                if 'OpenAI' in config:
                    selected_model = config.get('OpenAI', 'model', fallback="GPT-4o")
                    if selected_model in self.openai_models:
                        self.selected_openai_model.set(selected_model)

                    
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to config file"""
        config = configparser.ConfigParser()
        
        # Whisper settings
        config['Whisper'] = {
            'model': self.whisper_model_var.get()
        }
        
        # Ollama settings
        config['Ollama'] = {
            'url': self.ollama_url_var.get(),
            'auto_start': str(self.auto_start_ollama_var.get()),
            'model': self.ollama_model_var.get()
        }
        
        # System prompt
        config['Prompts'] = {
            'system': self.system_prompt_var.get()
        }
        
        # Audio settings
        config['Audio'] = {
            'sample_rate': str(self.sample_rate_var.get())
        }
        
        # API provider settings
        config['APIProvider'] = {
            'provider': self.api_provider_var.get()
        }
        if 'OpenAI' not in config:
            config['OpenAI'] = {}
            config['OpenAI']['model'] = self.selected_openai_model.get()
        
        # API keys
        config['APIKeys'] = {}
        for provider, key_var in self.api_keys.items():
            if isinstance(key_var, tk.StringVar):
                config['APIKeys'][provider] = key_var.get()
            else:
                config['APIKeys'][provider] = key_var
        
        try:
            with open(self.config_file, 'w') as f:
                config.write(f)
            
            self.status_var.set("Settings saved")
        except Exception as e:
            self.status_var.set(f"Error saving settings: {str(e)}")
            messagebox.showerror("Settings Error", f"Failed to save settings: {str(e)}")
    
    def is_ollama_running(self):
        """Check if Ollama server is running by testing the API endpoint"""
        try:
            response = requests.get(f"{self.ollama_base_url}/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def check_ollama_status(self):
        """Check Ollama installation and server status"""
        # Check if the ollama command is available
        ollama_cmd = shutil.which('ollama')
        
        if ollama_cmd:
            # Ollama is installed, now check if it's running
            if self.is_ollama_running():
                self.status_var.set("Ollama is installed and running")
            else:
                self.status_var.set("Ollama is installed but not running")
        else:
            self.status_var.set("Ollama command not found. Please install Ollama from ollama.ai")
            messagebox.showwarning("Ollama Not Found", 
                                  "The ollama command was not found in your PATH.\n\n"
                                  "Please install Ollama from https://ollama.ai and complete the setup.")
    
    def update_ollama_status(self):
        """Update the Ollama status display"""
        if not hasattr(self, 'ollama_status_var'):
            return
            
        # Check if the ollama command is available
        ollama_cmd = shutil.which('ollama')
        
        if ollama_cmd:
            # Ollama is installed, now check if it's running
            if self.is_ollama_running() or self.ollama_process is not None:
                self.ollama_status_var.set("Ollama is installed and running")
            else:
                self.ollama_status_var.set("Ollama is installed but not running")
        else:
            self.ollama_status_var.set("Ollama command not found. Please install Ollama from ollama.ai")
    
    def start_ollama(self):
        """Start Ollama server"""
        # First check if it's already running
        if self.is_ollama_running():
            self.status_var.set("Ollama is already running")
            self.update_ollama_status()
            return

        if self.ollama_process is not None:
            self.status_var.set("Ollama startup already in progress")
            return
        
        # Find the ollama command
        ollama_cmd = shutil.which('ollama')
        if not ollama_cmd:
            messagebox.showerror("Ollama Error", 
                               "The ollama command was not found in your PATH.\n\n"
                               "Please install Ollama from https://ollama.ai and complete the setup.")
            return
        
        try:
            # Start Ollama as a background process
            self.status_var.set("Starting Ollama...")
            
            # Use different startup methods based on platform
            if platform.system() == "Windows":  # Windows
                self.ollama_process = subprocess.Popen(
                    [ollama_cmd, 'serve'],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:  # macOS/Linux
                self.ollama_process = subprocess.Popen(
                    [ollama_cmd, 'serve'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Give it a moment to start
            self.root.after(3000, self._check_ollama_startup)
            
        except Exception as e:
            self.status_var.set(f"Error starting Ollama: {str(e)}")
            messagebox.showerror("Ollama Error", f"Failed to start Ollama: {str(e)}")
    
    def _check_ollama_startup(self):
        """Check if Ollama has started successfully"""
        if self.is_ollama_running():
            self.status_var.set("Ollama started successfully")
            self.update_ollama_status()
            self.load_ollama_models()
        else:
            # Try again after a short delay
            self.root.after(2000, self._check_ollama_startup)
    
    def stop_ollama(self):
        """Stop Ollama server"""
        # Check if Ollama is running but wasn't started by us
        if self.is_ollama_running() and self.ollama_process is None:
            messagebox.showinfo("Ollama", 
                              "Ollama server is not running. Please close the Ollama application manually.")
            return
            
        # Otherwise, try to stop our process
        if self.ollama_process is None:
            messagebox.showinfo("Ollama", "Ollama is not running")
            return
        
        try:
            # Terminate the process
            self.ollama_process.terminate()
            
            # Wait for process to terminate
            try:
                self.ollama_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ollama_process.kill()
            
            self.ollama_process = None
            self.status_var.set("Ollama stopped")
            self.update_ollama_status()
        except Exception as e:
            self.status_var.set(f"Error stopping Ollama: {str(e)}")
            messagebox.showerror("Ollama Error", f"Failed to stop Ollama: {str(e)}")
    
    def on_closing(self):
        """Handle window closing event"""
        # Stop ollama if it was started by the app
        if self.ollama_process is not None:
            self.stop_ollama()
        
        # Remove temporary audio file if it exists
        if os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except Exception:
                pass
        
        self.root.destroy()
    
    def load_ollama_models(self):
        try:
            response = requests.get(f"{self.ollama_base_url}/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.ollama_models = [model["name"] for model in data.get("models", [])]
                
                # Populate the model listbox if it exists
                if hasattr(self, 'model_listbox'):
                    self.model_listbox.delete(0, tk.END)
                    for model in self.ollama_models:
                        self.model_listbox.insert(tk.END, model)
                
                # Set the first model as default if none is selected and models are available
                if not self.ollama_model_var.get() and self.ollama_models:
                    self.ollama_model_var.set(self.ollama_models[0])
                
                self.status_var.set(f"Loaded {len(self.ollama_models)} Ollama models")
            else:
                self.status_var.set(f"Failed to load Ollama models: {response.status_code}")
        except Exception as e:
            self.status_var.set(f"Error connecting to Ollama: {str(e)}")
    
    def connect_to_ollama(self):
        """Test connection to Ollama server and refresh models"""
        self.ollama_base_url = self.ollama_url_var.get()
        
        try:
            response = requests.get(f"{self.ollama_base_url}/tags", timeout=5)
            if response.status_code == 200:
                self.status_var.set("Successfully connected to Ollama")
                self.load_ollama_models()
            else:
                self.status_var.set(f"Failed to connect to Ollama: {response.status_code}")
                messagebox.showerror("Connection Error", f"Failed to connect to Ollama: {response.status_code}")
        except Exception as e:
            self.status_var.set(f"Error connecting to Ollama: {str(e)}")
            messagebox.showerror("Connection Error", f"Error connecting to Ollama: {str(e)}")
            
            # If not running, offer to start Ollama
            if "Connection refused" in str(e):
                if messagebox.askyesno("Ollama Not Running", 
                                      "Ollama server is not running. Would you like to start it?"):
                    self.start_ollama()
    
    def refresh_models(self):
        """Refresh the list of available Ollama models"""
        self.load_ollama_models()
    
    def on_model_select(self, event=None):
        """Handle model selection from listbox"""
        if not self.model_listbox.curselection():
            return
        
        selected_index = self.model_listbox.curselection()[0]
        selected_model = self.model_listbox.get(selected_index)
        
        # Just highlight the selection, don't set it as active model yet
        self.model_listbox.selection_set(selected_index)
    
    def select_model(self):
        """Set the selected model as the active model"""
        if not self.model_listbox.curselection():
            messagebox.showinfo("Model Selection", "Please select a model first")
            return
        
        selected_index = self.model_listbox.curselection()[0]
        selected_model = self.model_listbox.get(selected_index)
        
        self.ollama_model_var.set(selected_model)
        messagebox.showinfo("Model Selection", f"Model '{selected_model}' selected for use")
    
    def download_model(self):
        """Download a new Ollama model"""
        # Get the model name from either the dropdown or custom entry
        model = self.download_model_var.get() or self.custom_model_var.get()
        
        if not model:
            messagebox.showerror("Download Error", "Please select or enter a model name")
            return
        
        # Confirm download
        if not messagebox.askyesno("Confirm Download", 
                                   f"Do you want to download the model '{model}'?\n\n"
                                   "This may take a while depending on the model size and your internet connection."):
            return
        
        # Check if Ollama is running
        if not self.is_ollama_running():
            if messagebox.askyesno("Ollama Not Running", 
                                  "Ollama needs to be running to download models. Start Ollama now?"):
                self.start_ollama()
                # Wait a moment for Ollama to start before downloading
                self.root.after(3000, lambda m=model: self._start_model_download(m))
                return
            else:
                return
                
        # Start download directly if Ollama is already running
        self._start_model_download(model)
    
    def _start_model_download(self, model):
        """Start the model download process"""
        # Clear previous download status
        self.download_status_var.set("Starting download...")
        self.download_progress_var.set(0)
        
        # Start download in a separate thread
        threading.Thread(target=self._download_model_thread, args=(model,), daemon=True).start()
    
    def _download_model_thread(self, model):
        """Thread function to download an Ollama model"""
        try:
            # Find the ollama command
            ollama_cmd = shutil.which('ollama')
            if not ollama_cmd:
                self.root.after(0, lambda: messagebox.showerror("Download Error", 
                                                             "The ollama command was not found in your PATH.\n\n"
                                                             "Please install Ollama from https://ollama.ai and complete the setup."))
                return
            
            # Create a process to run ollama pull
            process = subprocess.Popen(
                [ollama_cmd, "pull", model],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Track download progress
            for line in iter(process.stdout.readline, ''):
                # Update status with the latest output
                self.root.after(0, lambda l=line: self.download_status_var.set(l.strip()))
                
                # Try to parse progress percentage if available
                if "%" in line:
                    try:
                        # Extract percentage from a line like "downloading: 45.23%"
                        percent_str = line.split("%")[0].split(":")[-1].strip()
                        percent = float(percent_str)
                        self.root.after(0, lambda p=percent: self.download_progress_var.set(p))
                    except (ValueError, IndexError):
                        pass
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                self.root.after(0, lambda: self.download_status_var.set(f"Successfully downloaded model '{model}'"))
                self.root.after(0, lambda: self.download_progress_var.set(100))
                
                # Refresh the model list
                self.root.after(0, self.load_ollama_models)
                
                # Set as current model
                self.root.after(0, lambda: self.ollama_model_var.set(model))
            else:
                self.root.after(0, lambda: self.download_status_var.set(f"Error downloading model: return code {return_code}"))
        
        except Exception as e:
            self.root.after(0, lambda err=str(e): self.download_status_var.set(f"Error downloading model: {err}"))
            self.root.after(0, lambda err=str(e): messagebox.showerror("Download Error", err))
    
    def load_whisper_model(self, model_name):
        try:
            self.root.after(0, lambda: self.status_var.set(f"Loading Whisper {model_name} model..."))
            self.whisper_model = whisper.load_model(model_name)
            self.root.after(0, lambda: self.status_var.set(f"Whisper {model_name} model loaded"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error loading Whisper model: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Whisper Error", f"Error loading Whisper model: {str(e)}"))
    
    def change_whisper_model(self, event=None):
        model_name = self.whisper_model_var.get()
        threading.Thread(target=self.load_whisper_model, args=(model_name,), daemon=True).start()
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        # Reset any existing recording completion flag
        if hasattr(self, 'recording_completed'):
            delattr(self, 'recording_completed')
            
        self.is_recording = True
        self.record_button.config(text="Stop Recording")
        self.transcribe_button.config(state=tk.DISABLED)
        self.frames = []
        
        self.status_var.set("Recording...")
        
        # Start recording in a separate thread
        self.audio_thread = threading.Thread(target=self.record_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
    
    def record_audio(self):
        try:
            p = pyaudio.PyAudio()
            
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate_var.get(),
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=None  # Use default device
            )
            
            # Set a flag to track completion
            self.recording_completed = False
            
            # Record audio
            try:
                while self.is_recording:
                    try:
                        # Non-blocking read with timeout
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        self.frames.append(data)
                    except Exception as e:
                        print(f"Error during recording: {e}")
                        # Don't break the loop on errors, just continue
            finally:
                # Always clean up resources
                try:
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                except:
                    pass
            
            # Save the recorded audio to a temporary file
            try:
                if self.frames:  # Only save if we have frames
                    wf = wave.open(self.temp_audio_file, 'wb')
                    wf.setnchannels(1)
                    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(self.sample_rate_var.get())
                    wf.writeframes(b''.join(self.frames))
                    wf.close()
                else:
                    print("No audio frames recorded")
            except Exception as e:
                print(f"Error saving audio file: {e}")
            
            # Signal that recording is completed - don't update UI directly from this thread
            self.recording_completed = True
            
        except Exception as e:
            print(f"Recording error: {e}")
            self.recording_completed = True  # Mark as completed even on error
    
    def stop_recording(self):
        self.is_recording = False
        self.record_button.config(text="Start Recording")
        self.status_var.set("Recording stopping...")
        
        # Don't wait for the recording thread to complete - this would freeze the UI
        # Instead, periodically check if it's finished
        self.root.after(100, self._check_recording_stopped)
    
    def _check_recording_stopped(self):
        """Periodically check if recording has stopped and update UI accordingly"""
        if not hasattr(self, 'recording_completed'):
            # Still waiting for recording to complete
            self.root.after(100, self._check_recording_stopped)
            return
            
        if self.recording_completed:
            # Recording has completed
            self.status_var.set("Recording stopped")
            
            # Enable the transcribe button if we have audio
            if os.path.exists(self.temp_audio_file):
                self.transcribe_button.config(state=tk.NORMAL)
            
            # Reset the flag
            delattr(self, 'recording_completed')
        else:
            # Still waiting for recording to complete
            self.root.after(100, self._check_recording_stopped)
    
    def transcribe_audio(self):
        if not os.path.exists(self.temp_audio_file):
            messagebox.showerror("Error", "No recording found to transcribe")
            return
        
        if self.whisper_model is None:
            messagebox.showerror("Error", "Whisper model not loaded yet")
            return
        
        self.status_var.set("Transcribing audio...")
        self.progress_var.set(0)
        
        # Run transcription in a separate thread
        threading.Thread(target=self._transcribe_audio_thread).start()
    
    def _transcribe_audio_thread(self):
        try:
            # Update progress
            self.root.after(0, lambda: self.progress_var.set(10))
            
            # Transcribe audio using the loaded Whisper model
            result = self.whisper_model.transcribe(self.temp_audio_file)
            
            self.root.after(0, lambda: self.progress_var.set(90))
            
            # Get the transcribed text
            transcribed_text = result["text"]
            
            # Update UI with the transcribed text
            def update_ui():
                self.transcribed_text.delete(1.0, tk.END)
                self.transcribed_text.insert(tk.END, transcribed_text)
                self.progress_var.set(100)
                self.convert_button.config(state=tk.NORMAL)
                self.status_var.set("Transcription complete")
            
            self.root.after(0, update_ui)
        except Exception as e:
            def show_error(err=e):
                self.status_var.set(f"Transcription error: {str(err)}")
                messagebox.showerror("Transcription Error", str(err))
            
            self.root.after(0, show_error)
    
    def chunk_text(self, text, max_length=2000):
      """Splits text into chunks not exceeding max_length characters."""
      words = text.split()
      chunks = []
      current_chunk = ""
      for word in words:
        if len(current_chunk) + len(word) + 1 > max_length:
          chunks.append(current_chunk)
          current_chunk = word
        else:
          current_chunk = current_chunk + " " + word if current_chunk else word
      if current_chunk:
        chunks.append(current_chunk)
      return chunks
  
    def _call_api_with_retry(self, api_call, max_retries=5):
      retries = 0
      while retries < max_retries:
        response = api_call()
        if response.status_code != 429:
          return response
        # Use the Retry-After header if provided, otherwise exponential backoff
        retry_after = response.headers.get("Retry-After")
        wait_time = float(retry_after) if retry_after else (2 ** retries)
        time.sleep(wait_time)
        retries += 1
      raise Exception("Maximum retries reached; API rate limit persists.")
    
    def convert_to_latex(self):
        text = self.transcribed_text.get(1.0, tk.END).strip()
        
        if not text:
            messagebox.showerror("Error", "No text to convert to LaTeX")
            return
        
        # Get the current provider
        provider = self.api_provider_var.get()
        
        # Check provider-specific requirements
        if provider == "Ollama (Local)":
            if not self.ollama_models:
                messagebox.showerror("Error", "No Ollama models available")
                return
            
            model = self.ollama_model_var.get()
            if not model:
                messagebox.showerror("Error", "Please select an Ollama model")
                return
                
            self.status_var.set(f"Converting to LaTeX using Ollama model: {model}...")
        else:
            # Check API key for cloud providers
            api_key = self.api_keys[provider].get() if provider in self.api_keys else ""
            if not api_key:
                messagebox.showerror("Error", f"No API key configured for {provider}. Please add your API key in the settings.")
                return
                
            self.status_var.set(f"Converting to LaTeX using {provider} API...")
            # Use a dummy model name for cloud APIs - will be ignored
            model = "dummy"
        
        self.progress_var.set(0)
        
        # Run conversion in a separate thread
        threading.Thread(target=self._convert_to_latex_thread, args=(text, model)).start()
    
    def _convert_to_latex_thread(self, text, model):
      start_time = time.time()
      def update_timer():
        elapsed = int(time.time() - start_time)
        self.loading_label.config(text=f"Processing... {elapsed}s")
        self.timer_id = self.root.after(1000, update_timer)
      update_timer()
      try:
        provider = self.api_provider_var.get()
        system_prompt = self.system_prompt_var.get()
        mode = self.selected_prompt_mode.get()
        prompt_template = self.mode_prompts[mode]
        
        # For Google Gemini, process the entire text at once
        if provider == "Google Gemini":
          if mode == "Class Notes (PDF Style)":
            # Use string replacement instead of format() for PDF Style
            combined_prompt = prompt_template.replace("{INPUT_TEXT}", text)
          else:
            combined_prompt = prompt_template.format(text=text)
          
          # Process the entire text with Google Gemini
          final_output = self._convert_using_gemini(text, combined_prompt, system_prompt)
          
          # Update progress
          self.root.after(0, lambda: self.progress_var.set(80))
        else:
          # Define maximum chunk length (adjust based on model limits)
          max_chunk_length = 10000  
          if len(text) > max_chunk_length:
            chunks = self.chunk_text(text, max_length=max_chunk_length)
          else:
            chunks = [text]
            
          final_output = ""
          accumulated_context = ""
          
          for i, chunk in enumerate(chunks):
            # If there is already context, prepend it to the prompt
            if accumulated_context:
              if mode == "Class Notes (PDF Style)":
                # Use string replacement instead of format() for PDF Style
                combined_prompt = f"CONTEXT:\n{accumulated_context}\n\n" + prompt_template.replace("{INPUT_TEXT}", chunk)
              else:
                combined_prompt = f"CONTEXT:\n{accumulated_context}\n\n" + prompt_template.format(text=chunk)
            else:
              if mode == "Class Notes (PDF Style)":
                # Use string replacement instead of format() for PDF Style
                combined_prompt = prompt_template.replace("{INPUT_TEXT}", chunk)
              else:
                combined_prompt = prompt_template.format(text=chunk)
              
            # Process chunk according to provider
            if provider == "Ollama (Local)":
              latex_chunk = self._convert_using_ollama(chunk, combined_prompt, system_prompt, model)
            elif provider == "OpenAI":
              latex_chunk = self._convert_using_openai(chunk, combined_prompt, system_prompt)
            elif provider == "Anthropic":
              latex_chunk = self._convert_using_anthropic(chunk, combined_prompt, system_prompt)
            elif provider == "Perplexity":
              latex_chunk = self._convert_using_perplexity(chunk, combined_prompt, system_prompt)
            elif provider == "Mistral":
              latex_chunk = self._convert_using_mistral(chunk, combined_prompt, system_prompt)
            else:
              raise ValueError(f"Unsupported provider: {provider}")
              
            final_output += latex_chunk + "\n"
            accumulated_context += latex_chunk + "\n"
            # Optionally update progress based on chunk index
            progress = 40 + 40 * (i + 1) / len(chunks)
            self.root.after(0, lambda p=progress: self.progress_var.set(p))
          
        def update_ui():
          self.latex_text.delete(1.0, tk.END)
          self.latex_text.insert(tk.END, final_output)
          self.progress_var.set(100)
          self.save_button.config(state=tk.NORMAL)
          self.status_var.set("LaTeX conversion complete")
          if hasattr(self, 'timer_id'):
            self.root.after_cancel(self.timer_id)
            self.loading_label.config(text="")
        self.root.after(0, update_ui)
      except Exception as err:
        def show_error(err=err):
          self.status_var.set(f"LaTeX conversion error: {str(err)}")
          messagebox.showerror("Conversion Error", str(err))
        self.root.after(0, show_error)
            
    def _convert_using_ollama(self, text, prompt, system_prompt, model):
        """Convert text to LaTeX using Ollama API"""
        # Prepare the request
        request_data = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "temperature": 0.2
        }
        
        self.root.after(0, lambda: self.progress_var.set(40))
        
        # Send request to Ollama
        response = requests.post(
            f"{self.ollama_base_url}/generate",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        self.root.after(0, lambda: self.progress_var.set(80))
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                        
    def _convert_using_anthropic(self, text, prompt, system_prompt):
        """Convert text to LaTeX using Anthropic API"""
        api_key = self.api_keys["Anthropic"].get()
        if not api_key:
            raise ValueError("Anthropic API key is not configured. Please add your API key in the settings.")
            
        endpoint = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-3-opus-20240229",
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
            "temperature": 0.3
        }
        
        self.root.after(0, lambda: self.progress_var.set(40))
        
        response = requests.post(endpoint, headers=headers, json=payload)
        
        self.root.after(0, lambda: self.progress_var.set(80))
        
        if response.status_code == 200:
            result = response.json()
            return result["content"][0]["text"]
        else:
            error_message = f"Anthropic API error: {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_message += f" - {error_data['error']['message']}"
            except:
                error_message += f" - {response.text}"
            raise Exception(error_message)
            
    def _convert_using_perplexity(self, text, prompt, system_prompt):
        """Convert text to LaTeX using Perplexity API"""
        api_key = self.api_keys["Perplexity"].get()
        if not api_key:
            raise ValueError("Perplexity API key is not configured. Please add your API key in the settings.")
            
        endpoint = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "sonar-medium-online",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        self.root.after(0, lambda: self.progress_var.set(40))
        
        response = requests.post(endpoint, headers=headers, json=payload)
        
        self.root.after(0, lambda: self.progress_var.set(80))
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            error_message = f"Perplexity API error: {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_message += f" - {error_data['error']['message']}"
            except:
                error_message += f" - {response.text}"
            raise Exception(error_message)
            
    def _convert_using_mistral(self, text, prompt, system_prompt):
        """Convert text to LaTeX using Mistral API"""
        api_key = self.api_keys["Mistral"].get()
        if not api_key:
            raise ValueError("Mistral API key is not configured. Please add your API key in the settings.")
            
        endpoint = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "mistral-large-latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        self.root.after(0, lambda: self.progress_var.set(40))
        
        response = requests.post(endpoint, headers=headers, json=payload)
        
        self.root.after(0, lambda: self.progress_var.set(80))
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            error_message = f"Mistral API error: {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_message += f" - {error_data['error']['message']}"
            except:
                error_message += f" - {response.text}"
            raise Exception(error_message)
    
    def _convert_using_gemini(self, text, prompt, system_prompt):
        """Convert text to LaTeX using Google Gemini API"""
        api_key = self.api_keys["Google Gemini"].get()
        if not api_key:
            raise ValueError("Google Gemini API key is not configured. Please add your API key in the settings.")
        
        # Create a client instance
        client = genai.Client(api_key=api_key)
        
        self.root.after(0, lambda: self.progress_var.set(40))
        
        try:
            # Generate content using the Gemini model
            response = client.models.generate_content(
                model="gemini-2.5-pro-exp-03-25",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3
                )
            )
            
            self.root.after(0, lambda: self.progress_var.set(80))
            
            # Extract the response text
            return response.text.strip()
            
        except Exception as e:
            error_message = f"Google Gemini API error: {str(e)}"
            raise Exception(error_message)
    
    def save_latex(self):
        latex_text = self.latex_text.get(1.0, tk.END).strip()
        
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
        self.transcribed_text.delete(1.0, tk.END)
        self.latex_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.transcribe_button.config(state=tk.DISABLED)
        self.convert_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        
        # Delete temporary audio file if it exists
        if os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except Exception:
                pass
        
        self.status_var.set("Ready")

    def import_audio_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.ogg"), ("WAV files", "*.wav"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Check if we need to convert the audio (for non-WAV files)
                if not file_path.lower().endswith('.wav'):
                    self.status_var.set(f"Importing and converting audio file: {file_path}")
                    # Use ffmpeg to convert to WAV format if available
                    ffmpeg_cmd = shutil.which('ffmpeg')
                    if ffmpeg_cmd:
                        # Create command to convert to WAV
                        convert_cmd = [
                            ffmpeg_cmd, 
                            '-i', file_path, 
                            '-ar', str(self.sample_rate_var.get()),
                            '-ac', '1',  # Mono audio
                            '-y',  # Overwrite output file
                            self.temp_audio_file
                        ]
                        subprocess.run(convert_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        self.status_var.set(f"Audio file converted and imported: {file_path}")
                    else:
                        # No ffmpeg, can't convert
                        messagebox.showerror("Import Error", 
                                           "Cannot convert non-WAV files without ffmpeg. "
                                           "Please install ffmpeg or use WAV files.")
                        return
                else:
                    # For WAV files, just copy
                    shutil.copy(file_path, self.temp_audio_file)
                    self.status_var.set(f"Audio file imported: {file_path}")
                
                # Enable transcribe button
                self.transcribe_button.config(state=tk.NORMAL)
                
            except Exception as e:
                self.status_var.set(f"Error importing file: {str(e)}")
                messagebox.showerror("Import Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = SpeechToLatexApp(root)
    root.mainloop()