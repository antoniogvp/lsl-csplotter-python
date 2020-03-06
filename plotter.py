import numpy as np
from pylsl import StreamInlet, resolve_stream, local_clock
from qtpy import QtCore, QtGui, QtWidgets
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
        self.inlet = StreamInlet(sortedStreams["continuous"][windowParameters["stream_num"]])
        
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
        
        ticks = self.getPlotTicks()
        self.datareceived = False
        self.str_buffer = self.create_buffer()
        self.eventList = []
        self.configureTimers()
        
        if self.windowParameters["plot_library"] == 0:
            from matplotlib_wrapper import PlotWrapper
        else:
            from pyqtgraph_wrapper import PlotWrapper
        
        plotParams = {"name":self.inlet.info().name(), 
                      "max_time_range": windowParameters["max_time_range"],
                      "init_time_range": windowParameters["init_time_range"],
                      "chann_num": self.channel_num, "ticks": ticks}
        self.plotWrapper = PlotWrapper(plotParams)
        self.win = self.plotWrapper.getWindow()
        
    def configureTimers(self):
        self.timerData = QtCore.QTimer()
        self.timerData.timeout.connect(self.updateData)
        self.timerData.start(1000.0/self.windowParameters["sampling_rate"])
        
        self.timerPlot = QtCore.QTimer()
        self.timerPlot.timeout.connect(self.updatePlot)
        self.timerPlot.start(1000.0/self.windowParameters["refresh_rate"])
    
    def create_buffer(self):
        str_buffer={}
        if self.inlet.info().nominal_srate() > 0:
            str_buffer["srate"] = self.inlet.info().nominal_srate()
        else:
            str_buffer["srate"] = self.windowParameters["sampling_rate"]
        
        str_buffer["buffer"] = np.zeros((self.inlet.info().channel_count(), 
                                         int(max(max(self.windowParameters["max_time_range"], self.windowParameters["init_time_range"])*str_buffer["srate"],100))))
        str_buffer["nsamples"] = 0
        return str_buffer

    def updateData(self):
        self.updateDataContinuousStream()
        self.updateDataEvents()
        
    def updateDataContinuousStream(self):
        # Read data from the inlet. Use a timeout of 0.0 so we don't block GUI interaction.
        chunk, timestamps = self.inlet.pull_chunk(timeout=0.0)
        if timestamps:
            ts = np.asarray(timestamps)
            y = np.asarray(chunk).transpose()
            
            if len(np.shape(y))==1:
                y=y[np.newaxis,:]
            
            if self.B.size != 0:
                y = lfilter(self.B,np.asarray(1),y,0)
                self.datareceived = True
            
            # append to buffer
            self.str_buffer["nsamples"] += np.shape(y)[1]
            self.str_buffer["buffer"][:, np.remainder(np.arange(self.str_buffer["nsamples"], self.str_buffer["nsamples"] + np.shape(y)[1]), np.shape(self.str_buffer["buffer"])[1])] = y
            
            samples_to_get = min(np.shape(self.str_buffer["buffer"])[1], round(self.str_buffer["srate"]*self.plot_duration));
            channels_to_get = np.arange(self.channel_min-1,self.channel_max)
            samples_indexes = np.remainder(np.arange(self.str_buffer["nsamples"]-samples_to_get,self.str_buffer["nsamples"],int(self.str_buffer["srate"]/self.windowParameters["sampling_rate"])),np.shape(self.str_buffer["buffer"])[1])
            self.yData = self.str_buffer["buffer"][channels_to_get[:,np.newaxis], samples_indexes[np.newaxis,:]]
            
            if len(np.shape(self.yData))==1:
                self.yData = self.yData[np.newaxis,:]
                
            [nchan, npoints] = np.shape(self.yData)
            xmax = np.amax(ts) - local_clock();
            xmin = xmax - (samples_to_get-1)/self.str_buffer["srate"]
            
            ## POST-PROCESS ##
            if(self.windowParameters["common_average"] is True):
                self.common_average()
            
            if(self.windowParameters["standardize"] is True):
                self.standardize()
                
            if(self.windowParameters["zero_mean"] is True):
                self.zero_average()
                
            self.timeData = np.linspace(xmin,xmax,npoints)
            self.datareceived = True
        
    def updateDataEvents(self):
        for stream in self.eventInlet:
            chunk, timestamps = stream.pull_chunk(timeout=0.0)
            if timestamps:
                ts = np.asarray(timestamps)
                    
                for n in range(np.size(ts)):
                    event = []
                    event.append(float(ts[n]))
                    event.append(self.eventInlet.index(stream)%6)
                    event.append(stream.info().name())
                    self.eventList.append(event)
                        
    def updatePlot(self):
        if (self.datareceived is True):
            clock_val = local_clock()
            
            self.plotWrapper.updatePlotData(self.timeData, self.yData, self.scale)
            
            for i in reversed(range(len(self.plotWrapper.markerList))):
                newMarkerTs = self.plotWrapper.markerList[i]["ts"] - clock_val
                
                if newMarkerTs < - self.windowParameters["max_time_range"]:
                    self.plotWrapper.deleteMarker(i)
                else:
                    self.plotWrapper.setNewValMarker(i, newMarkerTs, self.plot_duration)
            
            for event in self.eventList:
                self.plotWrapper.addMarker(event, clock_val)
                
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
                if ch.child_value("label") == "":
                    markers.append("Ch" + str(k))
                else:
                    markers.append(ch.child_value("label"))
                chanpos.append(-self.channel_num+chancounter+1)
                chancounter = chancounter + 1
            ch = ch.next_sibling()
    
        ticks = [list(zip(chanpos, markers))]
            
        return ticks
    
    def common_average(self):
        self.yData = self.yData-(np.mean(self.yData,axis=0)[np.newaxis,:])
        
    def standardize(self):
        try:
            stdev = np.std(self.yData,axis=1,ddof=1).reshape((-1, 1))
            self.yData = self.yData*(1/stdev)
        except: 
            pass
        
    def zero_average(self):
        self.yData = self.yData-(np.mean(self.yData,axis=1)[:,np.newaxis])
        
    def decr_datascale(self, k):
        self.scale = self.scale*1.1
    
    def incr_datascale(self, k):
        self.scale = self.scale*0.9
    
    def decr_timerange(self, k):
        newAxisVal = self.plotWrapper.decr_timerange()
        self.plot_duration = -newAxisVal
    
    def incr_timerange(self, k):
        newAxisVal = self.plotWrapper.incr_timerange()
        self.plot_duration = -newAxisVal
        
    def getWindow(self):
        return self.win

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
                result = dialogMarkers.exec_()
                if result == 1:
                    checkedMarkers = dialogMarkers.returnWindowParameters()
            p = Plotter(windowParameters, checkedMarkers, sortedStreams)
            win = p.getWindow()
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
        QtWidgets.QApplication.instance().exec_()
    return win 

if __name__ == '__main__':
    import sys
    win = Start()
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    if (((sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION')) ):
        app.instance().exec_()
    sys.exit(0)
