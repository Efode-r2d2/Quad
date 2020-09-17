import librosa
import numpy as np


class STFT(object):
    """
    This is a class used for computing a time-frequency representation (spectrogram) of an audio given its mono
    phonic time-series representation. This transform is based on a well known music analysis tool called Short Time
    Fourier Transform (STFT)."

    Attributes:
        n_fft (int): defines number of DFT bins.
        hop_length (int): hop length required by the transform function.
        sr (int): sampling rate

    """

    def __init__(self, n_fft=1024, hop_length=32, sr=7000):
        """
        The constructor for Spectrogram class.

        Parameters:
            n_fft (int): NFFT of the transform function.
            hop_length (int): hop length of the transform function.
            sr (int): Sampling rate.
        """
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.sr = sr

    def __compute_spectrogram(self, audio_data):
        """
        A method to compute the spectrogram of an audio from its time series representation.

        Parameters:
            audio_data (numpy.ndarray): Time series representation of a given audio.

        Returns:
            numpy.ndarray: Time-frequency representation of of given time series audio data.

        """
        spectrogram = librosa.stft(y=audio_data, n_fft=self.n_fft, hop_length=self.hop_length)
        return spectrogram

    def __compute_spectrogram_magnitude(self, audio_data):
        """
        A method to compute a a spectrogram magnitude of give time series audio data.

        Parameters:
            audio_data (numpy.ndarray): Monophonic time series representation of audio data.

        Returns:
            numpy.ndarray: Magnitude of spectrogram of a give audio data.

        """
        spectrogram = self.__compute_spectrogram(audio_data)
        spectrogram_magnitude = np.abs(spectrogram)
        return spectrogram_magnitude

    def compute_spectrogram_magnitude_in_db(self, audio_data):
        """
        A method to compute a magnitude of spectrogram of an audio in db.

        Parameters:
            audio_data (numpy.ndarray): Monophonic time series representation of a given audio.

        Returns:
            numpy.ndarray: magnitude of spectrogram of an audio in db.

        """
        spectrogram_magnitude = self.__compute_spectrogram_magnitude(audio_data)
        spectrogram_magnitude_in_db = librosa.amplitude_to_db(spectrogram_magnitude, ref=np.max)
        return spectrogram_magnitude_in_db
