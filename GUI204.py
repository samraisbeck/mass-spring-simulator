
from PySide import QtGui, QtCore
import sys, os
from subprocess import Popen
import matplotlib
matplotlib.use('Qt4Agg')
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import math

"""
To do:
- Forcing Functions
- data printed on simulation window
    - i.e mass, damping, stiffness, etc
- make it all look better
- spring on both sides (possibly?)
- add hanging spring version
    - this could maybe be just a checkbox the user can select, or a new tab
    in the GUI
    - if this is selected, then run the hanging mass calculation, if not,
    run the calculation we have going right now.
"""

class MainGUI(QtGui.QMainWindow):
    def __init__(self):
        super(MainGUI, self).__init__()
        self._initUI()
        self.springArgs = []
        self.mass = 0
        self.damping = 0

### GUI SETUP STARTS HERE ####################

    def _initUI(self):
        """Initializes GUI elements, probably should put certain sections into
        their own methods later to organize it better."""
        grid = QtGui.QGridLayout()
        grid.addLayout(self._UISprings(), 0, 0)
        # Other paramaters section (mass, damping, etc...) #
        grid.addLayout(self._UIMass(), 1, 0)
        grid.addLayout(self._UIDamping(), 2, 0)
        grid.addLayout(self._UIForcingOptions(), 3, 0)
        grid.addLayout(self._UIInitPosAndSpeed(), 4, 0)
        # Plot section #
        self.canvas = self._UISetupPlot()
        grid.addWidget(self.canvas, 5, 0)
        # Main controls #
        grid.addLayout(self._UIMainControls(), 6, 0)
        Qw = QtGui.QWidget()
        Qw.setLayout(grid)
        self.setCentralWidget(Qw)
        self.show()

    def _UISprings(self):
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
        return hbox

    def _UIMass(self):
        hbox = QtGui.QHBoxLayout()
        labelMass = QtGui.QLabel('Mass: ', parent=self)
        self.massEdit = QtGui.QLineEdit()
        self.massEdit.setText('1')
        hbox.addWidget(labelMass)
        hbox.addWidget(self.massEdit)
        return hbox

    def _UIDamping(self):
        hbox = QtGui.QHBoxLayout()
        labelDamping = QtGui.QLabel('Damping: ', parent=self)
        self.dampingEdit = QtGui.QLineEdit()
        self.dampingEdit.setText('0')
        hbox.addWidget(labelDamping)
        hbox.addWidget(self.dampingEdit)
        return hbox

    def _UIForcingOptions(self):
        hbox = QtGui.QHBoxLayout()
        leftGroupbox = QtGui.QGroupBox()
        leftInnerHBox = QtGui.QHBoxLayout()

        self.direction="X"
        self.horizontalDirection = QtGui.QRadioButton('Horizontal Spring', parent=self)
        self.horizontalDirection.setChecked(True)
        self.horizontalDirection.clicked.connect(self.setHorizontal)
        self.verticalDirection = QtGui.QRadioButton('Vertical Spring', parent=self)
        self.verticalDirection.clicked.connect(self.setVertical)

        leftInnerHBox.addWidget(self.horizontalDirection)
        leftInnerHBox.addWidget(self.verticalDirection)
        leftGroupbox.setLayout(leftInnerHBox)
        leftGroupbox.setContentsMargins(0,0,0,0)
        hbox.addWidget(leftGroupbox)

        labelForcing = QtGui.QLabel('Forcing Function: ', parent=self)
        self.forcingDropDown = QtGui.QComboBox()

        hbox.addWidget(labelForcing, 0, QtCore.Qt.AlignRight)
        self.forcingDropDown.addItem('None')
        self.forcingDropDown.addItem('f(t) = 10')
        self.forcingDropDown.addItem('f(t) = t')
        self.forcingDropDown.addItem('f(t) = t^2')
        self.forcingDropDown.addItem('f(t) = sin(t)')
        self.forcingDropDown.addItem('f(t) = e^-t')
        hbox.addWidget(self.forcingDropDown)

        groupbox = QtGui.QGroupBox()
        innerHBox = QtGui.QHBoxLayout()

        self.doParams = QtGui.QRadioButton('Show Current Parameters', parent=self)
        self.doParams.setChecked(True)
        self.doParams.clicked.connect(self.reEnableForcingMenu)
        self.resonanceCheck = QtGui.QRadioButton('Show Resonance', parent=self)
        self.antiResonanceCheck = QtGui.QRadioButton('Show Anti-Resonance', parent=self)
        self.resonanceCheck.clicked.connect(self.resonanceForcing)
        self.antiResonanceCheck.clicked.connect(self.resonanceForcing)

        innerHBox.addWidget(self.doParams)
        innerHBox.addWidget(self.resonanceCheck)
        innerHBox.addWidget(self.antiResonanceCheck)
        groupbox.setLayout(innerHBox)
        groupbox.setContentsMargins(0,0,0,0)
        hbox.addWidget(groupbox)
        button = QtGui.QPushButton("What's this doing?", parent=self)
        button.clicked.connect(self.resonanceHelp)
        hbox.addWidget(button)
        return hbox

    def _UIInitPosAndSpeed(self):
        hbox = QtGui.QHBoxLayout()
        label = QtGui.QLabel('Initial Position (-5 to 5 meters): ', parent=self)
        self.initPosEdit = QtGui.QLineEdit()
        self.initPosEdit.setText('2')
        hbox.addWidget(label)
        hbox.addWidget(self.initPosEdit)
        label = QtGui.QLabel('Speed of Simulation (1 to 150%): ', parent=self)
        self.speedPercentEdit = QtGui.QLineEdit()
        self.speedPercentEdit.setText('100')
        self.speedPercentEdit.setToolTip('100 is full speed, 50 is half speed, etc...')
        hbox.addWidget(label)
        hbox.addWidget(self.speedPercentEdit)
        label = QtGui.QLabel('Length of Simulation (0 to 20s): ', parent=self)
        self.lengthEdit = QtGui.QLineEdit()
        self.lengthEdit.setText('10')
        hbox.addWidget(label)
        hbox.addWidget(self.lengthEdit)
        return hbox

    def _UISetupPlot(self):
        self.fig = Figure(figsize=(600,600), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
        ax = self.fig.add_subplot(111)
        ax.plot([0,0])
        ax.set_title("Position vs. Time (nothing entered)")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Position (m)")
        # the canvas is the actual thing you add to the GUI
        return FigureCanvas(self.fig)

    def _UIMainControls(self):
        hbox = QtGui.QHBoxLayout()
        button = QtGui.QPushButton('Plot', parent=self)
        button.clicked.connect(self.plotData)
        hbox.addWidget(button)
        button = QtGui.QPushButton('Launch Simulator', parent=self)
        button.clicked.connect(self.launchSimulator)
        hbox.addWidget(button)
        return hbox

### GUI SETUP ENDS HERE #############################

    def addSprings(self):
        """Based on text in the spring stiffness box, and also whether the
        parallel/series dot is filled, adds the spring stiffness(es) to the
        list (SP means spring parallel, SS means spring series. SS is always
        followed by the number of springs on that series, then the values of
        the stiffnesses themselves)"""

        # if self.springsEdit.text() == "" or float(self.springsEdit.text()) <= 0:
        #     box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'You must '\
        #                       'enter a non-zero value for spring stiffness.', parent=self)
        #     box.exec_()
        #     return
        #
        # I feel like this check is better done in a loop below, because users
        # can enter in multiple values for stiffness.
        # Also we can then see if each element is in fact a number greater than
        # 0 and not like a word or letter or something.

        text = self.springsEdit.text().split()
        if len(text) == 0:
            # someone didn't enter anything
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Must have at '\
                                    'least one stiffness value.', parent=self)
            box.exec_()
            return
        for number in text:
            try:
                if float(number) <= 0:
                    # someone entered 0 or a negative number
                    box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Stiffnesses '\
                                      'must be above 0.', parent=self)
                    box.exec_()
                    return
            except:
                # someone entered something that can't be converted to a float (like a letter)
                box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Something went '\
                                  'wrong. Stiffnesses not entered. Should be in the format of '\
                                  '"100 200 100" as an example.', parent=self)
                box.exec_()
                return
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

    def resonanceHelp(self):
        """Nothing helpful right now"""
        box = QtGui.QMessageBox(parent=self)
        box.setText("If 'Show Current Parameters' is checked, the program will "+\
                     "plot the position with the parameters you have entered. If "+\
                     "'Show Resonance' is checked, the position will be plotted for "+\
                     "a mass of 2 and a stiffness of 8. In this case, the homogeneous "+\
                     "component of the solution has the same frequency as the forcing "+\
                     "function, so the oscillations are forced to grow. If 'Show Anti-'"+\
                     "Resonance' is selected, the same thing happens as with resonance, "+\
                     "but the mass starts at the opposite side. Therefore, the frequencies "+\
                     "are opposite each other, and oscillations decrease even though there "+\
                     "is no damping force.")

        box.exec_()

    def setHorizontal(self):
        self.direction = "X"

    def setVertical(self):
        self.direction = "Y"

    def resonanceForcing(self):
        self.forcingDropDown.setCurrentIndex(0)
        self.forcingDropDown.setEnabled(False)

    def reEnableForcingMenu(self):
        self.forcingDropDown.setEnabled(True)

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
        if len(self.springArgs) == 0 and self.doParams.isChecked():
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'You must '\
                              'enter at least one spring stiffness.', parent=self)
            box.exec_()
            return
        elif abs(float(self.initPosEdit.text())) > 5 and self.doParams.isChecked():
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Initial position must '\
                              'be in the range of -5 to 5 meters.', parent=self)
            box.exec_()
            return
        elif float(self.speedPercentEdit.text()) <= 0 or float(self.speedPercentEdit.text()) > 150:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Speed percentage '\
                              'must be greater than 0% and less or equal to 150%', parent=self)
            box.exec_()
            return
        elif float(self.massEdit.text()) <= 0:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Mass must be '\
                              'greater than zero', parent=self)
            box.exec_()
            return
        elif int(self.lengthEdit.text()) <= 0 or int(self.lengthEdit.text()) > 20:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Length of  '\
                              'simulation must be greater than 0s but no more than 20s', parent=self)
            box.exec_()
            return
        directory = os.path.dirname(os.path.realpath(__file__))
        springArg = self.springArgs
        massArg = 'M'+self.massEdit.text()
        dampingArg = 'DAM'+self.dampingEdit.text()
        initPosArg = 'IP'+self.initPosEdit.text()
        speedArg = 'PS'+self.speedPercentEdit.text()
        funcNumArg = 'FN'+str(self.forcingDropDown.currentIndex()+1)
        directionArg = "DIR" + self.direction
        lengthArg = 'LEN' + self.lengthEdit.text()
        if self.resonanceCheck.isChecked() or self.antiResonanceCheck.isChecked():
            # Basically force predetermined values if a special case is selected
            massArg = 'M2'
            dampingArg = 'D0'
            springArg = ['SP8']
            funcNumArg = 'FN0'
            initPosArg = 'IP-3'
        if self.antiResonanceCheck.isChecked():
            initPosArg = 'IP3'
        args = [sys.executable, directory+'\\spring.py']+springArg+[massArg, \
                dampingArg, initPosArg, speedArg, funcNumArg, directionArg, lengthArg]
        Popen(args, cwd = directory)

    def getForcingVal(self, time, funcNum):
        """ Eventually, when we have a variety of forcing functions in the drop-down,
            we can just go by their index number and then return the appropriate
            function value here (fNum will indicate which function we need)."""
        if funcNum == 0:
            return math.sin(2*time)
        elif funcNum == 1:
            return 0
        elif funcNum == 2:
            return 10
        elif funcNum == 3:
            return time
        elif funcNum == 4:
            return time**2
        elif funcNum == 5:
            return math.sin(time)
        elif funcNum == 6:
            return math.exp(-1*time)



    def plotData(self):
        """Unfortunately, right now we need to calculate the approximation when
        plotting AND when simulating. This is because a good way of passing a
        huge array of position/time data to a pygame window has not been
        found (or from the pygame window to the GUI). This is fine for now
        since the math takes less than half a second to complete...but it's
        a little messy.
        Watch this to understand Euler's method: https://www.youtube.com/watch?v=k2V2UYr6lYw"""
        if float(self.massEdit.text()) <= 0:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Mass must be '\
                              'greater than zero', parent=self)
            box.exec_()
            return
        y_t = [] # temp y
        y_t.append(float(self.initPosEdit.text()))
        t_t = [] # temp t
        t_t.append(0)
        z = []
        z.append(0) # z = dy/dx for Euler method
        # gotta be floats for the math
        b = float(self.dampingEdit.text())
        m = float(self.massEdit.text())
        k = self.getStiffness()
        # + 1 here because fNum = 0 reserved for the resonance cases
        fNum = self.forcingDropDown.currentIndex() + 1
        if self.resonanceCheck.isChecked() or self.antiResonanceCheck.isChecked():
            # Force values if special case is selected
            b = 0.0
            m = 2.0
            k = 8.0
            y_t[0] = -3
            fNum = 0
        if self.antiResonanceCheck.isChecked():
            y_t[0] = 3
        inc = 0.0001
        iterations = int(int(self.lengthEdit.text())/inc)
        print iterations
        for i in range(1, iterations):
            forcingFunction = self.getForcingVal(t_t[i-1], fNum) if self.direction == 'X' else (self.getForcingVal(t_t[i-1], fNum) - 9.81*m)
            """
            Here's my attempt at Midpoint, didn't help much if at all
            k1y = z[i-1]
            k1z = (forcingFunction - b*z[i-1] - k*y_t[i-1])/m
            forcingFunctionInc = self.getForcingVal(t_t[i-1]+0.5*inc, fNum) if self.direction == 'X' else (self.getForcingVal(t_t[i-1]+0.5*inc, fNum) - 9.81*m)
            k2y = z[i-1]+0.5*k1y*inc
            k2z = (forcingFunctionInc - b*(z[i-1]+0.5*k1z*inc) - k*(y_t[i-1]+0.5*k1z*inc))/m
            y_t.append(y_t[i-1] + k2y*inc)
            z.append(z[i-1] + k2z*inc)
            t_t.append(t_t[i-1]+inc)
            """
            t_t.append(t_t[i-1]+inc)
            y_t.append(y_t[i-1] + z[i-1]*inc)
            z.append(z[i-1] + (forcingFunction/m - (b/m)*z[i-1] - (k/m)*y_t[i-1])*inc)

        ax = self.fig.add_subplot(111)
        ax.clear()
        ax.plot(t_t, y_t)
        ax.set_title("Position vs. Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(self.direction+" Position (m)")
        self.canvas.draw()

    def getStiffness(self):
        """Gets the stiffness of all the springs in springArgs to be used
        in the plot function."""
        stiffness = 0
        for i in range(len(self.springArgs)):
            if self.springArgs[i][0:2] == 'SP':
                stiffness += float(self.springArgs[i][2:])
            elif self.springArgs[i][0:2] == 'SS':
                num = int(self.springArgs[i][2:])
                seriesK = 0
                for j in range(num):
                    seriesK += 1.0/float(self.springArgs[i+1+j])
                stiffness += 1.0/seriesK
        return stiffness

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mw = MainGUI()
    app.exec_()
