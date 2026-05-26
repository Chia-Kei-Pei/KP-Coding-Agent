import pygame
import sys
import random

# Constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class Paddle:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)

class Ball:
    def __init__(self, x, y, radius):
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        self.radius = radius

    def draw(self, screen):
        pygame.draw.ellipse(screen, WHITE, self.rect)

class PongGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pong")
        self.clock = pygame.time.Clock()
        
        # Initialize objects
        self.left_paddle = Paddle(20, SCREEN_HEIGHT // 2 - 50, 15, 100)
        self.right_paddle = Paddle(SCREEN_WIDTH - 35, SCREEN_HEIGHT // 2 - 50, 15, 100)
        self.ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 10)
        
        self.running = True

    def draw_court(self):
        self.screen.fill(BLACK)
        # Center line (dashed)
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH // 2 - 2, y, 4, 20))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        pass

    def draw(self):
        self.draw_court()
        self.left_paddle.draw(self.screen)
        self.right_paddle.draw(self.screen)
        self.ball.draw(self.screen)
        pygame.display.flip()

if __name__ == "__main__":
    game = PongGame()
    game.run()
