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
- **Python 3.10+**

### Python packages

Installable via `pip`:

- `python-vlc`  
- Standard library modules:
  - `tkinter`
  - `threading`
  - `time`
  - `re`
  - `tkinter.ttk`
  - `tkinter.font`

> Most Python for Windows installations include `tkinter` by default.

### VLC

This project uses **VLC Media Player** via `python-vlc` bindings.

You must have:

- **VLC Media Player** installed on your system  
- `python-vlc` correctly linked to that installation

---

## Installation

1. Download and Install **VLC Media Player**:  
   <https://www.videolan.org/vlc/>

2. Install Python dependency:

   ```bash
   pip install python-vlc
   ```

   If you're using a virtual environment, activate it before installing.

---

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
