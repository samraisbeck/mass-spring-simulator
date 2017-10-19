from PySide import QtGui, QtCore
import sys, os
from subprocess import Popen
import matplotlib
matplotlib.use('Qt4Agg')
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MainGUI(QtGui.QMainWindow):
    def __init__(self):
        super(MainGUI, self).__init__()
        self._initUI()
        self.springArgs = []
        self.mass = 0
        self.damping = 0

    def _initUI(self):
        """Initializes GUI elements, probably should put certain sections into
        their own methods later to organize it better."""
        grid = QtGui.QGridLayout()
        hbox = QtGui.QHBoxLayout()

        # Spring editing section #
        groupbox = QtGui.QGroupBox()
        self.parallelCheck = QtGui.QRadioButton('Parallel', parent=self)
        self.parallelCheck.setChecked(True)
        self.seriesCheck = QtGui.QRadioButton('Series', parent=self)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.parallelCheck)
        vbox.addWidget(self.seriesCheck)
        groupbox.setLayout(vbox)
        groupbox.setContentsMargins(0,0,0,0)
        hbox.addWidget(groupbox)
        vbox = QtGui.QVBoxLayout()
        hbox2 = QtGui.QHBoxLayout()
        self.springsEdit = QtGui.QLineEdit()
        self.springsEdit.setPlaceholderText('Add series or parallel springs...')
        self.springsEdit.setToolTip('Series example: 100 200 35 ... Parallel example: 150')
        hbox2.addWidget(self.springsEdit)
        button = QtGui.QPushButton('Add Spring(s)', parent=self)
        button.clicked.connect(self.addSprings)
        hbox2.addWidget(button)
        button = QtGui.QPushButton('Delete Last Spring', parent=self)
        button.clicked.connect(self.deleteLastSpring)
        hbox2.addWidget(button)
        button = QtGui.QPushButton('Delete All Springs', parent=self)
        button.clicked.connect(self.deleteAllSprings)
        hbox2.addWidget(button)
        vbox.addLayout(hbox2)
        self.curSpringsLabel = QtGui.QLabel('Current Springs: ', parent=self)
        vbox.addWidget(self.curSpringsLabel)
        hbox.addLayout(vbox)
        grid.addLayout(hbox, 0, 0)

        # Other paramaters section (mass, damping, etc...) #
        hbox = QtGui.QHBoxLayout()
        labelMass = QtGui.QLabel('Mass: ', parent=self)
        self.massEdit = QtGui.QLineEdit()
        self.massEdit.setText('1')
        hbox.addWidget(labelMass)
        hbox.addWidget(self.massEdit)
        grid.addLayout(hbox, 1, 0)
        hbox = QtGui.QHBoxLayout()
        labelDamping = QtGui.QLabel('Damping: ', parent=self)
        self.dampingEdit = QtGui.QLineEdit()
        self.dampingEdit.setText('0')
        hbox.addWidget(labelDamping)
        hbox.addWidget(self.dampingEdit)
        grid.addLayout(hbox, 2, 0)
        hbox = QtGui.QHBoxLayout()
        labelForcing = QtGui.QLabel('Forcing Function: ', parent=self)
        self.forcingEdit = QtGui.QLineEdit()
        self.forcingEdit.setText('0')
        hbox.addWidget(labelForcing)
        hbox.addWidget(self.forcingEdit)
        button = QtGui.QPushButton('Format Help', parent=self)
        button.clicked.connect(self.showForcingHelp)
        hbox.addWidget(button)
        grid.addLayout(hbox, 3, 0)
        hbox = QtGui.QHBoxLayout()
        label = QtGui.QLabel('Initial Position (0 to 5 meters): ', parent=self)
        self.initPosEdit = QtGui.QLineEdit()
        self.initPosEdit.setText('2')
        hbox.addWidget(label)
        hbox.addWidget(self.initPosEdit)
        label = QtGui.QLabel('Speed of Simulation (%): ', parent=self)
        self.speedPercentEdit = QtGui.QLineEdit()
        self.speedPercentEdit.setText('100')
        self.speedPercentEdit.setToolTip('100 is full speed, 50 is half speed, etc...')
        hbox.addWidget(label)
        hbox.addWidget(self.speedPercentEdit)
        grid.addLayout(hbox, 4, 0)

        # Plot section #
        self.fig = Figure(figsize=(600,600), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
        ax = self.fig.add_subplot(111)
        ax.plot([0,0])
        ax.set_title("Position vs. Time (nothing entered)")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Position (m)")
        # the canvas is the actual thing you add to the GUI
        self.canvas = FigureCanvas(self.fig)
        grid.addWidget(self.canvas, 5, 0)

        # Main controls #
        hbox = QtGui.QHBoxLayout()
        button = QtGui.QPushButton('Plot', parent=self)
        button.clicked.connect(self.plotData)
        hbox.addWidget(button)
        button = QtGui.QPushButton('Launch Simulator', parent=self)
        button.clicked.connect(self.launchSimulator)
        hbox.addWidget(button)
        grid.addLayout(hbox, 6, 0)
        Qw = QtGui.QWidget()
        Qw.setLayout(grid)
        self.setCentralWidget(Qw)
        self.show()

    def addSprings(self):
        """Based on text in the spring stiffness box, and also whether the
        parallel/series dot is filled, adds the spring stiffness(es) to the
        list (SP means spring parallel, SS means spring series. SS is always
        followed by the number of springs on that series, then the values of
        the stiffnesses themselves)"""
        text = self.springsEdit.text().split()
        l = len(text)
        tempText = 'Current Springs: '
        if self.parallelCheck.isChecked():
            for i in range(l):
                self.springArgs.append('SP'+text[i])
        else:
            self.springArgs.append('SS'+str(l))
            for i in range(l):
                self.springArgs.append(text[i])
        for spring in self.springArgs:
            tempText += spring+' '
        self.curSpringsLabel.setText(tempText)

    def showForcingHelp(self):
        """Nothing helpful right now"""
        box = QtGui.QMessageBox(parent=self)
        box.setText("help")

        box.exec_()

    def deleteLastSpring(self):
        """Deletes the last spring entered. If it's a series spring, deletes
        all springs on that series."""
        if len(self.springArgs) == 0:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'There are '\
                              'no springs to delete.', parent=self)
            box.exec_()
            return
        temp = self.springArgs.pop()
        tempText = 'Current Springs: '
        if temp[0:2] == 'SP':
            pass
        else:
            while temp[0:2] != 'SS':
                temp = self.springArgs.pop()
        for spring in self.springArgs:
            tempText += spring+' '
        self.curSpringsLabel.setText(tempText)

    def deleteAllSprings(self):
        """Deletes all springs"""
        if len(self.springArgs) == 0:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'There are '\
                              'no springs to delete.', parent=self)
            box.exec_()
            return
        self.springArgs = []
        self.curSpringsLabel.setText('Current Springs: ')

    def launchSimulator(self):
        """Launches the pygame simulator via command line. Sends the springArgs
        (which indicate parallel or series), mass, damping, initial position,
        and speed of simulation to be processed in the spring.py file."""
        if len(self.springArgs) == 0:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'You must '\
                              'enter at least one spring stiffness.', parent=self)
            box.exec_()
            return
        elif float(self.initPosEdit.text()) < 0 or float(self.initPosEdit.text()) > 5:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Initial position must '\
                              'be in the range of 0-5 meters.', parent=self)
            box.exec_()
            return
        elif float(self.speedPercentEdit.text()) <= 0 or float(self.speedPercentEdit.text()) > 100:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Speed percentage '\
                              'must be greater than 0% and less or equal to 100%', parent=self)
            box.exec_()
            return
        directory = os.path.dirname(os.path.realpath(__file__))
        massArg = 'M'+self.massEdit.text()
        dampingArg = 'D'+self.dampingEdit.text()
        initPosArg = 'IP'+self.initPosEdit.text()
        speedArg = 'PS'+self.speedPercentEdit.text()
        args = [sys.executable, directory+'\\spring.py']+self.springArgs+[massArg, dampingArg, initPosArg, speedArg]
        Popen(args, cwd = directory)

    def plotData(self):
        """Unfortunately, right now we need to calculate the approximation when
        plotting AND when simulating. This is because a good way of passing a
        huge array of position/time data to a pygame window has not been
        found (or from the pygame window to the GUI). This is fine for now
        since the math takes less than half a second to complete...but it's
        a little messy.
        Watch this to understand Euler's method: https://www.youtube.com/watch?v=k2V2UYr6lYw"""
        y_t = [] # temp y
        y_t.append(float(self.initPosEdit.text())) # Needs ot be user entered
        t_t = [] # temp t
        t_t.append(0)
        z = []
        z.append(0) # z = dy/dx for Euler method
        b = int(self.dampingEdit.text())
        m = int(self.massEdit.text())
        k = self.getStiffness()
        inc = 0.0001
        for i in range(1, 100000):
            t_t.append(t_t[i-1]+inc)
            y_t.append(y_t[i-1] + z[i-1]*inc)
            z.append(z[i-1] + ((-b/m)*z[i-1] - (k/m)*y_t[i-1])*inc)
        ax = self.fig.add_subplot(111)
        ax.clear()
        ax.plot(t_t, y_t)
        ax.set_title("Position vs. Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Position (m)")
        self.canvas.draw()

    def getStiffness(self):
        """Gets the stiffness of all the springs in springArgs to be used
        in the plot function."""
        stiffness = 0
        for i in range(len(self.springArgs)):
            if self.springArgs[i][0:2] == 'SP':
                stiffness += int(self.springArgs[i][2:])
            elif self.springArgs[i][0:2] == 'SS':
                num = int(self.springArgs[i][2])
                seriesK = 0
                for j in range(num):
                    seriesK += 1.0/int(self.springArgs[i+1+j])
                stiffness += 1.0/seriesK
        return stiffness

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mw = MainGUI()
    app.exec_()
