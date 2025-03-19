import pygame
from dataclasses import dataclass
from typing import Callable
import postfix
import time
import math

def signof(x):
    return (x >= 0) * 2 - 1

start = next

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
    def __init__(self, expression, settings=None):
        self.expression = expression
        self.call = postfix.getFunctionFromPostfix(self.expression)
        self.settings = settings or funcSettings()

class lineStyleGenerators:
    @staticmethod
    def drawSolid(surface, lineWidth, lineColor, progress):
        p1 = yield
        while (p2 := (yield)) != None:
            pygame.draw.line(surface, lineColor, p1, p2, 1)
            progress += 1
            p1 = p2

    @staticmethod
    def drawDotted(surface, lineWidth, lineColor, progress):
        p1 = yield
        while (p2 := (yield)) != None:
            if math.sin(progress / 50) > 0:
                pygame.draw.line(surface, lineColor, p1, p2, lineWidth)
            progress += 1
            p1 = p2

    @staticmethod
    def drawSquiggly(surface, lineWidth, lineColor, progress):
        p1 = yield
        while (p2 := (yield)) != None:
            # do something
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            normal = math.atan2(dy, dx) + NINETYDEG
            offset = (math.sin(progress / 80) * 1.5) + (math.sin((progress / 100) + 2) * 2) + (math.sin(progress / 200) * 3)
            dx = math.cos(normal) * offset
            dy = math.sin(normal) * offset
            p2 = p2[0] + dx, p2[1] + dy
            p1 = p2

class grid:
    plotMethods = [lineStyleGenerators.drawSolid, lineStyleGenerators.drawDotted, lineStyleGenerators.drawSquiggly]
    def __init__(self, settings=None):
        self.settings = settings or gridSettings
        self.functions = []
    @staticmethod
    def translateToRegion(point, region):
        point = point[0] - region.left, point[1] - region.top
        return point

    def drawGridlinesForAxis(self, region, surface, axis):
        if axis == "x":
            transform = (0, 1)
            rng = (region.left, region.right)
        elif axis == "y":
            rng = (region.top, region.bottom)
            transform = (1, 0)
        else:
            raise ValueError(f"axis should be \"x\" or \"y\"; got {axis}")
        frequency, subdivision = self.settings.gridDivision
        for grade in range(*rng):
            lineweight = 0
            if grade == 0:
                lineweight = self.settings.lineWeightAxis
            elif (grade % frequency) == 0:
                lineweight = self.settings.lineWeightMajor
            elif (grade % (frequency/subdivision)) == 0:
                lineweight = self.settings.lineWeightMinor
            else:
                continue
            if axis == "x":
                newLine = (grade - region.left, 0), (grade - region.left, region.height * transform[1])
            elif axis == "y":
                newLine = (0, grade - region.top), (region.width * transform[0], grade - region.top)
            pygame.draw.line(surface, self.settings.lineColor, *newLine, lineweight)

    def drawGridlines(self, region, surface):
        self.drawGridlinesForAxis(region, surface, "x")
        self.drawGridlinesForAxis(region, surface, "y")

    def plotSegment(self, surface, p1, p2, lineColor, lineWidth, lineType, step, progress):
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        differences = signof(dx), signof(dy)
        normal = math.atan2(dy, dx)
        magnitude = math.hypot(dx, dy)
        plotter = self.plotMethods[lineType](surface, lineWidth, lineColor, progress)
        start(plotter)
        if p1 != p2:
            increment = (dx/magnitude) * step, (dy/magnitude) * step
        while (signof(dx), signof(dy)) == differences:
            p1 = increment[0] + p1[0], increment[1] + p1[1]
            plotter.send(p1)
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
        return magnitude # as progress

    def plotPath(self, surface, path, lineWidth, lineColor, lineType, step = 1):
        progress = 0
        if not path:
            return
        lastPoint = path[0]
        for nextPoint in path[1:]:
            progress += self.plotSegment(surface, lastPoint, nextPoint, lineColor, lineWidth, lineType, step, progress)
            #lastPoint = nextPoint

    def plotPathFast(self, surface, path, lineWidth, lineColor, *_):
        if not path:
            return
        lastPoint = path.pop(0)
        for nextPoint in path:
            pygame.draw.line(surface, lineColor, lastPoint, nextPoint, lineWidth)
            lastPoint = nextPoint

    def graphFunctions(self, region, surface):
        lineSurface = pygame.Surface((region.width, region.height))
        lineSurface.set_colorkey((255, 255, 255))
        for function in self.functions:
            if not function.settings.visible:
                continue
            lineSurface.fill((255, 255, 255))
            color = function.settings.lineColor
            width = function.settings.lineWidth
            typ = function.settings.lineType

            path = []
            rng = range(region.left, region.right + 1)
            segments = len(rng)
            maxSegments = self.settings.maxFunctionSegments
            step = max(segments // maxSegments, 1)
            yValues = [None, None, None]
            for x in range(rng.start, rng.stop, step):
                if yValues[1] is None:
                    yValues[1] = -function.call(x)
                yValues[2] = -function.call(x + 1)
                y = yValues[1]
                point = (x, y)
                point = grid.translateToRegion(point, region)
                onScreen = False
                for yValue in yValues:
                    if yValue is None:
                        continue
                    if (0 < (yValue - region.top) < region.height):
                        onScreen = True
                if onScreen:
                    path.append(point)
                yValues = [yValues[1], yValues[2], None]
            self.plotPath(surface, path, width, color, typ, 10)
        return
    
    def labelXAxis(self, region, surface):
        renderer = pygame.freetype.SysFont(pygame.freetype.get_default_font(), self.settings.labelScale)
        _, minBox = renderer.render("012345679")
        minHeight = minBox[1]
        minWidth = minBox[0]
        xAxis = -region.left
        yAxis = region.bottom
        direction = "right"
        if region.right < 0:
            xAxis = region.width
            direction = "left"
        elif region.left > 0:
            xAxis = 0
        for i in range(region.top - minHeight, region.bottom):
            if i % self.settings.labelYInterval == 0:
                iGlobal = i - region.top
                newLabel, rect = renderer.render(str(-i))
                offset = [2, 2]
                if direction == "left":
                    offset[0] = -offset[0] -rect.width
                surface.blit(newLabel, (xAxis + offset[0], iGlobal + offset[1]))

    def render(self, region):
        region = pygame.Rect(region)

        surface = pygame.Surface((region.size))
        surface.fill(self.settings.gridColor)
        self.drawGridlines(region, surface)
        self.graphFunctions(region, surface)
        self.labelXAxis(region, surface)
        return surface

    def addFunc(self, func):
        self.functions.append(func)
    
    def addFuncFromString(self, string, lineColor = None, lineType = None, lineWidth = None):
        infixExpression = postfix.strToInfix(string)
        postfixExpression = postfix.infixToPostfix(infixExpression)
        f = function(postfixExpression)
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
