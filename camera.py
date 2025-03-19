import grid
import pygame
import math
import time
import threading
from dataclasses import dataclass, field

def normalizeRatio(ratio):
    normal = min(ratio)
    if normal == 0:
        raise ValueError("cannot normalize if 0 in ratio")
    scale = 1 / normal
    return ratio[0] * scale, ratio[1] * scale

class Camera:
    def __init__(self, x, y, zoomMagnitude, zoomMin, zoomMax, renderable, ratio, screen):
        self.renderable = renderable
        self.position = (x, y)
        self.zoomMagnitude = zoomMagnitude
        self.zoomMin = zoomMin
        self.zoomMax = zoomMax
        self.ratio = normalizeRatio(ratio)
        self.panning = False
        self.panStart = [0, 0]
        self.panCurrent = [0, 0]
        self.screen = screen
    def getPanDifference(self):
        scale = self.getScaleDifference()
        return (self.panStart[0] - self.panCurrent[0]) * scale[0], (self.panStart[1] - self.panCurrent[1]) * scale[1]
    def lockPan(self):
        panDifference = self.getPanDifference()
        self.position = (self.position[0] + panDifference[0], self.position[1] + panDifference[1])
    def panTo(self, position):
        self.position = position
    def getSize(self):
        return self.ratio[0] * self.zoomMagnitude, self.ratio[1] * self.zoomMagnitude
    def getScaleDifference(self):
        screenSize = self.screen.get_rect().size
        selfSize = self.getSize()
        scaleDifference = selfSize[0] / screenSize[0], selfSize[1] / screenSize[1]
        return scaleDifference
    def setMagnitudeByScale(self, scale):
        currentScale = self.getScaleDifference()[0]
        self.zoomMagnitude *= (scale / currentScale)
    def render(self):
        width, height = self.getSize()
        viewport = pygame.Rect((0, 0, width, height))
        viewport.center = self.position
        if self.panning:
            panDifference = self.getPanDifference()
            viewport.center = (viewport.center[0] + panDifference[0], viewport.center[1] + panDifference[1])
        return self.renderable.render(viewport)
    def zoomTo(self, amount):
        difference = self.zoomMagnitude - amount
        self.zoom(1, difference)
    def zoomIn(self, amount):
        self.zoomMagnitude -= amount
    def zoomOut(self, amount):
        self.zoomMagnitude += amount
    def setZoom(self, amount):
        self.zoomMagnitude = amount

class UI:
    def __init__(self, camera, intervalMap):
        self.camera = camera
        self.intervalMap = intervalMap

    def dispatchEvents(self, events):
        running = True
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.camera.panning = True
                    self.camera.panStart = event.pos
                    self.camera.panCurrent = event.pos
                elif event.button == 4:
                    self.camera.zoomIn(20)
                elif event.button == 5:
                    self.camera.zoomOut(20)
            elif event.type == pygame.MOUSEMOTION:
                self.camera.panCurrent = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.camera.panning = False
                    self.camera.lockPan()
            elif event.type == pygame.QUIT:
                running = False
                break
        return running
    
    def setGridByZoom(self, grid):
        scaleDifference = self.camera.getScaleDifference()[0]
        for interval, settings in self.intervalMap.items():
            if interval[0] < scaleDifference <= interval[1]:
                for itemName, value in settings.items():
                    setattr(grid.settings, itemName, value)


def main():
    screenRatio = (800, 800)
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode(screenRatio)

    g = grid.grid()
    c = Camera(0, 0, 800, 0.1, 100, g, screenRatio, screen)
    u = UI(c, {
            (0, 0.5): {
                "gridDivision": (16, 1),
                "lineWeightAxis": 2,
                "lineWeightMajor": 1,
                "lineWeightMinor": 1,
                "labelXInterval": 64,
                "labelYInterval": 64,
                },
            (0.5, 1): {
                "gridDivision": (128, 2),
                "lineWeightAxis": 4,
                "lineWeightMajor": 3,
                "lineWeightMinor": 2,
                "labelXInterval": 64,
                "labelYInterval": 64,
                },
            (1, 1.5): {
                "gridDivision": (256, 2),
                "lineWeightAxis": 6,
                "lineWeightMajor": 4,
                "lineWeightMinor": 3,
                "labelXInterval": 128,
                "labelYInterval": 128,
                },
            (1.5, 3): {
                "gridDivision": (256, 1),
                "lineWeightAxis": 7,
                "lineWeightMajor": 5,
                "lineWeightMinor": 3,
            }
        })
    """
    g.addFuncFromString("x", (0, 0, 255), grid.linetype.solid, 2)
    g.addFuncFromString("x", (0, 255, 0), grid.linetype.squiggly, 4)
    g.addFuncFromString("(1/100)x ^ 2", (255, 0, 0), grid.linetype.squiggly, 4)
    g.addFuncFromString("2x + 10", (255, 0, 255), grid.linetype.dotted, 6)
    """
    g.addFuncFromString("(1/9x)^2", (0, 0, 255), grid.linetype.solid, 2)
    surface = c.render()
    running = True
    inputBuffer = {"text": None}
    def getInput():
        while True:
            inputBuffer["text"] = input("input a new equation: ")
    getInputThread = threading.Thread(target=getInput)
    #getInputThread.start()
    while running:
        if inputBuffer["text"] is not None:
            g.addFuncFromString(inputBuffer["text"], lineWidth=5)
            inputBuffer["text"] = None
        surface = c.render()
        surface = pygame.transform.scale(surface, screen.get_rect().size)
        screen.blit(surface, (0, 0))
        pygame.display.flip()
        running = u.dispatchEvents(pygame.event.get())
        u.setGridByZoom(g)
    pygame.quit()

if __name__ == '__main__':
    main()
