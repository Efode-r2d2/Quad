from Utilities import DirManager
from Utilities import AudioManager
from Core import STFT
from Core import PeakExtractor
from Core import FingerprintGenerator
from DataManager import DataManager

# source directory for query audios
src_dir = "../../../Test_Data/Modified_Audios/Speed_Change/80"
# retrieving all query audios under specified directory
query_audios = DirManager.find_wav_files(src_dir=src_dir)
# loading a time series audio data from one of the query audio
audio_data = AudioManager.load_audio(audio_path=query_audios[1], sampling_rate=7000, offset=10.0, duration=30.0)
# an object for computing stft based spectrogram
stft = STFT(n_fft=1024, hop_length=32, sr=700)
# computing stft based spectrogram of time series audio data
spectrogram = stft.compute_stft_magnitude_in_db(audio_data=audio_data)
# an object to extract spectral peaks from stft based spectrogram
peak_extractor = PeakExtractor(maximum_filter_width=150, maximum_filter_height=75)
# extracting spectral peaks from STFT based spectrogram
spectral_peaks = peak_extractor.extract_spectral_peaks_2(spectrogram=spectrogram)
# an object to generate quad based audio fingerprints
fingerprint_generator = FingerprintGenerator(target_zone_width=1, target_zone_center=2, tolerance=0.31)
# generate quad based fingerprints
audio_fingerprints = fingerprint_generator.__generate_fingerprints__(spectral_peaks=spectral_peaks[0])
# DataManager object
data_manager = DataManager(db_path="../../../Hashes/Quad/Quad.db")
# query matches
data_manager.__query__(audio_fingerprints=audio_fingerprints)

