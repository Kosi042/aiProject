import pygame
import sys
import random
import numpy as np
import matplotlib.pyplot as plt
import time

HIGHSCORE = 0

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Game settings
GRAVITY = 0.4
FLAP_STRENGTH = -7
PIPE_GAP = 150
PIPE_FREQUENCY = 1500  # milliseconds

# Load images
bird_img_d = pygame.image.load('bird_d.png')
bird_img_u = pygame.image.load('bird_u.png')
pipe_img = pygame.image.load('pipe.png')
background_img = pygame.image.load('background.png')

# Scale images
bird_img_d = pygame.transform.scale(bird_img_d, (40, 30))
bird_img_u = pygame.transform.scale(bird_img_u, (40, 30))
pipe_img = pygame.transform.scale(pipe_img, (80, 800))
background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Create game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Clock for controlling frame rate
clock = pygame.time.Clock()

Q = np.zeros((20, 16, 2), dtype=float)


# Bird class
class Bird:

    def __init__(self):
        self.image = bird_img_d
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.velocity = -7
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.number_of_flaps = 0

    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.centery = self.y
        self.change_image()

    def flap(self):
        self.number_of_flaps += 1
        self.velocity = FLAP_STRENGTH

    def draw(self, screen_):
        screen_.blit(self.image, self.rect)

    def change_image(self):
        if self.velocity > 0:
            self.image = bird_img_d
        elif self.velocity < 0:
            self.image = bird_img_u


# Pipe class
class Pipe:
    def __init__(self, x, height, is_top):
        self.image = pipe_img
        self.is_top = is_top
        self.x = x
        if is_top:
            self.image = pygame.transform.flip(pipe_img, False, True)
            self.y = height
            self.rect = self.image.get_rect(midbottom=(self.x, self.y))
        else:
            self.y = height + PIPE_GAP
            self.rect = self.image.get_rect(midtop=(self.x, self.y))

    def update(self, x):
        self.x = x
        self.rect.x = x

    def draw(self, screen_):
        screen_.blit(self.image, self.rect)


# Main game function
def run_game():
    global Q
    global HIGHSCORE

    bird = Bird()
    pipes = []
    spawn_pipe_event = pygame.USEREVENT
    pygame.time.set_timer(spawn_pipe_event, PIPE_FREQUENCY)
    score = 0
    running = True

    while running:

        pipe_idx = 0
        if len(pipes) > 1 and bird.x > pipes[0][0].x + pipes[0][0].image.get_width():
            pipe_idx = 1

        if len(pipes) > 0:
            # print(pipes[0][1].x)
            x_prev, y_prev = convert(bird.y, pipes[pipe_idx][1].x, pipes[pipe_idx][1].y)
        else:
            x_prev, y_prev = convert(bird.y, 0, 0)

        print(f"x {x_prev}, y {y_prev}")
        jump = ai_clac(x_prev, y_prev)
        if jump:
            bird.flap()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.flap()
                if event.key == pygame.K_s:
                    np.save(f"Q{time.time()}.npy", Q)
            if event.type == spawn_pipe_event:
                height = random.randint(100, SCREEN_HEIGHT - 200)
                pipes.append([Pipe(SCREEN_WIDTH, height, True), Pipe(SCREEN_WIDTH, height, False), SCREEN_WIDTH])

        # Update bird and pipes
        bird.update()
        for pipe in pipes:
            pipe[2] = pipe[2] - 5  # x position to make sure that both top and bottom pipe align
            pipe[0].update(pipe[2])
            pipe[1].update(pipe[2])
            if pipe[0].rect.right < 0:
                pipes.remove(pipe)
                score += 1

        # Check for collisions
        if bird.rect.top <= 0 or bird.rect.bottom >= SCREEN_HEIGHT:
            running = False
        for pipe in pipes:
            if bird.rect.colliderect(pipe[0].rect) or bird.rect.colliderect(pipe[1].rect):
                running = False

        # Draw everything
        screen.blit(background_img, (0, 0))
        bird.draw(screen)
        for pipe in pipes:
            pipe[0].draw(screen)
            pipe[1].draw(screen)

        # Display score
        font = pygame.font.Font(None, 36)
        text = font.render(f"Score: {score}, Highscore: {HIGHSCORE}", True, WHITE)
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

        if len(pipes) > 0:
            x_new, y_new = convert(bird.y, pipes[0][1].x, pipes[0][1].y)
        else:
            x_new, y_new = 0, 0

        if not running:
            if HIGHSCORE < score:
                HIGHSCORE = score
            reward = -1500
            q_update(x_prev, y_prev, jump, reward, x_new, y_new)

        reward = 15
        q_update(x_prev, y_prev, jump, reward, x_new, y_new)

    run_game()

def ai_clac(x, y):
    global Q
    jump = False

    if (Q[x][y][1] > Q[x][y][0]):
        jump = True
    return jump


def convert(birdy, lowpipex, lowpipey):
    global SCREEN_WIDTH
    x = min(SCREEN_WIDTH, lowpipex)

    y = lowpipey - birdy
    if y < 0:
        y = y + SCREEN_HEIGHT
    x = max(0, int(x/40-1))
    return x, int(y/40)


def q_update(x_prev, y_prev, jump, reward, x_new, y_new):

    if jump:
        Q[x_prev][y_prev][1] = 0.4 * Q[x_prev][y_prev][1] + 0.6 * (reward + max(Q[x_new][y_new][0], Q[x_new][y_new][1]))
    else:
        Q[x_prev][y_prev][0] = 0.4 * Q[x_prev][y_prev][0] + 0.6 * (reward + max(Q[x_new][y_new][0], Q[x_new][y_new][1]))


def main():
    global Q
    lq = input("Load Q? Press y")
    if lq.lower() == "y":
        Q = np.load(input("Give file name"))
    run_game()


if __name__ == "__main__":
    main()
