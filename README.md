# Multimedia Player Project

This project is a **Multimedia Player** developed for the **Multimedia Laboratory Course**.

It includes:
- An **audio player** with seek bar, time display, and volume control.
- A **video player** with support for seek bar, volume control, and external subtitles (`.srt`).
- A **main menu** to choose between audio and video players.
- Basic **dark/light theme** support with a modern UI.

---

## Requirements

- **Windows** operating system (due to the use of `set_hwnd` for video output).  
- **Python 3.8 or higher**
- **VLC Media Player (64-bit recommended)**

### Python Libraries
- python-vlc

> **Note:** `python-vlc` requires VLC Media Player to be installed on the system because it uses the `libvlc` library.

---

## Installation

### 1. Install Python
Download and install Python from:
https://www.python.org/downloads/

Make sure to check **"Add Python to PATH"** during installation.

---

### 2. Install VLC Media Player
Download and install VLC Media Player from:
https://www.videolan.org/vlc/

 **Important**:
- Python 64-bit → VLC 64-bit  
- Python 32-bit → VLC 32-bit  

Both must match to avoid runtime errors.

---

### 3. Install Python Dependencies
All required Python libraries are listed in the `dependencies.txt` file.

Run the following command from the project folder:

```bash
pip install -r dependencies.txt
```

## Running the Application

Clone or download this repository.

Ensure that VLC is installed and `python-vlc` is available in your Python environment.

To start the application, run:

```bash
python reproductor.py
```

---

## Features

### Main Menu

- Launch the audio or video player
- Toggle light/dark theme

### Audio Player

- Play, pause, and stop
- Seek bar with current and total time
- Volume control
- Displays loaded file name

### Video Player

- Play, pause, and stop
- Seek bar with time display
- Volume control
- Support for `.srt` subtitles
- Overlay display for subtitles

---

## Notes

- The application is designed and tested for Windows.
- Ensure VLC is properly installed and accessible by `python-vlc`.
- Subtitle support is limited to `.srt` format.
