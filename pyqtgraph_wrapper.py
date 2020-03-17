import pyqtgraph as pg
import numpy as np

class PlotWrapper:
    def __init__(self, plotParams):
        # Create the pyqtgraph window
        self.win = pg.GraphicsWindow()
        self.win.setWindowTitle('LSL Plot ' + plotParams["name"])
        self.plt = self.win.addPlot()
        self.plt.setTitle(plotParams["name"])
        self.plt.setLimits(xMin=-plotParams["max_time_range"], xMax=0.0, yMin=-1.0 * (plotParams["chann_num"] + 1.0), yMax=1.0)
        self.plt.setXRange(-plotParams["init_time_range"], 0.0, padding=0)
        self.plt.setYRange(-1.0 * plotParams["chann_num"], 1.0, padding=0)
        self.plt.setLabel('left', "Activation")
        self.plt.setLabel('bottom', "Time (s)")
        self.markerList = []
        self.tableColorList = ['r', 'g', 'y', 'c', 'm', 'b']

        self.curves = []
        for ch_ix in range(plotParams["chann_num"]):
            self.curves += [self.plt.plot()]
    
        yax = self.plt.getAxis('left')
        yax.setTicks(plotParams["ticks"])
        self.win.show()
        
    def getWindow(self):
        return self.win
    
    def updatePlotData(self, timeData, yData, scale):
        for ch in range(np.shape(yData)[0]):
            self.curves[ch].setData(timeData, ((yData[ch,:])/scale)-np.shape(yData)[0]+ch+1)
            
    def addMarker(self, event, clock_val):
        eventParam = {}
        eventParam["ts"] = event[0]
        label_opts = {'position': 0.98, 'movable': False, 
                      'anchors': [(0.5, 0.5), (0.5, 0.5)],
                      'fill': pg.mkBrush('k')}
        eventParam["marker"] = pg.InfiniteLine(
            angle=90,movable=False,pos=eventParam["ts"]-clock_val,
            pen=pg.mkPen(self.tableColorList[event[1]]),
            label=event[2], labelOpts=label_opts)
        self.markerList.append(eventParam)
        
        self.plt.addItem(self.markerList[-1]["marker"])
        
    def deleteMarker(self, markerNum):
        self.plt.removeItem(self.markerList[markerNum]["marker"])
        self.markerList.remove(self.markerList[markerNum])
        
    def setNewValMarker(self, markerNum, newVal, plot_duration):
        self.markerList[markerNum]["marker"].setValue(newVal)
        
    def decr_timerange(self):
        gca = self.plt.getViewBox().viewRange()
        newAxisVal = gca[0][0]*0.9
        self.plt.setXRange(newAxisVal,0.0,padding=0)
        return newAxisVal
    
    def incr_timerange(self):
        gca = self.plt.getViewBox().viewRange()
        newAxisVal = gca[0][0]*1.1
        self.plt.setXRange(newAxisVal, 0.0, padding=0)
        return newAxisVal
        