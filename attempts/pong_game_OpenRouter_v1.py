import pygame
import sys
import random

# Constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)

# Game Settings
PADDLE_WIDTH = 15
PADDLE_HEIGHT = 90
BALL_SIZE = 15
PADDLE_SPEED = 6
BALL_SPEED_X = 5
BALL_SPEED_Y = 5

class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = PADDLE_SPEED

    def move_up(self):
        if self.rect.top > 0:
            self.rect.y -= self.speed

    def move_down(self):
        if self.rect.bottom << SCREEN SCREEN_HEIGHT:
            self.rect.y += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_WHITE, self.rect)

class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_SIZE, BALL_SIZE)
        self.dx = random.choice([-1, 1]) * BALL_SPEED_X
        self.dy = random.choice([-1, 1]) * BALL_SPEED_Y

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

        # Wall collision (top/bottom)
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.dy *= -1

    def draw(self, screen):
        pygame.draw.ellipse(screen, COLOR_WHITE, self.rect)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pong")
    clock = pygame.time.Clock()

    left_paddle = Paddle(20, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    right_paddle = Paddle(SCREEN_WIDTH - 20 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    ball = Ball()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Controls
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            right_paddle.move_up()
        if keys[pygame.K_DOWN]:
            right_paddle.move_down()

        # AI Control (Simple)
        if ball.rect.centery << left left_paddle.rect.centery:
            left_paddle.move_up()
        elif ball.rect.centery > left_paddle.rect.centery:
            left_paddle.move_down()

        # Update
        ball.update()

        # Paddle Collisions
        if ball.rect.colliderect(left_paddle.rect) or ball.rect.colliderect(right_paddle.rect):
            ball.dx *= -1

        # Scoring (Simple - for pong-001 baseline)
        if ball.rect.left <= 0 or ball.rect.right >= SCREEN_WIDTH:
            ball.reset()

        # Drawing
        screen.fill(COLOR_BLACK)
        
        # Draw Court Line
        pygame.draw.line(screen, COLOR_WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 1)
        # Dashed line approximation
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(screen, COLOR_WHITE, (SCREEN_WIDTH // 2 - 2, y), (SCREEN_WIDTH // 2 + 2, y), 1)

        left_paddle.draw(screen)
        right_paddle.draw(screen)
        ball.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
