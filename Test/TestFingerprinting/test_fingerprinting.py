from Utilities import dir_manager
from Utilities import audio_manager
from Core import STFT
from Core import PeakExtractor
from Core import FingerprintGenerator
from FingerprintManager import FingerprintManager

# defining constants
SAMPLING_RATE = 7000

# a source directory for all reference audios
src_dir = "../../../Test_Data/Reference_Audios"
# retrieving all reference audios under specified source directory
reference_audios = dir_manager.find_mp3_files(src_dir=src_dir)
# Declaring an object for Short Time Fourier Transform (STFT)
stft = STFT(n_fft=1024, hop_length=32, sr=7000)
# Spectral peak extractor object
peak_extractor = PeakExtractor(maximum_filter_width=150, maximum_filter_height=75)
# Fingerprint generator object
fingerprint_generator = FingerprintGenerator(
    frames_per_second=219,
    target_zone_width=1,
    target_zone_center=2,
    number_of_quads_per_second=9,
    tolerance=0.31)
# reading 10 second audio data sampled at 7KHz
audio_data = audio_manager.load_audio(audio_path=reference_audios[0], sr=SAMPLING_RATE, offset=10.0, duration=10.0)
# computing spectrogram of times series audio data.
spectrogram = stft.compute_spectrogram_magnitude_in_db(audio_data=audio_data)
print(spectrogram)
# extracting spectral peaks from the spectrogram of the audio.
spectral_peaks = peak_extractor.extract_spectral_peaks(spectrogram=spectrogram)
print(spectral_peaks)
# generate audio fingerprints
audio_fingerprints = fingerprint_generator.generate_fingerprints(
    spectral_peaks=spectral_peaks[0],
    spectrogram=spectrogram)
print(audio_fingerprints)
