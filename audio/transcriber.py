import threading
import os
import whisper

class Transcriber:
    def __init__(self, model_name="base"):
        self.whisper_model_name = model_name
        self.whisper_model = None
        self.temp_audio_file = "temp_recording.wav"
    
    def load_model(self, model_name=None):
        """Load Whisper model"""
        if model_name:
            self.whisper_model_name = model_name
        
        try:
            self.whisper_model = whisper.load_model(self.whisper_model_name)
            return True, f"Whisper {self.whisper_model_name} model loaded"
        except Exception as e:
            return False, f"Error loading Whisper model: {str(e)}"
    
    def transcribe(self, callback=None):
        """Transcribe audio file and return the text via callback"""
        if not os.path.exists(self.temp_audio_file):
            if callback:
                callback(False, "No recording found to transcribe", None)
            return False, "No recording found to transcribe", None
        
        if self.whisper_model is None:
            if callback:
                callback(False, "Whisper model not loaded yet", None)
            return False, "Whisper model not loaded yet", None
        
        try:
            # Transcribe audio using the loaded Whisper model
            result = self.whisper_model.transcribe(self.temp_audio_file)
            
            # Get the transcribed text
            transcribed_text = result["text"]
            
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