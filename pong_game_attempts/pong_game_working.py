import pygame
import sys

# Initialize Pygame
pygame.init()

# --- Game Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Setup screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simple Pong")
clock = pygame.time.Clock()

# --- Game Objects ---

# Paddle dimensions and initialization
PADDLE_WIDTH = 15
PADDLE_HEIGHT = 100
PADDLE_SPEED = 7

# Player 1 (Left Paddle)
player1 = pygame.Rect(20, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)

# Player 2 (Right Paddle)
player2 = pygame.Rect(SCREEN_WIDTH - 20 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)

# Ball initialization
BALL_SIZE = 15
ball = pygame.Rect(SCREEN_WIDTH // 2 - BALL_SIZE // 2, SCREEN_HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)

# Ball speed and direction
ball_speed_x = 7
ball_speed_y = 7

# Scores
score1 = 0
score2 = 0
font = pygame.font.Font(None, 74)

# --- Helper Functions ---

def handle_movement(paddle, speed):
    """Handles player input for moving a paddle."""
    keys = pygame.key.get_pressed()
    if paddle == player1:
        if keys[pygame.K_w]:
            paddle.y -= speed
        if keys[pygame.K_s]:
            paddle.y += speed
    elif paddle == player2:
        if keys[pygame.K_UP]:
            paddle.y -= speed
        if keys[pygame.K_DOWN]:
            paddle.y += speed

    # Keep paddle within bounds
    if paddle.top < 0:
        paddle.top = 0
    if paddle.bottom > SCREEN_HEIGHT:
        paddle.bottom = SCREEN_HEIGHT

def reset_ball():
    """Resets the ball to the center after a score."""
    global ball_speed_x, ball_speed_y
    ball.x = SCREEN_WIDTH // 2 - BALL_SIZE // 2
    ball.y = SCREEN_HEIGHT // 2 - BALL_SIZE // 2
    # Reverse direction slightly to keep things interesting
    ball_speed_x = ball_speed_x * (1 if (score1 > score2) else (-1))
    ball_speed_y = 7

def update_ball_position():
    """Moves the ball and handles collisions."""
    global ball_speed_x, ball_speed_y, score1, score2

    # 1. Move the ball
    ball.x += ball_speed_x
    ball.y += ball_speed_y

    # 2. Wall Collision Detection (Top/Bottom)
    if ball.top <= 0 or ball.bottom >= SCREEN_HEIGHT:
        ball_speed_y *= -1

    # 3. Scoring/Out of Bounds Detection (Left/Right)
    if ball.left <= 0:
        score2 += 1
        reset_ball()
        return
    
    if ball.right >= SCREEN_WIDTH:
        score1 += 1
        reset_ball()
        return

    # 4. Paddle Collision Detection
    if ball.colliderect(player1) and ball_speed_x < 0:
        ball_speed_x *= -1.05 # Increase speed slightly on paddle hit
    
    if ball.colliderect(player2) and ball_speed_x > 0:
        ball_speed_x *= -1.05 # Increase speed slightly on paddle hit

def draw_elements():
    """Draws all game elements to the screen."""
    # Fill background
    screen.fill(BLACK)
    
    # Draw center line (optional)
    pygame.draw.aaline(screen, WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT))

    # Draw paddles and ball
    pygame.draw.rect(screen, WHITE, player1)
    pygame.draw.rect(screen, WHITE, player2)
    pygame.draw.ellipse(screen, WHITE, ball)

    # Draw scores
    text1 = font.render(f"{score1}", True, WHITE)
    text2 = font.render(f"{score2}", True, WHITE)
    
    screen.blit(text1, (SCREEN_WIDTH // 4, 20))
    screen.blit(text2, (SCREEN_WIDTH * 3 // 4 - text1.get_width(), 20))


# --- Main Game Loop ---
def game_loop():
    global ball_speed_x, ball_speed_y
    running = True

    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

        # 2. Input Handling (Move Paddles)
        handle_movement(player1, PADDLE_SPEED)
        handle_movement(player2, PADDLE_SPEED)
        
        # 3. Update Game State
        update_ball_position()

        # 4. Drawing
        draw_elements()
        
        # Update the display and cap the frame rate
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == '__main__':
    game_loop()