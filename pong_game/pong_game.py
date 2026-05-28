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
        
        # Ball physics for pong-004
        self.ball_speed_val = 5
        self.ball_dx = random.choice([-1, 1]) * self.ball_speed_val
        self.ball_dy = random.choice([-1, 1]) * self.ball_speed_val

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

        # Handle AI paddle movement for pong-003 (Left paddle)
        if self.ball_rect.centery < self.left_paddle.rect.centery:
            self.left_paddle.move_up()
        elif self.ball_rect.centery > self.left_paddle.rect.centery:
            self.left_paddle.move_down()

        # Ball movement and wall bouncing for pong-004
        self.ball_rect.x += self.ball_dx
        self.ball_rect.y += self.ball_dy

        # Bounce off top and bottom walls
        if self.ball_rect.top <= 0:
            self.ball_rect.top = 0
            self.ball_dy *= -1
        elif self.ball_rect.bottom >= SCREEN_HEIGHT:
            self.ball_rect.bottom = SCREEN_HEIGHT
            self.ball_dy *= -1

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
