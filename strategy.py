from abc import ABC, abstractmethod
import math
from typing import Tuple, List, Optional, Any

class AIStrategy(ABC):
    """
    Abstract base class for AI targeting strategies.
    All concrete strategies must implement the select_target method.
    """
    
    @abstractmethod
    def select_target(self, ship, aliens, boss, powerups, boss_bullets):
        """
        Select a target for the AI ship based on the current game state.
        
        Args:
            ship: The AI ship object
            aliens: List of alien objects
            boss: Boss object or None
            powerups: List of powerup objects
            boss_bullets: List of boss bullet objects
            
        Returns:
            tuple: (action, target) where action is a string describing the action
                  and target is the object to target (or None)
        """
        pass


class AggressiveStrategy(AIStrategy):
    """
    An aggressive AI strategy that prioritizes:
    1. Dodging bullets in danger zone
    2. Avoiding dangerously close enemies
    3. Targeting boss with predictive targeting
    4. Collecting powerups based on value and proximity
    5. Targeting nearest alien
    6. Patrolling (centering) when no targets
    """
    
    def select_target(self, ship, aliens, boss, powerups, boss_bullets):
        """
        Implements the targeting logic for the aggressive strategy with enhanced
        multi-target awareness and predictive targeting.
        
        Args:
            ship: The AI ship object
            aliens: List of alien objects
            boss: Boss object or None
            powerups: List of powerup objects
            boss_bullets: List of boss bullet objects
            
        Returns:
            tuple: (action, target) where action is a string describing the action
                  and target is the object to target (or None)
        """
        # PRIORITY 1: Immediate threat avoidance - always check regardless of current engagement
        
        # Check for bullets in danger zone
        if boss_bullets:
            dangerous_bullet = self._find_dangerous_bullet(ship, boss_bullets)
            if dangerous_bullet:
                return ('dodge', dangerous_bullet)
        
        # Check for dangerously close enemies
        dangerous_enemy = self._find_dangerous_enemy(ship, aliens)
        if dangerous_enemy:
            return ('dodge', dangerous_enemy)
        
        # PRIORITY 2: Strategic targeting based on game state
        
        # Target boss if present - high priority after immediate threats
        # Uses predictive targeting for more accurate engagement
        if boss:
            # Even while targeting boss, check for high-value powerups in close proximity
            high_value_powerup = self._find_high_value_powerup(ship, powerups)
            if high_value_powerup and self._is_easily_reachable(ship, high_value_powerup):
                return ('target_powerup', high_value_powerup)
                
            # Otherwise focus on the boss with predictive targeting
            return ('target_boss', boss)
        
        # PRIORITY 3: Resource collection and normal enemy engagement
        
        # Target valuable powerups
        if powerups:
            nearest_powerup = self._find_nearest_powerup(ship, powerups)
            if nearest_powerup:
                return ('target_powerup', nearest_powerup)
        
        # Target nearest alien
        if aliens:
            nearest_alien = self._find_nearest_alien(ship, aliens)
            if nearest_alien:
                return ('target_alien', nearest_alien)
        
        # Default: patrol (center the ship)
        return ('patrol', None)
    
    def _find_dangerous_bullet(self, ship, bullets):
        """
        Find the most dangerous bullet that threatens the ship.
        
        Args:
            ship: The AI ship object
            bullets: List of bullet objects
            
        Returns:
            The most dangerous bullet or None
        """
        # Define danger zone parameters
        horizontal_danger = 250  # pixels ahead of ship (increased from 200)
        vertical_range = 70      # pixels above/below ship (increased from 50)
        
        # Get ship position and dimensions
        if hasattr(ship, 'rect'):
            ship_x = ship.rect.centerx
            ship_y = ship.rect.centery
            ship_height = ship.rect.height
        else:
            ship_x = ship.x
            ship_y = ship.y
            ship_height = getattr(ship, 'height', 30)  # Default height if not available
        
        # Adjust vertical range based on ship size
        vertical_range = max(vertical_range, ship_height * 1.5)
        
        dangerous_bullets = []
        for bullet in bullets:
            # Get bullet position
            if hasattr(bullet, 'rect'):
                bullet_x = bullet.rect.centerx
                bullet_y = bullet.rect.centery
            else:
                bullet_x = bullet.x
                bullet_y = bullet.y
                
            # Get bullet velocity if available
            bullet_vel_x, bullet_vel_y = 0, 0
            if hasattr(bullet, 'velocity'):
                if isinstance(bullet.velocity, tuple):
                    bullet_vel_x, bullet_vel_y = bullet.velocity
                elif hasattr(bullet.velocity, 'x') and hasattr(bullet.velocity, 'y'):
                    bullet_vel_x, bullet_vel_y = bullet.velocity.x, bullet.velocity.y
            
            # Calculate time to potential collision
            # If bullet is moving toward ship
            if bullet_vel_x < 0:  # Moving left (toward ship)
                time_to_collision = (ship_x - bullet_x) / abs(bullet_vel_x) if bullet_vel_x != 0 else float('inf')
            else:
                # If bullet is ahead of ship but not moving toward it
                if bullet_x > ship_x:
                    time_to_collision = float('inf')  # Will never collide
                else:
                    time_to_collision = float('inf')  # Will never collide
            
            # Check if bullet is ahead of ship and within horizontal danger zone
            if bullet_x > ship_x and bullet_x - ship_x < horizontal_danger:
                # Check if bullet is within vertical range of ship
                if abs(bullet_y - ship_y) < vertical_range:
                    # Calculate danger score based on distance and trajectory
                    distance = self._distance(ship, bullet)
                    
                    # Bullets on direct collision course are more dangerous
                    trajectory_factor = 1.0
                    if bullet_vel_y != 0:
                        # Calculate where bullet will be horizontally when it reaches ship's x position
                        time_to_reach_ship_x = (ship_x - bullet_x) / bullet_vel_x if bullet_vel_x != 0 else float('inf')
                        if time_to_reach_ship_x > 0:  # Only if bullet will reach ship's x in the future
                            projected_y = bullet_y + bullet_vel_y * time_to_reach_ship_x
                            # If projected position is close to ship's y, it's on collision course
                            if abs(projected_y - ship_y) < ship_height:
                                trajectory_factor = 0.5  # Lower score = more dangerous
                    
                    danger_score = distance * trajectory_factor
                    dangerous_bullets.append((bullet, danger_score))
        
        # Return the most dangerous bullet
        if dangerous_bullets:
            dangerous_bullets.sort(key=lambda x: x[1])  # Sort by danger score
            return dangerous_bullets[0][0]
        
        return None
    
    def _find_dangerous_enemy(self, ship, aliens):
        """
        Find enemies that are dangerously close to the ship.
        
        Args:
            ship: The AI ship object
            aliens: List of alien objects
            
        Returns:
            The most dangerous alien or None
        """
        if not aliens:
            return None
            
        dangerous_aliens = []
        horizontal_danger = 70  # pixels ahead of ship
        vertical_danger = 50    # pixels above/below ship
        
        for alien in aliens:
            if hasattr(alien, 'rect') and hasattr(ship, 'rect'):
                # Check if alien is very close horizontally and within vertical range
                if (alien.rect.left - ship.rect.right < horizontal_danger and 
                    abs(alien.rect.centery - ship.rect.centery) < vertical_danger):
                    dangerous_aliens.append((alien, self._distance(ship, alien)))
        
        if dangerous_aliens:
            dangerous_aliens.sort(key=lambda x: x[1])  # Sort by distance
            return dangerous_aliens[0][0]
            
        return None
    
    def _find_nearest_powerup(self, ship, powerups):
        """
        Find the nearest powerup, prioritizing those ahead of the ship.
        
        Args:
            ship: The AI ship object
            powerups: List of powerup objects
            
        Returns:
            The best powerup to target or None
        """
        if not powerups:
            return None
            
        # Prioritize powerups ahead of the ship
        ahead_powerups = []
        other_powerups = []
        
        for powerup in powerups:
            if self._is_ahead(ship, powerup):
                ahead_powerups.append((powerup, self._distance(ship, powerup)))
            else:
                other_powerups.append((powerup, self._distance(ship, powerup)))
        
        # First check powerups ahead
        if ahead_powerups:
            ahead_powerups.sort(key=lambda x: x[1])  # Sort by distance
            return ahead_powerups[0][0]
        
        # If no powerups ahead, check others
        if other_powerups:
            other_powerups.sort(key=lambda x: x[1])  # Sort by distance
            return other_powerups[0][0]
        
        return None
    
    def _find_high_value_powerup(self, ship, powerups):
        """
        Find high-value powerups that are worth deviating from boss targeting.
        
        Args:
            ship: The AI ship object
            powerups: List of powerup objects
            
        Returns:
            A high-value powerup or None
        """
        if not powerups:
            return None
            
        # In a real implementation, we would check powerup type/value
        # For now, we'll just prioritize closer powerups
        close_powerups = []
        for powerup in powerups:
            distance = self._distance(ship, powerup)
            if distance < 150:  # Only consider powerups within reasonable range
                close_powerups.append((powerup, distance))
        
        if close_powerups:
            close_powerups.sort(key=lambda x: x[1])  # Sort by distance
            return close_powerups[0][0]
            
        return None
    
    def _is_ahead(self, ship, obj):
        """
        Check if an object is ahead of the ship.
        
        Args:
            ship: The AI ship object
            obj: The object to check
            
        Returns:
            bool: True if the object is ahead of the ship
        """
        # Get ship x position
        if hasattr(ship, 'rect'):
            ship_x = ship.rect.centerx
        else:
            ship_x = ship.x
            
        # Get object x position
        if hasattr(obj, 'rect'):
            obj_x = obj.rect.centerx
        else:
            obj_x = obj.x
            
        return obj_x > ship_x
    
    def _is_easily_reachable(self, ship, obj):
        """
        Determine if an object is easily reachable without significant deviation.
        
        Args:
            ship: The AI ship object
            obj: The object to check
            
        Returns:
            bool: True if the object is easily reachable
        """
        distance = self._distance(ship, obj)
        
        # Get ship and object positions
        if hasattr(ship, 'rect'):
            ship_y = ship.rect.centery
        else:
            ship_y = ship.y
            
        if hasattr(obj, 'rect'):
            obj_y = obj.rect.centery
        else:
            obj_y = obj.y
            
        # If object is close and doesn't require much vertical movement
        return distance < 120 and abs(ship_y - obj_y) < 60
    
    def _find_nearest_alien(self, ship, aliens):
        """
        Find the nearest alien to the ship, with preference for aliens ahead of the ship.
        
        Args:
            ship: The AI ship object
            aliens: List of alien objects
            
        Returns:
            The nearest alien or None
        """
        if not aliens:
            return None
        
        # Get ship position
        if hasattr(ship, 'rect'):
            ship_x, ship_y = ship.rect.centerx, ship.rect.centery
        else:
            ship_x, ship_y = ship.x, ship.y
        
        scored_aliens = []
        
        for alien in aliens:
            # Get alien position
            if hasattr(alien, 'rect'):
                alien_x, alien_y = alien.rect.centerx, alien.rect.centery
            else:
                alien_x, alien_y = alien.x, alien.y
                
            # Calculate distance
            dist = self._distance(ship, alien)
            
            # Calculate angle to determine if alien is ahead
            # Prefer aliens ahead of the ship (positive x direction)
            position_score = 1.0
            if alien_x > ship_x:  # Ahead of ship
                position_score = 0.7  # Lower score is better
            else:
                position_score = 1.5  # Higher score for aliens behind (less desirable)
                
            # Final score combines distance and position
            final_score = dist * position_score
            
            scored_aliens.append((alien, final_score))
        
        # Sort by score (lower is better)
        scored_aliens.sort(key=lambda x: x[1])
        
        return scored_aliens[0][0] if scored_aliens else None
        
    def predict_target_position(self, target, projectile_speed, ship=None):
        """
        Predict the future position of a target based on its velocity and direction.
        
        Args:
            target: The target object (boss, alien, etc.)
            projectile_speed: Speed of the projectile that would be fired
            ship: Optional ship object for reference position
            
        Returns:
            tuple: (x, y) predicted position
        """
        # If target is boss, return exact center coordinates for 100% accuracy
        if hasattr(target, 'is_boss') and target.is_boss:
            return (target.rect.centerx, target.rect.centery)
            
        # Get current target position
        if hasattr(target, 'rect'):
            current_x, current_y = target.rect.centerx, target.rect.centery
        else:
            current_x, current_y = target.x, target.y
            
        # Get target velocity if available
        target_vx, target_vy = 0, 0
        if hasattr(target, 'velocity'):
            target_vx = target.velocity[0] if isinstance(target.velocity, (list, tuple)) else 0
            target_vy = target.velocity[1] if isinstance(target.velocity, (list, tuple)) else 0
        elif hasattr(target, 'vx') and hasattr(target, 'vy'):
            target_vx, target_vy = target.vx, target.vy
            
        # If we have a ship reference, calculate time to intercept
        if ship:
            if hasattr(ship, 'rect'):
                ship_x, ship_y = ship.rect.centerx, ship.rect.centery
            else:
                ship_x, ship_y = ship.x, ship.y
                
            # Calculate distance
            distance = math.sqrt((current_x - ship_x)**2 + (current_y - ship_y)**2)
            
            # Estimate time for projectile to reach target's current position
            time_to_target = distance / projectile_speed if projectile_speed > 0 else 0
        else:
            # Default time prediction if no ship reference
            time_to_target = 0.5  # seconds
            
        # Predict future position based on current velocity and time
        predicted_x = current_x + (target_vx * time_to_target)
        predicted_y = current_y + (target_vy * time_to_target)
        
        # Add some intelligence for boss movement patterns
        if hasattr(target, 'is_boss') and target.is_boss:
            # If boss is moving up or down rapidly, predict continued movement in that direction
            if abs(target_vy) > 2:
                predicted_y += target_vy * 0.5  # Additional prediction factor
                
            # If boss has a pattern attribute, use it for better prediction
            if hasattr(target, 'pattern'):
                if target.pattern == 'zigzag':
                    # For zigzag patterns, predict reversal point
                    if abs(target_vy) < 0.5 and target_y > 400:
                        predicted_y -= 50  # Predict upward movement at bottom
                    elif abs(target_vy) < 0.5 and target_y < 100:
                        predicted_y += 50  # Predict downward movement at top
        
        return (predicted_x, predicted_y)
    
    def predict_target_position(self, target, projectile_speed, ship=None):
        """
        Predict the future position of a target based on its velocity and direction.
        
        Args:
            target: The target object (boss, alien, etc.)
            projectile_speed: Speed of the projectile that would be fired
            ship: Optional ship object for reference position
            
        Returns:
            tuple: (x, y) predicted position
        """
        # If target is boss, return exact center coordinates for 100% accuracy
        if hasattr(target, 'is_boss') and target.is_boss:
            return (target.rect.centerx, target.rect.centery)
        # Get current target position
        if hasattr(target, 'rect'):
            current_x, current_y = target.rect.centerx, target.rect.centery
        else:
            current_x, current_y = target.x, target.y
            
        # Get target velocity if available
        target_vx, target_vy = 0, 0
        if hasattr(target, 'velocity'):
            target_vx = target.velocity[0] if isinstance(target.velocity, (list, tuple)) else 0
            target_vy = target.velocity[1] if isinstance(target.velocity, (list, tuple)) else 0
        elif hasattr(target, 'vx') and hasattr(target, 'vy'):
            target_vx, target_vy = target.vx, target.vy
            
        # If we have a ship reference, calculate time to intercept
        if ship:
            if hasattr(ship, 'rect'):
                ship_x, ship_y = ship.rect.centerx, ship.rect.centery
            else:
                ship_x, ship_y = ship.x, ship.y
                
            # Calculate distance
            distance = math.sqrt((current_x - ship_x)**2 + (current_y - ship_y)**2)
            
            # Estimate time for projectile to reach target's current position
            time_to_target = distance / projectile_speed if projectile_speed > 0 else 0
        else:
            # Default time prediction if no ship reference
            time_to_target = 0.5  # seconds
            
        # Predict future position based on current velocity and time
        predicted_x = current_x + (target_vx * time_to_target)
        predicted_y = current_y + (target_vy * time_to_target)
        
        # Add some intelligence for boss movement patterns
        if hasattr(target, 'is_boss') and target.is_boss:
            # If boss is moving up or down rapidly, predict continued movement in that direction
            if abs(target_vy) > 2:
                predicted_y += target_vy * 0.5  # Additional prediction factor
                
            # If boss has a pattern attribute, use it for better prediction
            if hasattr(target, 'pattern'):
                if target.pattern == 'zigzag':
                    # For zigzag patterns, predict reversal point
                    if abs(target_vy) < 0.5 and target_y > 400:
                        predicted_y -= 50  # Predict upward movement at bottom
                    elif abs(target_vy) < 0.5 and target_y < 100:
                        predicted_y += 50  # Predict downward movement at top
        
        return (predicted_x, predicted_y)
    
    def _distance(self, obj1, obj2):
        """
        Calculate Euclidean distance between two objects.
        
        Args:
            obj1: First object with x, y attributes or rect attribute
            obj2: Second object with x, y attributes or rect attribute
            
        Returns:
            float: The distance between the objects
        """
        # Check if obj1 has a rect attribute, otherwise use direct attributes
        if hasattr(obj1, 'rect'):
            x1, y1 = obj1.rect.centerx, obj1.rect.centery
        else:
            x1, y1 = obj1.x, obj1.y
            
        # Check if obj2 has a rect attribute, otherwise use direct attributes
        if hasattr(obj2, 'rect'):
            x2, y2 = obj2.rect.centerx, obj2.rect.centery
        else:
            x2, y2 = obj2.x, obj2.y
            
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    

