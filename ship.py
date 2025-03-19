import pygame
from settings import Settings
from strategy import EnhancedAIStrategy


class Ship:
    """A class to manage the ship."""

    def __init__(self, si_game):
        """Initialize the ship and set its starting positon."""
        self.screen = si_game.screen
        self.screen_rect = si_game.screen.get_rect()
        self.settings = Settings()
        self.si_game = si_game  # Store reference to the game
        
        # Initialize the AI strategy
        self.strategy = EnhancedAIStrategy()
        self.ai_controlled = True

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
        # AI movement speed - enhanced for better responsiveness
        self.ai_ship_speed = self.ship_speed * 8.0
        
        # Enhanced AI state tracking
        self.ai_state = 'patrol'  # Possible states: 'dodge', 'engage_boss', 'engage_enemy', 'collect_powerup', 'patrol'
        self.current_target = None  # Store the current target to prevent frequent switching
        self.target_persistence = 15  # Frames to keep targeting the same entity
        self.target_counter = 0  # Counter for target persistence
        self.boss_engaged = False  # Track if we've engaged with a boss to maintain persistence
        
        # Powerup tracking
        self.active_powerup = None  # Current active powerup type
        self.powerup_stacks = 0     # Number of powerup uses remaining
        self.powerup_damage = {
            'laser': 50,
            'spreadgun': 25,
            'default': 10  # Default bullet damage
        }
        
        # Invulnerability tracking
        self.invulnerable = False
        self.invulnerability_start_time = 0
        self.invulnerability_duration = 0
        self.flash_interval = 100  # milliseconds between flashes
        
        # Projectile properties
        self.projectile_speed = self.settings.bullet_speed
        self.projectile_damage = 10  # Default damage

    def update_ai(self, aliens, boss_bullets=None, boss=None, powerups=None):
        """AI-controlled ship movement using the strategy pattern to determine targeting and movement.
        Uses an enhanced state-based approach with predictive targeting and smooth movement.
        Dynamically detects window resolution and adjusts boundaries accordingly."""
        # Check if invulnerability has expired
        if self.invulnerable:
            current_time = pygame.time.get_ticks()
            if current_time - self.invulnerability_start_time >= self.invulnerability_duration:
                self.invulnerable = False
                
        # Get current window dimensions dynamically
        width, height = self.screen.get_size()
        
        # Define enhanced movement constraints and parameters
        max_speed = self.ai_ship_speed
        max_dodge_speed = max_speed * 2.0  # Increased for better evasion
        patrol_speed = max_speed * 0.6     # Slightly faster patrol
        dead_zone = 15  # Reduced pixels threshold for more precise movement
        safe_zone_margin = self.rect.height / 2  # Safe margin for targeting
        
        # Initialize vertical velocity for this frame
        vertical_velocity = 0
        
        # STEP 1: Use strategy to determine action and target with state machine
        action, target = self.strategy.select_target(self, aliens, boss, powerups, boss_bullets)
        
        # Map strategy actions to our enhanced state machine
        state_mapping = {
            'dodge': 'dodge',
            'target_boss': 'engage_boss',
            'target_alien': 'engage_enemy',
            'target_powerup': 'collect_powerup',
            'patrol': 'patrol'
        }
        
        # Convert action to our state machine terminology
        new_state = state_mapping.get(action, 'patrol')
        
        # If boss exists, prioritize boss engagement unless we need to dodge
        if boss is not None and new_state != 'dodge':
            new_state = 'engage_boss'
            target = boss

        
        # Update AI state based on strategy decision
        self.ai_state = new_state
        self.current_target = target
        
        # If targeting boss, mark as engaged
        if new_state == 'engage_boss':
            self.boss_engaged = True
            
            # Check if we have an active powerup to use against the boss
            if self.active_powerup and self.powerup_stacks > 0:
                # Trigger powerup usage in the game
                if hasattr(self.si_game, 'activate_ship_powerup'):
                    self.si_game.activate_ship_powerup(self.active_powerup)
                    self.powerup_stacks -= 1
                    if self.powerup_stacks <= 0:
                        self.active_powerup = None
        
        # STEP 2: Calculate movement based on action and target
        if self.ai_state == 'dodge' and target:
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
            dodge_factor = 0.5  # Increased for more responsive dodging
            vertical_velocity = -diff * dodge_factor
            
            # Clamp velocity to max dodge speed
            if vertical_velocity > max_dodge_speed:
                vertical_velocity = max_dodge_speed
            elif vertical_velocity < -max_dodge_speed:
                vertical_velocity = -max_dodge_speed
                
        elif self.ai_state == 'engage_boss' and target:
            # ENHANCED PREDICTIVE AIMING SYSTEM using strategy's prediction engine
            # Get projectile speed from settings
            projectile_speed = self.settings.bullet_speed
            
            # Use the strategy's prediction engine to calculate the future position
            predicted_x, predicted_y = self.strategy.predict_target_position(target, projectile_speed, self)
            
            # Calculate difference between ship and predicted boss position
            diff = predicted_y - self.rect.centery
            
            # Use a more aggressive targeting: reduced dead zone and higher damping
            boss_dead_zone = 5  # Further reduced for more precise targeting
            
            # Only move if outside the dead zone
            if abs(diff) > boss_dead_zone:
                # Calculate smooth movement with increased damping factor for more aggressive movement
                damping = 0.65  # Further increased for faster alignment with boss
                vertical_velocity = diff * damping
                
                # Clamp velocity to higher max speed for boss targeting
                if vertical_velocity > max_speed * 2.5:
                    vertical_velocity = max_speed * 2.5
                elif vertical_velocity < -max_speed * 2.5:
                    vertical_velocity = -max_speed * 2.5
                    
        elif self.ai_state == 'collect_powerup' and target:
            # Target with safe zone margin to allow for better targeting
            target_y = target.rect.centery
            
            # Calculate difference between ship and target
            diff = target_y - self.rect.centery
            
            # Use a more aggressive targeting for powerups
            powerup_dead_zone = 10  # Smaller dead zone for precise targeting
            
            # Only move if outside the dead zone
            if abs(diff) > powerup_dead_zone:
                # Calculate smooth movement with increased damping factor for more aggressive movement
                damping = 0.55  # Higher damping for faster alignment with powerup
                vertical_velocity = diff * damping
                
                # Clamp velocity to higher max speed for powerup targeting
                if vertical_velocity > max_speed * 1.5:
                    vertical_velocity = max_speed * 1.5
                elif vertical_velocity < -max_speed * 1.5:
                    vertical_velocity = -max_speed * 1.5
                    
        elif self.ai_state == 'engage_enemy' and target:
            # Target with safe zone margin to allow for better targeting
            target_y = target.rect.centery
            
            # Calculate difference between ship and target
            diff = target_y - self.rect.centery
            
            # Only move if outside the dead zone
            if abs(diff) > dead_zone:
                # Calculate smooth movement with damping factor
                damping = 0.45  # Increased for faster alignment
                vertical_velocity = diff * damping
                
                # Clamp velocity to max speed
                if vertical_velocity > max_speed:
                    vertical_velocity = max_speed
                elif vertical_velocity < -max_speed:
                    vertical_velocity = -max_speed
                    
        elif self.ai_state == 'patrol':
            # Move toward the center of the screen
            screen_middle = height * 0.5
            diff = screen_middle - self.rect.centery
            
            # Only move if outside the dead zone
            if abs(diff) > dead_zone:
                # Calculate smooth movement with damping factor
                damping = 0.15  # Increased for slightly more responsive patrol
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
        
        # Activate brief invulnerability after respawn
        self.activate_invulnerability(3000)  # 3 seconds of invulnerability
        
    def activate_invulnerability(self, duration):
        """Activate ship invulnerability for the specified duration (in milliseconds)."""
        self.invulnerable = True
        self.invulnerability_start_time = pygame.time.get_ticks()
        self.invulnerability_duration = duration
        print(f"Ship invulnerable for {duration/1000} seconds")
        
    def set_powerup(self, powerup_type, stacks=3):
        """Set the active powerup and number of uses."""
        self.active_powerup = powerup_type
        self.powerup_stacks = stacks
        print(f"Activated {powerup_type} powerup with {stacks} uses")
        
    def get_powerup_damage(self):
        """Return the damage value for the current powerup."""
        return self.powerup_damage.get(self.active_powerup, self.powerup_damage['default'])
