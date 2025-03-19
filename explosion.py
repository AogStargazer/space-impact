import pygame
import os

class Explosion(pygame.sprite.Sprite):
    """
    A class to represent an explosion animation.
    
    This class handles loading explosion sprite images and animating through them
    to create an explosion effect. Once the animation completes, the sprite
    removes itself from all sprite groups.
    """
    
    def __init__(self, center_x, center_y, scale=2.0):
        """
        Initialize the explosion animation.
        
        Args:
            center_x (float): The x-coordinate of the explosion center.
            center_y (float): The y-coordinate of the explosion center.
            scale (float): Scale factor for the explosion images (default: 2.0).
        """
        super().__init__()
        
        # Load explosion images
        self.images = []
        for i in range(1, 5):
            image_path = os.path.join('images', f'explode{i}.png')
            try:
                image = pygame.image.load(image_path)
                
                # Scale the image if needed
                if scale != 1.0:
                    original_width = image.get_width()
                    original_height = image.get_height()
                    new_width = int(original_width * scale)
                    new_height = int(original_height * scale)
                    image = pygame.transform.scale(image, (new_width, new_height))
                
                self.images.append(image)
            except pygame.error as e:
                print(f"Error loading explosion image {image_path}: {e}")
                # Add a placeholder if image loading fails
                placeholder = pygame.Surface((30, 30))
                placeholder.fill((255, 0, 0))  # Red square as placeholder
                self.images.append(placeholder)
        
        # Animation control attributes
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect(center=(center_x, center_y))
        
        # Timing control
        self.frame_duration = 100  # milliseconds per frame
        self.last_update = pygame.time.get_ticks()
        
    def update(self):
        """
        Update the explosion animation.
        
        This method advances the animation frame based on elapsed time.
        When the animation completes, the sprite is removed from all groups.
        """
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.last_update
        
        # Check if it's time to advance to the next frame
        if elapsed_time >= self.frame_duration:
            self.last_update = current_time
            self.frame_index += 1
            
            # If we've gone through all frames, remove the sprite
            if self.frame_index >= len(self.images):
                self.kill()  # Remove from all sprite groups
            else:
                # Update the current image and maintain the center position
                center = self.rect.center
                self.image = self.images[self.frame_index]
                self.rect = self.image.get_rect(center=center)
