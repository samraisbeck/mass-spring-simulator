import math
import pygame
import sys, os
import numpy as np
WIDTH = 1300
HEIGHT = 600
pygame.init()



class MassSpring(object):
    def __init__(self, springs, damping, mass, initPos, speedPercent, fNum):
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        self.window.fill((255,255,255))
        self.clock = pygame.time.Clock()
        self.fps = 100*speedPercent
        self.springs = springs
        self.k = 0
        self.getStiffness()
        print self.k
        self.block = pygame.image.load('block.png').convert_alpha()
        self.blockW, self.blockH = 40, 80
        self.block = pygame.transform.scale(self.block, (self.blockW, self.blockH))
        self.blockEq = (WIDTH/2) - self.blockW/2 # Block's resting point (middle)
        # Note that in pygame, (0,0) for an item is top left corner
        self.blockX = self.blockEq
        self.blockY = (HEIGHT/2) - self.blockH/2
        self.m = mass
        self.b = damping
        self.y = None # List of points after a calculation
        self.t = None # List of time values
        self.printTime = -2 # arbitrary value
        self.text = ''
        self.y0 = initPos
        self.dy0 = 0 # Initial velocity will always be 0
        self.t0 = 0
        self.inc = 0.0001
        self.funcNum = fNum

    def getStiffness(self):
        """Self explanatory. Series springs are stored in lists, hence the
        type-check."""
        for spring in self.springs:
            if type(spring) == list:
                # This is the case of springs in series
                self.k += 1.0/sum([1.0/sSpring for sSpring in spring])
            else:
                # This is the case of a spring on its own (parallel)
                self.k += spring
        self.k = round(self.k, 3)

    def getForcingVal(self, time, fNum):
        """ Eventually, when we have a variety of forcing functions in the drop-down,
            we can just go by their index number and then return the appropriate
            function value here (fNum will indicate which function we need)."""
        if fNum == 0:
            return math.sin(2*time)
        elif fNum == 1:
            return 0
        elif fNum == 2:
            return 10
        elif fNum == 3:
            return time
        elif fNum == 4:
            return time**2
        elif fNum == 5:
            return math.sin(time)
        elif fNum == 6:
            return math.exp(-1*time)

    def euler(self, iterations = 100000):
        """Unfortunately, right now we need to calculate the approximation when
        plotting AND when simulating. This is because a good way of passing a
        huge array of position/time data to a pygame window has not been
        found (or from the pygame window to the GUI). This is fine for now
        since the math takes less than half a second to complete...but it's
        a little messy.
        Watch this to understand Euler's method: https://www.youtube.com/watch?v=k2V2UYr6lYw"""
        sampleRate = iterations/1000 # only sample 1000 points.
        self.y = np.array([0])
        y_t = [] # temp y
        self.y[0] = self.y0
        y_t.append(self.y0)
        self.t = np.array([0])
        t_t = [] # temp t
        self.t[0] = self.t0
        t_t.append(self.t0)
        z = []
        z.append(self.dy0) # z = dy/dx for Euler method
        for i in range(1, iterations):
            t_t.append(t_t[i-1]+self.inc)
            y_t.append(y_t[i-1] + z[i-1]*self.inc)
            z.append(z[i-1] + (self.getForcingVal(t_t[i-1], self.funcNum)-(self.b/self.m)*z[i-1] - (self.k/self.m)*y_t[i-1])*self.inc)
            if i%sampleRate == 0:
                # sample every 100th point
                self.t = np.append(self.t, t_t[i])
                self.y = np.append(self.y, y_t[i])
    def analytical(self, iterations=100000):
        yAct = np.zeros(iterations)
        tAct = np.zeros(iterations)
        tAct[0] = 0
        yAct[0] = self.y0
        for i in range(1, iterations):
            tAct[i] = tAct[i-1]+self.inc
            yAct[i] = np.exp(-2.5*tAct[i])*(2*np.cos(9.682*tAct[i]) + 0.5164*np.sin(9.682*tAct[i]))
        # plt.plot(self.t, self.y) show the plots
        # plt.show()

    def update(self, frame):
        """Here's what draws everything"""
        self.clock.tick(self.fps) # Set FPS
        self.window.fill((255,255,255))
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                # this is hitting the exit button
                pygame.quit()
                sys.exit(0)
        if self.t[frame]//1 != self.printTime:
            # We floor the time at this frame to just get the integer part.
            # Then, we check to see if that equals the one on the screen. If it
            # does not, we render a new one (one second has elapsed). We don't use
            # system time to make sure computer lag does not cause the mass
            # simulation to be off sync with the time.
            self.printTime = self.t[frame]//1
            font = pygame.font.SysFont('arialblack', 40)
            self.timeText = font.render('Time: '+str(int(self.printTime)), 1, (255,0,0))
        self.window.blit(self.timeText, (100,100))
        for i in range(5):
            # Draw the measurement lines (lines are spaced out 1 meter)
            pygame.draw.line(self.window, (0,255,0), ((WIDTH/2)+(100*i), self.blockY-20), ((WIDTH/2)+(100*i), self.blockY+self.blockH+20))
            pygame.draw.line(self.window, (0,255,0), ((WIDTH/2)-(100*i), self.blockY-20), ((WIDTH/2)-(100*i), self.blockY+self.blockH+20))
        # print round(self.y[frame]*100)
        pygame.draw.line(self.window, (255,0,0), (WIDTH/2, self.blockY-20), (WIDTH/2, self.blockY+self.blockH+20)) # Equilibrium line
        # Multiply blockX by 100 so that an easy map to pixels can be made
        # i.e 1 meter = 100 pixels, 2.13 meters is 213 pixels, etc
        self.blockX = self.blockEq+round(self.y[frame]*100)
        for i in range(len(self.springs)):
            # Draw the springs. If it's a series spring, divide the distance
            # by the number of springs and change the color every division
            # so you can see there are multiple springs.
            if type(self.springs[i]) == list:
                Sum = sum([1/k for k in self.springs[i]])
                dist = (self.blockX+self.blockW/2 - WIDTH/2)
                startPos = WIDTH/2
                for j in range(len(self.springs[i])):
                    perc = (1/self.springs[i][j])/Sum
                    pygame.draw.line(self.window, (abs(math.cos(j*(math.pi/2)))*255,0,150), (startPos, ((-1)**i*(i*10))+HEIGHT/2), (startPos + perc*dist, ((-1)**i*(i*10))+HEIGHT/2), 5)
                    startPos += perc*dist
            else:
                pygame.draw.line(self.window, (255,0,150), (WIDTH/2, ((-1)**i*(i*10))+HEIGHT/2), (self.blockX+self.blockW/2, ((-1)**i*(i*10))+HEIGHT/2), 5)
        # self.block.x = self.blockEq + round(self.y[frame]*100)
        self.window.blit(self.block, (self.blockX, self.blockY))
        pygame.display.update()



