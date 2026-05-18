import pygame
import sys

# --- Initialization ---
pygame.init()

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)

# Setup Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple Pygame Pong")
clock = pygame.time.Clock()

# Fonts for scoring
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)

# --- Game Objects ---

class Paddle:
    def __init__(self, x, y, width, height, speed):
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = speed

    def move(self, direction):
        # Direction: 1 for down, -1 for up
        new_y = self.rect.y + direction * self.speed
        
        # Keep paddle within screen boundaries
        if new_y < 0:
            new_y = 0
        elif new_y + self.rect.height > SCREEN_HEIGHT:
            new_y = SCREEN_HEIGHT - self.rect.height
        
        self.rect.y = new_y

    def draw(self):
        pygame.draw.rect(screen, BLUE, self.rect)

class Ball:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.speed_x = 5
        self.speed_y = 5
        self.reset_ball()

    def reset_ball(self):
        # Reset ball to the center, giving it a slight random starting direction
        self.rect.x = SCREEN_WIDTH // 2 - 10
        self.rect.y = SCREEN_HEIGHT // 2 - 10
        self.speed_x = 5 * (pygame.time.get_ticks() % 2) - 5 # Random direction -5 to 5
        self.speed_y = 5 * (pygame.time.get_ticks() % 2) - 5

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

    def draw(self):
        pygame.draw.ellipse(screen, WHITE, self.rect)

    def check_collision(self, paddle):
        if self.rect.colliderect(paddle.rect):
            # Simple reflection logic
            if self.speed_x < 0: # Hitting right paddle
                self.speed_x = abs(self.speed_x) * 1.05
            elif self.speed_x > 0: # Hitting left paddle
                self.speed_x = -abs(self.speed_x) * 1.05
            
            # Simple bounce logic: slightly adjust vertical speed based on where it hits
            impact_y = self.rect.centery - paddle.rect.centery
            self.speed_y = impact_y * 0.2 + (self.speed_y * 0.8) # Makes rebound angle dependent on hit point

# --- Setup Game Elements ---

PADDLE_WIDTH = 15
PADDLE_HEIGHT = 100
BALL_SIZE = 15

# Initialize paddles (Left paddle controlled by 'W'/'S', Right paddle controlled by UP/DOWN arrows)
player1 = Paddle(20, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, 
                 PADDLE_WIDTH, PADDLE_HEIGHT, 8)
player2 = Paddle(SCREEN_WIDTH - 20 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, 
                 PADDLE_WIDTH, PADDLE_HEIGHT, 8)

# Initialize ball
ball = Ball(SCREEN_WIDTH // 2 - BALL_SIZE // 2, SCREEN_HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE)

# Score tracking
score1 = 0
score2 = 0

# --- Main Game Loop ---

def game_loop():
    global score1, score2
    running = True
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

        # 2. Input Handling (Movement)
        keys = pygame.key.get_pressed()
        
        # Player 1 (Left Paddle: W/S)
        if keys[pygame.K_w]:
            player1.move(direction=-1)
        if keys[pygame.K_s]:
            player1.move(direction=1)

        # Player 2 (Right Paddle: Up/Down Arrows)
        if keys[pygame.K_UP]:
            player2.move(direction=-1)
        if keys[pygame.K_DOWN]:
            player2.move(direction=1)

        # 3. Updates
        ball.move()

        # Wall collision (Top/Bottom)
        if ball.rect.top <= 0 or ball.rect.bottom >= SCREEN_HEIGHT:
            ball.speed_y *= -1
        
        # Paddle collision
        ball.check_collision(player1)
        ball.check_collision(player2)

        # Scoring and boundary checking (Left/Right)
        scored = False
        if ball.rect.left <= 0: # Player 2 scores (Ball passed P1)
            score2 += 1
            ball.reset_ball()
            scored = True
        elif ball.rect.right >= SCREEN_WIDTH: # Player 1 scores (Ball passed P2)
            score1 += 1
            ball.reset_ball()
            scored = True
        
        # If a score occurred, we might want to slightly pause the action or change the ball state
        if scored:
            pygame.time.wait(500) # Pause for half a second after a score

        # 4. Drawing
        screen.fill(BLACK) # Black background
        
        # Draw the center line
        pygame.draw.aaline(screen, WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT))

        # Draw game elements
        player1.draw()
        player2.draw()
        ball.draw()

        # Draw scores
        text1 = font.render(str(score1), True, WHITE)
        text2 = font.render(str(score2), True, WHITE)
        screen.blit(text1, (SCREEN_WIDTH // 4, 20))
        screen.blit(text2, (SCREEN_WIDTH * 3 // 4 - text1.get_width(), 20))

        # 5. Display Update and Frame Rate Control
        pygame.display.update()
        clock.tick(FPS)

if __name__ == '__main__':
    game_loop()