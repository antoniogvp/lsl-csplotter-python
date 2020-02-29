from qtpy import QtGui, QtCore, QtWidgets, uic
 
import os

qtCreatorFile = "markers_dialog.ui" # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(os.path.join(os.path.dirname(__file__),qtCreatorFile))
 
class DialogMarkers(QtWidgets.QDialog, Ui_MainWindow):
 
    def __init__(self, listStreams):
        super(DialogMarkers, self).__init__()
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        for stream in listStreams:
            chkBoxItem = QtWidgets.QListWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            chkBoxItem.setText(stream)
            self.listStreams.addItem(chkBoxItem)
            
    def returnWindowParameters(self):
        checkedItems = []
        for index in range(self.listStreams.count()):
            if self.listStreams.item(index).checkState() == QtCore.Qt.Checked:
                checkedItems.append(index)
        return checkedItems
            
    def showErrorNoStreams(self):
        QtWidgets.QMessageBox.critical(None,'Error','No online streams were found. Please make sure devices are correctly connected and linked.',QtWidgets.QMessageBox.Cancel)
     
if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = DialogMarkers(["test","2"])
    dialog.exec_()
    #sys.exit(dialog.exec_())
    items = dialog.returnWindowParameters()