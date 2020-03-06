# Continuous LSL stream plotter for Python
Online plotter for Lab Streaming Layer (LSL) continuous streams in Pyhton using `pyqtgraph` and `matplotlib`.
## Installation
* Prerequisites
  * Python > 3.5
  * PyQt: set of Python v2 and v3 bindings for the Qt application framework. Normally, they come by default with a default Qt installation.
  * [`liblsl`](https://github.com/sccn/labstreaminglayer/wiki/INSTALL) built from source code.
  * [`pylsl`](https://labstreaminglayer.readthedocs.io/dev/app_dev.html#python-apps): Python interface to the Lab Streaming Layer (LSL).
* Download and copy the files to a folder in the Lab Streaming Layer directory tree in your computer.
* Data visualization can be done either with `matplotlib` or `pyqtgraph`. Wrappers are available for both libraries. The library is selected at the beginning of the execution, in a Dialog that is prompted to the user.
* (Optional) To allow the keyboard shortcuts (variation of time range, scaling), install the [`keyboard`](https://pypi.org/project/keyboard/) module for Python

## Usage
* Start a LSL stream by linking a device with the computer with its corresponding application. 
* Run `plotter.py`. A dialog with several options will appear.
* Choose between the different buffering, filtering and visualization options and press OK.
* If marker streams are available, a new Dialog where the user can choose between them in order to display their associated events will appear. Select the desired streams and press OK.
* A new window with the plot will appear.


###### 