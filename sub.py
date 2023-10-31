import os
import subprocess
import speech_recognition as sr
from pydub import AudioSegment

# Prompt the user for the video URL and the word to search for
video_url = input("Enter the video URL: ")
search_word = input("Enter the word to search for: ")

# Create a directory for the output if it doesn't exist
if not os.path.exists("sub"):
    os.makedirs("sub")

# Step 1: Download the video using yt-dlp prioritizing H.264 codec
start_time = input("Enter the start time in seconds: ")
end_time = input("Enter the end time in seconds: ")
os.system(f'yt-dlp {video_url} -f bestvideo[ext=mp4][vcodec=avc1]+bestaudio[ext=m4a]/best[ext=mp4] --external-downloader ffmpeg --external-downloader-args "ffmpeg_i:-ss {start_time} -to {end_time}" -o video.mp4')

# Step 2: Convert the downloaded video to .wav audio format using ffmpeg
subprocess.call(['ffmpeg', '-i', 'video.mp4', 'audio.wav'])

# Step 3: Split the audio file into chunks
audio = AudioSegment.from_wav("audio.wav")
chunk_length_ms = 1000  # 1 second chunks
chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

# Step 4: Transcribe each chunk and search for the specified word
def transcribe_and_search(audio_chunk, chunk_number):
    temp_filename = f'temp_chunk{chunk_number}.wav'
    audio_chunk.export(temp_filename, format="wav")
    
    r = sr.Recognizer()
    with sr.AudioFile(temp_filename) as source:
        audio_data = r.record(source)
        try:
            transcription = r.recognize_google(audio_data)
            if search_word.lower() in transcription.lower():
                start_time = chunk_number
                end_time = chunk_number + 1
                
                output_filename = f'sub/chunk{chunk_number}.mp4'
                subprocess.call([
                    'ffmpeg', '-y',
                    '-i', 'video.mp4',
                    '-ss', str(start_time),
                    '-to', str(end_time),
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    output_filename
                ])
                print(f"Word found in chunk {chunk_number}. Video saved to {output_filename}")
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
        
    os.remove(temp_filename)

for i, chunk in enumerate(chunks):
    transcribe_and_search(chunk, i)

def merge_clips():
    user_input = input("Do you want to merge all clips into a single file? (y/n): ").lower()
    if user_input == 'y':
        with open('filelist.txt', 'w') as file:
            for i in range(len(chunks)):
                chunk_file = f'sub/chunk{i}.mp4'
                if os.path.exists(chunk_file):
                    file.write(f"file '{chunk_file}'\n")

        subprocess.call([
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', 'filelist.txt',
            '-c', 'copy',
            'merged_output.mp4'
        ])
        print("Merging completed. The merged file is saved as merged_output.mp4.")

merge_clips()

if os.path.exists("audio.wav"):
    os.remove("audio.wav")

if os.path.exists("video.mp4"):
    os.remove("video.mp4")