class EnhancedAIStrategy(AIStrategy):
    """
    An enhanced AI strategy that uses a simulated LiDAR detection system (1500 pixel range)
    and implements refined attack/defense priority hierarchies.
    
    This strategy implements a prioritized decision hierarchy:
    1. Dodge dangerous boss bullets or closely approaching aliens (defense priority)
    2. Target boss if within range, with check for offensive powerups during boss fights
    3. Collect powerups (higher priority than normal enemies)
    4. Target normal enemies if no boss is present and no powerups available
    5. Patrol when no targets are available in range
    
    The AI only uses offensive powerups (laser, spread gun) during boss fights and
    activates invulnerability when enemies or boss bullets are too near.
    """
    
    def _filter_within_range(self, ship, objects, max_range=1500):
        """
        Filter a list of objects to include only those within the specified range from the ship.
        
        Args:
            ship: The AI ship object
            objects: List of game objects to filter
            max_range: Maximum distance in pixels (default: 1500)
            
        Returns:
            list: Filtered list of objects within the specified range
        """
        if not objects:
            return []
            
        return [obj for obj in objects if self._distance(ship, obj) <= max_range]
    
    def _is_threatening(self, ship, obj):
        """
        Determine if an object is close enough to be considered a threat.
        
        Args:
            ship: The AI ship object
            obj: The object to check (bullet, enemy, etc.)
            
        Returns:
            bool: True if the object is within the threat threshold (150 pixels)
        """
        if not obj:
            return False
            
        # Threat threshold of 150 pixels
        return self._distance(ship, obj) < 150
    
    def _find_high_value_offensive_powerup(self, ship, powerups):
        """
        Find offensive powerups (green or orange) that are useful during boss fights.
        
        Args:
            ship: The AI ship object
            powerups: List of powerup objects
            
        Returns:
            The best offensive powerup to target or None
        """
        if not powerups:
            return None
            
        # Filter for offensive powerups (green = laser, orange = spread gun)
        offensive_powerups = []
        for powerup in powerups:
            # Check if powerup has a type attribute
            if hasattr(powerup, 'type'):
                # Green = laser, Orange = spread gun
                if powerup.type in ['green', 'orange']:
                    distance = self._distance(ship, powerup)
                    if distance < 150:  # Only consider powerups within reasonable range
                        offensive_powerups.append((powerup, distance))
        
        if offensive_powerups:
            offensive_powerups.sort(key=lambda x: x[1])  # Sort by distance
            return offensive_powerups[0][0]
            
        return None
    
    def select_target(self, ship, aliens, boss, powerups, boss_bullets):
        """
        Implements the targeting logic for the enhanced strategy with range-limited
        target detection and prioritized decision making.
        
        Args:
            ship: The AI ship object
            aliens: List of alien objects
            boss: Boss object or None
            powerups: List of powerup objects
            boss_bullets: List of boss bullet objects
            
        Returns:
            tuple: (action, target) where action is a string describing the action
                  and target is the object to target (or None)
                  
        Note:
            Powerups are prioritized over normal enemies in this implementation.
        """
        # Filter all objects to consider only those within detection range (1500 pixels)
        # This simulates a LiDAR-like detection system
        filtered_aliens = self._filter_within_range(ship, aliens)
        filtered_powerups = self._filter_within_range(ship, powerups)
        filtered_boss_bullets = self._filter_within_range(ship, boss_bullets)
        
        # Check if boss is within range
        filtered_boss = None
        if boss and self._distance(ship, boss) <= 1500:
            filtered_boss = boss
        
        # PRIORITY 1: Defense - Immediate threat avoidance
        
        # Check for threatening boss bullets in danger zone
        if filtered_boss_bullets:
            dangerous_bullet = self._find_dangerous_bullet(ship, filtered_boss_bullets)
            if dangerous_bullet and self._is_threatening(ship, dangerous_bullet):
                return ('dodge', dangerous_bullet)
        
        # Check for dangerously close enemies
        if filtered_aliens:
            dangerous_enemy = self._find_dangerous_enemy(ship, filtered_aliens)
            if dangerous_enemy and self._is_threatening(ship, dangerous_enemy):
                return ('dodge', dangerous_enemy)
        
        # PRIORITY 2: Attack - Strategic targeting based on game state
        
        # Target boss if present and within range
        if filtered_boss:
            # During boss fights, look for offensive powerups (laser, spread gun)
            if filtered_powerups:
                offensive_powerup = self._find_high_value_offensive_powerup(ship, filtered_powerups)
                if offensive_powerup and self._is_easily_reachable(ship, offensive_powerup):
                    return ('target_powerup', offensive_powerup)
            
            # Otherwise focus on the boss
            return ('target_boss', filtered_boss)
        
        # PRIORITY 3: Resource collection (higher priority than normal enemies)
        
        # Target powerups if available
        if filtered_powerups:
            nearest_powerup = self._find_nearest_powerup(ship, filtered_powerups)
            if nearest_powerup:
                return ('target_powerup', nearest_powerup)
        
        # PRIORITY 4: Normal enemy engagement (when no boss is present and no powerups available)
        
        # Target nearest alien if available
        if filtered_aliens:
            nearest_alien = self._find_nearest_alien(ship, filtered_aliens)
            if nearest_alien:
                return ('target_alien', nearest_alien)
        
        # Default: patrol (center the ship) when no valid targets in range
        return ('patrol', None)
    
    def _distance(self, obj1, obj2):
        """Calculate Euclidean distance between two objects."""
        if hasattr(obj1, 'rect'):
            x1, y1 = obj1.rect.centerx, obj1.rect.centery
        else:
            x1, y1 = obj1.x, obj1.y
        if hasattr(obj2, 'rect'):
            x2, y2 = obj2.rect.centerx, obj2.rect.centery
        else:
            x2, y2 = obj2.x, obj2.y
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    
    def predict_target_position(self, target, projectile_speed, ship=None):
        """
        Predict the future position of a target based on its velocity and direction.
        
        Args:
            target: The target object (boss, alien, etc.)
            projectile_speed: Speed of the projectile that would be fired
            ship: Optional ship object for reference position
            
        Returns:
            tuple: (x, y) predicted position
        """
        # If target is boss, return exact center coordinates for 100% accuracy
        if hasattr(target, 'is_boss') and target.is_boss:
            return (target.rect.centerx, target.rect.centery)
            
        # Get current target position
        if hasattr(target, 'rect'):
            current_x, current_y = target.rect.centerx, target.rect.centery
        else:
            current_x, current_y = target.x, target.y
            
        # Get target velocity if available
        target_vx, target_vy = 0, 0
        if hasattr(target, 'velocity'):
            target_vx = target.velocity[0] if isinstance(target.velocity, (list, tuple)) else 0
            target_vy = target.velocity[1] if isinstance(target.velocity, (list, tuple)) else 0
        elif hasattr(target, 'vx') and hasattr(target, 'vy'):
            target_vx, target_vy = target.vx, target.vy
            
        # If we have a ship reference, calculate time to intercept
        if ship:
            if hasattr(ship, 'rect'):
                ship_x, ship_y = ship.rect.centerx, ship.rect.centery
            else:
                ship_x, ship_y = ship.x, ship.y
                
            # Calculate distance
            distance = math.sqrt((current_x - ship_x)**2 + (current_y - ship_y)**2)
            
            # Estimate time for projectile to reach target's current position
            time_to_target = distance / projectile_speed if projectile_speed > 0 else 0
        else:
            # Default time prediction if no ship reference
            time_to_target = 0.5  # seconds
            
        # Predict future position based on current velocity and time
        predicted_x = current_x + (target_vx * time_to_target)
        predicted_y = current_y + (target_vy * time_to_target)
        
        # Add some intelligence for boss movement patterns
        if hasattr(target, 'is_boss') and target.is_boss:
            # If boss is moving up or down rapidly, predict continued movement in that direction
            if abs(target_vy) > 2:
                predicted_y += target_vy * 0.5  # Additional prediction factor
                
            # If boss has a pattern attribute, use it for better prediction
            if hasattr(target, 'pattern'):
                if target.pattern == 'zigzag':
                    # For zigzag patterns, predict reversal point
                    if abs(target_vy) < 0.5 and target_y > 400:
                        predicted_y -= 50  # Predict upward movement at bottom
                    elif abs(target_vy) < 0.5 and target_y < 100:
                        predicted_y += 50  # Predict downward movement at top
        
        return (predicted_x, predicted_y)
    
    # Reuse helper methods from AggressiveStrategy
    
    def _find_dangerous_bullet(self, ship, bullets):
        """
        Find the most dangerous bullet that threatens the ship.
        
        Args:
            ship: The AI ship object
            bullets: List of bullet objects
            
        Returns:
            The most dangerous bullet or None
        """
        # Define danger zone parameters
        horizontal_danger = 250  # pixels ahead of ship
        vertical_range = 70      # pixels above/below ship
        
        # Get ship position and dimensions
        if hasattr(ship, 'rect'):
            ship_x = ship.rect.centerx
            ship_y = ship.rect.centery
            ship_height = ship.rect.height
        else:
            ship_x = ship.x
            ship_y = ship.y
            ship_height = getattr(ship, 'height', 30)  # Default height if not available
        
        # Adjust vertical range based on ship size
        vertical_range = max(vertical_range, ship_height * 1.5)
        
        dangerous_bullets = []
        for bullet in bullets:
            # Get bullet position
            if hasattr(bullet, 'rect'):
                bullet_x = bullet.rect.centerx
                bullet_y = bullet.rect.centery
            else:
                bullet_x = bullet.x
                bullet_y = bullet.y
                
            # Get bullet velocity if available
            bullet_vel_x, bullet_vel_y = 0, 0
            if hasattr(bullet, 'velocity'):
                if isinstance(bullet.velocity, tuple):
                    bullet_vel_x, bullet_vel_y = bullet.velocity
                elif hasattr(bullet.velocity, 'x') and hasattr(bullet.velocity, 'y'):
                    bullet_vel_x, bullet_vel_y = bullet.velocity.x, bullet.velocity.y
            
            # Calculate time to potential collision
            # If bullet is moving toward ship
            if bullet_vel_x < 0:  # Moving left (toward ship)
                time_to_collision = (ship_x - bullet_x) / abs(bullet_vel_x) if bullet_vel_x != 0 else float('inf')
            else:
                # If bullet is ahead of ship but not moving toward it
                if bullet_x > ship_x:
                    time_to_collision = float('inf')  # Will never collide
                else:
                    time_to_collision = float('inf')  # Will never collide
            
            # Check if bullet is ahead of ship and within horizontal danger zone
            if bullet_x > ship_x and bullet_x - ship_x < horizontal_danger:
                # Check if bullet is within vertical range of ship
                if abs(bullet_y - ship_y) < vertical_range:
                    # Calculate danger score based on distance and trajectory
                    distance = self._distance(ship, bullet)
                    
                    # Bullets on direct collision course are more dangerous
                    trajectory_factor = 1.0
                    if bullet_vel_y != 0:
                        # Calculate where bullet will be horizontally when it reaches ship's x position
                        time_to_reach_ship_x = (ship_x - bullet_x) / bullet_vel_x if bullet_vel_x != 0 else float('inf')
                        if time_to_reach_ship_x > 0:  # Only if bullet will reach ship's x in the future
                            projected_y = bullet_y + bullet_vel_y * time_to_reach_ship_x
                            # If projected position is close to ship's y, it's on collision course
                            if abs(projected_y - ship_y) < ship_height:
                                trajectory_factor = 0.5  # Lower score = more dangerous
                    
                    danger_score = distance * trajectory_factor
                    dangerous_bullets.append((bullet, danger_score))
        
        # Return the most dangerous bullet
        if dangerous_bullets:
            dangerous_bullets.sort(key=lambda x: x[1])  # Sort by danger score
            return dangerous_bullets[0][0]
        
        return None
    
    def _find_dangerous_enemy(self, ship, aliens):
        """
        Find enemies that are dangerously close to the ship.
        
        Args:
            ship: The AI ship object
            aliens: List of alien objects
            
        Returns:
            The most dangerous alien or None
        """
        if not aliens:
            return None
            
        dangerous_aliens = []
        horizontal_danger = 70  # pixels ahead of ship
        vertical_danger = 50    # pixels above/below ship
        
        for alien in aliens:
            if hasattr(alien, 'rect') and hasattr(ship, 'rect'):
                # Check if alien is very close horizontally and within vertical range
                if (alien.rect.left - ship.rect.right < horizontal_danger and 
                    abs(alien.rect.centery - ship.rect.centery) < vertical_danger):
                    dangerous_aliens.append((alien, self._distance(ship, alien)))
        
        if dangerous_aliens:
            dangerous_aliens.sort(key=lambda x: x[1])  # Sort by distance
            return dangerous_aliens[0][0]
            
        return None
    
    def _find_nearest_powerup(self, ship, powerups):
        """
        Find the nearest powerup, prioritizing those ahead of the ship.
        
        Args:
            ship: The AI ship object
            powerups: List of powerup objects
            
        Returns:
            The best powerup to target or None
        """
        if not powerups:
            return None
            
        # Prioritize powerups ahead of the ship
        ahead_powerups = []
        other_powerups = []
        
        for powerup in powerups:
            if self._is_ahead(ship, powerup):
                ahead_powerups.append((powerup, self._distance(ship, powerup)))
            else:
                other_powerups.append((powerup, self._distance(ship, powerup)))
        
        # First check powerups ahead
        if ahead_powerups:
            ahead_powerups.sort(key=lambda x: x[1])  # Sort by distance
            return ahead_powerups[0][0]
        
        # If no powerups ahead, check others
        if other_powerups:
            other_powerups.sort(key=lambda x: x[1])  # Sort by distance
            return other_powerups[0][0]
        
        return None
    
    def _find_high_value_powerup(self, ship, powerups):
        """
        Find high-value powerups that are worth deviating from boss targeting.
        
        Args:
            ship: The AI ship object
            powerups: List of powerup objects
            
        Returns:
            A high-value powerup or None
        """
        if not powerups:
            return None
            
        # In a real implementation, we would check powerup type/value
        # For now, we'll just prioritize closer powerups
        close_powerups = []
        for powerup in powerups:
            distance = self._distance(ship, powerup)
            if distance < 150:  # Only consider powerups within reasonable range
                close_powerups.append((powerup, distance))
        
        if close_powerups:
            close_powerups.sort(key=lambda x: x[1])  # Sort by distance
            return close_powerups[0][0]
            
        return None
    
    def _is_ahead(self, ship, obj):
        """
        Check if an object is ahead of the ship.
        
        Args:
            ship: The AI ship object
            obj: The object to check
            
        Returns:
            bool: True if the object is ahead of the ship
        """
        # Get ship x position
        if hasattr(ship, 'rect'):
            ship_x = ship.rect.centerx
        else:
            ship_x = ship.x
            
        # Get object x position
        if hasattr(obj, 'rect'):
            obj_x = obj.rect.centerx
        else:
            obj_x = obj.x
            
        return obj_x > ship_x
    
    def _is_easily_reachable(self, ship, obj):
        """
        Determine if an object is easily reachable without significant deviation.
        
        Args:
            ship: The AI ship object
            obj: The object to check
            
        Returns:
            bool: True if the object is easily reachable
        """
        distance = self._distance(ship, obj)
        
        # Get ship and object positions
        if hasattr(ship, 'rect'):
            ship_y = ship.rect.centery
        else:
            ship_y = ship.y
            
        if hasattr(obj, 'rect'):
            obj_y = obj.rect.centery
        else:
            obj_y = obj.y
            
        # If object is close and doesn't require much vertical movement
        return distance < 120 and abs(ship_y - obj_y) < 60
    
    def _find_nearest_alien(self, ship, aliens):
        """
        Find the nearest alien to the ship, with preference for aliens ahead of the ship.
        
        Args:
            ship: The AI ship object
            aliens: List of alien objects
            
        Returns:
            The nearest alien or None
        """
        if not aliens:
            return None
        
        # Get ship position
        if hasattr(ship, 'rect'):
            ship_x, ship_y = ship.rect.centerx, ship.rect.centery
        else:
            ship_x, ship_y = ship.x, ship.y
        
        scored_aliens = []
        
        for alien in aliens:
            # Get alien position
            if hasattr(alien, 'rect'):
                alien_x, alien_y = alien.rect.centerx, alien.rect.centery
            else:
                alien_x, alien_y = alien.x, alien.y
                
            # Calculate distance
            dist = self._distance(ship, alien)
            
            # Calculate angle to determine if alien is ahead
            # Prefer aliens ahead of the ship (positive x direction)
            position_score = 1.0
            if alien_x > ship_x:  # Ahead of ship
                position_score = 0.7  # Lower score is better
            else:
                position_score = 1.5  # Higher score for aliens behind (less desirable)
                
            # Final score combines distance and position
            final_score = dist * position_score
            
            scored_aliens.append((alien, final_score))
        
        # Sort by score (lower is better)
        scored_aliens.sort(key=lambda x: x[1])
        
        return scored_aliens[0][0] if scored_aliens else None
