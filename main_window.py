from os import dup
import sys
#from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import numpy as np
from pyqtgraph.functions import mkPen

from scipy.io.wavfile import read 

#icons obtained from Freepik.com

class SelectedTrials(object):

    #this class will contain all the information about the repetitions, including coordinates in time, viewBox, color of signal, values, ...

    def __init__(self, parent=None):
        super().__init__()
      
        self.plotlines= []
        self.isHidden = []
        self.color = []
        self.values = dict()
        self.index_repetition = []
        self.name_repetition = []

    def clear_all(self):
        #clear everything to prepare for new data 

        self.plotlines.clear()
        self.isHidden.clear()
        self.color.clear()
        self.values.clear()
        self.index_repetition.clear()
        self.name_repetition.clear()


#this class re-implements pg.LinearRegionItem
#I re-implement it so that the is a signal every time there is a double click on the region
#in this way, we can identify if the subject double click on the region and we can remove the region of interest
class MyLinearRegionItem(pg.LinearRegionItem):
    #create the signal to emit
    sigDoubleClick = QtCore.Signal(object)

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        
    def mouseMoveEvent(self, ev):
        #needed for the function to work properly 
        super().mouseMoveEvent(ev)
        return
        
    def mouseReleaseEvent(self, ev):
        #needed for the function to work properly 
        super().mouseReleaseEvent(ev)
        return

    def mouseDoubleClickEvent(self, ev):
        super().mouseDoubleClickEvent(ev)
        if ev.button() == QtCore.Qt.LeftButton:
            #if there is a double click emit this signal
            self.sigDoubleClick.emit(self)


class MyPlotWidget(pg.PlotWidget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # self.scene() is a pyqtgraph.GraphicsScene.GraphicsScene.GraphicsScene
        # self.scene().sigMouseClicked.connect(self.mouse_clicked)    
        self.setBackground('w')
        self.plotItem.setMouseEnabled(y=False)

        self.filled_areas = []
        self.texts = []
        # self.lines  = []
        # self.index_lines = []
        self.num_clicks = 0  # a click counter
        self.total_repetition = 0 
        #self.selectedTrials = SelectedTrials()
        self.isDataAvaliable = False
        
        #generic infinite line
        self.line = pg.InfiniteLine( pen=pg.mkPen('r', width=1), movable = True)
        self.line.setHoverPen(color=(58,59,60))
        #self.line.sigPositionChangeFinished.connect(self.changeLinePosition)

        self.height = 0

    def get_ybound_viewBox(self):
        #function that gets the y-size of the rectangle that will be used to delimit the selected area
        if self.isDataAvaliable:
            y_min = self.plotItem.getViewBox().state['viewRange'][1][0]
            y_max = self.plotItem.getViewBox().state['viewRange'][1][1]
            self.height = y_max - y_min

        
    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)

        if self.isDataAvaliable:
            #get the x position of the mouse in view coordinates
            scenePos = self.plotItem.vb.mapDeviceToView(QtCore.QPointF(ev.pos()))#self.mapToScene(event.pos())
            x_mousePos = scenePos.x()

            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ControlModifier: #if the user is pressing Ctrl

                if self.num_clicks == 0 : # no selected area

                    #set the position of the line as the current mouse position
                    self.line.setPos(x_mousePos)
                    #put the line in the picture
                    self.addItem(self.line)
                    
                    #count the number of clicks
                    self.num_clicks += 1


                elif self.num_clicks == 1: # the user finized selecting the area 
                    #if there is a second click with Ctrl pressed then create a repetition, 
   
                    #remove the line, it will be replaced by a filled area
                    self.removeItem(self.line)
                    
                    #plot a filled area between the line and click position 
                    coords_0 = self.line.getXPos()
                    coords_1 = x_mousePos

                    #filled area
                    fill = MyLinearRegionItem([coords_0, coords_1], movable=False, pen=QtGui.QColor(255,0,255), brush = QtGui.QColor(0,0,255,25), hoverPen=QtGui.QColor(58,59,60), swapMode='block')
                    fill.setMovable(True)
                    fill.sigDoubleClick.connect(self.DoubleClickonRegion)
                    fill.sigRegionChanged.connect(self.changeRegionPosition)
                    
                    #text 
                    text = pg.TextItem(text="",color=(0, 0, 0), anchor=(0.5,0.5))
                    text.setPos((coords_0+coords_1)/2, (self.height/2)*0.8)
                    text.setText('Rep_'+str(self.total_repetition))
                    
                    #store the filled area and text to be able to modify them later
                    self.filled_areas.append(fill)
                    self.texts.append(text)

                    #add the elements to the picture
                    self.addItem(self.filled_areas[-1])
                    self.addItem(self.texts[-1])

                    #two clicks already, so reset the click counter
                    self.num_clicks = 0 

                    #count the repetitions
                    self.total_repetition +=1


    def mouseMoveEvent(self, ev):
        #needed for the function to work properly 
        super().mouseMoveEvent(ev)
        return
        
    def mouseReleaseEvent(self, ev):
        #needed for the function to work properly 
        super().mouseReleaseEvent(ev)
        return

    def changeRegionPosition(self):
        #the region limits were updated, update the position of the text
        idx_rep = self.filled_areas.index(self.sender()) #this is the repetition number associated with the filled area 

        coords_0, coords_1 = self.sender().getRegion()
        self.texts[idx_rep].setPos((coords_0+coords_1)/2, (self.height/2)*0.8)


    def DoubleClickonRegion(self):
        idx_rep = self.filled_areas.index(self.sender()) #this is the repetition number associated with the filled area 

        #These are the lines associated with the filled area 

        #remove elements from list and from graphic 
        self.removeItem(self.filled_areas[idx_rep])
        self.removeItem(self.texts[idx_rep])

        self.filled_areas.pop(idx_rep)
        self.texts.pop(idx_rep)

