# Multimedia Player Project

This project is a **Multimedia Player** developed for the **Multimedia Laboratory Course**.

## Requirements

- **Windows** operating system  
- **Python 3.10+**  
- Python packages:  
  - `tkinter`  
  - `pyaudio`  
  - `wave`  

- **FFmpeg executables** (`ffmpeg.exe`, `ffplay.exe`, `ffprobe.exe`) must be present in the root folder of the repository.  
  > **Note:** These are **not included** in the repository due to GitHub file size limits.

## Installing FFmpeg on Windows

1. Go to the official FFmpeg website: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)  
2. Download the **Windows static build**.  
3. Extract the contents and copy the following files into the **root folder** of this project:  
   - `ffmpeg.exe`  
   - `ffplay.exe`  
   - `ffprobe.exe`  

## Installation & Running

1. Clone or download this repository.  
2. Ensure the FFmpeg executables are in the root folder.  
3. Install the required Python packages (tkinter and wave are usually included with Python on Windows.):

```bash
pip install pyaudio
```
4. Run the python script:
```bash
python reproductor.py
```
