from Utilities import DirManager
from Utilities import AudioManager
from Core import STFT
from Core import PeakExtractor
from Core import FingerprintGenerator
from FingerprintMatching import MatchFingerprints
from FingerprintMatching import VerifyMatches
from DataManager import RTreeManager
from DataManager import RawDataManager

# query audios source directory
src_dir = "../../../Test_Data/Reference_Audios/"
# find all query audios under specified directory
query_audios = DirManager.find_mp3_files(src_dir=src_dir)
r_tree = "../../../Hashes/Quad/Test"
# raw_data_path
shelf = "../../../Raw_Data/Quad/Test"
# r_tree index
r_tree_index = RTreeManager.get_rtree_index(rtree_path=r_tree)
# raw data index
raw_data_index = RawDataManager.get_shelf_file_index(shelf_path=shelf)
'''
    Instantiate an object for short time fourier transform. This  object computes
    the spectrogram of an audio from its time series representation. 
'''
stft = STFT(n_fft=1024, hop_length=32, sr=7000)
'''
    Instantiating peak extractor object. A peak extractor object will accept
    STFT based spectrogram of an audio and it will return spectral peaks based on
    predefined parameters. Here, a spectral peak is defined in terms of its frequency and
    tempo information's.
'''
peak_extractor = PeakExtractor(maximum_filter_width=150, maximum_filter_height=75)
'''
    Instantiating a fingerprint generator object. A fingerprint generator function will accept
    spectral peaks extracted from STFT based spectrogram of an audio and it will return audio 
    fingerprints generated using the association of four spectral peaks.
'''
fingerprint_generator = FingerprintGenerator(target_zone_width=1, target_zone_center=2, tolerance=0.0)

for i in query_audios:
    audio_data = AudioManager.load_audio(audio_path=i)
    spectrogram = stft.compute_stft_magnitude_in_db(audio_data=audio_data)
    spectral_peaks = peak_extractor.extract_spectral_peaks_2(spectrogram=spectrogram)
    audio_fingerprints = fingerprint_generator.__generate_fingerprints__(spectral_peaks=spectral_peaks[0])
    # print(audio_fingerprints)
    match_in_bins = MatchFingerprints.match_fingerprints(raw_data_index=raw_data_index,
                                                         rtree_index=r_tree_index,
                                                         fingerprints=audio_fingerprints,
                                                         tolerance=0.31)
    match = VerifyMatches.verify_matches(matches_in_bins=match_in_bins)
    print(i, match)