# my application
class AppWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(AppWindow, self).__init__()

        self.pl1 = MyPlotWidget()

        self.pl2 = MyPlotWidget()
        self.pl2.setXLink(self.pl1)
        #self.pl2.setBackground('w')

        self.pl3 = pg.PlotWidget()
        self.pl3.setBackground('w')
        self.pl3.plotItem.setMouseEnabled(y=False)

        self.buttonload = QtWidgets.QPushButton('Load File')
        self.buttonload.pressed.connect(self.plot)
        self.buttonload.setMaximumWidth(150)
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



        self.buttonHide = QtWidgets.QPushButton('')
        self.buttonHide.setIcon(QtGui.QIcon("hide.png"))
        self.buttonHide.setIconSize(QtCore.QSize(24,24))
        self.buttonHide.setMaximumWidth(50)
        self.buttonEliminate= QtWidgets.QPushButton('')
        self.buttonEliminate.setIcon(QtGui.QIcon("dump.png"))
        self.buttonEliminate.setIconSize(QtCore.QSize(24,24))
        self.buttonEliminate.setMaximumWidth(50)
        self.buttonChangeColor = QtWidgets.QPushButton('')
        self.buttonChangeColor.setIcon(QtGui.QIcon("color-palette.png"))
        self.buttonChangeColor.setIconSize(QtCore.QSize(24,24))
        self.buttonChangeColor.setMaximumWidth(50)


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
        
        
        #data
        self.x = None #empty variable for x
        self.y = None #empty variable for y
        self.repetitions = dict()


        self.UIComponents()

    def UIComponents(self):

        widget = QtWidgets.QWidget()
        

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

        plot_layout = QtWidgets.QVBoxLayout()
        plot_layout.addWidget(self.pl1)
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
            samplerate, data = read(fname[0])
            length = data.shape[0] / samplerate
            samplerate, data = read(fname[0])
            length = data.shape[0] / samplerate
            x = np.linspace(0., length, data.shape[0])
            y = data[:,0]

            try:
                self.x = x
                self.y = y
                self.pl1.plot(x,y, pen=pg.mkPen(width=1))
                self.pl1.setYRange(np.min(y), np.max(y), padding=0.1)
                self.pl1.setXRange(np.min(x), np.max(x), padding=0)
                self.pl1.isDataAvaliable = True #a variable that tell the class that there is data
                self.pl1.get_ybound_viewBox() # a function that computes the y-limits of the rectangle  used to delimit the selected area
            except:
                pass

    def computeSTI(self):

        #verify that the is something to take 
        n = len(self.pl1.filled_areas)
        if n>0:
            for index in range(n):

                coords_0, coords_1 = self.pl1.filled_areas[index].getRegion()
                name = self.pl1.texts[index].textItem.toPlainText()
                self.table.insertRow(index)
                self.table.setItem(index,0,QtWidgets.QTableWidgetItem(str(name)))
                # idx_x = np.abs(np.subtract.outer(self.x, coords)).argmin(0)
                # self.repetitions[name]  = self.y[idx_x[0]:idx_x[1]] #get the data witing the line 
                # self.pl2.plot(self.y[idx_x[0]:idx_x[1]], pen=pg.mkPen(width=1))
                # #print(self.pl1.selectedTrials.coordsScene[index]
                # print(len(self.repetitions[name]))
        else:
            print('no')
        #for limits in self.pl1.

    def Save(self):
        pass

    @staticmethod
    def closest_value(x, value):
        idx = np.abs(x - value).argmin()
        return idx






app = QtWidgets.QApplication(sys.argv)
w = AppWindow()
w.show()
sys.exit(app.exec_())