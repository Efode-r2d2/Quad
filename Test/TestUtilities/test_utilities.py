from Utilities import audio_manager
from Utilities import dir_manager

# source directory for reference audio files
src_dir = "../../../Test_Data/Reference_Audios/"
# reading all mp3 audios under specified source directory
mp3_files = dir_manager.find_mp3_files(src_dir=src_dir)
# retrieved audio files under specified source directory
for i in mp3_files:
    print(i)
# load audio data with sampling rate of 7KHz and
audio_data = audio_manager.load_audio(audio_path=mp3_files[1], sr=7000, offset=10.0, duration=10.0)
print("Time Series Audio Data")
for i in audio_data:
    print(i)
