import subprocess
import shutil
import platform
import requests
import threading
import time
import os

class OllamaManager:
    def __init__(self, base_url="http://localhost:11434/api"):
        self.ollama_base_url = base_url
        self.ollama_process = None
        self.ollama_models = []
    
    def is_ollama_installed(self):
        """Check if the ollama command is available"""
        return shutil.which('ollama') is not None
    
    def is_ollama_running(self):
        """Check if Ollama server is running by testing the API endpoint"""
        try:
            response = requests.get(f"{self.ollama_base_url}/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def start_ollama(self, callback=None):
        """Start Ollama server"""
        # First check if it's already running
        if self.is_ollama_running():
            if callback:
                callback(True, "Ollama is already running")
            return True, "Ollama is already running"

        if self.ollama_process is not None:
            if callback:
                callback(False, "Ollama startup already in progress")
            return False, "Ollama startup already in progress"
        
        # Find the ollama command
        ollama_cmd = shutil.which('ollama')
        if not ollama_cmd:
            if callback:
                callback(False, "Ollama command not found. Please install Ollama from ollama.ai")
            return False, "Ollama command not found. Please install Ollama from ollama.ai"
        
        try:
            # Start Ollama as a background process
            if callback:
                callback(True, "Starting Ollama...", in_progress=True)
            
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
            
            # Start a thread to check if Ollama starts successfully
            threading.Thread(target=self._check_ollama_startup, args=(callback,), daemon=True).start()
            
            return True, "Starting Ollama..."
            
        except Exception as e:
            if callback:
                callback(False, f"Error starting Ollama: {str(e)}")
            return False, f"Error starting Ollama: {str(e)}"
    
    def _check_ollama_startup(self, callback=None, max_attempts=15, delay=2):
        """Check if Ollama has started successfully"""
        attempts = 0
        while attempts < max_attempts:
            if self.is_ollama_running():
                if callback:
                    callback(True, "Ollama started successfully")
                self.load_ollama_models()
                return
            
            # Wait and try again
            time.sleep(delay)
            attempts += 1
        
        # If we get here, Ollama failed to start
        if callback:
            callback(False, "Ollama failed to start after multiple attempts")
    
    def stop_ollama(self, callback=None):
        """Stop Ollama server"""
        # Check if Ollama is running but wasn't started by us
        if self.is_ollama_running() and self.ollama_process is None:
            if callback:
                callback(False, "Ollama was not started by this application. Please close the Ollama application manually.")
            return False, "Ollama was not started by this application. Please close the Ollama application manually."
            
        # Otherwise, try to stop our process
        if self.ollama_process is None:
            if callback:
                callback(False, "Ollama is not running")
            return False, "Ollama is not running"
        
        try:
            # Terminate the process
            self.ollama_process.terminate()
            
            # Wait for process to terminate
            try:
                self.ollama_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ollama_process.kill()
            
            self.ollama_process = None
            if callback:
                callback(True, "Ollama stopped")
            return True, "Ollama stopped"
        except Exception as e:
            if callback:
                callback(False, f"Error stopping Ollama: {str(e)}")
            return False, f"Error stopping Ollama: {str(e)}"
    
    def load_ollama_models(self, callback=None):
        """Load available Ollama models"""
        try:
            response = requests.get(f"{self.ollama_base_url}/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.ollama_models = [model["name"] for model in data.get("models", [])]
                
                if callback:
                    callback(True, f"Loaded {len(self.ollama_models)} Ollama models", self.ollama_models)
                return True, f"Loaded {len(self.ollama_models)} Ollama models", self.ollama_models
            else:
                if callback:
                    callback(False, f"Failed to load Ollama models: {response.status_code}")
                return False, f"Failed to load Ollama models: {response.status_code}", []
        except Exception as e:
            if callback:
                callback(False, f"Error connecting to Ollama: {str(e)}")
            return False, f"Error connecting to Ollama: {str(e)}", []
    
    def download_model(self, model, callback=None):
        """Download a new Ollama model"""
        if not model:
            if callback:
                callback(False, "Please provide a model name", 0)
            return False, "Please provide a model name"
        
        # Check if Ollama is running
        if not self.is_ollama_running():
            if callback:
                callback(False, "Ollama needs to be running to download models", 0)
            return False, "Ollama needs to be running to download models"
            
        # Start download in a separate thread
        threading.Thread(target=self._download_model_thread, args=(model, callback), daemon=True).start()
        
        return True, f"Starting download of model '{model}'..."
    
    def _download_model_thread(self, model, callback=None):
        """Thread function to download an Ollama model"""
        try:
            # Find the ollama command
            ollama_cmd = shutil.which('ollama')
            if not ollama_cmd:
                if callback:
                    callback(False, "Ollama command not found. Please install Ollama from ollama.ai", 0)
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
                if callback:
                    callback(True, line.strip(), progress=None, in_progress=True)
                
                # Try to parse progress percentage if available
                if "%" in line:
                    try:
                        # Extract percentage from a line like "downloading: 45.23%"
                        percent_str = line.split("%")[0].split(":")[-1].strip()
                        percent = float(percent_str)
                        if callback:
                            callback(True, line.strip(), progress=percent, in_progress=True)
                    except (ValueError, IndexError):
                        pass
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                if callback:
                    callback(True, f"Successfully downloaded model '{model}'", 100)
                self.load_ollama_models()
            else:
                if callback:
                    callback(False, f"Error downloading model: return code {return_code}", 0)
                
        except Exception as e:
            if callback:
                callback(False, f"Error downloading model: {str(e)}", 0)