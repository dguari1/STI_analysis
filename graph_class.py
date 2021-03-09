from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import numpy as np
from pyqtgraph.functions import mkPen


class SelectedRepetitions(object):

    #this class will contain all the information about the repetitions, including coordinates in time, viewBox, color of signal, values, ...

    def __init__(self, parent=None):
        super().__init__()
      
        self.label= []
        self.isHidden = []
        self.color = []
        self.values = dict()
        self.time_vect = dict()
        self.len_rep = []

        self.values_adjusted = dict()
        self.time_vect_adjusted = dict()

    def clear_all(self):
        #clear everything to prepare for new data 

        self.label.clear()
        self.isHidden.clear()
        self.color.clear()
        self.values.clear()
        #self.index_repetition.clear()
        #self.name_repetition.clear()

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
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ShiftModifier: #if the user is pressing Shift
                #if there is a double click + Shift -> emit  this signal
                self.sigDoubleClick.emit(self)


class MyPlotWidget(pg.PlotWidget):

    mouseDoubleClick = QtCore.pyqtSignal(float)

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

        self.positionControlLine = 0
        
        #generic infinite line
        self.line = pg.InfiniteLine( pen=pg.mkPen('r', width=1), movable = True)
        self.line.setHoverPen(color=(58,59,60))
        #self.line.sigPositionChangeFinished.connect(self.changeLinePosition)

        self.height = 0

        #infinite line used to control audio playback
        self.ControlLine = pg.InfiniteLine(pen=pg.mkPen('k', width=3), movable = True)  
        self.ControlLine.setPos(0)
        self.isWaveFile = False

    def addInfinteControlLine(self):
        self.isWaveFile = True
        #add an infinite line to control audio playback 
        self.addItem(self.ControlLine)
        #self.ControlLine.sigPositionChangeFinished.connect(self.InfoControlLine)

    def addFilledAreaandLabel(self,coords_0, coords_1, label):
        #filled area
        fill = MyLinearRegionItem([coords_0, coords_1], movable=True, pen=QtGui.QColor(255,0,255), brush = QtGui.QColor(0,0,255,25), hoverPen=QtGui.QColor(58,59,60), swapMode='block')
        fill.sigDoubleClick.connect(self.DoubleClickonRegion)
        fill.sigRegionChanged.connect(self.changeRegionPosition)
        
        #text 
        text = pg.TextItem(text="",color=(0, 0, 0), anchor=(0.5,0.5))
        text.setPos((coords_0+coords_1)/2, (self.height/2)*0.8)
        text.setText(label)
        
        #store the filled area and text to be able to modify them later
        self.filled_areas.append(fill)
        self.texts.append(text)

        #remove infinite line that controls audio plaback
        if self.isWaveFile: self.removeItem(self.ControlLine)

        #add the elements to the picture
        self.addItem(self.filled_areas[-1])
        self.addItem(self.texts[-1])

        #add again infinite line that controls audio plaback
        if self.isWaveFile: self.addItem(self.ControlLine)

    # def InfoControlLine(self):
    #    self.positionControlLine = self.ControlLine.getXPos()

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

                    self.addFilledAreaandLabel(coords_0, coords_1, 'Rep_'+str(self.total_repetition))

                    #two clicks already, so reset the click counter
                    self.num_clicks = 0 

                    #count the repetitions
                    self.total_repetition +=1

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:      
            scenePos = self.plotItem.vb.mapDeviceToView(QtCore.QPointF(ev.pos()))#self.mapToScene(event.pos())
            x_mousePos = scenePos.x()
            self.mouseDoubleClick.emit(x_mousePos)
        super().mouseDoubleClickEvent(ev)
        return

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
