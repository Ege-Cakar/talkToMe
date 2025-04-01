import threading
import os
import whisper
from openai import OpenAI
from pydub import AudioSegment
import tempfile

class Transcriber:
    def __init__(self, model_name="base", transcription_method="whisper"):
        self.whisper_model_name = model_name
        self.whisper_model = None
        self.transcription_method = transcription_method  # "whisper" or "openai"
        self.temp_audio_file = "temp_recording.wav"
        self.openai_client = None
        self.openai_model = "gpt-4o-transcribe"
        self.openai_api_key = None
    
    def load_model(self, model_name=None, transcription_method=None, api_key=None):
        """Load Whisper model or initialize OpenAI client"""
        if model_name:
            self.whisper_model_name = model_name
        
        if transcription_method:
            self.transcription_method = transcription_method
            
        if api_key:
            self.openai_api_key = api_key
        
        try:
            if self.transcription_method == "whisper":
                self.whisper_model = whisper.load_model(self.whisper_model_name)
                return True, f"Whisper {self.whisper_model_name} model loaded"
            elif self.transcription_method == "openai":
                if not self.openai_api_key:
                    return False, "OpenAI API key is required for transcription"
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                return True, "OpenAI transcription API ready"
            else:
                return False, f"Unknown transcription method: {self.transcription_method}"
        except Exception as e:
            return False, f"Error initializing transcription: {str(e)}"
    
    def transcribe(self, callback=None):
        """Transcribe audio file and return the text via callback"""
        if not os.path.exists(self.temp_audio_file):
            if callback:
                callback(False, "No recording found to transcribe", None)
            return False, "No recording found to transcribe", None
        
        # Ensure the proper model/client is initialized based on transcription method
        if self.transcription_method == "whisper" and self.whisper_model is None:
            try:
                self.whisper_model = whisper.load_model(self.whisper_model_name)
            except Exception as e:
                error_msg = f"Error loading Whisper model: {str(e)}"
                if callback:
                    callback(False, error_msg, None)
                return False, error_msg, None
                
        elif self.transcription_method == "openai" and self.openai_client is None:
            try:
                if not self.openai_api_key:
                    error_msg = "OpenAI API key is required for transcription"
                    if callback:
                        callback(False, error_msg, None)
                    return False, error_msg, None
                self.openai_client = OpenAI(api_key=self.openai_api_key)
            except Exception as e:
                error_msg = f"Error initializing OpenAI client: {str(e)}"
                if callback:
                    callback(False, error_msg, None)
                return False, error_msg, None
                
        # Final check if initialization succeeded
        if self.transcription_method == "whisper" and self.whisper_model is None:
            if callback:
                callback(False, "Whisper model not loaded yet", None)
            return False, "Whisper model not loaded yet", None
        elif self.transcription_method == "openai" and self.openai_client is None:
            if callback:
                callback(False, "OpenAI client not initialized", None)
            return False, "OpenAI client not initialized", None
        
        try:
            if self.transcription_method == "whisper":
                # Transcribe audio using the loaded Whisper model
                result = self.whisper_model.transcribe(self.temp_audio_file)
                transcribed_text = result["text"]
            elif self.transcription_method == "openai":
                # Transcribe audio using OpenAI API with chunking for large files
                full_transcription = ""
                
                # Load the audio file
                audio = AudioSegment.from_wav(self.temp_audio_file)
                
                # OpenAI limit: 25MB per chunk
                max_size_bytes = 25 * 1024 * 1024
                
                # Check if we need to chunk the audio
                file_size = os.path.getsize(self.temp_audio_file)
                
                if file_size <= max_size_bytes:
                    # Small enough to process directly
                    with open(self.temp_audio_file, "rb") as audio_file:
                        transcription = self.openai_client.audio.transcriptions.create(
                            model=self.openai_model,
                            file=audio_file
                        )
                    full_transcription = transcription.text
                else:
                    # Need to chunk the audio
                    if callback:
                        callback(True, f"Audio file is large ({file_size/1024/1024:.1f}MB). Splitting into chunks for processing...", None)
                    
                    # Determine chunk duration
                    # Estimate: ~1MB per minute for 16kHz, 16-bit mono WAV
                    # Conservative approach: 10 minutes per chunk
                    chunk_duration_ms = 10 * 60 * 1000  # 10 minutes in milliseconds
                    
                    # Calculate total duration and number of chunks
                    total_duration_ms = len(audio)
                    num_chunks = (total_duration_ms + chunk_duration_ms - 1) // chunk_duration_ms  # Ceiling division
                    
                    # Process each chunk
                    for i in range(num_chunks):
                        start_ms = i * chunk_duration_ms
                        end_ms = min((i + 1) * chunk_duration_ms, total_duration_ms)
                        
                        # Extract chunk
                        chunk = audio[start_ms:end_ms]
                        
                        # Create a temporary file for the chunk
                        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                            chunk_filename = temp_file.name
                            chunk.export(chunk_filename, format="wav")
                        
                        try:
                            # Process the chunk
                            if callback:
                                progress = (i * 100) // num_chunks
                                callback(True, f"Processing chunk {i+1}/{num_chunks} ({progress}% complete)", None)
                                
                            with open(chunk_filename, "rb") as audio_file:
                                chunk_transcription = self.openai_client.audio.transcriptions.create(
                                    model=self.openai_model,
                                    file=audio_file
                                )
                            
                            # Append to full transcription
                            if full_transcription and not full_transcription.endswith(('.', '!', '?', '\n')):
                                full_transcription += " "
                            full_transcription += chunk_transcription.text
                            
                        finally:
                            # Clean up temporary file
                            if os.path.exists(chunk_filename):
                                os.remove(chunk_filename)
                
                transcribed_text = full_transcription
            else:
                if callback:
                    callback(False, f"Unknown transcription method: {self.transcription_method}", None)
                return False, f"Unknown transcription method: {self.transcription_method}", None
            
            if callback:
                callback(True, "Transcription complete", transcribed_text)
            
            return True, "Transcription complete", transcribed_text
        except Exception as e:
            if callback:
                callback(False, f"Transcription error: {str(e)}", None)
            return False, f"Transcription error: {str(e)}", None
    
    def transcribe_async(self, callback):
        """Transcribe audio file asynchronously and call callback when done"""
        threading.Thread(target=self._transcribe_thread, args=(callback,), daemon=True).start()
    
    def _transcribe_thread(self, callback):
        """Thread function to handle transcription"""
        success, message, text = self.transcribe()
        callback(success, message, text)