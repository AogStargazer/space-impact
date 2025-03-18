import pygame.font
from heart import Heart
from pygame.sprite import Group


class Scoreboard:
    """A class to report scoring information."""

    def __init__(self, si_game):
        """Initialize scorekeeping attributes."""
        self.si_game = si_game
        self.screen = si_game.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = si_game.settings
        self.stats = si_game.stats

        # Font settings for scoring information.
        self.text_color = (0, 0, 0)
        # Font "Pixeled" created by OmegaPC777.
        self.font = pygame.font.Font("pixeled.ttf", int(self.settings.screen_height*0.04))
        # Prepate the initial score image.
        self.prep_score()
        self.prep_high_score()
        self.prep_hearts()
        self.prep_powerup_counts()

    def prep_score(self):
        """Turn the score into a rendered image."""
        rounded_score = round(self.stats.score)
        score_str = "S-{:,}".format(rounded_score)
        # Display the score at the top right of the screen.
        self.score_image = self.font.render(score_str, True, self.text_color)

    def prep_high_score(self):
        """Turn the high_score into a rendered image."""
        # rounded_high_score = round(self.stats.high_score)
        self.high_score = open("high_score.txt", "r")
        self.high_score = self.high_score.read()
        self.high_score_value = f"HS {self.high_score}"

        # Display the score at the top right of the screen.
        self.high_score_image = self.font.render(self.high_score_value, True, self.text_color)

    def prep_new_high_score(self):
        """Turn the high_score into a rendered image."""
        self.new_high_score = f"NEW HS {self.high_score} !"
        # Display the score at the top right of the screen.
        self.high_score_image = self.font.render(self.new_high_score, True, self.text_color)

    # Level functionality removed
    def prep_level(self):
        """Method kept for compatibility but no longer used"""
        pass

    def show_score(self):
        """Draw score to the screen."""
        # Draw heart icon and health count at the far left
        self.screen.blit(self.heart.image, self.heart_rect)
        self.screen.blit(self.health_count_image, self.health_count_rect)
        
        # Draw high score next to health count
        high_score_x = self.health_count_rect.right + 10
        high_score_rect = self.high_score_image.get_rect(x=high_score_x, y=self.settings.screen_height*0.001)
        self.screen.blit(self.high_score_image, high_score_rect)
        
        # Draw score next to high score
        score_x = high_score_rect.right + 10
        score_rect = self.score_image.get_rect(x=score_x, y=self.settings.screen_height*0.001)
        self.screen.blit(self.score_image, score_rect)
        
        # Position and draw powerup counts in sequence
        # Green powerup
        self.green_powerup_rect.x = score_rect.right + 10
        self.screen.blit(self.green_powerup_image, self.green_powerup_rect)
        
        # Orange powerup
        self.orange_powerup_rect.x = self.green_powerup_rect.right + 10
        self.screen.blit(self.orange_powerup_image, self.orange_powerup_rect)
        
        # Yellow powerup
        self.yellow_powerup_rect.x = self.orange_powerup_rect.right + 10
        self.screen.blit(self.yellow_powerup_image, self.yellow_powerup_rect)

    def check_high_score(self):
        """Check to see if there is a new high score."""
        if self.stats.score > int(self.high_score):
            self.high_score = self.stats.score
            self.high_score = str(self.high_score)

            self.high_score_file = open("high_score.txt", "r+")
            self.high_score_file.write(str(self.stats.score))

            self.prep_new_high_score()

    def prep_hearts(self):
        """Show a single heart icon with the current health count."""
        # Create a single heart icon at the far left edge
        self.heart = Heart(self.si_game)
        self.heart_rect = self.heart.rect
        self.heart_rect.x = self.settings.screen_width * 0.002  # Positioned at extreme left
        self.heart_rect.y = self.settings.screen_width * 0.01
        
        # Create the health count text with minimal spacing
        health_str = str(self.stats.ships_left)
        self.health_count_image = self.font.render(health_str, True, self.text_color)
        self.health_count_rect = self.health_count_image.get_rect()
        self.health_count_rect.left = self.heart_rect.right + 2  # Minimal spacing
        self.health_count_rect.centery = self.heart_rect.centery
            
    def prep_powerup_counts(self):
        """Render text for the three powerup counts."""
        # Calculate base position from score and high score
        # We'll position these dynamically in show_score() based on other elements
        
        # Green powerup count
        green_str = f"G-({self.stats.green_powerups})"
        self.green_powerup_image = self.font.render(green_str, True, self.text_color)
        self.green_powerup_rect = self.green_powerup_image.get_rect()
        # Position will be set in show_score()
        self.green_powerup_rect.y = self.settings.screen_height * 0.001
        
        # Orange powerup count
        orange_str = f"O-({self.stats.orange_powerups})"
        self.orange_powerup_image = self.font.render(orange_str, True, self.text_color)
        self.orange_powerup_rect = self.orange_powerup_image.get_rect()
        # Position will be set in show_score()
        self.orange_powerup_rect.y = self.settings.screen_height * 0.001
        
        # Yellow powerup count
        yellow_str = f"Y-({self.stats.yellow_powerups})"
        self.yellow_powerup_image = self.font.render(yellow_str, True, self.text_color)
        self.yellow_powerup_rect = self.yellow_powerup_image.get_rect()
        # Position will be set in show_score()
        self.yellow_powerup_rect.y = self.settings.screen_height * 0.001
        
    def reset_scoreboard(self):
        """Reset the scoreboard when the game is reset."""
        self.prep_score()
        self.prep_high_score()
        self.prep_hearts()
        self.prep_powerup_counts()
