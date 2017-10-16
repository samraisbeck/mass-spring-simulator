import math
import pygame
import sys, os
import numpy as np
import matplotlib.pyplot as plt
from random import randint
WIDTH = 1000
HEIGHT = 600
pygame.init()

"""
TODO:
- Is this the best way to go about this?
    - any other possible ways to go?
- Forcing function (probably drop-down choice)
    - this will be easy to implement
- Display useful data on screen
    - like relaxation time, # oscillations, input parameters, etc...
    - again, will be easy
- Make everything look more professional
    - more or less in the pygame window
- Test with hand calculations
    - Already did for one basic case but we need more
- Is there anything else to make this better?
"""

class MassSpring(object):
    def __init__(self, springs, damping, mass, initPos, speedPercent):
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        self.window.fill((255,255,255))
        self.clock = pygame.time.Clock()
        self.fps = 100*speedPercent
        self.springs = springs
        self.k = 0
        self.getStiffness()
        self.block = pygame.image.load('block.png').convert_alpha()
        self.blockW, self.blockH = 40, 80
        self.block = pygame.transform.scale(self.block, (self.blockW, self.blockH))
        self.blockEq = (WIDTH/2) - self.blockW/2
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

    def getStiffness(self):
        for spring in self.springs:
            if type(spring) == list:
                # This is the case of springs in series
                self.k += 1.0/sum([1.0/sSpring for sSpring in spring])
            else:
                # This is the case of a spring on its own (parallel)
                self.k += spring
        self.k = round(self.k, 3)


    def euler(self, iterations = 100000):
        """Unfortunately, right now we need to calculate the approximation when
        plotting AND when simulating. This is because a good way of passing a
        huge array of position/time data to a pygame window has not been
        found (or from the pygame window to the GUI). This is fine for now
        since the math takes less than half a second to complete...but it's
        a little messy. """
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
            z.append(z[i-1] + ((-self.b/self.m)*z[i-1] - (self.k/self.m)*y_t[i-1])*self.inc)
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
        self.clock.tick(self.fps)
        self.window.fill((255,255,255))
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
        if self.t[frame]//1 != self.printTime:
            self.printTime = self.t[frame]//1
            font = pygame.font.SysFont('arialblack', 40)
            self.text = font.render('Time: '+str(int(self.printTime)), 1, (255,0,0))
        self.window.blit(self.text, (100,100))
        pygame.draw.line(self.window, (255,0,0), (WIDTH/2, self.blockY-20), (WIDTH/2, self.blockY+self.blockH+20))
        for i in range(5):
            pygame.draw.line(self.window, (0,255,0), ((WIDTH/2)+(100*i), self.blockY-20), ((WIDTH/2)+(100*i), self.blockY+self.blockH+20))
            pygame.draw.line(self.window, (0,255,0), ((WIDTH/2)-(100*i), self.blockY-20), ((WIDTH/2)-(100*i), self.blockY+self.blockH+20))
        # print round(self.y[frame]*100)
        self.blockX = self.blockEq+round(self.y[frame]*100)
        for i in range(len(self.springs)):
            if type(self.springs[i]) == list:
                div = (self.blockX+self.blockW/2 - WIDTH/2)/len(self.springs[i])
                for j in range(len(self.springs[i])):
                    pygame.draw.line(self.window, (abs(math.cos(j*(math.pi/2)))*255,0,150), (WIDTH/2 + j*div, ((-1)**i*(i*10))+HEIGHT/2), (WIDTH/2 + (j+1)*div, ((-1)**i*(i*10))+HEIGHT/2), 5)

            else:
                pygame.draw.line(self.window, (255,0,150), (WIDTH/2, ((-1)**i*(i*10))+HEIGHT/2), (self.blockX+self.blockW/2, ((-1)**i*(i*10))+HEIGHT/2), 5)
        # self.block.x = self.blockEq + round(self.y[frame]*100)
        self.window.blit(self.block, (self.blockX, self.blockY))
        pygame.display.update()



if __name__ == '__main__':
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
            num = int(sys.argv[i][2])
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
    totalSprings = parallelSprings+seriesSprings
    MassSpringSim = MassSpring(totalSprings, damping, mass, pos0, percSpeed)
    MassSpringSim.euler()
    MassSpringSim.analytical()
    for i in range(len(MassSpringSim.t)):
        MassSpringSim.update(i)
    pygame.quit()
    sys.exit(0)
