import numpy as np
from operator import itemgetter
from scipy.ndimage import maximum_filter
from scipy.ndimage import minimum_filter


class PeakExtractor(object):
    """
    A class to extract spectral peaks from spectrogram of an audio.

    Attributes:
        maximum_filter_height (int): Defines height of maximum filter.
        maximum_filter_width (int): Defines the width of maximum filter.
        minimum_filter_height (int): Defines the height of minimum filter.
        minimum_filter_width (int): Defines the width of minimum filter.

    """
    def __init__(self, maximum_filter_height=75, minimum_filter_height=3,
                 maximum_filter_width=150, minimum_filter_width=3):
        """
        A constructor method for PeakExtractor class.

        Parameters:
            maximum_filter_height (int): Defines the height of maximum filter.
            maximum_filter_width (int): Defines the width of maximum filter.
            minimum_filter_height (int): Defines the height of minimum filter.
            minimum_filter_width (int): Defines the width of minimum filter.

        """
        self.maximum_filter_height = maximum_filter_height
        self.maximum_filter_width = maximum_filter_width
        self.minimum_filter_height = minimum_filter_height
        self.minimum_filter_width = minimum_filter_width

    def extract_spectral_peaks(self, spectrogram):
        """
        A method to extract spectral peaks given the spectrogram of an audio.

        Parameters:
            spectrogram (
        """
        # computing local maximum points with the specified maximum filter dimension
        local_max_values = maximum_filter(input=spectrogram, size=(self.maximum_filter_height,
                                                                   self.maximum_filter_width))
        # extracting time and frequency information for local maximum points
        j, i = np.where(spectrogram == local_max_values)
        peaks = list(zip(i, j))
        # computing local minimum points with specified minimum filter dimension
        local_min_values = minimum_filter(input=spectrogram, size=(self.minimum_filter_height,
                                                                   self.minimum_filter_width))
        # extracting time and frequency information for local minimums
        k, m = np.where(spectrogram == local_min_values)
        lows = list(zip(m, k))
        # avoiding spectral points with are both local maximum and local minimum
        spectral_peaks = list(set(peaks) - set(lows))
        # time and frequency information for extracted spectral peaks
        time_indices = [i[0] for i in spectral_peaks]
        freq_indices = [i[1] for i in spectral_peaks]
        spectral_peaks.sort(key=itemgetter(0))
        return spectral_peaks, time_indices, freq_indices
