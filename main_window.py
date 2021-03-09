#from os import dup
import sys
import os
#from PyQt5.QtGui import QBrush, QColor
#from PyQt5.QtCore import pyqtSignal
#from PyQt5.QtGui import QIcon
#from PyQt5 import QtWidgets
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import numpy as np
#from pyqtgraph.functions import mkPen


import wave
from  itertools import cycle
from scipy import interpolate
#icons obtained from Freepik.com

from audio_class import audioStream
from graph_class import MyPlotWidget, SelectedRepetitions



# my application
class AppWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(AppWindow, self).__init__()

                
        #colors
        self.kelly_colors = cycle(['#222222', '#F3C300', '#875692', '#F38400', '#A1CAF1', '#BE0032', '#C2B280', '#848482', '#008856', '#E68FAC', '#0067A5', '#F99379', '#604E97', '#F6A600', '#B3446C', '#DCD300', '#882D17', '#8DB600', '#654522', '#E25822', '#2B3D26'])
        self.InfoRepetitions = SelectedRepetitions()

        #data
        self.x = None #empty variable for x
        self.y = None #empty variable for y
        self.repetitions = dict()

        self.audio_file = None #this object will handle playback 
        self.file_name = None #file name
        
        self.thread = QtCore.QThread()  # no parent!
        self.audioObj = audioStream()  # no parent!
        self.audioObj.moveToThread(self.thread)
        self.thread.started.connect(self.audioObj.run)
        self.audioObj.PositioninStream.connect(self.updateSliderPosition)
        self.audioObj.finished.connect(self.ResetAudioPlayBack)

        self.UIComponents()

    def UIComponents(self):

        widget = QtWidgets.QWidget()
        
        #components
        self.pl1 = MyPlotWidget()
        #self.pl1.ControlLine.sigPositionChangeFinished.connect(self.ControlAudioPlayBack)
        self.pl1.mouseDoubleClick.connect(self.mouseDoubleClick)
        

        self.pl2 = MyPlotWidget()
        self.pl2.setXLink(self.pl1)
        #self.pl2.setBackground('w')

        self.pl3 = pg.PlotWidget()
        self.pl3.setBackground('w')
        self.pl3.plotItem.setMouseEnabled(y=False)

        self.buttonload = QtWidgets.QPushButton('Load &File')
        self.buttonload.pressed.connect(self.plot)
        self.buttonload.setMaximumWidth(150)
        self.buttonload.setShortcut("Ctrl+F")
        self.buttonSTI = QtWidgets.QPushButton('Compute STI')
        self.buttonSTI.pressed.connect(self.computeSTI)
        self.buttonSTI.setMaximumWidth(150)
        self.buttonSave = QtWidgets.QPushButton('Save')
        self.buttonSave.pressed.connect(self.Save)
        self.buttonSave.setMaximumWidth(150)
        self.buttonPeriodogram = QtWidgets.QPushButton('Periodogram')
        self.buttonPeriodogram.pressed.connect(self.Save)
        self.buttonPeriodogram.setMaximumWidth(150)
        self.buttonFirstDerivative = QtWidgets.QPushButton('First Derivative ')
        self.buttonFirstDerivative .pressed.connect(self.Save)
        self.buttonFirstDerivative.setMaximumWidth(150)
        self.buttonSecondDerivative  = QtWidgets.QPushButton('Second Derivative')
        self.buttonSecondDerivative .pressed.connect(self.Save)
        self.buttonSecondDerivative.setMaximumWidth(150)


        self.buttonPlay = QtWidgets.QPushButton('')
        self.buttonPlay.setIcon(QtGui.QIcon("play.png"))
        self.buttonPlay.setIconSize(QtCore.QSize(24,24))
        self.buttonPlay.setMaximumWidth(50)
        self.buttonPlay.setEnabled(False)
        self.buttonPlay.pressed.connect(self.playAudio)
        self.buttonPlay.setShortcut("Ctrl+A")

        self.buttonPause = QtWidgets.QPushButton('')
        self.buttonPause.setIcon(QtGui.QIcon("pause.png"))
        self.buttonPause.setIconSize(QtCore.QSize(24,24))
        self.buttonPause.setMaximumWidth(50)
        self.buttonPause.setEnabled(False)
        self.buttonPause.pressed.connect(self.stopAudio)
        self.buttonPause.setShortcut("Ctrl+D")

        self.playBackSpeed = QtWidgets.QComboBox()
        self.playBackSpeed.addItems(["x1.00", "x0.75", "x0.50", "x0.25", "x0.10"])
        self.playBackSpeed.currentIndexChanged.connect(self.playBackSpeedChange)


        self.buttonHide = QtWidgets.QPushButton('')
        self.buttonHide.setIcon(QtGui.QIcon("hide.png"))
        self.buttonHide.setIconSize(QtCore.QSize(24,24))
        self.buttonHide.setMaximumWidth(50)
        self.buttonHide.pressed.connect(self._Hide)
        self.buttonEliminate= QtWidgets.QPushButton('')
        self.buttonEliminate.setIcon(QtGui.QIcon("dump.png"))
        self.buttonEliminate.setIconSize(QtCore.QSize(24,24))
        self.buttonEliminate.setMaximumWidth(50)
        self.buttonEliminate.pressed.connect(self._Eliminate)
        self.buttonChangeColor = QtWidgets.QPushButton('')
        self.buttonChangeColor.setIcon(QtGui.QIcon("color-palette.png"))
        self.buttonChangeColor.setIconSize(QtCore.QSize(24,24))
        self.buttonChangeColor.setMaximumWidth(50)
        self.buttonChangeColor.pressed.connect(self._ChangeColor)


        self.table = QtWidgets.QTableWidget(1,1)
        self.table.setColumnWidth(0,75)
        self.table.setHorizontalHeaderLabels(['Repetition'])
        self.table.horizontalHeader().setStretchLastSection(True )
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumWidth(100)
        #self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        #self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        #print(self.table.columnWidth(0))
        #self.table.itemClicked.connect(self.selected_in_table)
        #self.table.itemSelectionChanged.connect(self.change_selected_in_table)


        #layouts 

        layout = QtWidgets.QGridLayout()

        # layout.addWidget(self.buttonload, 0,1,3,1)
        # layout.addWidget(self.buttonSTI, 3,1,3,1)
        # layout.addWidget(self.buttonSave, 6,1,3,1)
        # layout.addWidget(self.pl1, 0,2,4,4)
        # layout.addWidget(self.pl2, 6,2,4,4)
        # layout.addWidget(self.pl3, 10,1,4,3)

        left_button_layout = QtWidgets.QVBoxLayout()
        left_button_layout.addWidget(self.buttonload)
        left_button_layout.addWidget(self.buttonPeriodogram)
        left_button_layout.addWidget(self.buttonFirstDerivative)
        left_button_layout.addWidget(self.buttonSecondDerivative)
        left_button_layout.addWidget(self.buttonSTI)
        left_button_layout.addWidget(self.buttonSave)
        left_button_layout.addStretch()

       

        spaceItem = QtWidgets.QSpacerItem(100, 10, QtWidgets.QSizePolicy.Expanding)
        center_button_layout = QtWidgets.QHBoxLayout()
        center_button_layout.addSpacerItem(spaceItem)
        center_button_layout.addWidget(self.playBackSpeed)
        center_button_layout.addWidget(self.buttonPlay)
        center_button_layout.addWidget(self.buttonPause)
        center_button_layout.addSpacerItem(spaceItem)

        plot_layout = QtWidgets.QVBoxLayout()
        plot_layout.addWidget(self.pl1)
        plot_layout.addLayout(center_button_layout)
        plot_layout.addWidget(self.pl2)

        right_button_layout=QtWidgets.QVBoxLayout()
        right_button_layout.addWidget(self.buttonHide)
        right_button_layout.addWidget(self.buttonEliminate)
        right_button_layout.addWidget(self.buttonChangeColor)
        right_button_layout.addStretch()

        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addWidget(self.table)
        bottom_layout.addLayout(right_button_layout)

        layout.addLayout(left_button_layout,0,0,1,1)
        layout.addLayout(plot_layout,0,1,2,3)
        layout.addWidget(self.pl3,2,1,2,2)
        layout.addLayout(bottom_layout,2,3,1,1)
        #layout.addLayout(right_button_layout,3,2,1,1)


        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.resize(1000,600)

    def plot(self):
        self.pl1.clear()
        #self.pl1.selectedTrials.clear_all()  #clear everything in the class
        self.pl1.isDataAvaliable = False

        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', ' ',"WAV files (*.WAV *.wav, *.m4a)")

        if fname[0]:
            self.file_name = fname[0]
            # Read file to get buffer   
            if fname[0][-4:] == '.wav':                                                                                            
                self.audio_file = wave.open(fname[0])
                samples = self.audio_file.getnframes()
                samplerate = self.audio_file.getframerate()
                audio = self.audio_file.readframes(samples)
                self.audio_file.rewind() #return pointer to begining of file
                # Convert buffer to float32 using NumPy                                                                                 
                audio_as_np_int16 = np.frombuffer(audio, dtype=np.int16)
                audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

                # Normalise float32 array so that values are between -1.0 and +1.0                                                      
                max_int16 = 2**15
                audio_normalized = audio_as_np_float32 / max_int16
                audio_normalized = audio_normalized.reshape(samples,-1)
                data = np.mean(audio_normalized,axis=1)
                x = np.linspace(0., samples/samplerate, samples)
                y = data

                try:
                    self.x = x
                    self.y = y
                    self.pl1.plot(x,y, pen=pg.mkPen(width=1))
                    self.pl1.setLimits(xMin=np.min(x), xMax=np.max(x), yMin=np.min(y), yMax=np.max(y))
                    self.pl1.isDataAvaliable = True #a variable that tells the class that there is data
                    self.pl1.get_ybound_viewBox() # a function that computes the y-limits of the rectangle  used to delimit the selected area
                
                    self.pl1.addInfinteControlLine()

                    self.buttonPlay.setEnabled(True)
                    self.buttonPause.setEnabled(True)
                except:
                    pass

 
            if os.path.exists(fname[0][:-4]+'.Table'):
                array = np.loadtxt(fname[0][:-4]+'.Table', dtype=object, skiprows=1)
                for row in array:
                    self.pl1.addFilledAreaandLabel(float(row[0]), float(row[2]), row[1])
                    self.pl1.total_repetition +=1


    @QtCore.pyqtSlot(float)
    def updateSliderPosition(self, position):
        #change position of slider controling audio playback 
        if position<=0:position=0
        if position>=self.audio_file.getnframes(): position=self.audio_file.getnframes()
        self.pl1.ControlLine.setPos(position)

    def playAudio(self):
        #play audio 
        
        if  not self.thread.isRunning():
            #if thread is not active then create the audio stream (PyAudio) and start thread 
            self.audioObj.audio_file = self.audio_file
            self.audioObj.setUpStream(float(self.playBackSpeed.currentText()[1:])) #set the playback speed 
            self.audioObj.isPlay = True
            position = int(self.pl1.ControlLine.getXPos()*self.audio_file.getframerate()) #- 1024
            if position<=0:position=0
            if position>=self.audio_file.getnframes(): position=self.audio_file.getnframes()
            self.audioObj.audio_file.setpos(position) #set the position of the audio file
            self.thread.start()
        else:
            #if thread is active only re-start stream 
            position = int(self.pl1.ControlLine.getXPos()*self.audio_file.getframerate()) #- 1024
            if position<=0:position=0
            if position>=self.audio_file.getnframes(): position=self.audio_file.getnframes()
            self.audioObj.audio_file.setpos(position)
            self.audioObj.isPlay = True
            self.thread.start()

    def stopAudio(self):
        self.audioObj.isPlay = False

    def playBackSpeedChange(self, i):
        #update the playback speed
        self.isPlay = False
        self.audioObj.updateStream(float(self.playBackSpeed.currentText()[1:])) 
        self.playAudio()


    def ResetAudioPlayBack(self):
        #end of sound file 
        #reset line to zero and terminate thread that plays sound
        self.pl1.ControlLine.setPos(0)
        self.audioObj.close()
        self.thread.quit()
        self.thread.wait()

    @QtCore.pyqtSlot(float)
    def mouseDoubleClick(self, position):
        #change position of line that controls audio playback with double click 
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier: #if the user is pressing Shift
            pass
        else:
            if self.audio_file is not None:
                self.isPlay = False
                self.pl1.ControlLine.setPos(position)
                self.playAudio()


    def computeSTI(self):
        self.table.setRowCount(0)
        #verify that the is something to take 
        n = len(self.pl1.filled_areas)
        if n>0:
            #get the information from the plot
            for index in range(n):

                coords_0, coords_1 = self.pl1.filled_areas[index].getRegion()
                name = self.pl1.texts[index].textItem.toPlainText()
                self.table.insertRow(index)
                item = QtWidgets.QTableWidgetItem(str(name))
                color = next(self.kelly_colors)
                item.setForeground(QtGui.QBrush(QtGui.QColor(color)))
                self.table.setItem(index,0,item)

                self.InfoRepetitions.label.append(str(name))
                self.InfoRepetitions.isHidden.append(False)
                self.InfoRepetitions.color.append(color)
                self.InfoRepetitions.values[str(name)]=self.y[self.closest_value(self.x, coords_0):self.closest_value(self.x, coords_1)]
                self.InfoRepetitions.time_vect[str(name)]=self.x[self.closest_value(self.x, coords_0):self.closest_value(self.x, coords_1)]
                self.InfoRepetitions.len_rep.append(len(self.InfoRepetitions.values[str(name)]))

            
            #compute the time-space adjusted sequences 
            min_val = np.min(self.InfoRepetitions.len_rep)
            for label in self.InfoRepetitions.label:
                sig = self.InfoRepetitions.values[label]
                time_v = self.InfoRepetitions.time_vect[label]
                new_sig, des_time = self.adjustAmplitudeandTime(sig, time_v-time_v[0], normalize=True,des_n=min_val)
                self.InfoRepetitions.values_adjusted[label] = new_sig
                self.InfoRepetitions.time_vect_adjusted[label] = des_time

            self.plotSTI()
        else:
            pass

    def plotSTI(self):
        childItems= self.pl3.allChildItems() 
        for item in childItems:
            self.pl3.removeItem(item)

        for label in self.InfoRepetitions.label:
            idx = self.InfoRepetitions.label.index(label)
            if not self.InfoRepetitions.isHidden[idx]:
                y = self.InfoRepetitions.values_adjusted[label]
                x = self.InfoRepetitions.time_vect_adjusted[label]
                color = self.InfoRepetitions.color[idx]
                self.pl3.plot(x[:,0],y[:,0], pen=pg.mkPen(color=QtGui.QColor(color),width=1))
                self.pl3.setLimits(xMin=np.min(x), xMax=np.max(x), yMin=np.min(y), yMax=np.max(y))

    def Save(self):
        n = len(self.pl1.filled_areas)
        to_save = np.empty((n+1,3),dtype=object) #matrix that will contain the segmenets 
        to_save[0,:] = np.array(['t_start', 'rep', 't_end']) #header in row zero
        if n>0:
            for index in range(n):

                coords_0, coords_1 = self.pl1.filled_areas[index].getRegion()
                name = self.pl1.texts[index].textItem.toPlainText()
                to_save[index+1,0] = np.round(coords_0,4)
                to_save[index+1,1] = name
                to_save[index+1,2] = np.round(coords_1,4)

            np.savetxt(self.file_name[:-4]+'.Table',to_save, fmt=('%s'), delimiter='\t')

    def _Hide(self):
        for item in self.table.selectedItems():
            text = item.text()
            #find item index in list 
            idx = self.InfoRepetitions.label.index(text)
            if self.InfoRepetitions.isHidden[idx] == False:
                self.InfoRepetitions.isHidden[idx] = True
            else:
                self.InfoRepetitions.isHidden[idx] = False

            self.plotSTI()

    def _Eliminate(self):
        pass

    def _ChangeColor(self):
        pass

    @staticmethod
    def closest_value(x, value):
        idx = np.abs(x - value).argmin()
        return idx

    @staticmethod
    def adjustAmplitudeandTime(sig, time,normalize=True, des_n = None):
        """
        Takes a signal x of length n and return a new signal x_n of lenght des_n and with zero meand and unit standard deviation
        
        Interpolation is performed using cubic splines
        """
        sig = sig[:,None]
        time = time [:,None]
        
        if des_n is None:
            des_time = time
        else:
            des_time = np.linspace(time[0],time[-1],des_n)
    
        if normalize:
            sig = (sig-np.mean(sig))/np.std(sig)
        try:
            tck = interpolate.splrep(time, sig, s=0)
        except:
            tck = interpolate.splrep(np.sort(time,axis=None), sig, s=0)
        
        new_sig = interpolate.splev(des_time, tck, der=0)
        
        #new_sig_der = interpolate.splev(des_time, tck, der=1)
        
        return new_sig, des_time#, new_sig_der 

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).closeEvent(*args, **kwargs)
        if self.audioObj.stream is not None:
            self.audioObj.close()
        #self.thread.quit()
        #self.thread.wait()






app = QtWidgets.QApplication(sys.argv)
w = AppWindow()
w.show()
sys.exit(app.exec_())