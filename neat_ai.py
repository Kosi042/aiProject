import pygame
import sys
import random
import neat
import os


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

# Genreations
GEN = 0


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
        self.rect.x = x

    def draw(self, screen_):
        screen_.blit(self.image, self.rect)


# Set up the NEAT Neural Network
def main(config_path_):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path_
    )

    pop = neat.Population(config)
    pop.add_reporter(neat.StdOutReporter(True))
    pop.add_reporter(neat.StatisticsReporter())
    winner = pop.run(run_game, 50)


# Main game function
def run_game(genomes, config):
    global GEN, HIGHSCORE

    nets = []
    birds = []
    gens = []
    GEN += 1

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird())
        gens.append(genome)

    pipes = []
    spawn_pipe_event = pygame.USEREVENT
    pygame.time.set_timer(spawn_pipe_event, PIPE_FREQUENCY)
    score = 0
    old_score = 0
    running = True

    while running and len(birds) > 0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    birds[0].flap()
            if event.type == spawn_pipe_event:
                height = random.randint(100, SCREEN_HEIGHT - 200)
                pipes.append([Pipe(SCREEN_WIDTH, height, True), Pipe(SCREEN_WIDTH, height, False), SCREEN_WIDTH])
                # pipes.append(Pipe(SCREEN_WIDTH, height, False))

        # Update birds and pipes
        for pipe in pipes:
            pipe[2] = pipe[2] - 5  # x position to make sure that both top and bottom pipe align
            pipe[0].update(pipe[2])
            pipe[1].update(pipe[2])
            if pipe[0].rect.right < 0:
                pipes.remove(pipe)
                # if not pipe.is_top:
                old_score = score
                score += 1

        pipe_idx = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0][0].x + pipes[0][0].image.get_width():
                pipe_idx = 1

        for i, bird in enumerate(birds):
            gens[i].fitness += 0.1
            if old_score != score:
                gens[i].fitness += score
                old_score = score

            if len(pipes) > 0:
                output = nets[i].activate((bird.y, abs(bird.y - pipes[pipe_idx][0].y),
                                           abs(bird.y - pipes[pipe_idx][1].y), bird.number_of_flaps))
                ''' print(f"Bird number: {i}, "
                      f"Abs upper Pipe: {abs(bird.y - pipes[pipe_idx][0].y)}, "
                      f"Abs lower Pipe: {abs(bird.y - pipes[pipe_idx][1].y)}")'''
            else:
                output = nets[i].activate((bird.y, 0, 0, bird.number_of_flaps))
           # print(f"Bird number: {i} output: {output}")

            if output[0] > 0.5:
                bird.flap()

        screen.blit(background_img, (0, 0))
        for bird in birds:
            bird.update()
            if bird.rect.top <= 0 or bird.rect.bottom >= SCREEN_HEIGHT:
                gens[birds.index(bird)].fitness -= 5
                nets.pop(birds.index(bird))
                gens.pop(birds.index(bird))
                birds.pop(birds.index(bird))

            # Check for collisions
            for pipe in pipes:
                if bird.rect.colliderect(pipe[0].rect) or bird.rect.colliderect(pipe[1].rect):
                    gens[birds.index(bird)].fitness += score - 5
                    nets.pop(birds.index(bird))
                    gens.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            bird.draw(screen)

        for pipe in pipes:
            pipe[0].draw(screen)
            pipe[1].draw(screen)

        # Display score
        font = pygame.font.Font(None, 36)
        text = font.render(f"Score: {score}             "
                           f"Gen: {GEN}                 "
                           f"Birds alive: {len(birds)}  "
                           f"Highscore: {HIGHSCORE}"
                           , True, WHITE)
        screen.blit(text, (10, 10))

        if score > HIGHSCORE:
            HIGHSCORE = score
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    local_dir = os.getcwd()
    config_path = os.path.join(local_dir, 'config.txt')
    main(config_path_= config_path)
