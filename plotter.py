import numpy as np
from pylsl import StreamInlet, resolve_stream, local_clock
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from stream_viewer import Dialog
from markers_dialog import DialogMarkers
from scipy.signal import lfilter
from filter_BP import BandPassFilter

try:
    import keyboard
except:
    print("keyboard module not found. Keyboard functionalities disabled.")

def classifyStreamInlet(streams):
    contStreamsNames = []
    discStreamsNames = []
    sortedStreams = {}
    sortedStreams["continuous"] = []
    sortedStreams["discrete"] = []
    
    for stream in streams:
        stream_type = StreamInlet(stream).info().type()
        if stream_type == "Markers" or stream_type == "Events":
            sortedStreams["discrete"].append(stream)
            discStreamsNames.append(StreamInlet(stream).info().name())
        else:
            sortedStreams["continuous"].append(stream)
            contStreamsNames.append(StreamInlet(stream).info().name())
    return sortedStreams, contStreamsNames, discStreamsNames
    
class Plotter:
    def __init__(self, windowParameters, checkedMarkers, sortedStreams):
        #Initializes the stream chosen by the user.
        self.plot_duration = windowParameters["init_time_range"]
        self.windowParameters = windowParameters

        # create a new inlet to read from the stream
        self.inlet = StreamInlet(sortedStreams["continuous"][windowParameters["stream_num"]],
                                 max_buflen = windowParameters["max_time_range"])
        
        # Marker streams
        self.eventInlet = []
        for num in checkedMarkers:
            self.eventInlet.append(StreamInlet(sortedStreams["discrete"][num]))
        
        self.channel_min = windowParameters["channel_min"]
        self.channel_max = self.getHighestChannel(self.inlet.info().channel_count())
        self.channel_num = (self.channel_max - self.channel_min) + 1
        self.scale = windowParameters["init_data_scale"]
        frequency_filter = [int(i) for i in windowParameters["frequency_filter"]]
        self.B = BandPassFilter(frequency_filter, self.inlet.info().nominal_srate()).returnFilter()
        
        self.ticks = self.getPlotTicks()
        self.datareceived = False
        self.initializeDataLists()
        self.eventList = []
        self.markerList = []
        self.tableColorList = ['r', 'g', 'y', 'c', 'm', 'b']
        self.configureTimers()
        
    def configureTimers(self):
        self.timerData = QtCore.QTimer()
        self.timerData.timeout.connect(self.updateData)
        self.timerData.start(1000.0/self.windowParameters["sampling_rate"])
        
        self.timerPlot = QtCore.QTimer()
        self.timerPlot.timeout.connect(self.updatePlot)
        self.timerPlot.start(1000.0/self.windowParameters["refresh_rate"])
        
    def initializeDataLists(self):
        self.dataX = []
        self.dataY = []
        for ch_ix in range(self.channel_min-1,self.channel_max):
            self.dataX.append([])
            self.dataY.append([])

    def createPlot(self):
        # Create the pyqtgraph window
        win = pg.GraphicsWindow()
        win.setWindowTitle('LSL Plot ' + self.inlet.info().name())
        self.plt = win.addPlot()
        self.plt.setLimits(xMin=0.0, xMax=30, yMin=-1.0 * (self.channel_num + 1.0), yMax=1.0)
        self.plt.setXRange(0.0, self.plot_duration, padding=0)
        self.plt.setYRange(-1.0 * self.channel_num, 1.0, padding=0)
        self.plt.setLabel('left', "Activation")
        self.plt.setLabel('bottom', "Time (s)")

        self.t0 = [local_clock()] * self.channel_num
        self.curves = []
        for ch_ix in range(self.channel_num):
            self.curves += [self.plt.plot()]
        
        # if len(self.eventInlet)>0:
        #     legend = self.plt.addLegend(size = (100,10))
        
        #     for t in self.eventInlet:
        #         self.plt.plot (y=[-30.0], 
        #                    pen=pg.mkPen(self.tableColorList[self.eventInlet.index(t)%6]),
        #                    name=t.info().name())
    
        yax = self.plt.getAxis('left')
        yax.setTicks(self.ticks)
        return win

    def updateData(self):
        self.updateDataContinuousStream()
        self.updateDataEvents()
        
    def updateDataContinuousStream(self):
        # Read data from the inlet. Use a timeout of 0.0 so we don't block GUI interaction.
        chunk, timestamps = self.inlet.pull_chunk(timeout=0.0, max_samples=100)
        if timestamps:
            self.ts = np.asarray(timestamps)
            self.y = np.asarray(chunk)
            
            if self.B.size != 0:
                self.y = lfilter(self.B,np.asarray(1),self.y,0)
                self.datareceived = True
            
            ## POST-PROCESS ##
            if(self.windowParameters["common_average"] is True):
                self.common_average()
            
            if(self.windowParameters["standardize"] is True):
                self.standardize()
                
            if(self.windowParameters["zero_mean"] is True):
                self.zero_average()
            
            self.datareceived = True
        
    def updateDataEvents(self):
        for stream in self.eventInlet:
            chunk, timestamps = stream.pull_chunk(timeout=0.0, max_samples=100)
            if timestamps:
                ts = np.asarray(timestamps)
                # y = np.asarray(chunk)
                    
                for n in range(np.size(ts)):
                    event = []
                    event.append(float(ts[n]))
                    event.append(self.eventInlet.index(stream)%6)
                    event.append(stream.info().name())
                    self.eventList.append(event)
                        
    def updatePlot(self):
        if (self.datareceived is True):
            chancounter = 0
            oldMaxTs = self.t0[0]
            for ch_ix in range(self.channel_min-1,self.channel_max):
                if len(self.dataX[chancounter])>0:
                    self.dataX[chancounter] += self.t0[ch_ix]  # Undo t0 subtraction
                self.dataX[chancounter] = np.hstack((self.dataX[chancounter], self.ts[-1]))
                self.dataY[chancounter] = np.hstack((self.dataY[chancounter], self.y[[-1], ch_ix]))
                self.t0[ch_ix] = self.dataX[chancounter][-1] - self.plot_duration
                self.dataX[chancounter] -= self.t0[ch_ix]
                self.dataX[chancounter] = [x for x in self.dataX[chancounter] if x >= -30.0]
                self.dataY[chancounter] = self.dataY[chancounter][-len(self.dataX[chancounter]):]
                self.curves[chancounter].setData(self.dataX[chancounter], (self.dataY[chancounter]/self.scale)-ch_ix)
                chancounter = chancounter + 1
            
            for marker in reversed(self.markerList):
                newMarkerTs = (marker.value() + oldMaxTs) - self.t0[0]
                
                if newMarkerTs < -30.0:
                    self.markerList.remove(marker)
                else:
                    marker.setValue(newMarkerTs)
            
            for event in self.eventList:
                label_opts = {'position': 0.98, 'movable': False, 
                              'anchors': [(0.5, 0.5), (0.5, 0.5)],
                              'fill': pg.mkBrush('k')}
                self.markerList.append(pg.InfiniteLine(
                    angle=90,movable=False,pos=event[0]-self.t0[0],
                    pen=pg.mkPen(self.tableColorList[event[1]]),
                    label=event[2], labelOpts=label_opts))
                self.plt.addItem(self.markerList[-1])
                
            self.eventList.clear()
            
                
    def getHighestChannel(self, channel_count):
        if(channel_count < self.windowParameters["channel_max"]):
            channel_max = channel_count
        else:
            channel_max = self.windowParameters["channel_max"]
        return channel_max
    
    def getPlotTicks(self):
        chancounter = 0
        
        ch = self.inlet.info().desc().child("channels").child("channel")
        markers = list()
        chanpos = list()
        for k in range(self.inlet.info().channel_count()):
            if(k>=self.channel_min-1 and k<self.channel_max):
                markers.append(ch.child_value("label"))
                chanpos.append(-self.channel_num+chancounter+1)
                chancounter = chancounter + 1
            ch = ch.next_sibling()
    
        ticks = [list(zip(chanpos, markers))]
        return ticks
    
    def common_average(self):
        self.y = self.y-(np.mean(self.y))
        
    def standardize(self):
        self.y = self.y-(np.mean(self.y))
        
    def zero_average(self):
        stdev = np.std(self.y,axis=1,ddof=1).reshape((-1, 1))
        self.y = self.y*(1/stdev)
        
    def decr_datascale(self, k):
        self.scale = self.scale*0.9
    
    def incr_datascale(self, k):
        self.scale = self.scale*1.1
    
    def decr_timerange(self, k):
        gca = self.plt.getViewBox().viewRange()
        newAxisVal = gca[0][1]*0.9
        self.plt.setXRange(0.0,newAxisVal,padding=0)
        self.plot_duration = newAxisVal
    
    def incr_timerange(self, k):
        gca = self.plt.getViewBox().viewRange()
        newAxisVal = gca[0][1]*1.1
        self.plt.setXRange(0.0, newAxisVal, padding=0)
        self.plot_duration = newAxisVal

