# -*- coding: utf-8 -*-
"""
Created on Wed Oct 30 12:50:50 2019

@author: Antonio
"""

from qtpy import QtCore, QtWidgets, QtGui,uic
 
import sys,os

qtCreatorFile = "stream_viewer.ui" # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(os.path.join(os.path.dirname(__file__),qtCreatorFile))
 
class Dialog(QtWidgets.QDialog, Ui_MainWindow):
 
    def __init__(self, listStreams):
        super(Dialog, self).__init__()
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        for name in listStreams:
            self.comboBox_lslStream.addItem(name)
            
        self.setValuePatterns()
            
    def returnWindowParameters(self):
        windowParameters={}
        windowParameters["stream_num"] = self.comboBox_lslStream.currentIndex()
        windowParameters["max_time_range"] = int(self.lineEdit_maxTimeRange.text())
        windowParameters["init_time_range"] = int(self.lineEdit_initTimeRange.text())
        windowParameters["init_data_scale"] = int(self.lineEdit_initDataScale.text())
        windowParameters["channel_min"] = int(self.lineEdit_channelMin.text())
        windowParameters["channel_max"] = int(self.lineEdit_channelMax.text())
        windowParameters["sampling_rate"] = float(self.lineEdit_samplingRate.text())
        windowParameters["refresh_rate"] = int(self.lineEdit_refreshRate.text())
        windowParameters["frequency_filter"] = self.lineEdit_freqFilter.text().split()
        windowParameters["common_average"] = self.checkBox_commonAverage.isChecked()
        windowParameters["standardize"] = self.checkBox_standardize.isChecked()
        windowParameters["zero_mean"] = self.checkBox_zeroMean.isChecked()
        
        return windowParameters
    
    def setValuePatterns(self):
        self.lineEdit_maxTimeRange.setValidator(QtGui.QIntValidator(0, 2147483647))
        self.lineEdit_initTimeRange.setValidator(QtGui.QIntValidator(0, 2147483647))
        self.lineEdit_initDataScale.setValidator(QtGui.QIntValidator(0, 2147483647))
        self.lineEdit_channelMin.setValidator(QtGui.QIntValidator(1, 2147483647))
        self.lineEdit_channelMax.setValidator(QtGui.QIntValidator(1, 2147483647))
        self.lineEdit_samplingRate.setValidator(QtGui.QIntValidator(0, 2147483647))
        self.lineEdit_refreshRate.setValidator(QtGui.QIntValidator(0, 2147483647))
        self.lineEdit_freqFilter.setValidator(QtGui.QRegExpValidator(
                QtCore.QRegExp("[0-9]{1,3}([ ][0-9]{1,3}[ ][0-9]{1,3}[ ][0-9]{1,3})?")))
            
    def showError(self):
        QtWidgets.QMessageBox.critical(None,'Error','No online streams were found. Please make sure devices are correctly connected and linked.',QtWidgets.QMessageBox.Cancel)
        
    def checkLineEditPattern(self):
        parameters_ok = True
        freqFilter_validator = QtGui.QRegExpValidator(
                QtCore.QRegExp("[0-9]{1,3}([ ][0-9]{1,3}[ ][0-9]{1,3}[ ][0-9]{1,3})?"))
        
        lineEditList = [self.lineEdit_maxTimeRange,self.lineEdit_initTimeRange,self.lineEdit_initDataScale,
                        self.lineEdit_channelMin,self.lineEdit_channelMax,self.lineEdit_samplingRate,
                        self.lineEdit_refreshRate]
        
        for lineEdit in lineEditList:
            if lineEdit.text() == "":
                parameters_ok = False
                
        freqFilter_validation = freqFilter_validator.validate(self.lineEdit_freqFilter.text(),0)
        if freqFilter_validation[0] != 2:
            parameters_ok = False
        
        if parameters_ok is False:
            QtWidgets.QMessageBox.critical(None,'Error','Some parameters were not correctly specified.',QtWidgets.QMessageBox.Cancel)
                
        return parameters_ok
                
 
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    dialog = Dialog()
    sys.exit(dialog.exec_())