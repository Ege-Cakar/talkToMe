import configparser
import os
import tkinter as tk

class Settings:
    def __init__(self):
        # Set up default variables
        self.config_file = os.path.join(os.path.expanduser("~"), ".speech2latex.ini")
        self.app_dir = os.path.join(os.path.expanduser("~"), ".speech2latex")
        os.makedirs(self.app_dir, exist_ok=True)
        
        # Default settings
        self.whisper_model_name = "base"
        self.ollama_model_name = ""
        self.ollama_base_url = "http://localhost:11434/api"
        self.auto_start_ollama = False
        self.sample_rate = 16000
        self.selected_provider = "Ollama (Local)"
        self.selected_prompt_mode = "Direct Transcription"
        self.transcription_method = "whisper"  # Can be "whisper" or "openai"
        
        # System prompt
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

        # API provider variables
        self.api_providers = ["Ollama (Local)", "OpenAI", "Anthropic", "Perplexity", "Mistral", "Google Gemini"]
        self.api_keys = {
            "OpenAI": "",
            "Anthropic": "",
            "Perplexity": "",
            "Mistral": "",
            "Google Gemini": ""
        }
        
        # OpenAI models
        self.openai_models = {
            "GPT-4o": "gpt-4o",
            "GPT-4o-mini": "gpt-4o-mini",
            "o3-mini": "o3-mini",
            "o1": "o1"
        }
        self.selected_openai_model = "o3-mini"
        
        # OpenAI transcription models
        self.openai_transcription_models = {
            "GPT-4o Transcribe": "gpt-4o-transcribe",
            "Whisper-1": "whisper-1"
        }
        self.selected_openai_transcription_model = "gpt-4o-transcribe"
        
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
                """
        }
        
        # Load settings from config file
        self.load_settings()

    def load_settings(self):
        """Load settings from config file"""
        config = configparser.ConfigParser()
        
        if os.path.exists(self.config_file):
            try:
                config.read(self.config_file)
                
                # Load Whisper settings
                if 'Whisper' in config:
                    self.whisper_model_name = config.get('Whisper', 'model', fallback=self.whisper_model_name)
                    self.transcription_method = config.get('Whisper', 'transcription_method', fallback=self.transcription_method)
                
                # Load Ollama settings
                if 'Ollama' in config:
                    self.ollama_base_url = config.get('Ollama', 'url', fallback=self.ollama_base_url)
                    self.auto_start_ollama = config.getboolean('Ollama', 'auto_start', fallback=False)
                    model = config.get('Ollama', 'model', fallback='')
                    if model:
                        self.ollama_model_name = model
                
                # Load system prompt
                if 'Prompts' in config:
                    self.system_prompt = config.get('Prompts', 'system', fallback=self.system_prompt)
                
                # Load audio settings
                if 'Audio' in config:
                    self.sample_rate = config.getint('Audio', 'sample_rate', fallback=self.sample_rate)
                
                # Load API provider settings
                if 'APIProvider' in config:
                    provider = config.get('APIProvider', 'provider', fallback="Ollama (Local)")
                    self.selected_provider = provider
                
                # Load API keys
                if 'APIKeys' in config:
                    for provider in self.api_keys.keys():
                        self.api_keys[provider] = config.get('APIKeys', provider, fallback="")
                
                # Load OpenAI model
                if 'OpenAI' in config:
                    selected_model = config.get('OpenAI', 'model', fallback="GPT-4o")
                    if selected_model in self.openai_models:
                        self.selected_openai_model = selected_model
                    
                    # Load OpenAI transcription model
                    selected_transcription_model = config.get('OpenAI', 'transcription_model', fallback="GPT-4o Transcribe")
                    if selected_transcription_model in self.openai_transcription_models:
                        self.selected_openai_transcription_model = selected_transcription_model
                    
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def save_settings(self, whisper_model_var, ollama_url_var, auto_start_ollama_var, 
                      ollama_model_var, system_prompt_var, sample_rate_var, 
                      api_provider_var, selected_openai_model, api_keys,
                      transcription_method_var=None, selected_openai_transcription_model=None):
        """Save settings to config file"""
        config = configparser.ConfigParser()
        
        # Whisper settings
        config['Whisper'] = {
            'model': whisper_model_var.get()
        }
        
        # Add transcription method if provided
        if transcription_method_var:
            config['Whisper']['transcription_method'] = transcription_method_var.get()
        
        # Ollama settings
        config['Ollama'] = {
            'url': ollama_url_var.get(),
            'auto_start': str(auto_start_ollama_var.get()),
            'model': ollama_model_var.get()
        }
        
        # System prompt
        config['Prompts'] = {
            'system': system_prompt_var.get()
        }
        
        # Audio settings
        config['Audio'] = {
            'sample_rate': str(sample_rate_var.get())
        }
        
        # API provider settings
        config['APIProvider'] = {
            'provider': api_provider_var.get()
        }
        
        # OpenAI settings
        if 'OpenAI' not in config:
            config['OpenAI'] = {}
        config['OpenAI']['model'] = selected_openai_model.get()
        
        # Add OpenAI transcription model if provided
        if selected_openai_transcription_model:
            config['OpenAI']['transcription_model'] = selected_openai_transcription_model.get()
        
        # API keys
        config['APIKeys'] = {}
        for provider, key_var in api_keys.items():
            if isinstance(key_var, tk.StringVar):
                config['APIKeys'][provider] = key_var.get()
            else:
                config['APIKeys'][provider] = key_var
        
        try:
            with open(self.config_file, 'w') as f:
                config.write(f)
            return True, "Settings saved"
        except Exception as e:
            return False, f"Error saving settings: {str(e)}"