def Start():
    streams = resolve_stream()
    
    sortedStreams, contStreamsNames, discStreamsNames = classifyStreamInlet(streams)
    dialogContinuous = Dialog(contStreamsNames)
    dialogMarkers = DialogMarkers(discStreamsNames)

    if(len(sortedStreams["continuous"]) == 0):
        dialogContinuous.showError()
    
    else:
        if dialogContinuous.exec_() and dialogContinuous.checkLineEditPattern():
            windowParameters = dialogContinuous.returnWindowParameters()
            checkedMarkers = []
            if len(discStreamsNames) > 0:
                dialogMarkers.exec_()
                if dialogMarkers.accepted is True:
                    checkedMarkers = dialogMarkers.returnWindowParameters()
            p = Plotter(windowParameters, checkedMarkers, sortedStreams)
            win = p.createPlot()
            win.show()
            try:
                keyboard.on_press_key('down', p.decr_datascale)
                keyboard.on_press_key('up', p.incr_datascale)
                keyboard.on_press_key('left', p.decr_timerange)
                keyboard.on_press_key('right', p.incr_timerange)
            except:
                pass
            
        else:
            print("Plot window was not created.")
        
    return win

def main():
    win = Start()
    import sys
    if (((sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION')) ):
        QtGui.QApplication.instance().exec_()
    return win 

if __name__ == '__main__':
    import sys
    win = Start()
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    if (((sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION')) ):
        app.instance().exec_()
    sys.exit(0)

