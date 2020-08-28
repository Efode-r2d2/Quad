
import librosa


def load_audio(audio_path, sr=7000, offset=None, duration=None):
    """
    A function to load monophonic time series representation of an audio.

    Parameters:
        audio_path (String): relative/absolute path of a give audio.
        sr (int): sampling rate
        offset (int): an offset in seconds where reading the audio starts.
        duration (int): duration of reading (in seconds).

    Returns:
        numpy.ndarray: monophonic time series representation of the given audio.

    """
    if offset is not None and duration is not None:
        audio_data, sr = librosa.load(path=audio_path,
                                      sr=sr, offset=offset, duration=duration)
        return audio_data
    else:
        audio_data, sr = librosa.load(path=audio_path,
                                      sr=sr)
        return audio_data
