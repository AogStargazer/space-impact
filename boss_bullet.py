import pygame
from settings import Settings

class BossBullet(pygame.sprite.Sprite):
    """A class to manage bullets fired from the boss"""
    
    def __init__(self, ai_game, boss):
        """Create a bullet object at the boss's position"""
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.color = (255, 0, 0)  # Red color for boss bullets
        
        # Create a bullet rect at (0, 0) and then set correct position
        # Increase size by 1.5 times compared to regular bullets
        bullet_width = int(self.settings.bullet_width * 1.5)
        bullet_height = int(self.settings.bullet_height * 1.5)
        self.rect = pygame.Rect(0, 0, bullet_width, bullet_height)
        
        # Position the bullet at the boss's midleft
        self.rect.midleft = boss.rect.midleft
        
        # Store the bullet's position as a decimal value
        self.x = float(self.rect.x)
        
        # Set bullet speed (1.2 times faster than regular bullets)
        self.speed = self.settings.bullet_speed * 1.2
    
    def update(self):
        """Move the bullet to the left across the screen"""
        # Update the decimal position of the bullet
        self.x -= self.speed
        
        # Update the rect position
        self.rect.x = self.x
    
    def draw_bullet(self):
        """Draw the bullet to the screen"""
        pygame.draw.rect(self.screen, self.color, self.rect)
