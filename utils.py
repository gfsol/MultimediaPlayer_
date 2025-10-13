from pydub import AudioSegment
import subprocess

def mp3_to_wav(mp3Path, wavPath):

    audio = AudioSegment.from_mp3(mp3Path)
    audio.export(wavPath, format="wav")

def convert_mp4_to_avi(input_file, output_file):
    command = [
        "ffmpeg",
        "-i", input_file,
        "-c:v", "mpeg4",    # codec de video compatible
        "-c:a", "mp3",      # codec de audio
        output_file
    ]
    subprocess.run(command, check=True)
    
    