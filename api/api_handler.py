import requests
import time
import threading
from google import genai

class APIHandler:
    def __init__(self, settings):
        self.settings = settings
    
    def convert_text(self, text, callback=None):
        """Convert text to LaTeX using the selected API provider"""
        provider = self.settings.selected_provider
        mode = self.settings.selected_prompt_mode
        system_prompt = self.settings.system_prompt
        prompt_template = self.settings.mode_prompts[mode]
        
        # Start conversion in a separate thread
        threading.Thread(
            target=self._convert_text_thread,
            args=(text, provider, mode, prompt_template, system_prompt, callback),
            daemon=True
        ).start()
    
    def _convert_text_thread(self, text, provider, mode, prompt_template, system_prompt, callback):
        """Thread function to handle text conversion"""
        try:
            start_time = time.time()
            
            # For Google Gemini, process the entire text at once
            if provider == "Google Gemini":
                if mode == "Class Notes (PDF Style)":
                    # Use string replacement instead of format() for PDF Style
                    combined_prompt = prompt_template.replace("{INPUT_TEXT}", text)
                else:
                    combined_prompt = prompt_template.format(text=text)
                
                # Process the entire text with Google Gemini
                final_output = self._convert_using_gemini(text, combined_prompt, system_prompt)
                
                if callback:
                    callback(True, "LaTeX conversion complete", final_output)
                return
            
            # For other providers, chunk the text if needed
            max_chunk_length = 10000  # Define maximum chunk length (adjust based on model limits)
            if len(text) > max_chunk_length:
                chunks = self._chunk_text(text, max_length=max_chunk_length)
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
                    model = self.settings.ollama_model_name
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
                
                # Calculate progress
                progress = (i + 1) / len(chunks) * 100
                if callback:
                    callback(True, f"Processing chunk {i+1}/{len(chunks)}", final_output, progress)
            
            if callback:
                callback(True, "LaTeX conversion complete", final_output, 100)
            
        except Exception as e:
            if callback:
                callback(False, f"LaTeX conversion error: {str(e)}", None)
    
    def _chunk_text(self, text, max_length=2000):
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
        """Call API with retry logic for rate limiting"""
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
        
        # Send request to Ollama
        response = requests.post(
            f"{self.settings.ollama_base_url}/generate",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
    
    def _convert_using_openai(self, text, prompt, system_prompt):
        """Convert text to LaTeX using OpenAI API"""
        api_key = self.settings.api_keys["OpenAI"]
        if not api_key:
            raise ValueError("OpenAI API key is not configured. Please add your API key in the settings.")
            
        # Get selected model ID
        model_name = self.settings.selected_openai_model
        
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
        
        response = self._call_api_with_retry(api_call)
        
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
    
    def _convert_using_anthropic(self, text, prompt, system_prompt):
        """Convert text to LaTeX using Anthropic API"""
        api_key = self.settings.api_keys["Anthropic"]
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
        
        response = requests.post(endpoint, headers=headers, json=payload)
        
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
        api_key = self.settings.api_keys["Perplexity"]
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
        
        response = requests.post(endpoint, headers=headers, json=payload)
        
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
        api_key = self.settings.api_keys["Mistral"]
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
        
        response = requests.post(endpoint, headers=headers, json=payload)
        
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
        api_key = self.settings.api_keys["Google Gemini"]
        if not api_key:
            raise ValueError("Google Gemini API key is not configured. Please add your API key in the settings.")
        
        # Create a client instance
        client = genai.Client(api_key=api_key)
        
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
            
            # Extract the response text
            return response.text.strip()
            
        except Exception as e:
            error_message = f"Google Gemini API error: {str(e)}"
            raise Exception(error_message)