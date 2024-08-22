import pygame
import sys
import random
import neat
import os

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

# Bird class
class Bird:
    def __init__(self):
        self.image = bird_img_d
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.velocity = -7
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.centery = self.y
        self.change_image()

    def flap(self):
        self.velocity = FLAP_STRENGTH

    def draw(self, screen): 
        screen.blit(self.image, self.rect)

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
        if is_top:
            self.image = pygame.transform.flip(pipe_img, False, True)
            self.rect = self.image.get_rect(midbottom=(x, height))
        else:
            self.rect = self.image.get_rect(midtop=(x, height + PIPE_GAP))

    def update(self, x): 
        self.rect.x = x

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# Setup the NEAT Neural Network
def main(config_path):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )

    pop = neat.Population(config)
    pop.run(run_game, 50)

# Main game function
def run_game():
    bird = Bird() 
    pipes = []
    spawn_pipe_event = pygame.USEREVENT
    pygame.time.set_timer(spawn_pipe_event, PIPE_FREQUENCY)
    score = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.flap()
            if event.type == spawn_pipe_event:
                height = random.randint(100, SCREEN_HEIGHT - 200)
                pipes.append([Pipe(SCREEN_WIDTH, height, True), Pipe(SCREEN_WIDTH, height, False), SCREEN_WIDTH])
                #pipes.append(Pipe(SCREEN_WIDTH, height, False))

        # Update bird and pipes
        bird.update()
        for pipe in pipes:
            pipe[2] = pipe[2]-5 # x position to make sure that both top and bottom pipe aline
            pipe[0].update(pipe[2]) 
            pipe[1].update(pipe[2])
            if pipe[0].rect.right < 0:
                pipes.remove(pipe)
                #if not pipe.is_top:
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
        text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    main()
