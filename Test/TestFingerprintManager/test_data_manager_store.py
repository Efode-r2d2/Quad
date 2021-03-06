from Utilities import dir_manager
from Utilities import audio_manager
from Core import STFT
from Core import PeakExtractor
from Core import FingerprintGenerator
from FingerprintManager import FingerprintManager

# Source directory for reference audio files
src_dir = "../../../Test_Data/Reference_Audios/"
# retrieving all reference audios under specified source directory
reference_audios = dir_manager.find_mp3_files(src_dir=src_dir)
# an object for Short Time Fourier Transform
stft = STFT(n_fft=1024, hop_length=32, sr=7000)
# an object to extract spectral peaks from STFT based spectrogram
peak_extractor = PeakExtractor(maximum_filter_width=150, maximum_filter_height=75)
# an object to generate fingerprints using the association of four spectral peaks
fingerprint_generator = FingerprintGenerator(
    frames_per_second=219,
    target_zone_width=2,
    target_zone_center=4,
    number_of_quads_per_second=9,
    tolerance=0.0
)
# Data manager object
fingerprint_manager = FingerprintManager(db_path="../../../Databases/Quads_Test_1.db")
count = 1
for i in reference_audios:
    audio_title = i.split("/")[5].split(".")[0]
    # loading time series audio data of one of reference audio
    audio_data = audio_manager.load_audio(audio_path=i, sr=7000)
    # computing the spectrogram of time series audio data
    spectrogram = stft.compute_spectrogram_magnitude_in_db(audio_data=audio_data)
    # extracting spectral peaks from STFT based spectrogram
    spectral_peaks = peak_extractor.extract_spectral_peaks(spectrogram=spectrogram)
    # generate fingerprints using the association of four spectral peaks
    audio_fingerprints = fingerprint_generator.generate_fingerprints(spectral_peaks=spectral_peaks[0],
                                                                     spectrogram=spectrogram)
    # storing fingerprints
    fingerprint_manager.store_fingerprints(audio_fingerprints=audio_fingerprints,
                                           spectral_peaks=spectral_peaks[0],
                                           audio_title=audio_title)
    print("Done Fingerprinting ", count, audio_title)
    count += 1