if __name__ == '__main__':
    """
    Here, we are initializing the simulator. Remember, this file is called from
    the GUI with the proper parameters as the arguments in the command line.
    So here, we are reading in the arguments and adding them to the proper
    variables so we can pass them onto the simulator object.
    totalSprings is just the addition of seriesSprings and parallelSprings.
    It is a list of stiffnesses for each spring, and if the spring is a series
    spring, it shows up in totalSprings as a list of stiffnesses.
    """
    seriesSprings = []
    parallelSprings = []
    totalSprings = []
    damping = 0
    mass = 0

    for i in range(len(sys.argv)):
        if i == 0:
            pass
        elif sys.argv[i][0:2] == 'SS':
            springs = []
            num = int(sys.argv[i][2:])
            for j in range(num):
                springs.append(float(sys.argv[i+1+j]))
            seriesSprings.append(springs)
        elif sys.argv[i][0:2] == 'SP':
            parallelSprings.append(float(sys.argv[i][2:]))
        elif sys.argv[i][0] == 'M':
            mass = float(sys.argv[i][1:])
            print "Mass is "+str(mass)+" kg"
        elif sys.argv[i][0] == 'D':
            damping = float(sys.argv[i][1:])
            print "Damping is "+str(damping)
        elif sys.argv[i][0:2] == 'IP':
            pos0 = float(sys.argv[i][2:])
        elif sys.argv[i][0:2] == 'PS':
            percSpeed = float(sys.argv[i][2:])/100
        elif sys.argv[i][0:2] == 'FN':
            fNum = int(sys.argv[i][2:])
    totalSprings = parallelSprings+seriesSprings
    MassSpringSim = MassSpring(totalSprings, damping, mass, pos0, percSpeed, fNum)
    MassSpringSim.euler()
    #MassSpringSim.analytical()
    for i in range(len(MassSpringSim.t)):
        MassSpringSim.update(i)
    pygame.quit()
    sys.exit(0)
