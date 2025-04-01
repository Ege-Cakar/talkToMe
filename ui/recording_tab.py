import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

class RecordingTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        
        # Variables
        self.progress_var = tk.DoubleVar()
        
        # Create tab contents
        self.setup_recording_tab()
    
    def setup_recording_tab(self):
        # Control frame
        control_frame = ttk.Frame(self.parent)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Add a frame for LLM prompt mode selection
        prompt_mode_frame = ttk.LabelFrame(self.parent, text="Select LLM Prompt Mode")
        prompt_mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for mode in self.app.settings.mode_prompts.keys():
            rb = ttk.Radiobutton(prompt_mode_frame, text=mode, variable=self.app.selected_prompt_mode, value=mode)
            rb.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.record_button = ttk.Button(control_frame, text="Start Recording", command=self.app.toggle_recording)
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        self.import_button = ttk.Button(control_frame, text="Import Audio", command=self.app.import_audio_file)
        self.import_button.pack(side=tk.LEFT, padx=5)
        
        self.transcribe_button = ttk.Button(control_frame, text="Transcribe", command=self.app.transcribe_audio, state=tk.DISABLED)
        self.transcribe_button.pack(side=tk.LEFT, padx=5)
        
        self.convert_button = ttk.Button(control_frame, text="Convert to LaTeX", command=self.app.convert_to_latex, state=tk.DISABLED)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(control_frame, text="Save LaTeX", command=self.app.save_latex, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(control_frame, text="Clear All", command=self.app.clear_all)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(control_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.loading_label = ttk.Label(control_frame, text="")
        self.loading_label.pack(side=tk.LEFT, padx=5)
        
        # Text display frame
        text_frame = ttk.Frame(self.parent)
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
    
    def update_recording_button(self, is_recording):
        """Update recording button text based on recording state"""
        if is_recording:
            self.record_button.config(text="Stop Recording")
        else:
            self.record_button.config(text="Start Recording")
    
    def update_transcribe_button(self, state):
        """Enable or disable the transcribe button"""
        self.transcribe_button.config(state=state)
    
    def update_progress(self, value):
        """Update progress bar value"""
        self.progress_var.set(value)
    
    def update_loading_label(self, text):
        """Update loading label text"""
        self.loading_label.config(text=text)
    
    def clear_text_areas(self):
        """Clear both text areas"""
        self.transcribed_text.delete(1.0, tk.END)
        self.latex_text.delete(1.0, tk.END)
    
    def get_transcribed_text(self):
        """Get text from transcribed text area"""
        return self.transcribed_text.get(1.0, tk.END).strip()
    
    def set_transcribed_text(self, text):
        """Set text in transcribed text area"""
        self.transcribed_text.delete(1.0, tk.END)
        self.transcribed_text.insert(tk.END, text)
    
    def get_latex_text(self):
        """Get text from LaTeX text area"""
        return self.latex_text.get(1.0, tk.END).strip()
    
    def set_latex_text(self, text):
        """Set text in LaTeX text area"""
        self.latex_text.delete(1.0, tk.END)
        self.latex_text.insert(tk.END, text)