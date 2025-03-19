# Created by Michal Niemiec michal.niemiec.it@gmail.com
# I created this little "game" while learning python
# This project is based on project from book "Python Crash Course" and I modified it quite a bit.

import sys
import pygame

from pygame.locals import *
from settings import *
from ship import Ship
from bullet import Bullet
from alien import Alien
from alien_2 import Alien2
from alien_3 import Alien3
from space import Starfield
from game_stats import GameStats
from time import *
from button import Button
from scoreboard import Scoreboard
from boss import Boss
from boss_bullet import BossBullet
from powerup import Powerup
from ai_projectiles import LaserBullet, SpreadBullet, create_spread_shot
from explosion import Explosion

clock = pygame.time.Clock()


class SpaceImpact:
    """Main class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()

        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height),
                                              HWSURFACE | DOUBLEBUF | RESIZABLE)
        pygame.display.set_caption("Space Impact")

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()  # Group to manage explosion animations
        
        # Powerup spawn timer
        self.last_powerup_spawn_time = pygame.time.get_ticks()
        
        # Boss related attributes
        self.boss = None
        self.boss_bullets = pygame.sprite.Group()
        self.boss_active = False
        # Initialize with current time to ensure first boss spawns after 2 minutes from game start
        self.last_boss_death_time = pygame.time.get_ticks()
        self.boss_respawn_delay = 120000  # 2 minutes in milliseconds

        self._create_fleet_1()
        self._create_fleet_2()
        self._create_fleet_3()

        # Set the background image
        self.bg_image = self.settings.bg_image
        self.imageship = self.ship.image
        
        # Initialize starfield
        self.starfield = Starfield(300)
        
        # AI auto-fire settings
        self.ai_fire_cooldown = 100  # milliseconds
        self.last_ai_shot = pygame.time.get_ticks()

        # Instance to store game statistic.
        self.stats = GameStats(self)
        # Draw the score information.
        self.scoreboard = Scoreboard(self)
        self.scoreboard.show_score()

        # Make the Play button.
        self.play_button = Button(self)

    def run_game(self):
        """Start the main loop for the game."""

        while True:
            # Watch for keyboard and mouse events.
            self._check_events()

            if self.stats.game_active:
                # Check if it's time to spawn a boss
                # Boss spawns 2 minutes after game start or 2 minutes after previous boss death
                current_time = pygame.time.get_ticks()
                if not self.boss_active and current_time - self.last_boss_death_time >= self.boss_respawn_delay:
                    self._spawn_boss()
                
                # Check if it's time to spawn a powerup (every 10 seconds)
                current_time = pygame.time.get_ticks()
                if current_time - self.last_powerup_spawn_time >= 10000:  # 10 seconds
                    self._spawn_powerup()
                    self.last_powerup_spawn_time = current_time
                
                # Update game elements
                # Pass the boss instance to the ship's AI if boss is active
                self.ship.update_ai(
                    self.aliens, 
                    self.boss_bullets if self.boss_active else None,
                    self.boss if self.boss_active else None,
                    self.powerups
                )
                self.bullets.update()
                self._update_aliens()
                self._update_bullets()
                self._update_powerups()
                self.explosions.update()  # Update explosion animations
                
                # Update boss if active
                if self.boss_active and self.boss:
                    self._update_boss()
                    self._update_boss_bullets()
                
                # AI auto-fire logic
                if current_time - self.last_ai_shot > self.ai_fire_cooldown:
                    self._fire_bullet()
                    self.last_ai_shot = current_time

            # Redraw the screen during each pass through the loop.
            self._update_screen()

    def _check_events(self):
        """Respond to keypress and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_keydown_events(self, event):
        """Respond to keydown events."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_UP:
            self.ship.moving_up = True
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        """Respond to keydown events."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False
        elif event.key == pygame.K_UP:
            self.ship.moving_up = False
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = False

    def _spawn_powerup(self):
        """Spawn a random powerup on the screen."""
        import random
        
        # Define powerup types
        powerup_types = ['red', 'green', 'orange', 'yellow']
        
        # Choose a random powerup type
        powerup_type = random.choice(powerup_types)
        
        # Generate random y position (within screen bounds)
        y_position = random.randint(50, self.settings.screen_height - 50)
        
        # Create powerup at the right edge of the screen
        new_powerup = Powerup(self, powerup_type, self.settings.screen_width, y_position)
        self.powerups.add(new_powerup)
    
    def _apply_powerup_effect(self, powerup_type):
        """Apply the effect of the collected powerup."""
        if powerup_type == 'red':
            # Health powerup - increase ship lives
            self.stats.ships_left += 1
            self.scoreboard.prep_hearts()
        elif powerup_type == 'green':
            # Laser projectile powerup
            self.stats.green_powerups += 1
            self.scoreboard.prep_powerup_counts()
        elif powerup_type == 'orange':
            # Spread projectile powerup
            self.stats.orange_powerups += 1
            self.scoreboard.prep_powerup_counts()
        elif powerup_type == 'yellow':
            # Invulnerability powerup: simply collect and increment counter.
            self.stats.yellow_powerups += 1
            self.scoreboard.prep_powerup_counts()
    
    def _update_powerups(self):
        """Update powerups position and check for collisions."""
        # Update powerup positions
        self.powerups.update()
        
        # Check for collisions between bullets and powerups
        collisions = pygame.sprite.groupcollide(self.bullets, self.powerups, True, True)
        
        if collisions:
            for powerups in collisions.values():
                for powerup in powerups:
                    # Apply the effect based on powerup type
                    self._apply_powerup_effect(powerup.type)
        
        # Check for ship-powerup collisions
        powerup_hit = pygame.sprite.spritecollideany(self.ship, self.powerups)
        if powerup_hit:
            self._apply_powerup_effect(powerup_hit.type)
            powerup_hit.kill()
        
        # Remove powerups that have gone off screen
        for powerup in self.powerups.copy():
            if powerup.rect.right < 0:
                self.powerups.remove(powerup)
    
    def reset_game(self):
        """Reset the game to its initial state."""
        self.stats.reset_stats()
        self.settings.initialize_dynamic_settings()
        self.stats.game_active = True
        self.scoreboard.prep_score()
        self.scoreboard.prep_hearts()
        self.scoreboard.prep_powerup_counts()

        # Hide the mouse cursor.
        pygame.mouse.set_visible(False)
        
        # Get rid of any remaining aliens, bullets, powerups, explosions, and boss.
        self.aliens.empty()
        self.bullets.empty()
        self.powerups.empty()
        self.explosions.empty()
        self.boss_bullets.empty()
        self.boss_active = False
        self.boss = None
        self.last_boss_death_time = pygame.time.get_ticks()
        
        self.ship.center_ship()
        self._create_fleet_1()
        self._create_fleet_2()
        self._create_fleet_3()

    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks Play."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            self.reset_game()

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group."""
        # Check if the ship is AI-controlled
        if hasattr(self.ship, 'ai_controlled') and self.ship.ai_controlled:
            # Using offensive powerups against the boss if available.
            # Check for laser projectile (green powerup) when engaging boss
            if (self.stats.green_powerups > 0 and 
                hasattr(self.ship, 'ai_state') and 
                (self.ship.ai_state == 'engage_boss' or self.ship.ai_state == 'target_boss')):
                # Create a laser bullet
                new_bullet = LaserBullet(self.ship.rect.right, self.ship.rect.centery)
                new_bullet.predicted_shot = True
                self.bullets.add(new_bullet)
                # Decrement green powerup count
                self.stats.green_powerups -= 1
                self.scoreboard.prep_powerup_counts()
                print("AI using laser against boss with predictive targeting!")
            
            # Using offensive powerups against the boss if available.
            # Check for spread projectile (orange powerup) when engaging boss
            elif (self.stats.orange_powerups > 0 and 
                  hasattr(self.ship, 'ai_state') and 
                  (self.ship.ai_state == 'engage_boss' or self.ship.ai_state == 'target_boss')):
                # Create spread bullets with improved prediction
                if self.boss and hasattr(self.ship, 'strategy') and hasattr(self.ship.strategy, 'predict_target_position'):
                    # Use prediction to aim at boss's future position
                    predicted_x, predicted_y = self.ship.strategy.predict_target_position(
                        self.boss, 
                        self.settings.bullet_speed, 
                        self.ship
                    )
                    # Calculate angle adjustment based on prediction
                    angle_adjustment = 0
                    if predicted_y != self.ship.rect.centery:
                        # Simple angle calculation based on predicted position
                        dy = predicted_y - self.ship.rect.centery
                        angle_adjustment = min(max(dy / 100, -10), 10)  # Limit adjustment to ±10 degrees
                    
                    spread_bullets = create_spread_shot(
                        self.ship.rect.right, 
                        self.ship.rect.centery, 
                        num_bullets=3, 
                        spread_angle=20, 
                        speed=10,
                        angle_offset=angle_adjustment  # Apply prediction-based adjustment
                    )
                else:
                    # Fallback to standard spread shot if prediction isn't available
                    spread_bullets = create_spread_shot(
                        self.ship.rect.right, 
                        self.ship.rect.centery, 
                        num_bullets=3, 
                        spread_angle=20, 
                        speed=10
                    )
                
                # Add all spread bullets to the bullets group and mark as predicted shots
                for bullet in spread_bullets:
                    bullet.predicted_shot = True
                    self.bullets.add(bullet)
                # Decrement orange powerup count
                self.stats.orange_powerups -= 1
                self.scoreboard.prep_powerup_counts()
                print("AI using spread gun against boss with predictive targeting!")
            
            # Check for invulnerability powerup (yellow powerup) when not already invulnerable
            elif (self.stats.yellow_powerups > 0 and 
                  hasattr(self.ship, 'ai_state') and 
                  not self.ship.invulnerable and
                  (pygame.sprite.spritecollideany(self.ship, self.boss_bullets) or 
                   pygame.sprite.spritecollideany(self.ship, self.aliens))):
                # Activate invulnerability powerup when in danger
                self.stats.yellow_powerups -= 1
                self.ship.activate_invulnerability(5000)  # 5 seconds in milliseconds
                self.scoreboard.prep_powerup_counts()
                
                # Still fire a normal bullet
                new_bullet = Bullet(self)
                self.bullets.add(new_bullet)
            
            # Default to normal bullet
            else:
                new_bullet = Bullet(self)
                self.bullets.add(new_bullet)
        else:
            # For manual control, always use normal bullet
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _create_fleet_1(self):
        """Create the fleet of aliens."""
        # Make multiple aliens (increased spawn rate)
        for _ in range(10):  # Increased from 5 to 10
            alien = Alien(self, self.settings)
            self.aliens.add(alien)

    def _create_fleet_2(self):
        """Create the fleet of aliens."""
        # Make multiple aliens (increased spawn rate)
        for _ in range(4):  # Increased from 2 to 4
            alien_2 = Alien2(self, self.settings)
            self.aliens.add(alien_2)

    def _create_fleet_3(self):
        """Create the fleet of aliens."""
        # Make multiple aliens (increased spawn rate)
        for _ in range(4):  # Increased from 2 to 4
            alien_3 = Alien3(self, self.settings)
            self.aliens.add(alien_3)
            
    def _spawn_boss(self):
        """Create a new boss instance."""
        self.boss = Boss(self)
        self.boss_active = True
        
        # Reduce the number of regular aliens when boss appears to maintain game balance
        # Remove half of the current aliens
        aliens_to_remove = list(self.aliens)[:len(self.aliens)//2]
        for alien in aliens_to_remove:
            self.aliens.remove(alien)
        
    def _fire_boss_bullet(self, boss):
        """Create a new boss bullet and add it to the boss_bullets group."""
        # Only fire bullets if the boss is in combat phase
        if boss.phase == 'combat':
            new_bullet = BossBullet(self, boss)
            self.boss_bullets.add(new_bullet)
        
    def _update_boss(self):
        """Update the boss position and check for collisions."""
        if self.boss_active and self.boss:
            # Update boss position and animation
            self.boss.update()
            
            # Check for bullet collisions with boss
            collisions = pygame.sprite.spritecollide(self.boss, self.bullets, True)
            if collisions:
                for bullet in collisions:
                    # Check if boss has already been destroyed by a previous bullet
                    if not self.boss:
                        break
                        
                    # Determine damage based on bullet type
                    hit_multiplier = 1.0  # Base multiplier
                    
                    # Determine base damage and damage multiplier by bullet type
                    if isinstance(bullet, LaserBullet):
                        base_damage = 50
                        damage_multiplier = 1.0  # Initialize with default value
                        # Bonus damage for predicted laser shots
                        if hasattr(bullet, 'predicted_shot') and bullet.predicted_shot:
                            damage_multiplier = 1.5  # 50% bonus damage for predicted laser shots
                    elif isinstance(bullet, SpreadBullet):
                        base_damage = 25
                        damage_multiplier = 1.0  # Initialize with default value
                        # Bonus damage for predicted spread shots
                        if hasattr(bullet, 'predicted_shot') and bullet.predicted_shot:
                            damage_multiplier = 1.3  # 30% bonus damage for predicted spread shots
                    else:
                        # Default for normal bullets
                        base_damage = 10
                        damage_multiplier = 1.0
                        
                    # Calculate final damage with multiplier
                    damage = int(base_damage * damage_multiplier)
                    
                    # Check if the ship has a strategy with prediction capability
                    if hasattr(self.ship, 'strategy') and hasattr(self.ship.strategy, 'predict_target_position'):
                        # Get current boss position
                        boss_x, boss_y = self.boss.rect.centerx, self.boss.rect.centery
                        
                        # Get predicted position
                        predicted_x, predicted_y = self.ship.strategy.predict_target_position(
                            self.boss, 
                            self.settings.bullet_speed, 
                            self.ship
                        )
                        
                        # Calculate accuracy of prediction (how close the bullet is to where the boss actually is)
                        accuracy = 1.0 - min(abs(boss_y - predicted_y) / 100.0, 0.5)  # 0.5 to 1.0 range
                        
                        # Apply accuracy bonus to damage (up to 50% bonus for perfect prediction)
                        hit_multiplier = 1.0 + (accuracy * 0.5)
                        
                        # Apply the additional hit multiplier to damage
                        damage = int(damage * hit_multiplier)
                        
                        # Debug output for hit quality
                        if hit_multiplier > 1.2:
                            print(f"Critical hit! Damage: {damage}, Multiplier: {hit_multiplier:.2f}")
                    
                    # If boss is hit, reduce health by the appropriate damage
                    if self.boss.hit(damage):
                        # Boss is destroyed - create a large explosion effect
                        explosion = Explosion(self.boss.rect.centerx, self.boss.rect.centery, scale=5.0)
                        self.explosions.add(explosion)
                        
                        # Boss is destroyed
                        self.boss_active = False
                        # Record time of boss death to start 2-minute respawn countdown
                        self.last_boss_death_time = pygame.time.get_ticks()
                        # Award extra points for defeating the boss
                        self.stats.score += self.settings.alien_points * 10
                        self.scoreboard.prep_score()
                        self.scoreboard.check_high_score()
                        self.boss = None
                        
                        # Spawn more aliens when boss is defeated to maintain game balance
                        self._create_fleet_1()
                        
                        # Break out of the loop since boss is now destroyed
                        break
                        
    def _update_boss_bullets(self):
        """Update boss bullets position and check for collisions."""
        self.boss_bullets.update()
        
        # Check for collisions between player bullets and boss bullets
        collisions = pygame.sprite.groupcollide(self.bullets, self.boss_bullets, True, True)
        
        # Check for collisions with the ship
        if hasattr(self.ship, 'invulnerable') and self.ship.invulnerable:
            # If ship is invulnerable, destroy boss bullets that collide with it
            collided_bullet = pygame.sprite.spritecollideany(self.ship, self.boss_bullets)
            if collided_bullet:
                collided_bullet.kill()
        else:
            # Normal collision processing - ship takes damage
            if pygame.sprite.spritecollideany(self.ship, self.boss_bullets):
                self._ship_hit()
            
        # Remove bullets that have gone off screen
        for bullet in self.boss_bullets.copy():
            if bullet.rect.right <= 0:
                self.boss_bullets.remove(bullet)
                
        # Limit the number of boss bullets on screen to prevent overwhelming the player
        if len(self.boss_bullets) > 10:
            # Remove the oldest bullets
            oldest_bullets = list(self.boss_bullets)[:len(self.boss_bullets) - 10]
            for bullet in oldest_bullets:
                self.boss_bullets.remove(bullet)

    def _ship_hit(self):
        """Respond to the ship being hit by an alien or boss bullet."""

        # If ship is invulnerable, don't take damage
        # Note: Collision handling for invulnerability is now done in the respective update methods
        if hasattr(self.ship, 'invulnerable') and self.ship.invulnerable:
            return

        if self.stats.ships_left > 0:
            # Lower ships left.
            self.stats.ships_left -= 1
            self.scoreboard.prep_hearts()

            # Get rid of any remaining aliens, bullets, explosions, and powerups.
            self.aliens.empty()
            self.bullets.empty()
            self.boss_bullets.empty()
            self.powerups.empty()
            self.explosions.empty()
            
            # Create explosion effect at ship's position
            explosion = Explosion(self.ship.rect.centerx, self.ship.rect.centery, scale=3.0)
            self.explosions.add(explosion)

            # Reset boss state if active
            if self.boss_active:
                self.boss_active = False
                self.boss = None
                # Don't reset the boss timer to allow it to spawn again after delay
            
            # Create a new fleet and center the ship.
            self.ship.center_ship()
            if self.boss_active:
                self.ship.ai_state = 'engage_boss'
                self.ship.boss_engaged = True
            else:
                self.ship.ai_state = 'engage_enemy'
                self.ship.boss_engaged = False
            self.ship.target_counter = 0
            self._create_fleet_1()
            self._create_fleet_2()
            self._create_fleet_3()

            print(self.stats.ships_left)
            # Pause.
            sleep(1)
        else:
            print("Game over - Resetting game")
            self.reset_game()
            # Set game to inactive to show play button
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _update_aliens(self):
        """Update the position of all liens in the fleet."""
        self.aliens.update()
        # Look for alien-ship collision.
        if hasattr(self.ship, 'invulnerable') and self.ship.invulnerable:
            # If ship is invulnerable, destroy aliens that collide with it
            collided_alien = pygame.sprite.spritecollideany(self.ship, self.aliens)
            if collided_alien:
                # Create explosion effect at alien's position
                explosion = Explosion(collided_alien.rect.centerx, collided_alien.rect.centery)
                self.explosions.add(explosion)
                
                collided_alien.kill()
                # Award points for destroying the alien
                self.stats.score += self.settings.alien_points
                self.scoreboard.prep_score()
                self.scoreboard.check_high_score()
        else:
            # Normal collision processing - ship takes damage
            if pygame.sprite.spritecollideany(self.ship, self.aliens):
                self._ship_hit()

    def _update_bullets(self):
        # Check for any bullets that have hit aliens.
        # If so, get rid of the bullet and the alien.
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                for alien in aliens:
                    # Create explosion effect at alien's position
                    # Using the Explosion class from explosion.py
                    explosion = Explosion(alien.rect.centerx, alien.rect.centery)
                    self.explosions.add(explosion)
                    
                    # Add points for destroying the alien
                    self.stats.score += self.settings.alien_points
                
            self.scoreboard.prep_score()
            self.scoreboard.check_high_score()

        # Delete bullets that are off the screen
        for bullet in self.bullets.copy():
            if bullet.rect.right >= resolution_width * 1.1:
                self.bullets.remove(bullet)

        if not self.aliens:
            # Create new fleets when all aliens are destroyed
            self._create_fleet_1()
            self._create_fleet_2()
            self._create_fleet_3()

    def _update_screen(self):
        """Update images on the screen and flip to the new screen."""

        # Fill with white background
        self.screen.fill((255, 255, 255))
        
        # Update and draw starfield
        self.starfield.update()
        self.starfield.draw(self.screen)
        self.ship.blitme()
        
        # Draw bullets
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
            
        # Draw powerups
        for powerup in self.powerups.sprites():
            powerup.draw()
            
        # Draw boss bullets if boss is active
        if self.boss_active:
            for boss_bullet in self.boss_bullets.sprites():
                boss_bullet.draw_bullet()
            
            # Draw the boss
            if self.boss:
                self.boss.draw()

        self.aliens.draw(self.screen)

        self.scoreboard.show_score()
        # Delete aliens that are off the screen
        for alien in self.aliens.copy():
            if alien.rect.right < 0:
                self.aliens.remove(alien)

        # Lines of code to show FPS counter
        # font = pygame.font.Font(None, 30)
        # fps = font.render(str(int(clock.get_fps())), True, pygame.Color('white'))
        # self.screen.blit(fps, (50, 50))

        # Regulate speed of the game by limiting FPS count.
        clock.tick(60)

        # Draw explosions
        self.explosions.draw(self.screen)
        
        # Draw the play button if the game is inactive.
        if not self.stats.game_active:
            self.play_button.draw_button()

        # Make the most recently draw screen visible.
        pygame.display.flip()


if __name__ == '__main__':
    # Make a game instance, and run the game.
    si = SpaceImpact()
    si.run_game()
