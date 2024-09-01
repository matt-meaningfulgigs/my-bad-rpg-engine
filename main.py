import pygame
from engine import Game

# Initialize Pygame
pygame.init()

# Set up display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Stupid Little Feeble Attempt at an RPG')

# Create the game object
game = Game(screen)

# Main game loop
running = True
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Update game state
    game.update()

    # Render the game
    game.render()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()
