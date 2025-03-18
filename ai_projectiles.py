import pygame
import math

class LaserBullet(pygame.sprite.Sprite):
    """
    A specialized laser projectile exclusively for AI usage.
    Travels faster than normal bullets and has a thinner, brighter appearance.
    """
    
    def __init__(self, x, y, speed=15):
        """
        Initialize a laser bullet.
        
        Args:
            x (int): Starting x-coordinate
            y (int): Starting y-coordinate
            speed (int): Speed of the laser bullet (default: 15, faster than normal bullets)
        """
        super().__init__()
        
        # Create a thinner, brighter laser beam
        self.image = pygame.Surface((20, 3), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 50, 50), (0, 0, 20, 3))  # Bright red laser
        
        # Add a glow effect
        glow_surf = pygame.Surface((24, 7), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (255, 100, 100, 128), (0, 0, 24, 7), border_radius=2)
        
        # Combine the base and glow
        final_surf = pygame.Surface((24, 7), pygame.SRCALPHA)
        final_surf.blit(glow_surf, (0, 0))
        final_surf.blit(self.image, (2, 2))
        self.image = final_surf
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.x = float(x)
        self.y = float(y)
    
    def update(self):
        """Update the laser bullet's position."""
        self.x += self.speed
        self.rect.x = self.x
        
        # Remove if it goes off-screen
        if self.rect.left > pygame.display.get_surface().get_width():
            self.kill()


class SpreadBullet(pygame.sprite.Sprite):
    """
    A specialized spread projectile exclusively for AI usage.
    Travels at an angle to create a shotgun spread effect.
    """
    
    def __init__(self, x, y, speed=10, angle=0):
        """
        Initialize a spread bullet.
        
        Args:
            x (int): Starting x-coordinate
            y (int): Starting y-coordinate
            speed (int): Speed of the spread bullet
            angle (float): Angle in degrees for the bullet's trajectory
        """
        super().__init__()
        
        # Create a small, distinctive bullet
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 200, 50), (4, 4), 4)  # Yellow-orange bullet
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.angle = math.radians(angle)  # Convert to radians for math calculations
        self.x = float(x)
        self.y = float(y)
    
    def update(self):
        """Update the spread bullet's position based on its angle."""
        # Calculate x and y components based on angle
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
        
        # Update the rect position
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Remove if it goes off-screen
        screen = pygame.display.get_surface()
        if (self.rect.left > screen.get_width() or 
            self.rect.right < 0 or 
            self.rect.top > screen.get_height() or 
            self.rect.bottom < 0):
            self.kill()


def create_spread_shot(x, y, num_bullets=3, spread_angle=20, speed=10):
    """
    Create multiple SpreadBullet instances with varied angles for a spread shot effect.
    
    Args:
        x (int): Starting x-coordinate
        y (int): Starting y-coordinate
        num_bullets (int): Number of bullets in the spread
        spread_angle (float): Total angle of spread in degrees
        speed (int): Speed of the bullets
        
    Returns:
        list: List of SpreadBullet instances
    """
    bullets = []
    
    # Calculate the angle step between bullets
    if num_bullets > 1:
        angle_step = spread_angle / (num_bullets - 1)
    else:
        angle_step = 0
    
    # Calculate the starting angle (to center the spread)
    start_angle = -spread_angle / 2
    
    # Create bullets at different angles
    for i in range(num_bullets):
        angle = start_angle + (i * angle_step)
        bullets.append(SpreadBullet(x, y, speed, angle))
    
    return bullets