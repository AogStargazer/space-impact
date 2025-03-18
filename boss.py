import pygame
import os
from random import choice

class Boss(pygame.sprite.Sprite):
    """A class to represent the boss enemy in the game."""
    
    def __init__(self, game):
        """Initialize the boss and set its starting position."""
        super().__init__()
        self.screen = game.screen
        self.settings = game.settings
        self.game = game
        
        # Load boss images and create animation frames
        self.frames = []
        self.load_images()
        
        # Start with the first image
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        
        # Position the boss on the right side of the screen
        self.rect.right = self.settings.screen_width - 50
        self.rect.centery = self.settings.screen_height // 2
        
        # Store the boss's exact position
        self.y = float(self.rect.y)
        self.x = float(self.rect.x)
        
        # Movement flags
        self.moving_down = True
        
        # Boss phase: 'approach' or 'combat'
        self.phase = 'approach'
        
        # Boss health
        self.health = 200
        
        # Attack cooldown
        self.attack_timer = 0
        self.attack_cooldown = 5000  # 5 seconds in milliseconds
        self.last_attack_time = pygame.time.get_ticks()
        
        # Animation timer
        self.animation_time = pygame.time.get_ticks()
        self.animation_cooldown = 200  # Animation frame change rate in milliseconds

    def load_images(self):
        """Load the boss images and scale them larger."""
        # Scale factor for the boss (making it 20x larger)
        scale_factor = 20.0
        
        # Define a list of enemy sprite paths
        enemy_sprite_sets = [
            ('images/alien_1_1.png', 'images/alien_1_2.png'),
            ('images/alien_2_1.png', 'images/alien_2_2.png'),
            ('images/alien_3_1.png', 'images/alien_3_2.png')
        ]
        
        # Randomly select one set of enemy sprites
        selected_sprites = choice(enemy_sprite_sets)
        
        # Try to load the selected sprites
        try:
            for sprite_path in selected_sprites:
                if os.path.exists(sprite_path):
                    image = pygame.image.load(sprite_path)
                    # Scale the image to be larger
                    width = int(image.get_width() * scale_factor)
                    height = int(image.get_height() * scale_factor)
                    scaled_image = pygame.transform.scale(image, (width, height))
                    self.frames.append(scaled_image)
        except Exception:
            # Fallback to boss-specific images if they exist
            try:
                boss_images_path = os.path.join('images', 'boss')
                if os.path.exists(boss_images_path):
                    for filename in sorted(os.listdir(boss_images_path)):
                        if filename.endswith('.png') or filename.endswith('.bmp'):
                            image = pygame.image.load(os.path.join(boss_images_path, filename))
                            # Scale the image to be larger
                            width = int(image.get_width() * scale_factor)
                            height = int(image.get_height() * scale_factor)
                            scaled_image = pygame.transform.scale(image, (width, height))
                            self.frames.append(scaled_image)
            except Exception:
                # Fallback to alien images if boss images aren't available
                alien_images_path = os.path.join('images', 'alien')
                if os.path.exists(alien_images_path):
                    for filename in sorted(os.listdir(alien_images_path)):
                        if filename.endswith('.png') or filename.endswith('.bmp'):
                            image = pygame.image.load(os.path.join(alien_images_path, filename))
                            # Scale the image to be larger
                            width = int(image.get_width() * scale_factor)
                            height = int(image.get_height() * scale_factor)
                            scaled_image = pygame.transform.scale(image, (width, height))
                            self.frames.append(scaled_image)
                else:
                    # Create a default image if no images are found
                    default_image = pygame.Surface((60, 60))
                    default_image.fill((255, 0, 0))  # Red color for the boss
                    self.frames.append(default_image)
        
        # Ensure we have at least one frame
        if not self.frames:
            default_image = pygame.Surface((60, 60))
            default_image.fill((255, 0, 0))  # Red color for the boss
            self.frames.append(default_image)

    def update(self):
        """Update the boss's position and handle attacks."""
        # Check if we need to transition from approach to combat phase
        if self.phase == 'approach':
            # Move horizontally from right to left
            self.x -= self.settings.alien_speed
            
            # Check if we've reached the 75% mark of the screen width
            combat_position = self.settings.screen_width * 0.75
            if self.x <= combat_position:
                self.phase = 'combat'
                # Ensure we stop exactly at the combat position
                self.x = combat_position
        
        # In combat phase, move up and down
        if self.phase == 'combat':
            if self.moving_down:
                self.y += self.settings.alien_speed * 0.5
                if self.rect.bottom >= self.settings.screen_height - 10:
                    self.moving_down = False
            else:
                self.y -= self.settings.alien_speed * 0.5
                if self.rect.top <= 10:
                    self.moving_down = True
        
        # Update rect position
        self.rect.y = self.y
        self.rect.x = self.x
        
        # Handle attack cooldown (only in combat phase)
        current_time = pygame.time.get_ticks()
        if self.phase == 'combat' and current_time - self.last_attack_time >= self.attack_cooldown:
            self.attack()
            self.last_attack_time = current_time
        
        # Handle animation
        if current_time - self.animation_time >= self.animation_cooldown:
            self.animation_time = current_time
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.image = self.frames[self.frame_index]

    def attack(self):
        """Fire a boss bullet."""
        if hasattr(self.game, '_fire_boss_bullet'):
            self.game._fire_boss_bullet(self)

    def hit(self, damage=1):
        """Process a hit on the boss."""
        self.health -= damage
        # Return True if the boss is destroyed
        return self.health <= 0

    def draw(self):
        """Draw the boss at its current location."""
        self.screen.blit(self.image, self.rect)
