import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from qtpy import QtWidgets

class PlotWrapper(QtWidgets.QWidget):
    def __init__(self, plotParams, parent=None):     
        super(PlotWrapper, self).__init__(parent)
        self.setWindowTitle('LSL Plot ' + plotParams["name"])
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.ax = self.figure.add_subplot(111)
        self.curves = []
        self.markerList = []
        self.tableColorList = ['r', 'g', 'y', 'c', 'm', 'b']
        self.maxTimeRange = plotParams["max_time_range"]
        
        tick_pos = []
        tick_name = []
        for tick in plotParams["ticks"][0]:
            tick_pos.append(tick[0])
            tick_name.append(tick[1])
        
        self.ax.set(xlim=(-plotParams["init_time_range"], 0.0), ylim=(-1.0 * plotParams["chann_num"], 1.0), 
               xlabel='Time (s)', ylabel='Activation', yticks = tick_pos,
               yticklabels = tick_name);
        for ch_ix in range(plotParams["chann_num"]):
            line, = self.ax.plot([],[])
            self.curves.append(line)
        self.canvas.draw()
        self.canvas.flush_events()
        self.show()
        
    def getWindow(self):
        return self.figure
    
    def updatePlotData(self, timeData, yData, scale):
        for ch in range(np.shape(yData)[0]):
            self.curves[ch].set_data(timeData, ((yData[ch,:])/scale)-ch)
        self.canvas.draw()
        self.canvas.flush_events()
            
    def addMarker(self, event, clock_val):
        eventParam = {}
        eventParam["ts"] = event[0]
        markerLine = self.ax.axvline(x=eventParam["ts"]-clock_val, color=self.tableColorList[event[1]])
        markerText = self.ax.text(eventParam["ts"]-clock_val, self.ax.get_ylim()[1]+0.1,
                        event[2], fontsize=9, color=self.tableColorList[event[1]],
                        horizontalalignment='center')
        eventParam["line"] = markerLine
        eventParam["text"] = markerText
        self.markerList.append(eventParam)
        self.canvas.draw()
        self.canvas.flush_events()
        
    def deleteMarker(self, markerNum):
        self.markerList[markerNum]["line"].remove()
        self.markerList[markerNum]["text"].remove()
        self.markerList.remove(self.markerList[markerNum])
        self.canvas.draw()
        self.canvas.flush_events()
        
    def setNewValMarker(self, markerNum, newVal, plot_duration):
        self.markerList[markerNum]["text"].set_x(newVal)
        if newVal < - plot_duration:
            self.markerList[markerNum]["text"].set_visible(False)
        else:
            self.markerList[markerNum]["text"].set_visible(True)
        self.markerList[markerNum]["line"].set_xdata((newVal,newVal))
        
    def decr_timerange(self):
        xlim_old = self.ax.get_xlim()
        xlim = (xlim_old[0]*0.9, 0.0)
        self.ax.set_xlim(xlim)
        return xlim[0]
    
    def incr_timerange(self):
        xlim_old = self.ax.get_xlim()
        newAxisVal = xlim_old[0]*1.1
        if newAxisVal < -self.maxTimeRange:
            newAxisVal = -self.maxTimeRange
        xlim = (newAxisVal, 0.0)
        self.ax.set_xlim(xlim)
        return xlim[0]
        