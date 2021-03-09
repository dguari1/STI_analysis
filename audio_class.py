from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, Qt
import pyaudio

class AudioHolder():

    def __init__(self, audio_file = None):

        self.audio_file = audio_file

    def setUpStream(self):
        self.pyAudio = pyaudio.PyAudio()

        self.stream = self.pyAudio.open(format=self.pyAudio.get_format_from_width(self.audio_file.getsampwidth()),
                        channels=self.audio_file.getnchannels(),
                        rate=self.audio_file.getframerate(),
                        output=True)
        self.CHUNK=512

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pyAudio.terminate()


class playAudioStream(QObject):

    PositioninStream = pyqtSignal(float)
    finished = pyqtSignal()

    def __init__(self, audio_file = None, stream = None, CHUNK=512):
        super(playAudioStream, self).__init__()
        self.audio_file = audio_file
        self.stream = stream
        self.CHUNK = CHUNK
        self.isPlay = False

    @pyqtSlot()
    def run(self):
        #data = self.audio_file.readframes(self.CHUNK)
        while self.isPlay: #len(data)>0 and self.isPlay:
            data = self.audio_file.readframes(self.CHUNK)
            if len(data)==0:
                self.isPlay=False
            else:
                position_in_time = self.audio_file.tell()/self.audio_file.getframerate()
                self.PositioninStream.emit(position_in_time)
                self.stream.write(data)
        self.finished.emit()


class audioStream(QObject):

    PositioninStream = pyqtSignal(float)
    finished = pyqtSignal()

    def __init__(self, audio_file = None):
        super(audioStream, self).__init__()

        self.audio_file = audio_file
        self.isPlay = False

    def setUpStream(self, playBackSpeedModifier):
        self.pyAudio = pyaudio.PyAudio()

        self.stream = self.pyAudio.open(format=self.pyAudio.get_format_from_width(self.audio_file.getsampwidth()),
                        channels=self.audio_file.getnchannels(),
                        rate=int(self.audio_file.getframerate()*playBackSpeedModifier),
                        output=True)
        self.CHUNK=1024

    def updateStream(self, playBackSpeedModifier):
        #self.stream.stop_stream()
        #self.stream.close()
        self.stream = self.pyAudio.open(format=self.pyAudio.get_format_from_width(self.audio_file.getsampwidth()),
                        channels=self.audio_file.getnchannels(),
                        rate=int(self.audio_file.getframerate()*playBackSpeedModifier),
                        output=True)


    @pyqtSlot()
    def run(self):
        
        while True: #len(data)>0 and self.isPlay:

            if self.isPlay:
                position_in_time = self.audio_file.tell()/self.audio_file.getframerate()
                self.PositioninStream.emit(position_in_time)
                data = self.audio_file.readframes(self.CHUNK)
                self.stream.write(data)
            else:
                continue 

            if len(data) == 0: #no more data to stream
                self.isPlay = False
                break
        
        self.finished.emit()



    def close(self):
        self.isPlay = False
        self.stream.stop_stream()
        self.stream.close()
        self.pyAudio.terminate()


