
from PySide import QtGui, QtCore
import sys, os
from subprocess import Popen
import matplotlib
from pyparsing import Literal,CaselessLiteral,Word,Combine,Group,Optional,\
    ZeroOrMore,Forward,nums,alphas
import operator
import re
matplotlib.use('Qt4Agg')
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from math import cos, sin, tan, exp, pi, sqrt

class MainGUI(QtGui.QMainWindow):
    def __init__(self):
        super(MainGUI, self).__init__()
        self.setStyleSheet("background-color: lightblue")
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
        grid.addLayout(self._UIMassDamping(), 1, 0)
        grid.addLayout(self._UIForcingOptions(), 2, 0)
        grid.addLayout(self._UIInitPosAndSpeed(), 3, 0)
        # Plot section #
        self.canvas = self._UISetupPlot()
        grid.addWidget(self.canvas, 4, 0)
        # Main controls #
        grid.addLayout(self._UIMainControls(), 5, 0)
        Qw = QtGui.QWidget()
        Qw.setLayout(grid)
        self.setCentralWidget(Qw)
        self.setWindowTitle('Mass-Spring Simulator')
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
        self.springsEdit.setStyleSheet('background-color: white')
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

    def _UIMassDamping(self):
        """This initializes the Mass and Damping fields, but it also
        adds in the check boxes for a vertical or horizontal system."""
        groupbox = QtGui.QGroupBox()
        ultHBox = QtGui.QHBoxLayout()
        self.direction="X"
        self.horizontalDirection = QtGui.QRadioButton('Horizontal System', parent=self)
        self.horizontalDirection.setToolTip("Simulate a mass moving horizontally")
        self.horizontalDirection.setChecked(True)
        self.horizontalDirection.clicked.connect(self.setHorizontal)
        self.verticalDirection = QtGui.QRadioButton('Vertical System', parent=self)
        self.verticalDirection.setToolTip("Simulate a hanging mass")
        self.verticalDirection.clicked.connect(self.setVertical)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.horizontalDirection)
        vbox.addWidget(self.verticalDirection)
        groupbox.setLayout(vbox)
        groupbox.setContentsMargins(0,0,0,0)
        ultHBox.addWidget(groupbox)

        vbox = QtGui.QVBoxLayout()
        inHbox = QtGui.QHBoxLayout()
        labelMass = QtGui.QLabel('Mass: ', parent=self)
        self.massEdit = QtGui.QLineEdit()
        self.massEdit.setStyleSheet('background-color: white')
        self.massEdit.setText('1')
        inHbox.addWidget(labelMass)
        inHbox.addWidget(self.massEdit)
        vbox.addLayout(inHbox)
        inHbox = QtGui.QHBoxLayout()
        labelDamping = QtGui.QLabel('Damping: ', parent=self)
        self.dampingEdit = QtGui.QLineEdit()
        self.dampingEdit.setStyleSheet('background-color: white')
        self.dampingEdit.setText('0')
        inHbox.addWidget(labelDamping)
        inHbox.addWidget(self.dampingEdit)
        vbox.addLayout(inHbox)

        ultHBox.addLayout(vbox)

        return ultHBox

    def _UIForcingOptions(self):
        """
        Set up the forcing function parameters, as well as the resonance
        options.
        """
        ultHBox = QtGui.QHBoxLayout()
        hbox = QtGui.QHBoxLayout()
        vbox = QtGui.QVBoxLayout()
        leftInnerHBox = QtGui.QHBoxLayout()

        self.forcingFunctionText = "0"
        labelForcing = QtGui.QLabel('Forcing Function f(t): ', parent=self)
        self.forcingField = QtGui.QLineEdit()
        self.forcingField.setStyleSheet('background-color: white')
        self.forcingField.setPlaceholderText('Add forcing function in terms of t...')
        forcingSubmit = QtGui.QPushButton('Set Forcing Function', parent=self)
        forcingSubmit.clicked.connect(self.setForcingFunction)
        self.forcingFunctionLabel = QtGui.QLabel('f(t) = 0', parent=self)
        button = QtGui.QPushButton("Forcing Syntax", parent=self)
        button.clicked.connect(self.forcingHelp)
        leftInnerHBox.addWidget(labelForcing, 0, QtCore.Qt.AlignRight)
        leftInnerHBox.addWidget(self.forcingField)
        leftInnerHBox.addWidget(forcingSubmit)
        leftInnerHBox.addWidget(self.forcingFunctionLabel)
        leftInnerHBox.addWidget(button)
        ultHBox.addLayout(leftInnerHBox)

        groupbox = QtGui.QGroupBox()
        innerHBox = QtGui.QHBoxLayout()

        self.doParams = QtGui.QRadioButton('Use Current Parameters', parent=self)
        self.doParams.setChecked(True)
        self.doParams.clicked.connect(self.reEnableForcingMenu)
        self.resonanceCheck = QtGui.QRadioButton('Show Resonance', parent=self)
        self.resonanceCheck.setToolTip("Set up a system that demonstrates resonance")
        self.antiResonanceCheck = QtGui.QRadioButton('Show Anti-Resonance', parent=self)
        self.antiResonanceCheck.setToolTip("Set up a system that demonstrates the opposite of resonance")
        self.resonanceCheck.clicked.connect(self.resonanceForcing)
        self.antiResonanceCheck.clicked.connect(self.resonanceForcing)

        innerHBox.addWidget(self.doParams)
        innerHBox.addWidget(self.resonanceCheck)
        innerHBox.addWidget(self.antiResonanceCheck)
        groupbox.setLayout(innerHBox)
        groupbox.setContentsMargins(0,0,0,0)
        ultHBox.addWidget(groupbox)
        return ultHBox

    def _UIInitPosAndSpeed(self):
        """Initial position, speed of simulation, and length of simulation"""
        hbox = QtGui.QHBoxLayout()
        label = QtGui.QLabel('Initial Position (-5 to +5 meters): ', parent=self)
        self.initPosEdit = QtGui.QLineEdit()
        self.initPosEdit.setStyleSheet('background-color: white')
        self.initPosEdit.setText('2')
        hbox.addWidget(label)
        hbox.addWidget(self.initPosEdit)
        label = QtGui.QLabel('Speed of Simulation (1 to 150%): ', parent=self)
        self.speedPercentEdit = QtGui.QLineEdit()
        self.speedPercentEdit.setStyleSheet('background-color: white')
        self.speedPercentEdit.setText('100')
        self.speedPercentEdit.setToolTip('100 is full speed, 50 is half speed, etc...')
        hbox.addWidget(label)
        hbox.addWidget(self.speedPercentEdit)
        label = QtGui.QLabel('Length of Simulation (0 to 20s): ', parent=self)
        self.lengthEdit = QtGui.QLineEdit()
        self.lengthEdit.setStyleSheet('background-color: white')
        self.lengthEdit.setText('10')
        hbox.addWidget(label)
        hbox.addWidget(self.lengthEdit)
        return hbox

    def _UISetupPlot(self):
        """Setup the plot"""
        self.fig = Figure(figsize=(600,600), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
        ax = self.fig.add_subplot(111)
        ax.plot([0,0])
        ax.set_title("Position vs. Time (nothing entered)")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Position (m)")
        # the canvas is the actual thing you add to the GUI
        return FigureCanvas(self.fig)

    def _UIMainControls(self):
        """Main controls (plot, launch)"""
        hbox = QtGui.QHBoxLayout()
        button = QtGui.QPushButton('Plot', parent=self)
        button.clicked.connect(self.plotData)
        button.setStyleSheet("font: bold; background-color: steelblue")
        hbox.addWidget(button)
        button = QtGui.QPushButton('Launch Simulator', parent=self)
        button.clicked.connect(self.launchSimulator)
        button.setStyleSheet("font: bold; background-color: steelblue")
        hbox.addWidget(button)
        return hbox

### GUI SETUP ENDS HERE #############################


    def setForcingFunction(self):
        """Here is where we set the forcing function depending on what the
        user has typed in. It is pretty versatile but proper format as
        indicated in the User Manual document should be followed."""
        if self.forcingField.text() == '':
            self.forcingField.setText('0')
        self.setForcingFunctionText = "0"
        initialForcingFunction = self.forcingField.text().lower()
        #print initialForcingFunction
        initialForcingFunction.replace(" ", "") # Gets rid of spaces (makes checks easier)

        #convert to python syntax
        newForcingFunction = re.sub(r'(e\^)([t0-9]+\b)', r'exp(\2)', initialForcingFunction)
        newForcingFunction = re.sub(r'(e\^)(-)([t0-9]+\b)', r'exp(\2\3)', newForcingFunction)
        newForcingFunction = re.sub(r'\^', "**", newForcingFunction)
        newForcingFunction = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', newForcingFunction)
        newForcingFunction = re.sub(r'([a-zA-Z\)])(\d)', r'\1*\2', newForcingFunction)

        try:
            t = 0.01
            self.forcingFunctionText = newForcingFunction
            eval(newForcingFunction)
        except:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Invalid expression '\
                                  'was entered. Check to make sure there are no variables other than '\
                                  't, and that there are no mistakes in your expression ', parent=self)
            self.forcingFunctionText = "0"
            box.exec_()
        self.forcingFunctionLabel.setText('f(t) = ' + self.forcingFunctionText)

    def forcingHelp(self):
        """Nothing helpful right now"""
        box = QtGui.QMessageBox(parent=self)
        box.setText("You can add a variety of forcing functions. For best results, "+\
                     "it is recommended to use an asterix (*) for any multiplication, and to use "+\
                     "brackets to be safe. "+\
                     "An example of a function which will work is 3sin(3t), which is the "+\
                     "same as 3*sin(3*t). \n\nA function which will not work is tsin(2t), "+\
                     "as opposed to t*sin(2t), which will work.\n\nExponentials will work too (e"+\
                     "^t, e^(-t)), and exponents (t^2, t^(3*t). This should be fairly "+\
                     "easy to use, try and use proper syntax like * and () wherever possible, and "+\
                     "you should be fine. \n\nAlso, REMEMBER to click 'Set Forcing Function' when "+\
                     "you are done entering one in, or the solver will not consider it.")

        box.setWindowTitle('Forcing Help')

        box.exec_()


    def addSprings(self):
        """Based on text in the spring stiffness box, and also whether the
        parallel/series dot is filled, adds the spring stiffness(es) to the
        list (SP means spring parallel, SS means spring series. SS is always
        followed by the number of springs on that series, then the values of
        the stiffnesses themselves)"""

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

    def setHorizontal(self):
        self.direction = "X"

    def setVertical(self):
        self.direction = "Y"

    def resonanceForcing(self):
        """Set the correct forcing function for resonance or anti-resonance"""
        self.forcingFunctionText = "sin(2*t)"
        self.forcingFunctionLabel.setText('Forcing Function: '+self.forcingFunctionText)
        self.forcingField.setEnabled(False)

    def reEnableForcingMenu(self):
        """Reset forcing function to what it was before resonance was checked"""
        self.forcingField.setEnabled(True)
        self.setForcingFunction()

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

        # BEGIN ERROR CHECKING ############
        try:

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
            elif float(self.dampingEdit.text()) < 0:
                box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Damping must be '\
                                  'greater than or equal to zero', parent=self)
                box.exec_()
                return
            elif int(self.lengthEdit.text()) <= 0 or int(self.lengthEdit.text()) > 20:
                box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Length of  '\
                                  'simulation must be greater than 0s but no more than 20s', parent=self)
                box.exec_()
                return
        except:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Your parameters '\
                              'are incorrect, check them. Most likely you entered something '\
                              'other than a number. Also, length of simulation has to be a whole number.', parent=self)
            box.exec_()
            return
        # END ERROR CHECKING ############

        # Here, we set up the parameters so that they can be identified properly
        # in spring.py (the simulation file)
        directory = os.path.dirname(os.path.realpath(__file__))
        springArg = self.springArgs
        massArg = 'M'+self.massEdit.text()
        dampingArg = 'DAM'+self.dampingEdit.text()
        initPosArg = 'IP'+self.initPosEdit.text()
        speedArg = 'PS'+self.speedPercentEdit.text()
        funcNumArg = 'FN'+str(self.forcingFunctionText)
        directionArg = "DIR" + self.direction
        lengthArg = 'LEN' + self.lengthEdit.text()
        if self.resonanceCheck.isChecked() or self.antiResonanceCheck.isChecked():
            # Force predetermined values if a special case is selected
            massArg = 'M2'
            dampingArg = 'D0'
            springArg = ['SP8']
            initPosArg = 'IP-3' # For resonance, init position is -3
        if self.antiResonanceCheck.isChecked():
            initPosArg = 'IP3' # for anti-resonance, init position is 3
        args = [sys.executable, directory+os.sep+'spring.py']+springArg+[massArg, \
                dampingArg, initPosArg, speedArg, funcNumArg, directionArg, lengthArg]
        Popen(args, cwd = directory) # Open the simulation window

    def getForcingVal(self, time):
        """ Gets the value of the forcing function at the given time"""

        function = self.forcingFunctionText.replace("t", str(time))
        return eval (function);

    def plotData(self):
        """Unfortunately, right now we need to calculate the approximation when
        plotting AND when simulating. This is because a good way of passing a
        huge array of position/time data to a pygame window has not been
        found (or from the pygame window to the GUI). This is fine for now
        since the math takes less than half a second to complete...but it's
        a little messy."""
        try:
            if float(self.massEdit.text()) <= 0:
                box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Mass must be '\
                                  'greater than zero', parent=self)
                box.exec_()
                return
            elif float(self.dampingEdit.text()) < 0:
                box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Damping must be '\
                                  'greater than or equal to zero', parent=self)
                box.exec_()
                return
            elif len(self.springArgs) == 0 and self.doParams.isChecked():
                box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'You must '\
                                  'enter at least one spring stiffness.', parent=self)
                box.exec_()
                return
            elif float(self.initPosEdit.text()) < -5 or float(self.initPosEdit.text()) > 5:
                box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Initial position '\
                                  'must be between -5 and 5 meters', parent=self)
                box.exec_()
                return
            elif int(self.lengthEdit.text()) <= 0 or int(self.lengthEdit.text()) > 20:
                box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Length of  '\
                                  'simulation must be greater than 0s but no more than 20s', parent=self)
                box.exec_()
                return
        except:
            box = QtGui.QMessageBox(QtGui.QMessageBox.Critical, 'Error', 'Your parameters '\
                              'are incorrect, check them. Most likely you entered something '\
                              'other than a number. Also, length of simulation has to be a whole number.', parent=self)
            box.exec_()
            return
        y_t = [] # position values
        y_t.append(float(self.initPosEdit.text()))
        t_t = [] # time values
        t_t.append(0)
        v = [] # velocity values
        v.append(0) # v = dy/dx
        # gotta be floats for the math
        b = float(self.dampingEdit.text())
        m = float(self.massEdit.text())
        k = self.getStiffness()
        if self.resonanceCheck.isChecked() or self.antiResonanceCheck.isChecked():
            # Force values if special case is selected
            b = 0.0
            m = 2.0
            k = 8.0
            y_t[0] = -3
        if self.antiResonanceCheck.isChecked():
            y_t[0] = 3
        inc = 0.0005
        iterations = int(int(self.lengthEdit.text())/inc)
        #print iterations
        for i in range(1, iterations):
            forcingFunction = self.getForcingVal(t_t[i-1]) if self.direction == 'X' else (self.getForcingVal(t_t[i-1]) - 9.81*m)

            # Midpoint Method
            # More comments for this method are in spring.py as it is used
            # there too.
            k1y = v[i-1]
            k1v = (forcingFunction - b*v[i-1] - k*y_t[i-1])/m
            forcingFunctionInc = self.getForcingVal(t_t[i-1]+0.5*inc) if self.direction == 'X' else (self.getForcingVal(t_t[i-1]+0.5*inc) - 9.81*m)
            k2y = v[i-1]+0.5*k1v*inc
            k2v = (forcingFunctionInc - b*(v[i-1]+0.5*k1v*inc) - k*(y_t[i-1]+0.5*k1y*inc))/m
            y_t.append(y_t[i-1] + k2y*inc)
            v.append(v[i-1] + k2v*inc)
            t_t.append(t_t[i-1]+inc)
            """
            # Euler method
            t_t.append(t_t[i-1]+inc)
            y_t.append(y_t[i-1] + v[i-1]*inc)
            v.append(v[i-1] + (forcingFunction/m - (b/m)*v[i-1] - (k/m)*y_t[i-1])*inc)
            """
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
    """Launch the GUI"""
    app = QtGui.QApplication(sys.argv)
    mw = MainGUI()
    app.exec_()
