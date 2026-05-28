import pygame
import sys

# Constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class Paddle:
    def __init__(self, x, y, width, height, speed=6):
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = speed

    def move_up(self):
        if self.rect.top > 0:
            self.rect.y -= self.speed

    def move_down(self):
        if self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)

class PongGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pong")
        self.clock = pygame.time.Clock()
        self.running = True

        # Initial positions/dimensions for pong-001
        self.paddle_width = 15
        self.paddle_height = 90
        
        self.left_paddle = Paddle(20, SCREEN_HEIGHT // 2 - self.paddle_height // 2, self.paddle_width, self.paddle_height)
        self.right_paddle = Paddle(SCREEN_WIDTH - 20 - self.paddle_width, SCREEN_HEIGHT // 2 - self.paddle_height // 2, self.paddle_width, self.paddle_height)
        
        self.ball_radius = 10
        self.ball_rect = pygame.Rect(SCREEN_WIDTH // 2 - self.ball_radius, SCREEN_HEIGHT // 2 - self.ball_radius, self.ball_radius * 2, self.ball_radius * 2)

    def draw_dashed_line(self):
        # Draw a dashed centre line
        dash_length = 10
        gap_length = 10
        for y in range(0, SCREEN_HEIGHT, dash_length + gap_length):
            pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH // 2 - 1, y, 2, dash_length))

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
        # Handle paddle movement for pong-002 (Right paddle)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.right_paddle.move_up()
        if keys[pygame.K_DOWN]:
            self.right_paddle.move_down()

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_dashed_line()
        self.left_paddle.draw(self.screen)
        self.right_paddle.draw(self.screen)
        pygame.draw.ellipse(self.screen, WHITE, self.ball_rect)
        pygame.display.flip()

if __name__ == "__main__":
    game = PongGame()
    game.run()
