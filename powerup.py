import pygame
from pygame.sprite import Sprite

class Powerup(Sprite):
    """A class to represent a powerup in the game."""
    
    def __init__(self, game, powerup_type, x, y):
        """Initialize the powerup and set its starting position."""
        super().__init__()
        self.screen = game.screen
        self.settings = game.settings
        self.type = powerup_type
        
        # Set the color based on the powerup type
        if self.type == 'red':
            self.color = (255, 0, 0)  # Health powerup
        elif self.type == 'green':
            self.color = (0, 255, 0)  # Laser projectile powerup
        elif self.type == 'orange':
            self.color = (255, 165, 0)  # Spread projectile powerup
        elif self.type == 'yellow':
            self.color = (255, 255, 0)  # Invulnerability powerup
        else:
            self.color = (255, 255, 255)  # Default white if type is unknown
        
        # Set the powerup dimensions and properties
        self.radius = 15
        
        # Create a rect for the powerup (for collision detection)
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        self.rect.centerx = x
        self.rect.centery = y
        
        # Store the powerup's exact position as a float
        self.x = float(self.rect.x)
        
        # Set the powerup speed (1.5 times the alien speed)
        self.speed = self.settings.alien_speed * 1.5
    
    def update(self):
        """Move the powerup from right to left."""
        # Update the exact position
        self.x -= self.speed
        
        # Update the rect position
        self.rect.x = self.x
        
    def draw(self):
        """Draw the powerup to the screen."""
        pygame.draw.circle(
            self.screen,
            self.color,
            (self.rect.centerx, self.rect.centery),
            self.radius
        )