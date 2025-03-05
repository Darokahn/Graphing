import grid
import pygame
import math
import time

def normalizeRatio(ratio):
    normal = min(ratio)
    if normal == 0:
        raise ValueError("cannot normalize if 0 in ratio")
    scale = 1 / normal
    return ratio[0] * scale, ratio[1] * scale

class Camera:
    def __init__(self, x, y, zoomMagnitude, renderable, ratio):
        self.renderable = renderable
        self.x = x
        self.y = y
        self.zoomMagnitude = zoomMagnitude
        self.ratio = normalizeRatio(ratio)
    def render(self):
        width = self.ratio[0] * self.zoomMagnitude
        height = self.ratio[1] * self.zoomMagnitude
        viewport = pygame.Rect((0, 0, width, height))
        viewport.center = (self.x, self.y)
        return self.renderable.render(viewport)
    def zoomIn(self, amount):
        self.zoomMagnitude -= amount
    def zoomOut(self, amount):
        self.zoomMagnitude += amount
    def setZoom(self, amount):
        self.zoomMagnitude = amount

def main():
    g = grid.grid()
    screenRatio = (800, 800)
    c = Camera(0, 0, 800, g, screenRatio)
    g.addFuncFromString("x", (0, 255, 0), grid.linetype.squiggly, 4)
    g.addFuncFromString("((1/10)x)^2", (0, 100, 0), grid.linetype.solid, 4)
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode(screenRatio)
    running = True
    while running:
        c.setZoom(300 * math.sin(time.time()) + 500)
        surface = c.render()
        surface = pygame.transform.scale(surface, screen.get_rect().size)
        screen.blit(surface, (0, 0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()

if __name__ == '__main__':
    main()
