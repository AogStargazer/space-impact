from abc import ABC, abstractmethod
import math

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
    2. Targeting boss
    3. Collecting powerups
    4. Targeting nearest alien
    5. Patrolling (centering) when no targets
    """
    
    def select_target(self, ship, aliens, boss, powerups, boss_bullets):
        """
        Implements the targeting logic for the aggressive strategy.
        
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
        # Check for bullets in danger zone
        if boss_bullets:
            dangerous_bullet = self._find_dangerous_bullet(ship, boss_bullets)
            if dangerous_bullet:
                return ('dodge', dangerous_bullet)
        
        # Check for nearby aliens that are too close (dangerous)
        if aliens:
            for alien in aliens:
                # If an alien is very close horizontally (within 50 pixels of ship's right edge)
                # and within a vertical threshold (50 pixels), consider it dangerous
                if hasattr(alien, 'rect') and hasattr(ship, 'rect'):
                    if alien.rect.left - ship.rect.right < 50 and abs(alien.rect.centery - ship.rect.centery) < 50:
                        return ('dodge', alien)
        
        # Target boss if present
        if boss:
            return ('target_boss', boss)
        
        # Target powerups ahead of the ship
        if powerups:
            nearest_powerup = self._find_nearest_powerup_ahead(ship, powerups)
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
        Find the nearest bullet in the danger zone.
        
        Args:
            ship: The AI ship object
            bullets: List of bullet objects
            
        Returns:
            The nearest dangerous bullet or None
        """
        # Define danger zone parameters
        horizontal_danger = 200  # pixels ahead of ship
        vertical_range = 50      # pixels above/below ship
        
        dangerous_bullets = []
        for bullet in bullets:
            # Check if bullet is ahead of ship and within horizontal danger zone
            if bullet.x > ship.x and bullet.x - ship.x < horizontal_danger:
                # Check if bullet is within vertical range of ship
                if abs(bullet.y - ship.y) < vertical_range:
                    dangerous_bullets.append((bullet, self._distance(ship, bullet)))
        
        # Return the nearest dangerous bullet
        if dangerous_bullets:
            dangerous_bullets.sort(key=lambda x: x[1])  # Sort by distance
            return dangerous_bullets[0][0]
        
        return None
    
    def _find_nearest_powerup_ahead(self, ship, powerups):
        """
        Find the nearest powerup ahead of the ship.
        
        Args:
            ship: The AI ship object
            powerups: List of powerup objects
            
        Returns:
            The nearest powerup ahead or None
        """
        ahead_powerups = []
        for powerup in powerups:
            if powerup.x > ship.x:  # Only consider powerups ahead of the ship
                ahead_powerups.append((powerup, self._distance(ship, powerup)))
        
        if ahead_powerups:
            ahead_powerups.sort(key=lambda x: x[1])  # Sort by distance
            return ahead_powerups[0][0]
        
        return None
    
    def _find_nearest_alien(self, ship, aliens):
        """
        Find the nearest alien to the ship.
        
        Args:
            ship: The AI ship object
            aliens: List of alien objects
            
        Returns:
            The nearest alien or None
        """
        if not aliens:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for alien in aliens:
            dist = self._distance(ship, alien)
            if dist < min_distance:
                min_distance = dist
                nearest = alien
        
        return nearest
    
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
