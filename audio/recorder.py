import pyaudio
import wave
import threading
import os
import subprocess
import shutil
from pathlib import Path

class AudioRecorder:
    def __init__(self, sample_rate=16000, chunk_size=1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_recording = False
        self.audio_thread = None
        self.frames = []
        self.temp_audio_file = "temp_recording.wav"
        self.recording_completed = False
    
    def start_recording(self):
        # Reset any existing recording completion flag
        self.recording_completed = False
        self.is_recording = True
        self.frames = []
        
        # Start recording in a separate thread
        self.audio_thread = threading.Thread(target=self.record_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        return True
    
    def stop_recording(self):
        self.is_recording = False
        return True
    
    def record_audio(self):
        try:
            p = pyaudio.PyAudio()
            
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
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
            if self.frames:  # Only save if we have frames
                try:
                    wf = wave.open(self.temp_audio_file, 'wb')
                    wf.setnchannels(1)
                    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(self.frames))
                    wf.close()
                except Exception as e:
                    print(f"Error saving audio file: {e}")
            else:
                print("No audio frames recorded")
            
            # Signal that recording is completed
            self.recording_completed = True
            
        except Exception as e:
            print(f"Recording error: {e}")
            self.recording_completed = True  # Mark as completed even on error
    
    def import_audio_file(self, file_path):
        """Import an audio file with optional conversion to WAV format"""
        if not file_path:
            return False, "No file selected"
        
        try:
            # Check if we need to convert the audio (for non-WAV files)
            if not file_path.lower().endswith('.wav'):
                # Use ffmpeg to convert to WAV format if available
                ffmpeg_cmd = shutil.which('ffmpeg')
                if ffmpeg_cmd:
                    # Create command to convert to WAV
                    convert_cmd = [
                        ffmpeg_cmd, 
                        '-i', file_path, 
                        '-ar', str(self.sample_rate),
                        '-ac', '1',  # Mono audio
                        '-y',  # Overwrite output file
                        self.temp_audio_file
                    ]
                    subprocess.run(convert_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    return True, f"Audio file converted and imported: {file_path}"
                else:
                    # No ffmpeg, can't convert
                    return False, "Cannot convert non-WAV files without ffmpeg. Please install ffmpeg or use WAV files."
            else:
                # For WAV files, just copy
                shutil.copy(file_path, self.temp_audio_file)
                return True, f"Audio file imported: {file_path}"
                
        except Exception as e:
            return False, f"Error importing file: {str(e)}"
    
    def clean_up(self):
        """Remove temporary audio file if it exists"""
        if os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
                return True
            except Exception as e:
                print(f"Error removing temporary file: {e}")
                return False
        return True  # Nothing to clean up