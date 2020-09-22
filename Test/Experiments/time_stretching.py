from Utilities import dir_manager
from Utilities import audio_manager
from Core import STFT
from Core import PeakExtractor
from Core import FingerprintGenerator
from FingerprintManager import FingerprintManager
import time
import csv

# source directory for query audios
src_dir = "../../../Test_Data/Query_Audios/Time_Stretched/"
# retrieving all query audios under specified source directory

# STFT based spectrogram object
stft = STFT(n_fft=1024, hop_length=32, sr=7000)
# peak extractor object
peak_extractor = PeakExtractor(maximum_filter_width=150, maximum_filter_height=75)
# fingerprint generator object
fingerprint_generator = FingerprintGenerator(
    frames_per_second=219,
    target_zone_width=2,
    target_zone_center=4,
    number_of_triplets_per_second=50,
    tolerance=0.31)
# fingerprint manager object
data_manager = FingerprintManager(db_path="../../../Databases/Quads_Test_1.db")
result_path = "../../../New_Results/Quad/Time_Stretching/"
for j in range(70, 135, 5):
    query_audios = dir_manager.find_wav_files(src_dir=src_dir + str(j))
    count = 1
    for i in query_audios:
        audio_title = i.split("/")[7].split(".")[0]
        audio_data = audio_manager.load_audio(audio_path=i, sr=7000, offset=0.0, duration=30.0)
        spectrogram = stft.compute_spectrogram_magnitude_in_db(audio_data=audio_data)
        spectral_peaks = peak_extractor.extract_spectral_peaks(spectrogram=spectrogram)
        audio_fingerprints = fingerprint_generator.generate_fingerprints(spectral_peaks=spectral_peaks[0],
                                                                         spectrogram=spectrogram)
        start = time.time()
        match = data_manager.query_audio(audio_fingerprints=audio_fingerprints, spectral_peaks=spectral_peaks[0])
        end = time.time()
        print("Requested ", "Match Found ", "Detected at ", "Temp Mod ", "Pitch Mod ", "Response Time ", "V_Score")
        print(audio_title, match[0], round((match[1] / 219), 3), round(match[2], 3), round(match[3], 3), end - start,
              round(match[4], 3))
        result = None
        if match[0] == "No Match":
            result = "False Negative"
        else:
            if audio_title == match[0]:
                result = "True Positive"
            else:
                result = "False Positive"
        row = [count, audio_title, match[0], result, round((match[1] / 219), 3), round(match[2], 3), round(match[3], 3),
               end - start,
               round(match[4], 3)]
        with open(result_path + str(j) + ".csv", 'a') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(row)
        csvFile.close()
        count += 1
