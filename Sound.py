#import os, sys
import simpleaudio as sa
# import numpy as np
import wave
import JESConfig
from SoundSample import SoundSample
#import FileChooser

class Sound:
    MAX_NEG = -32768
    MAX_POS = 32767
    SAMPLE_RATE = 22050
    NUM_BITS_PER_SAMPLE = 16
    _SoundIndexOffset = 0

    def __init__(self, sound=None, sampleRate=22050):
        """Construct new sound object
        
        If first passed parameter is the name of a WAV file, then read
        the file.

        If first passed parameter is an int representing a number of
        frames, then construct Sound object of the specified length.
        This sound will simply consist of an empty byte array and an
        AudioFileFormat with the following values:
            AudioFileFormat.Type.WAVE</code>
            22.05K sampling rate
            16 bit sample
            1 channel
            signed PCM encoding
            small-endian byte order
        Note that no new sound file is created, we only represent the
        sound with a buffer and the AudioFileFormat.  If a file is
        desired, then the method writeToFile(filename) must be called
        on this newly created sound.
    
        Parameters
        ----------
        sound : str
            the filename of containing a sound in WAV format
        sound : int
            the number of samples in the sound
        sound : Sound
            a preexisting Sound object
        sampleRate : int
            the frame rate for the sound
        """
        if (sound == None):
            self.__init__(self.SAMPLE_RATE * 3)
        elif isinstance(sound, str):
            self.filename = sound
            waveRead = wave.open(self.filename, 'rb')
            self.numFrames = waveRead.getnframes()
            self.numChannels = waveRead.getnchannels()
            self.sampleWidth = waveRead.getsampwidth()
            self.sampleRate = waveRead.getframerate()
            self.buffer = bytearray(waveRead.readframes(self.numFrames))
            waveRead.close()
        elif isinstance(sound, int):
            self.filename = ''
            self.numFrames = sound
            self.numChannels = 1
            self.sampleWidth = int(self.NUM_BITS_PER_SAMPLE / 8)
            self.sampleRate = sampleRate
            numBytes = self.numChannels * self.numFrames * self.sampleWidth
            self.buffer = bytearray([0] * numBytes)
        elif isinstance(sound, Sound):
            self.filename = sound.filename
            self.numFrames = sound.numFrames
            self.numChannels = sound.numChannels
            self.sampleWidth = sound.sampleWidth
            self.sampleRate = sound.sampleRate
            self.buffer = sound.buffer.copy()
        self.playbacks = []

    def __str__(self):
        """Return string representation of this sound

        Returns
        -------
        str
            representation of this sound
        """
        output = "Sound file: {} number of samples: {}".format(self.filename, self.numFrames)
        return output

    def __repr__(self):
        return self.__str__()

    # ----------------------- accessors --------------------------------------

    def getBuffer(self):
        return self.buffer

#    def getAudioFileFormat(self):
#        return self.audioFileFormat # not yet defined

    def getSamplingRate(self):
        return self.sampleRate

