import pygame
from dataclasses import dataclass
from typing import Callable
import postfix
import time
import math


class linetype:
    solid = 0
    dotted = 1
    squiggly = 2

@dataclass
class gridSettings:
    labelXInterval: int = 128 # negative for no label
    labelYInterval: int = 128
    gridDivision: tuple = (128, 2) # (Main frequency, subdivision)
    gridColor: tuple = (255, 255, 255)
    lineColor: tuple = (0, 0, 0)
    lineWeightAxis: int = 4 # line weight for x/y axes
    lineWeightMajor: int = 3 # line weight for major gridlines
    lineWeightMinor: int = 2 # line weight for subdividing gridlines
    labelScale: int = 15
    maxFunctionSegments: int = 1000

@dataclass
class funcSettings:
    lineType: int = linetype.solid
    lineColor: tuple = (0, 0, 0)
    lineWidth: int = 2
    visible: bool = True

NINETYDEG = math.pi/2

@dataclass
class function:
    def __init__(self, string, settings=None):
        self.name = string
        infixExpression = postfix.strToInfix(string)
        postfixExpression = postfix.infixToPostfix(infixExpression)
        self.expression = postfixExpression
        self.call = postfix.getFunctionFromPostfix(self.expression)
        self.settings = settings or funcSettings()
    def drawCurve(self, region):
        raise NotImplementedError()


def drawSolid(surface, position, lineWidth, lineColor, progress, normal):
    pygame.draw.circle(surface, lineColor, position, lineWidth/2)

def drawDotted(surface, position, lineWidth, lineColor, progress, normal):
    if math.sin(progress / 50) > 0:
        pygame.draw.circle(surface, lineColor, position, lineWidth/2)

def drawSquiggly(surface, position, lineWidth, lineColor, progress, normal):
    offset = (math.sin(progress / 80) * 1.5) + (math.sin((progress / 100) + 2) * 2) + (math.sin(progress / 200) * 3)
    normal += NINETYDEG
    dx = math.cos(normal) * offset
    dy = math.sin(normal) * offset
    position = position[0] + dx, position[1] + dy
    pygame.draw.circle(surface, lineColor, position, lineWidth/2)

class grid:
    plotMethods = [drawSolid, drawDotted, drawSquiggly]
    def __init__(self, settings=None):
        self.settings = settings or gridSettings
        self.functions = []
    @staticmethod
    def translateToRegion(point, region):
        point = point[0] - region.left, point[1] - region.top
        return point

    def drawGridlines(self, surface, initial, frequencyMap, viewportSize):
        pass

    def drawAllGridlines(self, surface, position, viewportSize, zoom):
        pass
    
    def drawLabels(self, surface, position, viewportSize, zoom):
        pass

    def plotPathMachine(self, surface, lineWidth, lineColor, lineType, step):
        progress = 0
        lastPoint = yield
        plotMethod = self.plotMethods[lineType]
        while (nextPoint := (yield)) is not None:
            dx, dy = nextPoint[0] - lastPoint[0], nextPoint[1] - lastPoint[1]
            normal = math.atan2(dy, dx)
            magnitude = math.sqrt((dx ** 2) + (dy ** 2))
            increment = 0
            if lastPoint != nextPoint:
                increment = (dx/magnitude) * step, (dy/magnitude) * step
            while lastPoint != nextPoint:
                dxCurrent = nextPoint[0] - lastPoint[0]
                dyCurrent = nextPoint[1] - lastPoint[1]
                if abs(dxCurrent) < abs(increment[0]) or abs(dyCurrent) < abs(increment[1]):
                    progress += math.sqrt((dxCurrent ** 2) + (dyCurrent ** 2)) * step
                    lastPoint = nextPoint
                else:
                    progress += 1 * step
                    lastPoint = lastPoint[0] + increment[0], lastPoint[1] + increment[1]
                plotMethod(surface, lastPoint, lineWidth, lineColor, progress, normal)

    def drawFunctions(self, surface, position, viewportSize, zoom):
        start = next
        for func in self.functions:
            plotter = self.plotPathMachine(surface, func.settings.lineWidth * (1/zoom[0]), func.settings.lineColor, func.settings.lineType, 10)
            start(plotter)
            rng = range(round(position[0] - viewportSize[0]/2), round(position[0] + viewportSize[0]/2))
            for index, x in enumerate(rng):
                y = -func.call(x * zoom[0]) # negate to translate to graphics coordinate system
                y /= zoom[1]
                y -= position[1]

                if all((
                    not (0 < (func.call(x-1) / zoom[1]) - position[1] < viewportSize[1]), 
                    not (0 < (y < viewportSize[1])), 
                    not (0 < (func.call(x+1) / zoom[1]) - position[1] < viewportSize[1])
                    )):
                    continue

                plotter.send([index, y])
            plotter.close()

    def render(self, position, viewportSize, zoom):
        surface = pygame.Surface(viewportSize)
        surface.fill(self.settings.gridColor)

        self.drawAllGridlines(surface, position, viewportSize, zoom)
        self.drawLabels(surface, position, viewportSize, zoom)
        self.drawFunctions(surface, position, viewportSize, zoom)
        return surface

    def addFunc(self, func):
        self.functions.append(func)
    
    def addFuncFromString(self, string, lineColor = None, lineType = None, lineWidth = None):
        f = function(string)
        f.settings.lineType = lineType or f.settings.lineType
        f.settings.lineColor = lineColor or f.settings.lineColor
        f.settings.lineWidth = lineWidth or f.settings.lineWidth
        self.addFunc(f)

if __name__ == '__main__':
    g = grid()
    g.addFuncFromString("-x")
    g.addFuncFromString("(1/100)x ^ 2")
    g.addFuncFromString("2x")
    g.addFuncFromString("-18")
    g.functions[0].settings.lineType = linetype.solid
    g.functions[0].settings.lineColor = (0, 0, 255)
    g.functions[0].settings.lineWidth = 2
    g.functions[1].settings.lineType = linetype.squiggly
    g.functions[1].settings.lineColor = (255, 0, 0)
    g.functions[1].settings.lineWidth = 4
    g.functions[2].settings.lineType = linetype.dotted
    g.functions[2].settings.lineColor = (255, 0, 255)
    g.functions[2].settings.lineWidth = 6
    g.functions[3].settings.lineType = linetype.squiggly
    g.functions[3].settings.lineColor = (0, 255, 0)
    g.functions[3].settings.lineWidth = 8
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((800, 800))
    running = True
    while running:
        screen.blit(g.render((-400 + math.sin(time.time()) * 30, -400 + math.cos(time.time()) * 30, 800, 800)), (0, 0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()
