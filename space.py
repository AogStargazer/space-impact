import pygame
import random

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1536, 864
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Travel Starfield")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
COLORS = [(0, 0, 0)]  # Monochrome black stars

class Star:
    def __init__(self, x=None, y=None):
        self.reset(x, y)
    
    def update(self):
        self.x -= self.speed
        
        if self.blinking:
            self.blink_timer -= 1
            if self.blink_timer <= 0:
                self.blink_timer = random.randint(5, 30)
                self.visible = not self.visible
        
        if self.x < -self.size:
            self.reset(WIDTH + random.randint(0, 20), random.randint(0, HEIGHT))
    
    def reset(self, x=None, y=None):
        self.x = x if x is not None else random.randint(0, WIDTH)
        self.y = y if y is not None else random.randint(0, HEIGHT)
        self.size = random.randint(1, 4)
        self.speed = self.size * random.uniform(0.5, 1.5)
        self.blinking = random.random() < 0.3
        self.blink_timer = random.randint(5, 30)
        self.visible = True
        self.color = random.choice(COLORS)
    
    def draw(self, screen):
        if self.visible:
            pygame.draw.rect(screen, self.color, (int(self.x) - self.size, int(self.y) - self.size, self.size * 2, self.size * 2))

class Starfield:
    def __init__(self, num_stars):
        self.stars = [Star(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(num_stars)]
    
    def update(self):
        for star in self.stars:
            star.update()
    
    def draw(self, screen):
        for star in self.stars:
            star.draw(screen)

def main():
    clock = pygame.time.Clock()
    starfield = Starfield(300)
    running = True
    
    while running:
        screen.fill(WHITE)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        starfield.update()
        starfield.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