#    def getSoundExplorer(self):
#        return self.soundExplorer # not yet defined

    def asArray(self):
        return self.getBuffer()

    def getPlaybacks(self):
        return playbacks

    def getFileName(self):
        return self.filename

    def getChannels(self):
        return self.numChannels

    #     /**
    #  * Returns an array containing all of the bytes in the specified
    #  * frame.
    #  *
    #  * @param frameNum the index of the frame to access
    #  * @return the array containing all of the bytes in frame
    #  *         <code>frameNum</code>
    #  * @throws SoundException if the frame number is invalid.
    #  */
    def getFrame(self, frameNum):
        if (frameNum >= self.numFrames):
            print("The index {}, does not exist. The last valid index is {}".format(frameNum, self.numFrames-1))
            
        frameSize = self.getLength()/self.getLengthInFrames()
        theFrame = bytearray(frameSize)
        for i in frameSize:
            theFrame[i] = buffer[frameNum * frameSize + i]
        return theFrame

    # ----------------------- modifiers --------------------------------------

    def setBuffer(self, newBuffer):
        if isinstance(newBuffer, int):
            buffer = bytearray(newBuffer)
        elif isinstance(newBuffer, bytearray):
            buffer = newBuffer.copy() #maybe not a copy?

    # def setAudioFileFormat(self, audioFileFormat):
    #     self.audioFileFormat = audioFileFormat
    
    # def setSoundExplorer(self, soundExplorer):
    #     self.soundExplorer = soundExplorer

    # ------------------------ methods ---------------------------------------

    def isStereo(self):
        """Method to check if a sound is stereo (2 channel) or not

        Returns
        -------
        bool
            True if stereo else False
        """
        return self.numChannels != 1

    def play(self):
        """Play a sound - nonblocking
        """
        waveObject = sa.WaveObject(self.buffer, self.numChannels, self.sampleWidth, self.sampleRate)
        self.playbacks.append(waveObject.play())

    def blockingPlay(self):
        """Play a sound - blocking
        """
        self.play()
        self.playbacks[-1].wait_done()

    def stopPlaying(self):
        """Stop playback of all currently playing sounds
        """
        while len(self.playbacks) > 0:
            self.playbacks.pop().stop()

    def removePlayback(self, playbackToRemove):
        """Method to remove a playback from the list of playbacks
        
        Parameters
        ----------
        playbackToRemove : PlayObject
            the playback that we want to remove

        """
        if (self.playbacks.contains(playbackToRemove)):
            self.playbacks.remove(playbackToRemove)
            playbackToRemove = None

    def getLengthInFrames(self):
        """Obtains number of sample frames in the audio data

        Returns
        -------
        int
            the number of sample frames of audio data in the sound
        """
        return self.numFrames

    def getNumSamples(self):
        """Returns the number of samples in this sound

        Returns
        -------
        int
            the number of sample frames
        """
        return self.getLengthInFrames()

    def getSample(self, frameNum):
        """Create and return a SoundSample object for the given frame number

        Parameters
        ----------
        frameNum : int
            the frame from which to retrieve the SoundSample object

        Returns
        -------
        SoundSample
            a SoundSample object for this frame number
        """
        return SoundSample(self, frameNum)

    def getSamples(self):
        """Method to create and return an array of SoundSample objects

        Returns
        -------
        list of SoundSample
            the array of SoundSample objects
        """
        samples = []
        for i in range(self.numFrames):
            samples.append(SoundSample(self, i))
        return samples

    def reportIndexException(self, index):
        """Method to report an index exception for this sound

        Parameters
        ----------
        index : int
            the index
        """
        print("The index {} isn't valid for this sound".format(index))

    def getSampleValueAt(self, index):
        """Get the sample at the passed index and handle any SoundExceptions

        Parameters
        ----------
        index : int
            the desired index

        Returns
        -------
        int
            the sample value
        """
        try:
            value = self.getSampleValue(index)
        except:
            reportIndexException(index)
        return value
    
    def getSampleValue(self, frameNum):
        """Sets the value of the sample at the indicated frame
        
        If this is a mono sound, obtains the single sample contained
        within this frame, else obtains the first (left) sample
        contained in the specified frame.

        Parameters
        ----------
        frameNum : int
            the index of the frame to access

        Returns
        -------
        int
            integer representation of the bytes contained within frame
        """
        n = frameNum * self.sampleWidth * self.numChannels
        m = n + self.sampleWidth
        return int.from_bytes(self.buffer[n:m], byteorder='little', signed=True)    

    def getLeftSample(self, frameNum):
        """Obtains the left sample contained at the specified frame

        Parameters
        ----------
        frameNum : int
            the index of the frame to access

        Returns
        -------
        int
            integer representation of the bytes contained in the specified frame.
        """
        if not self.isStereo():
            print("Sound is not stereo, cannot access left value")
        return self.getSampleValue(frameNum)

    def getRightSample(self, frameNum):
        """Obtains the right sample contained at the specified frame

        Parameters
        ----------
        frameNum : int
            the index of the frame to access

        Returns
        -------
        int
            integer representation of the bytes contained in the specified frame.
        """
        if not self.isStereo():
            print("Sound is not stereo, cannot access right value")
        else:
            n = frameNum * self.sampleWidth * self.numChannels + self.sampleWidth
            m = n + self.sampleWidth
            return int.from_bytes(self.buffer[n:m], byteorder='little', signed=True)    

    def getLengthInBytes(self):
        """Obtains the length of this sound in bytes
        
        Note, that this number is not neccessarily the same as the length of
        this sound's file in bytes

        Returns
        -------
        int
            the sound length in bytes
        """
        return len(buffer)

    def getLength(self):
        """Return the length of the sound as the number of samples

        Returns
        -------
        int
            the length of the sound as the number of samples
        """
        return self.getNumSamples()

    def setFrame(self, frameNum, frame):
        """Changes the value of each byte of the specified frame

        Parameters
        ----------
        frameNum : int
            the index of the frame to change
        frame : byte array
            the bytes that will be copied into this sound's buffer
        """
        if frameNum >= self.numFrames:
            print("The frame number {} does not exist".format(frameNum))
            print("The last valud frame number is {}".format(self.numFrames-1))
        else:
            for i in range(self.sampleWidth):
                self.buffer[frameNum * self.sampleWidth + i] = frame[i]

    def setSampleValueAt(self, index, value):
        """Method to set the sample value at the specified index

        Parameters
        ----------
        index : int
            the index
        value : int or float
            the new value
        """
        try:
            self.setSampleValue(index, int(value))
        except:
            reportIndexException(index)

    def setSampleValue(self, frameNum, value):
        """Sets the value of the sample found at the specified frame
        
        If this sound has more than one channel, then we default to setting
        only the first (left) sample.
    
        Parameters
        ----------
        frameNum : int
            the index of the frame where the sample should be changed
        value : int
           the new sample value
        """
        n = frameNum * self.sampleWidth * self.numChannels
        m = n + self.sampleWidth
        self.buffer[n:m] = value.to_bytes(self.sampleWidth,
                                          byteorder='little',
                                          signed=True)

    def setLeftSample(self, frameNum, value):
        """Set the left sample value in a stereo sample
        
        Parameters
        ----------
        frameNum : int
            the index of the frame where the sample should be changed
        value : int
            an integer representation of the new sample
        """
        if not self.isStereo():
            print("Sound is not stereo, cannot set left value")
        else:
            self.setSampleValue(frameNum, value)

    def setRightSample(self, frameNum, value):
        """Set the right sample value in a stereo sample
        
        Parameters
        ----------
        frameNum : int
            the index of the frame where the sample should be changed
        value : int
            an integer representation of the new sample
        """
        if not self.isStereo():
            print("Sound is not stereo, cannot set right value")
        else:
            n = frameNum * self.sampleWidth * self.numChannels + self.sampleWidth
            m = n + self.sampleWidth
            self.buffer[n:m] = value.to_bytes(self.sampleWidth,
                                              byteorder='little',
                                              signed=True)

    # ------------------------ File I/O ---------------------------------------

    def loadFromFile(self, inFileName):
        """Resets the fields of this sound so that it now represents the
           sound in the specified file.  If successful, the fileName variable
           is updated such that it is equivalent to the passed in file
 
        Parameters
        ----------
        inFileName : str
            the name of the file to read the sound in from
        """
        self.filename = inFileName
        waveRead = wave.open(self.filename, 'rb')
        self.numFrames = waveRead.getnframes()
        self.numChannels = waveRead.getnchannels()
        self.sampleWidth = waveRead.getsampwidth()
        self.sampleRate = waveRead.getframerate()
        self.buffer = bytearray(waveRead.readframes(self.numFrames))
        waveRead.close()

    def write(self, fileName):
        """Write the sound to a wav file and throw an error if it can't be written
 
        Parameters
        ----------
        fileName : str
            the name of the file to write the sound to
        """
        try:
            writeToFile(fileName)
        except IOError:
            print("Couldn't write file to " + fileName)

    def writeToFile(self, outFileName):
        """Write the sound to a wav file
 
        Parameters
        ----------
        outFileName : str
            the name of the file to write the sound to
        """
        file = wave.open(outFileName+".wav", "wb")

        file.setnframes(self.numFrames)
        file.setnchannels(self.numChannels)
        file.setsampwidth(self.sampleWidth)
        file.setframerate(self.sampleRate)
        file.writeframes(self.buffer)
        file.close()