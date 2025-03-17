import pygame

resolution_width = 1152
resolution_height = 648


class Settings:
    """A class to store all settings for Space Impact."""

    def __init__(self):
        """Initialize the game's static settings."""
        # Screen settings
        # Line removed to avoid overriding window mode configuration
        self.screen_width = resolution_width
        self.screen_height = resolution_height
        self.bg_image = pygame.image.load("images/background_1.png").convert()

        # Bullet settings
        self.bullet_speed = self.screen_width * 0.01
        self.bullet_width = self.screen_width * 0.02
        self.bullet_height = self.screen_height * 0.02
        self.bullet_color = (0, 0, 0)

        # Speed of an alien
        self.alien_speed = self.screen_width * 0.003 * 1.5
        # How quickly the game speeds up
        self.speedup_scale = 1.1
        # Ship Settings
        self.ships_limit = 3
        self.score_scale = 1.1
        self.initialize_dynamic_settings()

    def increase_speed(self):
        """Increase speed settings."""
        # Removed alien_speed increase to keep movement constant
        # self.alien_speed *= self.speedup_scale
        self.alien_points = int(self.alien_points * self.score_scale)

    def initialize_dynamic_settings(self):
        """Initialize settings that change throught the game."""
        self.alien_speed = self.screen_width * 0.003 * 1.5
        self.alien_points = 10
