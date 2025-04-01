# TalkToMe

TalkToMe is a desktop application that combines audio recording, transcription, and LaTeX conversion for academic and scientific content. It allows users to speak mathematical equations and technical content, which are then transcribed and converted to proper LaTeX notation.

## Features

- Audio recording and importing from various file formats
- Speech-to-text transcription using either:
  - Local Whisper model (offline processing)
  - OpenAI API (cloud-based processing)
- Conversion of transcribed text to LaTeX notation
- Multiple formatting options for output
- Support for various AI providers (Ollama for fully local operation, OpenAI, Google, etc.) (Some providers might not work properly for now, OpenAI and Google work great)
- Customizable system prompts and model settings

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/talkToMe.git
   cd talkToMe
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. For local transcription, you need:
   - OpenAI's Whisper for offline speech-to-text
   - ffmpeg for audio file processing (optional, for importing non-WAV files)

4. For OpenAI transcription API, you need:
   - An OpenAI API key with access to audio transcription models

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. Record audio or import an audio file
3. Transcribe the audio using either local Whisper or OpenAI API
4. Convert the transcription to LaTeX notation
5. Save the LaTeX output

## Configuration

TalkToMe stores configurations in `~/.speech2latex.ini`. Settings include:

- Transcription method (Local Whisper or OpenAI API)
- Whisper model size (tiny, base, small, medium, large)
- OpenAI API key and model selection
- Audio sample rate
- System prompts for LLM processing

## Requirements

- Python 3.8+
- PyAudio
- OpenAI Whisper
- tkinter
- Other dependencies in requirements.txt

## License

See LICENSE file for details.

## Disclaimer

This software is provided "as-is" without any guarantees or warranties. Users are responsible for complying with API terms of service and for any costs associated with API usage.