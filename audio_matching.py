import os, sys
import pyaudio
import wave
import numpy
import scikits.audiolab as audiolab
import matplotlib.pyplot as pyplot
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import generate_binary_structure, iterate_structure, binary_erosion

from time import sleep # DEBUG

# Audio stream settings.
AUDIO_PATH = './audio_files/'
FORMAT = pyaudio.paInt16
RATE = 44100
CHUNK = 1024

# Filter settings.
AMP_MIN = 1e-10
 
audio = pyaudio.PyAudio()

def get_audio_files():    
    result = {}
    files = [ f for f in os.listdir(AUDIO_PATH) if os.path.isfile(os.path.join(AUDIO_PATH, f)) ]
    index = 1
    for filename in files:
        if filename == '.DS_Store': continue
        result[index] = filename
        index = index + 1
    return result

audio_files = get_audio_files()

def show_menu():
    os.system('clear')

    print "\n-- Audio matching with Python --"
    print "\n  (1) Record an audio clip."
    if audio_files is not None:
        print "  (2) Play an audio clip."
        print "  (3) Match an audio clip."
        print "\n-- Audio library --\n"
        for index in audio_files:
            print "{:3}: {}".format(index, audio_files[index])

    try:
        return int(raw_input("\nPlease choose an option from the menu above, or CTRL-C and ENTER to quit: "))
    except: 
        raise

def get_2D_peaks(array2D):
    # This function is based on the function 'get_2D_peaks()' available at the URL below.
    # https://github.com/worldveil/dejavu/blob/master/dejavu/fingerprint.py
    # Copyright (c) 2013 Will Drevo, use permitted under the terms of the open-source MIT License.

    # Create a filter to extract peaks from the image data.
    struct = generate_binary_structure(2, 1)
    neighborhood = iterate_structure(struct, 25)

    # Find local maxima using our fliter shape. These are boolean arrays.
    local_maxima = maximum_filter(array2D, footprint=neighborhood) == array2D
    background = (array2D == 0)
    eroded_background = binary_erosion(background, structure=neighborhood, border_value=1)

    # Boolean mask of array2D with True at peaks.
    detected_peaks = local_maxima - eroded_background

    # Extract peak amplitudes and locations.
    amps = array2D[detected_peaks]
    j, i = numpy.where(detected_peaks)

    # Filter peaks for those exceeding the minimum amplitude.
    amps = amps.flatten()
    peaks = zip(i, j, amps)
    peaks_filtered = [x for x in peaks if x[2] > AMP_MIN]

    # Get frequency and time at peaks.
    frequency_idx = [x[1] for x in peaks_filtered]
    time_idx = [x[0] for x in peaks_filtered]

    return (frequency_idx, time_idx)

def record():
    try:
        print "\nYou chose record."
        filename = raw_input("Please enter a filename: ")
        print "Recording to '%s.wav'... Hit CTRL-C to stop recording." % filename
        
        frames = []
        while True:
            try:
                stream = audio.open(format=FORMAT, channels=1, rate=RATE,
                                    input=True, frames_per_buffer=CHUNK)
                data = stream.read(CHUNK)
                frames.append(data)

            except KeyboardInterrupt:
                # Stop recording.
                stream.stop_stream()
                stream.close()

                # Write to a WAV file.
                wave_file = wave.open(AUDIO_PATH + filename + '.wav', 'wb')
                wave_file.setnchannels(1)
                wave_file.setsampwidth(audio.get_sample_size(FORMAT))
                wave_file.setframerate(RATE)
                wave_file.writeframes(b''.join(frames))
                wave_file.close()
                break
    except:
        pass

def play():
    print "\nYou chose play."
    try:
        index_choice = int(raw_input("Please choose an audio file from the library to play: "))
        wave_file = wave.open(AUDIO_PATH + audio_files[index_choice], 'rb')
        stream = audio.open(format=FORMAT, channels=1, rate=RATE, output=True)

        data = wave_file.readframes(CHUNK)
        while data != '':
            stream.write(data)
            data = wave_file.readframes(CHUNK)
        stream.stop_stream()
        stream.close()
    
    except:
        pass

def match():
    print "\nYou chose match.\n"
    try:
        index_choice = int(raw_input("Please choose an audio file from the library to match: "))
        signal, fs, enc = audiolab.wavread(AUDIO_PATH + audio_files[index_choice])
        specgram, frequency, time, img = pyplot.specgram(signal, Fs=fs)

        peak_indices = get_2D_peaks(specgram)
        peak_times = [time[time_idx] for time_idx in peak_indices[1]]
        peak_frequencies = [frequency[freq_idx] for freq_idx in peak_indices[0]]

        # Plot the spectrogram image with an overlayed scatter plot of local peaks.
        pyplot.xlim(right=max(time))
        pyplot.ylim(top=20000)
        pyplot.ylabel('Frequency (Hz)')
        pyplot.xlabel('Time (s)')
        pyplot.title(audio_files[index_choice])

        pyplot.scatter(peak_times, peak_frequencies)
        pyplot.show()

    except:
        raise

# Define the menu options.
menu_option = { 1: record,
                2: play,
                3: match,
}

while True:
    try:
        # Put matplotlib in interactive mode so that the plots are shown in a background thread.
        pyplot.ion()
        # Main loop prompting user with menu options
        choice = show_menu()
        # Execute the menu option
        menu_option[choice]()
        audio_files = get_audio_files()

    except KeyboardInterrupt:
        print ""
        sys.exit(0)
