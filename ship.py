import pygame
from settings import Settings
from strategy import AggressiveStrategy


class Ship:
    """A class to manage the ship."""

    def __init__(self, si_game):
        """Initialize the ship and set its starting positon."""
        self.screen = si_game.screen
        self.screen_rect = si_game.screen.get_rect()
        self.settings = Settings()
        
        # Initialize the AI strategy
        self.strategy = AggressiveStrategy()

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
        self.ai_ship_speed = self.ship_speed * 6.0
        
        # AI state tracking
        self.ai_state = 'patrol'  # Possible states: 'dodge', 'target_boss', 'target_alien', 'target_powerup', 'patrol'
        self.current_target = None  # Store the current target to prevent frequent switching
        self.target_persistence = 10  # Frames to keep targeting the same entity
        self.target_counter = 0  # Counter for target persistence
        self.boss_engaged = False  # Track if we've engaged with a boss to maintain persistence
        
        # Invulnerability tracking
        self.invulnerable = False
        self.invulnerability_start_time = 0
        self.invulnerability_duration = 0
        self.flash_interval = 100  # milliseconds between flashes

    def update_ai(self, aliens, boss_bullets=None, boss=None, powerups=None):
        """AI-controlled ship movement using the strategy pattern to determine targeting and movement.
        Uses a state-based approach with smooth movement to prevent erratic behavior.
        Dynamically detects window resolution and adjusts boundaries accordingly."""
        # Check if invulnerability has expired
        if self.invulnerable:
            current_time = pygame.time.get_ticks()
            if current_time - self.invulnerability_start_time >= self.invulnerability_duration:
                self.invulnerable = False
                
        # Get current window dimensions dynamically
        width, height = self.screen.get_size()
        
        # Define movement constraints and parameters
        max_speed = self.ai_ship_speed
        max_dodge_speed = max_speed * 1.5
        patrol_speed = max_speed * 0.5
        dead_zone = 20  # Pixels threshold to prevent jitter
        safe_zone_margin = self.rect.height / 2  # Safe margin for targeting
        
        # Initialize vertical velocity for this frame
        vertical_velocity = 0
        
        # STEP 1: Use strategy to determine action and target
        action, target = self.strategy.select_target(self, aliens, boss, powerups, boss_bullets)
        
        # Update AI state based on strategy decision
        self.ai_state = action
        
        # If targeting boss, mark as engaged
        if action == 'target_boss':
            self.boss_engaged = True
        
        # STEP 2: Calculate movement based on action and target
        if action == 'dodge' and target:
            # Calculate distance from bullet center to determine dodge direction
            bullet_center_y = target.rect.centery
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
                
        elif action == 'target_boss' and target:
            # Target with safe zone margin to allow for better targeting
            target_y = target.rect.centery
            
            # Calculate difference between ship and target
            diff = target_y - self.rect.centery
            
            # Use a more aggressive targeting: reduced dead zone and higher damping
            boss_dead_zone = 10  # Reduced for more precise targeting
            
            # Only move if outside the dead zone
            if abs(diff) > boss_dead_zone:
                # Calculate smooth movement with increased damping factor for more aggressive movement
                damping = 0.50  # Increased for faster alignment with boss
                vertical_velocity = diff * damping
                
                # Clamp velocity to higher max speed for boss targeting
                if vertical_velocity > max_speed * 2.0:
                    vertical_velocity = max_speed * 2.0
                elif vertical_velocity < -max_speed * 2.0:
                    vertical_velocity = -max_speed * 2.0
                    
        elif action == 'target_powerup' and target:
            # Target with safe zone margin to allow for better targeting
            target_y = target.rect.centery
            
            # Calculate difference between ship and target
            diff = target_y - self.rect.centery
            
            # Use a more aggressive targeting for powerups
            powerup_dead_zone = 15  # Smaller dead zone for precise targeting
            
            # Only move if outside the dead zone
            if abs(diff) > powerup_dead_zone:
                # Calculate smooth movement with increased damping factor for more aggressive movement
                damping = 0.40  # Higher damping for faster alignment with powerup
                vertical_velocity = diff * damping
                
                # Clamp velocity to higher max speed for powerup targeting
                if vertical_velocity > max_speed * 1.5:
                    vertical_velocity = max_speed * 1.5
                elif vertical_velocity < -max_speed * 1.5:
                    vertical_velocity = -max_speed * 1.5
                    
        elif action == 'target_alien' and target:
            # Target with safe zone margin to allow for better targeting
            target_y = target.rect.centery
            
            # Calculate difference between ship and target
            diff = target_y - self.rect.centery
            
            # Only move if outside the dead zone
            if abs(diff) > dead_zone:
                # Calculate smooth movement with damping factor
                damping = 0.30  # For faster alignment
                vertical_velocity = diff * damping
                
                # Clamp velocity to max speed
                if vertical_velocity > max_speed:
                    vertical_velocity = max_speed
                elif vertical_velocity < -max_speed:
                    vertical_velocity = -max_speed
                    
        elif action == 'patrol':
            # Move toward the center of the screen
            screen_middle = height * 0.5
            diff = screen_middle - self.rect.centery
            
            # Only move if outside the dead zone
            if abs(diff) > dead_zone:
                # Calculate smooth movement with damping factor
                damping = 0.10  # For slightly more responsive patrol
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
            
        # Check if invulnerability has expired
        if self.invulnerable:
            current_time = pygame.time.get_ticks()
            if current_time - self.invulnerability_start_time > self.invulnerability_duration:
                self.invulnerable = False

    def blitme(self):
        """Draw ship at its current location."""
        
        # If ship is invulnerable, create a flashing effect and draw a yellow circle
        if self.invulnerable:
            # Draw yellow circle around the ship when invulnerable
            circle_center = self.rect.center
            circle_radius = 24
            pygame.draw.circle(self.screen, (255, 255, 0), circle_center, circle_radius, 2)
            
            current_time = pygame.time.get_ticks()
            if (current_time - self.invulnerability_start_time) % (self.flash_interval * 2) < self.flash_interval:
                # Create a semi-transparent version of the ship for flashing effect
                alpha_image = self.image.copy()
                alpha_image.set_alpha(128)  # 50% transparency
                self.screen.blit(alpha_image, self.rect)
            else:
                # Draw normal ship
                self.screen.blit(self.image, self.rect)
        else:
            # Draw normal ship
            self.screen.blit(self.image, self.rect)

    def center_ship(self):
        """Center the ship on the screen."""
        self.rect.center = (int(self.settings.screen_width*0.07), int(self.settings.screen_height*0.5))
        self.x = float(self.rect.x)
        # Do not reset AI state to maintain aggressive targeting after respawn
        # This allows the ship to continue targeting the boss after death
        
    def activate_invulnerability(self, duration):
        """Activate ship invulnerability for the specified duration (in milliseconds)."""
        self.invulnerable = True
        self.invulnerability_start_time = pygame.time.get_ticks()
        self.invulnerability_duration = duration
        print(f"Ship invulnerable for {duration/1000} seconds")
