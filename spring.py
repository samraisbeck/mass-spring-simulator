from math import cos, sin, tan, exp, sqrt, pi
import pygame
import sys, os
import numpy as np
import fourFn
import matplotlib.pyplot as plt
WIDTH = 1300
HEIGHT = 1000
pygame.init()



class MassSpring(object):
    def __init__(self, springs, damping, mass, initPos, speedPercent, forcingFunction, direction, lengthOfSim):
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        self.window.fill((255,255,255))
        self.clock = pygame.time.Clock()
        self.fps = 100*speedPercent
        self.springs = springs
        self.k = 0
        self.getStiffness()
        self.block = pygame.image.load('block.png').convert_alpha()
        self.blockW, self.blockH = (40, 80) if direction == 'X' else (80,40)
        self.block = pygame.transform.scale(self.block, (self.blockW, self.blockH))
        self.blockEq = (WIDTH/2) - self.blockW/2 # Block's resting point (middle)
        # Note that in pygame, (0,0) for an item is top left corner
        self.blockX = self.blockEq
        self.blockYEq = (HEIGHT/2) - self.blockH/2
        self.blockY = self.blockYEq
        self.m = mass
        self.b = damping
        self.y = None # List of points after a calculation
        self.t = None # List of time values
        self.printTime = -2 # arbitrary value
        self.text = ''
        self.y0 = initPos
        self.dy0 = 0 # Initial velocity will always be 0
        self.t0 = 0
        self.inc = 0.001
        self.maxInitPos = 5
        self.distanceTexts = []
        self.ODEstring = ''
        self.forcingStrings = ['sin(2t)', '0', '10', 't', 't^2', 'sin(t)', 'exp(t)']
        self.forcingFunction = forcingFunction
        self.direction = direction
        self.checkTimes = [0, 0, 0]
        self.length = lengthOfSim

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

    def getForcingVal(self, time):
        """ Eventually, when we have a variety of forcing functions in the drop-down,
            we can just go by their index number and then return the appropriate
            function value here (fNum will indicate which function we need)."""

        # Using external code to evaluate the forcing function at each time interval
        
        return eval(self.forcingFunction);

    def euler(self, iterations = 100000):
        """Unfortunately, right now we need to calculate the approximation when
        plotting AND when simulating. This is because a good way of passing a
        huge array of position/time data to a pygame window has not been
        found (or from the pygame window to the GUI). This is fine for now
        since the math takes less than half a second to complete...but it's
        a little messy.
        Watch this to understand Euler's method: https://www.youtube.com/watch?v=k2V2UYr6lYw"""
        sampleRate = 10 # only sample 100 points.
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
        self.forcingFunction = self.forcingFunction.replace("t", "time")
        for i in range(1, iterations+1): # iterations + 1 allows simmulaiton to update displayed time to the proper final value
            # If spring is oscillating in the y direction, subtract gravity as a forcing function
            forcingFunction = self.getForcingVal(t_t[i-1]) if self.direction == 'X' else (self.getForcingVal(t_t[i-1]) - 9.81*self.m)

            # Midpoint Method
            k1y = z[i-1]
            k1z = (forcingFunction - self.b*z[i-1] - self.k*y_t[i-1])/self.m
            forcingFunctionInc = self.getForcingVal(t_t[i-1]+0.5*self.inc) if self.direction == 'X' else (self.getForcingVal(t_t[i-1]+0.5*self.inc) - 9.81*self.m)
            k2y = z[i-1]+0.5*k1z*self.inc
            k2z = (forcingFunctionInc - self.b*(z[i-1]+0.5*k1z*self.inc) - self.k*(y_t[i-1]+0.5*k1y*self.inc))/self.m
            y_t.append(y_t[i-1] + k2y*self.inc)
            z.append(z[i-1] + k2z*self.inc)
            t_t.append(t_t[i-1]+self.inc)
            """
            # Euler method
            t_t.append(t_t[i-1]+self.inc)
            y_t.append(y_t[i-1] + z[i-1]*self.inc)
            z.append(z[i-1] + (forcingFunction/self.m - (self.b/self.m)*z[i-1] - (self.k/self.m)*y_t[i-1])*self.inc)
            """
            if i%sampleRate == 0:
                # sample every 100th point
                self.t = np.append(self.t, t_t[i])
                self.y = np.append(self.y, y_t[i])

    def analytical(self, iterations=100000):
        data = open('errorData.txt', 'w')
        yAct = np.zeros(iterations)
        tAct = np.zeros(iterations)
        tAct[0] = 0
        yAct[0] = self.y0
        sampleRate = 10

        for i in range(1, iterations):
            tAct[i] = tAct[i-1]+self.inc
            #yAct[i] = np.exp(-(1/3.0)*tAct[i])*(2*np.cos((math.sqrt(29)/3)*tAct[i]) + (2/math.sqrt(29))*np.sin((math.sqrt(29)/3)*tAct[i])) # test1
            yAct[i] = 2*np.cos((sqrt(1300)/sqrt(3))*tAct[i]) # test2
            if i%sampleRate==0:
                data.write(str(round(100*abs(yAct[i]-self.y[i/sampleRate])/abs(yAct[i]), 6))+'\n')
        data.close()

        plt.plot(self.t, self.y, tAct, yAct) # show the plots
        plt.show()

    def renderText(self, text, size, color = (0,0,0), fontStr = 'arialblack'):
        """Takes in text, font size, color (RGB tuple), font name (string) and
           returns a font object which can be blit onto a window."""
        font = pygame.font.SysFont(fontStr, size)
        return font.render(text, 1, color)

    def renderStaticTexts(self):
        for i in range(1,self.maxInitPos+1):
            self.distanceTexts.append(self.renderText(str(i), 15))
            self.distanceTexts.append(self.renderText(str(-i), 15))
        self.distanceTexts.append(self.renderText('0', 15))
        if self.direction == 'X':
            depVar = 'x'
        else:
            depVar = 'y'

        self.ODEstring += str(self.m)+depVar+"'' + "
        if self.b != 0:
            self.ODEstring += str(self.b)+depVar+"' + "
        self.ODEstring += str(self.k)+depVar+" = "
        self.ODEstring += self.forcingFunction
        self.ODEstring = self.renderText(self.ODEstring, 30)


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
            self.checkTimes[0] = self.checkTimes[1]
            self.checkTimes[1] = (self.checkTimes[1]+frame)/2
            self.checkTimes[2] = frame
            self.timeText = self.renderText('Time: '+str(int(self.printTime)), 40, (255,0,0))
        self.window.blit(self.timeText, (100,100))
        self.window.blit(self.ODEstring, (100, 50))

        if (self.direction == "X"):
            for i in range(1, self.maxInitPos+1):
                # Draw the measurement lines (lines are spaced out 1 meter)
                pygame.draw.line(self.window, (0,255,0), ((WIDTH/2)+(100*i), self.blockY-20), ((WIDTH/2)+(100*i), self.blockY+self.blockH+20))
                self.window.blit(self.distanceTexts[2*(i-1)], ((WIDTH/2)+(100*i), self.blockY+self.blockH+20))
                pygame.draw.line(self.window, (0,255,0), ((WIDTH/2)-(100*i), self.blockY-20), ((WIDTH/2)-(100*i), self.blockY+self.blockH+20))
                self.window.blit(self.distanceTexts[2*i-1], ((WIDTH/2)-(100*i), self.blockY+self.blockH+20))
            # print round(self.y[frame]*100)
            pygame.draw.line(self.window, (255,0,0), (WIDTH/2, self.blockY-20), (WIDTH/2, self.blockY+self.blockH+20)) # Equilibrium line
            self.window.blit(self.distanceTexts[-1], (WIDTH/2, self.blockY+self.blockH+20))

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
                        pygame.draw.line(self.window, (abs(cos(j*(pi/2)))*255,0,150), (startPos, ((-1)**i*(i*10))+HEIGHT/2), (startPos + perc*dist, ((-1)**i*(i*10))+HEIGHT/2), 5)
                        startPos += perc*dist
                else:
                    pygame.draw.line(self.window, (255,0,150), (WIDTH/2, ((-1)**i*(i*10))+HEIGHT/2), (self.blockX+self.blockW/2, ((-1)**i*(i*10))+HEIGHT/2), 5)
            # self.block.x = self.blockEq + round(self.y[frame]*100)
            self.window.blit(self.block, (self.blockX, self.blockY))

        # There were a few weird changes that needed to be made to the X direction case (such as swapping x and y expressions, and changing the order of statements) that I just
        # copied it and made the changes in the second function. Feel free to make any modifications to improve this.
        else:
            for i in range(1, self.maxInitPos+1):
                # Draw the measurement lines (lines are spaced out 1 meter)
                pygame.draw.line(self.window, (0,255,0), (self.blockX-20, HEIGHT/2 + 100*i), (self.blockX+self.blockW+20, HEIGHT/2 + 100*i))
                self.window.blit(self.distanceTexts[2*(i-1)], (self.blockX-20, HEIGHT/2 + 100*i))
                pygame.draw.line(self.window, (0,255,0), (self.blockX-20, HEIGHT/2 - 100*i), (self.blockX+self.blockW+20, HEIGHT/2 - 100*i))
                self.window.blit(self.distanceTexts[2*(i-1)], (self.blockX-20, HEIGHT/2 - 100*i))

            # print round(self.y[frame]*100)
            pygame.draw.line(self.window, (255,0,0), (self.blockX-20, HEIGHT/2), (self.blockX+self.blockW+20, HEIGHT/2)) # Equilibrium line
            self.window.blit(self.distanceTexts[-1], (self.blockX-20, HEIGHT/2))

            # Since positive is usually considered as going up, negate the values returned from the solver to make the orientation consistent
            self.blockY = self.blockYEq+round(-self.y[frame]*100)
            for i in range(len(self.springs)):
                # Draw the springs. If it's a series spring, divide the distance
                # by the number of springs and change the color every division
                # so you can see there are multiple springs.
                if type(self.springs[i]) == list:
                    Sum = sum([1/k for k in self.springs[i]])
                    dist = (self.blockY+self.blockH/2 - HEIGHT/2)
                    startPos = HEIGHT/2
                    for j in range(len(self.springs[i])):
                        perc = (1/self.springs[i][j])/Sum
                        pygame.draw.line(self.window, (abs(math.cos(j*(math.pi/2)))*255,0,150), (((-1)**i*(i*10))+WIDTH/2, startPos), (((-1)**i*(i*10))+WIDTH/2, startPos + perc*dist), 5)
                        startPos += perc*dist
                else:
                    pygame.draw.line(self.window, (255,0,150), ((-1)**i*(i*10)+WIDTH/2, HEIGHT/2), (((-1)**i*(i*10))+WIDTH/2, self.blockY+self.blockH/2), 5)
            # self.block.x = self.blockEq + round(self.y[frame]*100)
            self.window.blit(self.block, (self.blockX, self.blockY))

        pygame.display.update()
        # Check to see if the mass is still moving

        if abs((self.y[self.checkTimes[0]]-self.y[self.checkTimes[1]])*100) < 0.5 and\
           abs((self.y[self.checkTimes[1]]-self.y[self.checkTimes[2]])*100) < 0.5 and\
           abs((self.y[self.checkTimes[0]]-self.y[self.checkTimes[2]])*100) < 0.5 and\
           self.printTime != 0:
           return False

        return True



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
    direction = ""

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
        elif sys.argv[i][0:3] == 'DAM':
            damping = float(sys.argv[i][3:])
        elif sys.argv[i][0:2] == 'IP':
            pos0 = float(sys.argv[i][2:])
        elif sys.argv[i][0:2] == 'PS':
            percSpeed = float(sys.argv[i][2:])/100
        elif sys.argv[i][0:2] == 'FN':
            fNum = (sys.argv[i][2:])
        elif sys.argv[i][0:3] == 'DIR':
            direction = sys.argv[i][3:]
        elif sys.argv[i][0:3] == 'LEN':
            lengthOfSim = int(sys.argv[i][3:])
    totalSprings = parallelSprings+seriesSprings
    MassSpringSim = MassSpring(totalSprings, damping, mass, pos0, percSpeed, fNum, direction,\
                               lengthOfSim)
    MassSpringSim.euler(int(MassSpringSim.length/MassSpringSim.inc))
    MassSpringSim.renderStaticTexts()
    MassSpringSim.analytical(int(MassSpringSim.length/MassSpringSim.inc))
    run = True
    while True:
        if run == False:
            break
        else:
            #runs the simulation
            for i in range(len(MassSpringSim.t)):
                if not MassSpringSim.update(i):
                    break

            font = pygame.font.SysFont('arialblack', 40)
            replayText = font.render('Click Space to Replay or esc to Exit', 1, (0,0,125))
            MassSpringSim.window.blit(replayText, (260,HEIGHT/4))
            pygame.display.update()

            while True:
                pressed = 0
                run = False
                for key in pygame.event.get():
                    if key.type == pygame.QUIT:
                        pygame.quit()
                    if key.type == pygame.KEYDOWN:
                        if key.key == pygame.K_ESCAPE:
                            pressed = 1
                        elif key.key == pygame.K_SPACE:
                                run = True
                                pressed = 1
                if pressed == 1:
                    break
    pygame.quit()
    sys.exit(0)
