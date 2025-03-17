import pygame
from settings import Settings


class Ship:
    """A class to manage the ship."""

    def __init__(self, si_game):
        """Initialize the ship and set its starting positon."""
        self.screen = si_game.screen
        self.screen_rect = si_game.screen.get_rect()
        self.settings = Settings()

        # Load the ship image and get its react.
        self.image = pygame.image.load("images/ship_1.png")
        self.image = pygame.transform.scale(self.image, (80*int(self.settings.screen_width*0.0019),
                                            56*int(self.settings.screen_width*0.0019)))
        self.rect = self.image.get_rect()

        # This value is needed later to make ship appear in exact center in every resolution
        # v = 56*int(self.settings.screen_width*0.0019)

        # Start each new ship at the left center of the screen.
        self.rect.center = (int(self.settings.screen_width*0.07), int(self.settings.screen_height*0.5))

        # Movement flag
        self.moving_right = False
        self.moving_left = False
        self.moving_up = False
        self.moving_down = False

        self.ship_speed = self.settings.screen_width*0.005
        # AI movement speed - faster than normal ship speed
        self.ai_ship_speed = self.ship_speed * 3.0
        
        # AI state tracking
        self.ai_state = 'patrol'  # Possible states: 'dodge', 'target_boss', 'target_alien', 'patrol'
        self.current_target = None  # Store the current target to prevent frequent switching
        self.target_persistence = 10  # Frames to keep targeting the same entity
        self.target_counter = 0  # Counter for target persistence

    def update_ai(self, aliens, boss_bullets=None, boss=None):
        """AI-controlled ship movement to dodge boss bullets and target nearest alien or boss.
        Uses a state-based approach with smooth movement to prevent erratic behavior.
        Dynamically detects window resolution and adjusts boundaries accordingly.
        Ship is allowed to move within a safe margin of half its height for accurate targeting."""
        # Get current window dimensions dynamically
        width, height = self.screen.get_size()
        
        # Define movement constraints and parameters
        max_speed = self.ai_ship_speed
        max_dodge_speed = max_speed * 1.5
        patrol_speed = max_speed * 0.5
        dead_zone = 20  # Increased pixels threshold to prevent jitter
        safe_zone_margin = self.rect.height / 2  # Safe margin for targeting
        
        # Initialize vertical velocity for this frame
        vertical_velocity = 0
        
        # STEP 1: Determine AI state based on environment
        
        # Check for incoming boss bullets (highest priority)
        if boss_bullets:
            danger_zone_x = width * 0.3
            for bullet in boss_bullets.sprites():
                # Check if bullet is in front of the ship and within danger zone
                if bullet.rect.x > self.rect.x and bullet.rect.x < self.rect.x + danger_zone_x:
                    # Check if bullet is on a collision course with the ship (y-axis)
                    bullet_y_range = range(bullet.rect.top - 20, bullet.rect.bottom + 20)
                    
                    if self.rect.centery in bullet_y_range:
                        self.ai_state = 'dodge'
                        # Calculate distance from bullet center to determine dodge direction
                        bullet_center_y = bullet.rect.centery
                        # Negative difference means bullet is above ship, positive means below
                        diff = self.rect.centery - bullet_center_y
                        
                        # If difference is small, choose a preferred dodge direction
                        if abs(diff) < 30:
                            # Prefer to dodge upward if there's room, otherwise downward
                            if self.rect.top > max_dodge_speed * 2:
                                diff = -50  # Force upward dodge
                            else:
                                diff = 50   # Force downward dodge
                        
                        # Calculate smooth dodge velocity (opposite to the bullet direction)
                        dodge_factor = 0.3  # Higher value for more responsive dodging
                        vertical_velocity = -diff * dodge_factor
                        
                        # Clamp velocity to max dodge speed
                        if vertical_velocity > max_dodge_speed:
                            vertical_velocity = max_dodge_speed
                        elif vertical_velocity < -max_dodge_speed:
                            vertical_velocity = -max_dodge_speed
                        
                        # Once we've found a bullet to dodge, no need to check others
                        break
        
        # If not dodging, check for boss or aliens to target
        if self.ai_state != 'dodge':
            # Target boss if present (second priority)
            if boss:
                self.ai_state = 'target_boss'
                # Target with safe zone margin to allow for better targeting
                target_y = boss.rect.centery
                
                # Calculate difference between ship and target
                diff = target_y - self.rect.centery
                
                # Only move if outside the dead zone
                if abs(diff) > dead_zone:
                    # Calculate smooth movement with damping factor
                    damping = 0.15  # Lower value for smoother, slower approach
                    vertical_velocity = diff * damping
                    
                    # Clamp velocity to max speed
                    if vertical_velocity > max_speed:
                        vertical_velocity = max_speed
                    elif vertical_velocity < -max_speed:
                        vertical_velocity = -max_speed
            
            # If no boss, target nearest alien (third priority)
            elif aliens:
                # Find the nearest alien based on x-position (closest from the left)
                nearest_alien = None
                nearest_distance = float('inf')
                
                for alien in aliens.sprites():
                    # Focus on aliens that are ahead of the ship
                    if alien.rect.x > self.rect.x:
                        distance = alien.rect.x - self.rect.x
                        if distance < nearest_distance:
                            nearest_distance = distance
                            nearest_alien = alien
                
                # If we found a target alien, move toward its y-position
                if nearest_alien:
                    self.ai_state = 'target_alien'
                    # Target with safe zone margin to allow for better targeting
                    target_y = nearest_alien.rect.centery
                    
                    # Calculate difference between ship and target
                    diff = target_y - self.rect.centery
                    
                    # Only move if outside the dead zone
                    if abs(diff) > dead_zone:
                        # Calculate smooth movement with damping factor
                        damping = 0.12  # Lower value for smoother approach
                        vertical_velocity = diff * damping
                        
                        # Clamp velocity to max speed
                        if vertical_velocity > max_speed:
                            vertical_velocity = max_speed
                        elif vertical_velocity < -max_speed:
                            vertical_velocity = -max_speed
                else:
                    self.ai_state = 'patrol'
            else:
                self.ai_state = 'patrol'
        
        # If no targets or in patrol state, move toward the center of the screen
        if self.ai_state == 'patrol':
            screen_middle = height * 0.5
            diff = screen_middle - self.rect.centery
            
            # Only move if outside the dead zone
            if abs(diff) > dead_zone:
                # Calculate smooth movement with damping factor
                damping = 0.08  # Lower value for even smoother patrol
                vertical_velocity = diff * damping
                
                # Clamp velocity to patrol speed (slower than targeting)
                if vertical_velocity > patrol_speed:
                    vertical_velocity = patrol_speed
                elif vertical_velocity < -patrol_speed:
                    vertical_velocity = -patrol_speed
        
        # STEP 2: Apply the calculated velocity to the ship's position
        
        # Check boundaries before applying movement
        new_y = self.rect.y + vertical_velocity
        
        # Ensure the ship stays within screen boundaries
        # Use dynamic height to ensure ship is always fully visible
        if new_y < 0:
            new_y = 0
        elif new_y + self.rect.height > height:
            new_y = height - self.rect.height
        
        # Update the ship's position
        self.rect.y = new_y

    def update(self):
        """Update ship's position based on the movement flag.
        Note: This method is kept for compatibility but will be bypassed
        in favor of AI control in the main game loop.
        The AI control uses the update_ai method with state-based smooth movement."""
        # The AI control will override these movements, but we keep the method
        # for backward compatibility
        if self.moving_right and self.rect.x < self.settings.screen_width*0.85:
            self.rect.x += self.ship_speed
        elif self.moving_left and self.rect.x > 0:
            self.rect.x -= self.ship_speed
        elif self.moving_up and self.rect.y > 0:
            self.rect.y -= self.ship_speed
        elif self.moving_down and self.rect.y < self.settings.screen_height*0.84:
            self.rect.y += self.ship_speed

    def blitme(self):
        """Draw ship at its current location."""

        # Little system that will make sure that ship will be scaled with resolution
        self.screen.blit(self.image, self.rect)

    def center_ship(self):
        """Center the ship on the screen."""
        self.rect.center = (int(self.settings.screen_width*0.07), int(self.settings.screen_height*0.5))
        self.x = float(self.rect.x)
