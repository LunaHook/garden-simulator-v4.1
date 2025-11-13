
# v4.1 web

import pygame
import asyncio
import random
import math
import time
from enum import Enum
from typing import Dict, List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants - Expanded window size by 1.3x
SCREEN_WIDTH = int(1400)  # 1820
SCREEN_HEIGHT = int(800)  # 1300
FPS = 60
TILE_SIZE = 48
MAP_WIDTH = 150
MAP_HEIGHT = 150

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
BROWN = (139, 69, 19)
BLUE = (135, 206, 235)
DARK_BLUE = (25, 25, 112)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
LIGHT_GREEN = (144, 238, 144)
DARK_GREEN = (0, 100, 0)
SOIL_COLOR = (101, 67, 33)
WATER_COLOR = (64, 164, 223)
RED = (255, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Shop category colors
COMMON_COLOR = (0, 200, 0)
RARE_COLOR = (0, 100, 255)
MYTHIC_COLOR = (255, 0, 0)  # Changed from YELLOW to RED
LEGENDARY_COLOR = (255, 215, 0)
TOOLS_COLOR = (0, 0, 0)

class WeatherType(Enum):
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    SNOWING = "snowing"

class PlantType:

        def __init__(self, name: str, seed_cost: float, sell_value: float, growth_time: float, 
                 color: tuple, fruit_color: tuple = None, size: tuple = (1, 1), shape: str = 'rectangle'):
            self.name = name
            self.seed_cost = seed_cost
            self.sell_value = sell_value
            self.growth_time = growth_time
            self.color = color
            self.fruit_color = fruit_color or color
            self.size = size
            self.shape = shape  # 'rectangle', 'circle', 'star', or 'curved'

class PlantGrowthStage(Enum):
    SEED = 0
    SPROUT = 1
    YOUNG = 2
    MATURE = 3
    HARVESTABLE = 4

class Plant:
    def __init__(self, plant_type: PlantType, x: int, y: int):
        self.plant_type = plant_type
        self.x = x
        self.y = y
        self.planted_time = time.time()
        self.stage = PlantGrowthStage.SEED
        self.harvestable = False
        self.time_remaining = plant_type.growth_time  # Store actual time remaining
        self.last_update = time.time()  # Track last update time

    def update(self, weather_multiplier: float = 1.0, fertilizer_multiplier: float = 1.0, tile_type: str = 'grass'):
        """Update plant growth based on time passed with multipliers affecting rate"""
        if self.harvestable:
            return

        current_time = time.time()
        elapsed = current_time - self.last_update
        
        # Calculate soil multiplier
        soil_multiplier = 1.1 if tile_type == 'soil' else 1.0  # 1.1x buff on soil
        
        # Calculate how much time to subtract based on multipliers
        total_multiplier = weather_multiplier * fertilizer_multiplier * soil_multiplier
        time_reduction = elapsed * total_multiplier
        
        # Update time remaining
        self.time_remaining = max(0, self.time_remaining - time_reduction)
        self.last_update = current_time

        # Calculate growth progress
        progress = 1.0 - (self.time_remaining / self.plant_type.growth_time)
        
        if self.time_remaining <= 0:
            self.stage = PlantGrowthStage.HARVESTABLE
            self.harvestable = True
        elif progress >= 0.8:
            self.stage = PlantGrowthStage.MATURE
        elif progress >= 0.5:
            self.stage = PlantGrowthStage.YOUNG
        elif progress >= 0.2:
            self.stage = PlantGrowthStage.SPROUT
        else:
            self.stage = PlantGrowthStage.SEED

    def get_time_remaining(self, weather_multiplier: float = 1.0, fertilizer_multiplier: float = 1.0) -> float:
        """Get remaining time in seconds until harvestable"""
        if self.harvestable:
            return 0.0
        return max(0.0, self.time_remaining)
    
    def get_occupied_tiles(self) -> List[Tuple[int, int]]:
        """Get list of all tiles this plant occupies based on its shape"""
        tiles = []
        w, h = self.plant_type.size
        
        if self.plant_type.shape == 'rectangle':
            for dy in range(h):
                for dx in range(w):
                    tiles.append((self.x + dx, self.y + dy))
                    
        elif self.plant_type.shape == 'circle':
            center_x = self.x + w//2
            center_y = self.y + h//2
            radius = min(w, h)//2
            for dy in range(-radius, radius+1):
                for dx in range(-radius, radius+1):
                    if dx*dx + dy*dy <= radius*radius:
                        tiles.append((center_x + dx, center_y + dy))
                        
        elif self.plant_type.shape == 'star':
            # 5-point star pattern for 3x3 plants
            star_points = [
                (1,0), (0,1), (2,1),  # Top and sides
                (0,2), (2,2),         # Bottom corners
                (1,1), (1,2)          # Center and bottom
            ]
            for dx, dy in star_points:
                tiles.append((self.x + dx, self.y + dy))
                
        elif self.plant_type.shape == 'curved':
            # Curved rectangle (rounded corners)
            corners = [(0,0), (w-1,0), (0,h-1), (w-1,h-1)]  # Corner points excluded
            for dy in range(h):
                for dx in range(w):
                    if (dx,dy) not in corners:
                        tiles.append((self.x + dx, self.y + dy))
        
        return tiles
            
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """Draw the detailed plant at its current growth stage"""
        # Draw on all occupied tiles
        for dy in range(self.plant_type.size[1]):
            for dx in range(self.plant_type.size[0]):
                tile_x = self.x + dx
                tile_y = self.y + dy
                screen_x = tile_x * TILE_SIZE - camera_x
                screen_y = tile_y * TILE_SIZE - camera_y
                
                # Don't draw if off screen
                if (screen_x < -TILE_SIZE or screen_x > SCREEN_WIDTH or 
                    screen_y < -TILE_SIZE or screen_y > SCREEN_HEIGHT):
                    continue
                    
                rect = pygame.Rect(screen_x + 4, screen_y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
                center_x, center_y = rect.center
                
                # Scale plant parts based on plant size for larger plants
                scale_factor = min(self.plant_type.size[0], self.plant_type.size[1])
                
                if self.stage == PlantGrowthStage.SEED:
                    # Small brown seed with detail
                    pygame.draw.circle(screen, BROWN, (center_x, center_y), 4 * scale_factor)
                    pygame.draw.circle(screen, (80, 40, 20), (center_x - 1, center_y - 1), 2 * scale_factor)
                elif self.stage == PlantGrowthStage.SPROUT:
                    # Green sprout with stem
                    pygame.draw.circle(screen, LIGHT_GREEN, (center_x, center_y - 5), 8 * scale_factor)
                    pygame.draw.rect(screen, DARK_GREEN, (center_x - 2*scale_factor, center_y - 2, 4*scale_factor, 12))
                    # Small leaves
                    pygame.draw.ellipse(screen, LIGHT_GREEN, (center_x - 6*scale_factor, center_y - 8, 8*scale_factor, 4))
                elif self.stage == PlantGrowthStage.YOUNG:
                    # Larger plant with multiple leaves
                    pygame.draw.circle(screen, self.plant_type.color, (center_x, center_y - 8), 12 * scale_factor)
                    pygame.draw.rect(screen, DARK_GREEN, (center_x - 3*scale_factor, center_y - 5, 6*scale_factor, 18))
                    # Multiple leaves
                    for i, (ldx, ldy) in enumerate([(-8, -12), (8, -12), (-6, -6), (6, -6)]):
                        pygame.draw.ellipse(screen, self.plant_type.color, 
                                           (center_x + ldx*scale_factor, center_y + ldy, 10*scale_factor, 6))
                elif self.stage == PlantGrowthStage.MATURE:
                    # Full size plant with thick stem
                    pygame.draw.circle(screen, self.plant_type.color, (center_x, center_y - 12), 16 * scale_factor)
                    pygame.draw.rect(screen, DARK_GREEN, (center_x - 4*scale_factor, center_y - 8, 8*scale_factor, 24))
                    # Large leaves
                    for i, (ldx, ldy) in enumerate([(-12, -16), (12, -16), (-8, -8), (8, -8), (-10, -4), (10, -4)]):
                        pygame.draw.ellipse(screen, self.plant_type.color, 
                                           (center_x + ldx*scale_factor, center_y + ldy, 14*scale_factor, 8))
                elif self.stage == PlantGrowthStage.HARVESTABLE:
                    # Full plant with detailed fruits/flowers
                    pygame.draw.circle(screen, self.plant_type.color, (center_x, center_y - 15), 18 * scale_factor)
                    pygame.draw.rect(screen, DARK_GREEN, (center_x - 5*scale_factor, center_y - 10, 10*scale_factor, 28))
                    
                    # Large leaves
                    for i, (ldx, ldy) in enumerate([(-15, -20), (15, -20), (-10, -12), (10, -12), (-12, -6), (12, -6)]):
                        pygame.draw.ellipse(screen, self.plant_type.color, 
                                           (center_x + ldx*scale_factor, center_y + ldy, 16*scale_factor, 10))
                    
                    # Detailed fruits/flowers
                    fruit_positions = [(-10, -18), (10, -18), (-6, -12), (6, -12), (0, -8)]
                    for fx, fy in fruit_positions:
                        fruit_x, fruit_y = center_x + fx*scale_factor, center_y + fy
                        # Main fruit
                        pygame.draw.circle(screen, self.plant_type.fruit_color, (fruit_x, fruit_y), 6 * scale_factor)
                        # Highlight
                        pygame.draw.circle(screen, tuple(min(255, c + 40) for c in self.plant_type.fruit_color), 
                                         (fruit_x - 2, fruit_y - 2), 3 * scale_factor)

class Inventory:
    def __init__(self):
        self.seeds: Dict[str, int] = {}
        self.items: Dict[str, int] = {}
        
    def add_seeds(self, plant_name: str, quantity: int):
        self.seeds[plant_name] = self.seeds.get(plant_name, 0) + quantity
        
    def use_seed(self, plant_name: str) -> bool:
        if self.seeds.get(plant_name, 0) > 0:
            self.seeds[plant_name] -= 1
            if self.seeds[plant_name] == 0:
                del self.seeds[plant_name]
            return True
        return False
        
    def add_item(self, item_name: str, quantity: int):
        self.items[item_name] = self.items.get(item_name, 0) + quantity
        
    def remove_item(self, item_name: str, quantity: int) -> bool:
        if self.items.get(item_name, 0) >= quantity:
            self.items[item_name] -= quantity
            if self.items[item_name] == 0:
                del self.items[item_name]
            return True
        return False

class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.speed = 160  # Reduced from 200 to 160 (0.8x)
        self.money = 10.0  # Starting money as float #starting #inital #balance
        self.inventory = Inventory()
        # Fertilizer levels: 0=basic(1x), 1=iron(2x), 2=gold(10x), 3=diamond(100x)
        self.fertilizer_level = 0
        self.hoe_level = 0  # 0=basic(2), 1=iron(8), 2=gold(20), 3=diamond(100)
        self.shovel_level = 0  # 0=basic(1), 1=iron(4), 2=gold(8), 3=diamond(15)
        
    def get_fertilizer_multiplier(self) -> float:
        """Get current fertilizer growth speed multiplier"""
        multipliers = [1.0, 2.5, 50.0, 500.0]  # Updated multipliers
        return multipliers[self.fertilizer_level]
        
    def get_planting_range(self) -> int:
        """Get current planting range in tiles"""
        ranges = [2, 8, 20, 100]
        return ranges[self.hoe_level]
        
    def get_harvest_range(self) -> int:
        """Get current harvesting range in tiles"""
        ranges = [1, 4, 8, 15]
        return ranges[self.shovel_level]
        
    def get_fertilizer_multiplier(self) -> float:
        """Get current fertilizer growth speed multiplier"""
        multipliers = [1.0, 2.0, 10.0, 100.0]
        return multipliers[self.fertilizer_level]
        
    def update(self, dt: float, keys, map_obj):
        """Update player position based on input"""
        dx = dy = 0
        
        # Check for shift key (speed boost)
        speed_multiplier = 3.0 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 1.0
        current_speed = self.speed * speed_multiplier
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -current_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = current_speed * dt
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -current_speed * dt
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = current_speed * dt
            
        # Check collision and update position
        new_x = max(0, min(MAP_WIDTH * TILE_SIZE - TILE_SIZE, self.x + dx))
        new_y = max(0, min(MAP_HEIGHT * TILE_SIZE - TILE_SIZE, self.y + dy))
        
        # Simple boundary checking
        tile_x = int(new_x // TILE_SIZE)
        tile_y = int(new_y // TILE_SIZE)
        
        if map_obj.is_walkable(tile_x, tile_y):
            self.x = new_x
            self.y = new_y
            
    def get_tile_position(self) -> Tuple[int, int]:
        """Get the tile coordinates the player is standing on"""
        return int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """Draw the detailed player"""
        screen_x = self.x - camera_x + TILE_SIZE // 2
        screen_y = self.y - camera_y + TILE_SIZE // 2
        
        # Player shadow
        pygame.draw.ellipse(screen, (0, 0, 0, 50), (screen_x - 18, screen_y + 15, 36, 8))
        
        # Player body (torso)
        pygame.draw.ellipse(screen, (100, 150, 255), (screen_x - 12, screen_y - 5, 24, 30))
        
        # Player head
        pygame.draw.circle(screen, (255, 200, 150), (int(screen_x), int(screen_y - 15)), 14)
        
        # Eyes
        pygame.draw.circle(screen, BLACK, (int(screen_x - 5), int(screen_y - 18)), 2)
        pygame.draw.circle(screen, BLACK, (int(screen_x + 5), int(screen_y - 18)), 2)
        
        # Arms
        pygame.draw.ellipse(screen, (255, 200, 150), (screen_x - 20, screen_y - 8, 8, 20))
        pygame.draw.ellipse(screen, (255, 200, 150), (screen_x + 12, screen_y - 8, 8, 20))
        
        # Legs
        pygame.draw.ellipse(screen, (50, 50, 200), (screen_x - 10, screen_y + 15, 8, 18))
        pygame.draw.ellipse(screen, (50, 50, 200), (screen_x + 2, screen_y + 15, 8, 18))
        
        # Hat
        pygame.draw.ellipse(screen, (200, 100, 50), (screen_x - 16, screen_y - 25, 32, 12))

class Weather:
    def __init__(self):
        self.current_weather = WeatherType.SUNNY
        self.weather_timer = 0
        self.weather_duration = 85  # Check every 85 seconds for weather change
        self.current_special_duration = 0  # Duration for current special weather

    def update(self, dt: float):
        """Update weather system"""
        self.weather_timer += dt

        # If in special weather (RAINY or SNOWING), check if duration is up
        if self.current_weather in [WeatherType.RAINY, WeatherType.SNOWING]:
            self.current_special_duration -= dt
            if self.current_special_duration <= 0:
                # Return to normal weather
                self.current_weather = random.choice([WeatherType.SUNNY, WeatherType.CLOUDY])
                self.weather_timer = 0  # Reset timer
                return

        # Check for weather change every 85 seconds
        if self.weather_timer >= self.weather_duration:
            self.weather_timer = 0

            # Only attempt weather change if currently in normal weather
            if self.current_weather in [WeatherType.SUNNY, WeatherType.CLOUDY]:
                # 40% chance to change to special weather
                if random.random() < 0.4:
                    # 50/50 chance between rain and snow
                    self.current_weather = random.choice([WeatherType.RAINY, WeatherType.SNOWING])
                    # Random duration between 80 and 180 seconds
                    self.current_special_duration = random.uniform(80, 180)
                else:
                    # Stay in normal weather, but might switch between sunny and cloudy
                    self.current_weather = WeatherType.CLOUDY if self.current_weather == WeatherType.SUNNY else WeatherType.SUNNY

    def get_growth_multiplier(self) -> float:
        """Get growth speed multiplier based on weather"""
        if self.current_weather == WeatherType.RAINY:
            return 2.0  # 2x faster time passage
        elif self.current_weather == WeatherType.SNOWING:
            return 0.75  # 25% slower time passage
        return 1.0  # Normal speed for sunny/cloudy

    def draw_effects(self, screen: pygame.Surface):
        """Draw weather effects"""
        if self.current_weather == WeatherType.RAINY:
            # Draw rain
            for _ in range(100):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                pygame.draw.line(screen, BLUE, (x, y), (x + 3, y + 15), 2)
        elif self.current_weather == WeatherType.SNOWING:
            # Draw snow
            for _ in range(50):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                pygame.draw.circle(screen, WHITE, (x, y), random.randint(2, 4))
        elif self.current_weather == WeatherType.CLOUDY:
            # Draw cloud overlay
            cloud_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            cloud_surface.fill(GRAY)
            cloud_surface.set_alpha(30)
            screen.blit(cloud_surface, (0, 0))

class DayNightCycle:
    def __init__(self):
        self.time_of_day = 0.5  # 0 = midnight, 0.5 = noon, 1.0 = midnight
        self.day_length = 600  # 10 minutes per full day
        
    def update(self, dt: float):
        """Update day/night cycle"""
        self.time_of_day += dt / self.day_length
        if self.time_of_day >= 1.0:
            self.time_of_day = 0.0
            
    def get_lighting_alpha(self) -> int:
        """Get darkness overlay alpha based on time of day"""
        # Create smooth lighting curve
        if self.time_of_day <= 0.2 or self.time_of_day >= 0.8:
            # Night time
            darkness = 0.6
        elif 0.2 < self.time_of_day <= 0.3 or 0.7 <= self.time_of_day < 0.8:
            # Sunrise/sunset
            if self.time_of_day <= 0.3:
                progress = (self.time_of_day - 0.2) / 0.1
            else:
                progress = 1.0 - (self.time_of_day - 0.7) / 0.1
            darkness = 0.6 - (progress * 0.6)
        else:
            # Day time
            darkness = 0.0
            
        return int(darkness * 255)
        
    def draw_overlay(self, screen: pygame.Surface):
        """Draw day/night lighting overlay"""
        alpha = self.get_lighting_alpha()
        if alpha > 0:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((0, 0, 50))
            overlay.set_alpha(alpha)
            screen.blit(overlay, (0, 0))

class Map:
    def __init__(self):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.tiles = self.generate_map()
        self.sell_area = (self.width // 2, self.height // 2)  # Center of map
        # Color variations for tiles with slow cycling
        self.tile_colors = {}
        self.init_tile_colors()
        
    def init_tile_colors(self):
        """Initialize random colors for each tile"""
        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.tiles[y][x]
                if tile_type in ['grass', 'soil', 'stone']:
                    # Create a unique seed for each tile for consistent randomness
                    tile_seed = x * 1000 + y
                    random.seed(tile_seed)
                    
                    if tile_type == 'grass':
                        base_color = GREEN
                        # Generate random variation within green range
                        variation = random.randint(-30, 30)
                        color = tuple(max(0, min(255, c + variation)) for c in base_color)
                    elif tile_type == 'soil':
                        base_color = SOIL_COLOR
                        variation = random.randint(-20, 20)
                        color = tuple(max(0, min(255, c + variation)) for c in base_color)
                    elif tile_type == 'stone':
                        base_color = GRAY
                        variation = random.randint(-25, 25)
                        color = tuple(max(0, min(255, c + variation)) for c in base_color)
                    
                    # Store initial phase for cycling
                    phase = random.random() * 2 * math.pi
                    self.tile_colors[(x, y)] = {'base_color': color, 'phase': phase}
                    
        # Reset random seed
        random.seed()
        
    def get_tile_color(self, x: int, y: int, current_time: float) -> tuple:
        """Get current color for a tile with 2x faster cycling"""
        tile_type = self.tiles[y][x]
        
        if tile_type == 'water':
            # Animated water - 2x faster
            wave = int(10 * math.sin(current_time * 4 + x * 0.3 + y * 0.3))  # Changed from *2 to *4
            return (64 + wave, 164 + wave//2, 223)
        elif tile_type == 'sell_area':
            # Golden selling area - 2x faster
            glow = int(20 * math.sin(current_time * 6))  # Changed from *3 to *6
            return (255, 215 + glow, 0)
        elif (x, y) in self.tile_colors:
            # Cycling color for grass, soil, stone - 2x faster
            color_info = self.tile_colors[(x, y)]
            base_color = color_info['base_color']
            phase = color_info['phase']
            
            # 2x faster color cycling
            cycle_speed = 0.2  # Changed from 0.1 to 0.2 (2x faster)
            cycle_offset = math.sin(current_time * cycle_speed + phase) * 15  # Small variation
            
            # Apply cycling to each color channel
            new_color = []
            for c in base_color:
                new_c = c + cycle_offset
                new_color.append(max(0, min(255, int(new_c))))
            
            return tuple(new_color)
        else:
            # Default colors for tiles without cycling
            if tile_type == 'grass':
                return GREEN
            elif tile_type == 'soil':
                return SOIL_COLOR
            elif tile_type == 'stone':
                return GRAY
            
        return WHITE  # Fallback
        
    def generate_map(self) -> List[List[str]]:
        """Generate a smooth, varied map"""
        tiles = []
        center_x, center_y = MAP_WIDTH // 2, MAP_HEIGHT // 2
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Distance from center
                dist_from_center = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                # Create water border
                if x < 8 or x >= self.width - 8 or y < 8 or y >= self.height - 8:
                    row.append('water')
                # Selling area at center
                elif abs(x - center_x) <= 2 and abs(y - center_y) <= 2:
                    row.append('sell_area')
                # Use noise for terrain variation
                else:
                    noise_val = (math.sin(x * 0.1) + math.cos(y * 0.1) + 
                               math.sin(x * 0.05 + y * 0.05)) / 3
                    
                    if noise_val < -0.3:
                        row.append('water')
                    elif noise_val < 0.1:
                        row.append('soil')
                    elif noise_val < 0.5:
                        row.append('grass')
                    else:
                        row.append('stone')
                        
            tiles.append(row)
        return tiles
        
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a tile is walkable"""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return self.tiles[y][x] != 'water'
        
    def is_tillable(self, x: int, y: int) -> bool:
        """Check if a tile can be planted on"""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return self.tiles[y][x] in ['soil', 'grass']
        
    def is_sell_area(self, x: int, y: int) -> bool:
        """Check if player is in selling area"""
        return self.tiles[y][x] == 'sell_area'
        
    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        """Draw the map with cycling colors"""
        current_time = time.time()
        
        # Calculate visible tile range
        start_x = max(0, camera_x // TILE_SIZE - 1)
        start_y = max(0, camera_y // TILE_SIZE - 1)
        end_x = min(self.width, (camera_x + SCREEN_WIDTH) // TILE_SIZE + 2)
        end_y = min(self.height, (camera_y + SCREEN_HEIGHT) // TILE_SIZE + 2)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x = x * TILE_SIZE - camera_x
                screen_y = y * TILE_SIZE - camera_y
                rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                
                color = self.get_tile_color(x, y, current_time)
                pygame.draw.rect(screen, color, rect)
                
                # Add sparkle effect for sell area
                if self.tiles[y][x] == 'sell_area' and random.random() < 0.1:
                    sparkle_x = screen_x + random.randint(5, TILE_SIZE - 5)
                    sparkle_y = screen_y + random.randint(5, TILE_SIZE - 5)
                    pygame.draw.circle(screen, WHITE, (sparkle_x, sparkle_y), 2)

class Minimap:
    def __init__(self, map_obj: Map):
        self.map = map_obj
        self.size = 200
        self.scale = self.size / max(MAP_WIDTH, MAP_HEIGHT)
        
    def draw(self, screen: pygame.Surface, player_x: int, player_y: int):
        """Draw the minimap"""
        # Minimap background
        minimap_rect = pygame.Rect(SCREEN_WIDTH - self.size - 20, 20, self.size, self.size)
        pygame.draw.rect(screen, WHITE, minimap_rect)
        pygame.draw.rect(screen, BLACK, minimap_rect, 2)
        
        # Draw simplified map
        for y in range(0, MAP_HEIGHT, 4):  # Sample every 4th tile for performance
            for x in range(0, MAP_WIDTH, 4):
                tile_type = self.map.tiles[y][x]
                mini_x = minimap_rect.x + x * self.scale
                mini_y = minimap_rect.y + y * self.scale
                mini_size = max(1, int(4 * self.scale))
                
                color = WHITE
                if tile_type == 'water':
                    color = WATER_COLOR
                elif tile_type == 'soil':
                    color = SOIL_COLOR
                elif tile_type == 'grass':
                    color = GREEN
                elif tile_type == 'stone':
                    color = GRAY
                elif tile_type == 'sell_area':
                    color = YELLOW
                    
                pygame.draw.rect(screen, color, (mini_x, mini_y, mini_size, mini_size))
        
        # Draw player position
        player_mini_x = minimap_rect.x + (player_x // TILE_SIZE) * self.scale
        player_mini_y = minimap_rect.y + (player_y // TILE_SIZE) * self.scale
        pygame.draw.circle(screen, RED, (int(player_mini_x), int(player_mini_y)), 4)
        pygame.draw.circle(screen, WHITE, (int(player_mini_x), int(player_mini_y)), 2)

class HelpDialog:
    def __init__(self):
        self.is_open = False
        
    def toggle(self):
        """Toggle help dialog open/closed"""
        self.is_open = not self.is_open
        
    def close(self):
        """Close help dialog"""
        self.is_open = False
        
    def draw(self, screen: pygame.Surface, font, small_font):
        """Draw help dialog when open"""
        if not self.is_open:
            return
            
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(128)
        screen.blit(overlay, (0, 0))
        
        # Help dialog box - increased height
        dialog_width = 800
        dialog_height = 700  # Increased from 600 to 700
        dialog_rect = pygame.Rect(
            (SCREEN_WIDTH - dialog_width) // 2,
            (SCREEN_HEIGHT - dialog_height) // 2 - 30,  # Moved up by 30 pixels
            dialog_width,
            dialog_height
        )
        
        pygame.draw.rect(screen, WHITE, dialog_rect)
        pygame.draw.rect(screen, BLACK, dialog_rect, 4)
        
        # Title
        title_text = font.render("HELP & CONTROLS", True, BLACK)
        title_rect = title_text.get_rect(centerx=dialog_rect.centerx, y=dialog_rect.y + 20)
        screen.blit(title_text, title_rect)
        
        # Help content
        help_sections = [
            ("MOVEMENT & BASIC CONTROLS:", [
                "WASD or Arrow Keys: Move your character",
                "Hold Shift: Run (3x faster movement)",
                "P: Plant seeds (automatically finds nearby valid spots)",
                "H: Harvest crops when standing on mature plants"
            ]),
            ("SHOP & ECONOMY:", [
                "E: Open/Close shop",
                "Click BUY buttons to purchase seeds and fertilizers",
                "Left/Right arrows or click page buttons to navigate shop pages",
                "F: Sell all harvested items (only works in golden selling area)"
            ]),
            ("GAME MECHANICS:", [
                "Stand on plants to see their growth timers",
                "Weather affects growth: Rain speeds up, Snow slows down",
                "Fertilizers multiply growth speed: Iron (2.5x), Gold (50x), Diamond (500x)",
                "Hoes increase planting range: Basic (2), Iron (8), Gold (20), Diamond (100)",
                "Shovels increase harvest range: Basic (1), Iron (4), Gold (8), Diamond (15)",
                "Tools require previous level before upgrading",
                "Larger plants (2x2, 3x3, etc.) require more space but give better profits"
            ]),
            ("UI ELEMENTS:", [
                "Minimap (top-right): Shows your location and map layout",
                "Money display shows your current funds",
                "Inventory shows owned seeds and harvested items",
                "Weather display shows current conditions affecting growth"
            ])
        ]
        
        y_offset = 70
        for section_title, items in help_sections:
            # Section title
            section_surface = small_font.render(section_title, True, DARK_BLUE)
            screen.blit(section_surface, (dialog_rect.x + 30, dialog_rect.y + y_offset))
            y_offset += 30
            
            # Section items
            for item in items:
                item_surface = small_font.render(f"  • {item}", True, BLACK)
                screen.blit(item_surface, (dialog_rect.x + 40, dialog_rect.y + y_offset))
                y_offset += 22
            
            y_offset += 10  # Extra space between sections
        
        # Close instruction
        close_text = font.render("Press ESC to close this help dialog", True, RED)
        close_rect = close_text.get_rect(centerx=dialog_rect.centerx, y=dialog_rect.bottom - 40)
        screen.blit(close_text, close_rect)

class Shop:
    def __init__(self):
        self.plant_categories = self.create_plant_categories()
        self.is_open = False
        self.current_page = 0
        self.max_page = len(self.plant_categories) - 1
        self.buy_buttons = []  # Initialize buy buttons list
        self.nav_buttons = []  # Initialize navigation buttons list
        
    def calculate_sell_value(self, seed_cost: float, growth_time: float) -> float:
        """Calculate sell value proportional to wait time"""
        # Base multiplier: sell price = seed_cost * (1 + growth_time_minutes * 0.1)
        # This makes longer wait times more profitable

        # Old code

        #time_minutes = growth_time / 60.0
        #multiplier = 1 + (time_minutes * 0.1)
        #return seed_cost * multiplier

        # New code

        keys = [
            1.00, 2.00, 3.00, 5.00, 8.00, 15.00, 20.00, 25.00, 30.00, 35.00, 40.00, 50.00,
            60.00, 80.00, 100.00, 120.00, 150.00, 180.00, 200.00, 250.00, 280.00, 300.00,
            320.00, 350.00, 380.00, 400.00, 420.00, 450.00, 480.00, 500.00, 500.00, 750.00,
            1000.00, 1250.00, 1500.00, 1750.00, 2000.00, 2250.00, 2500.00, 2750.00, 3000.00,
            3250.00, 3500.00, 3750.00, 4000.00, 4250.00, 4500.00, 4750.00, 5000.00, 5000.00,
            10000.00, 15000.00, 20000.00, 25000.00, 30000.00, 35000.00, 40000.00, 45000.00,
            50000.00, 55000.00, 60000.00, 65000.00, 70000.00, 75000.00, 80000.00, 85000.00,
            90000.00, 95000.00, 100000.00, 200000.00, 1000000.00, 3000000.00, 5000000.00, 10000000.00
        ]

        # Second set of values
        values = [
            1.01, 2.06, 3.10, 6.30, 11.00, 26.00, 32.00, 40.00, 40.00, 55.00, 52.00, 68.00,
            68.00, 120.00, 130.00, 228.00, 250.00, 240.00, 320.00, 411.00, 515.00, 570.00,
            614.00, 676.00, 737.00, 780.00, 882.00, 945.00, 1027.00, 1080.00, 1090.00, 1725.00,
            2350.00, 3063.00, 3720.00, 4393.00, 5000.00, 5648.00, 6425.00, 7233.00, 7950.00,
            8938.00, 9730.00, 10463.00, 11240.00, 11985.00, 12780.00, 13538.00, 14450.00,
            14750.00, 30000.00, 45750.00, 68000.00, 90000.00, 113700.00, 136500.00, 160000.00,
            184500.00, 210000.00, 236500.00, 261000.00, 284050.00, 308000.00, 331500.00,
            355200.00, 379100.00, 403200.00, 427500.00, 451000.00, 1200000.00, 7000000.00,
            25500000.00, 500000000.00, 12000000000.00
        ]

        # Create the library dictionary
        library = dict(zip(keys, values))

        return library.get(seed_cost)

        
    def create_plant_categories(self) -> List[Dict]:
        """Create categorized plant types with new size distribution"""
        categories = []
        
        # Common Seeds ($1-$500) - All 1x1 with decimal prices for early crops
        common_plants = {}
        plants_data = [
            ('Radish', 1.0, 5, (255, 100, 100)),
            ('Lettuce', 2.0, 6, (100, 255, 100)),
            ('Spinach', 3.0, 4, (50, 200, 50)),
            ('Herbs', 5.0, 7, (100, 150, 50)),
            ('Green Onion', 8.0, 8, (200, 255, 200)),
            ('Carrot', 15.0, 15, (255, 140, 0)),
            ('Tomato', 20.0, 20, (255, 0, 0), (255, 50, 50)),
            ('Potato', 25, 25, (160, 82, 45)),
            ('Corn', 30, 30, (255, 255, 0), (255, 255, 100)),
            ('Broccoli', 35, 35, (0, 128, 0)),
            ('Cabbage', 40, 40, (100, 200, 100)),
            ('Pepper', 50, 45, (255, 100, 0), (255, 0, 0)),
            ('Cucumber', 60, 50, (0, 255, 100)),
            ('Eggplant', 80, 60, (128, 0, 128)),
            ('Sunflower', 100, 70, (255, 255, 0), (255, 215, 0)),
            ('Pumpkin', 120, 80, (255, 165, 0)),
            ('Strawberry', 150, 90, (255, 192, 203), (255, 0, 100)),
            ('Blueberry', 180, 100, (100, 149, 237), (0, 0, 255)),
            ('Apple Tree', 200, 120, (139, 69, 19), (255, 0, 0)),
            ('Orange Tree', 250, 140, (139, 69, 19), (255, 165, 0)),
            ('Cherry Tree', 280, 160, (139, 69, 19), (255, 20, 147)),
            ('Peach Tree', 300, 180, (139, 69, 19), (255, 218, 185)),
            ('Pear Tree', 320, 200, (139, 69, 19), (255, 255, 0)),
            ('Grape Vine', 350, 220, (128, 0, 128), (148, 0, 211)),
            ('Avocado Tree', 380, 240, (139, 69, 19), (107, 142, 35)),
            ('Mango Tree', 400, 260, (139, 69, 19), (255, 165, 0)),
            ('Coconut Palm', 420, 280, (139, 69, 19), (139, 69, 19)),
            ('Lemon Tree', 450, 300, (139, 69, 19), (255, 255, 0)),
            ('Lime Tree', 480, 320, (139, 69, 19), (0, 255, 0)),
            ('Banana Tree', 500, 340, (139, 69, 19), (255, 255, 0))
        ]
        
        for plant_data in plants_data:
            name, cost, time, color = plant_data[:4]
            fruit_color = plant_data[4] if len(plant_data) > 4 else color
            sell_value = self.calculate_sell_value(cost, time)
            # All common plants are 1x1
            common_plants[name] = PlantType(name, cost, sell_value, time, color, fruit_color, (1, 1))
        
        categories.append({
            'name': 'COMMON SEEDS',
            'color': COMMON_COLOR,
            'plants': common_plants
        })
        
        # Rare Seeds ($500-$5000) - Can be 3x3, 2x1, 3x2, 3x1
        rare_plants = {}
        rare_sizes = [(3, 3), (2, 1), (3, 2), (3, 1)]
        rare_data = [
            ('Dragon Fruit', 500, 360, (255, 20, 147), (255, 192, 203)),
            ('Golden Apple', 750, 420, (255, 215, 0), (255, 223, 0)),
            ('Rainbow Rose', 1000, 480, (255, 105, 180), (255, 20, 147)),
            ('Crystal Lotus', 1250, 540, (224, 255, 255), (173, 216, 230)),
            ('Starfruit', 1500, 600, (255, 255, 0), (255, 215, 0)),
            ('Phoenix Flower', 1750, 660, (255, 69, 0), (255, 140, 0)),
            ('Moonberry', 2000, 720, (230, 230, 250), (147, 112, 219)),
            ('Thunder Melon', 2250, 780, (255, 0, 255), (138, 43, 226)),
            ('Ice Mint', 2500, 840, (173, 216, 230), (224, 255, 255)),
            ('Fire Pepper', 2750, 900, (255, 69, 0), (255, 0, 0)),
            ('Wind Blossom', 3000, 960, (144, 238, 144), (0, 255, 127)),
            ('Solar Orchid', 3250, 1020, (255, 215, 0), (255, 255, 0)),
            ('Storm Lily', 3500, 1080, (75, 0, 130), (147, 112, 219)),
            ('Earth Root', 3750, 1140, (139, 69, 19), (160, 82, 45)),
            ('Void Berry', 4000, 1200, (25, 25, 112), (72, 61, 139)),
            ('Light Sage', 4250, 1260, (255, 255, 224), (255, 255, 255)),
            ('Shadow Thorn', 4500, 1320, (47, 79, 79), (0, 0, 0)),
            ('Time Blossom', 4750, 1380, (255, 20, 147), (255, 105, 180)),
            ('Space Fruit', 5000, 1440, (25, 25, 112), (65, 105, 225))
        ]
        
        for i, plant_data in enumerate(rare_data):
            name, cost, time, color = plant_data[:4]
            fruit_color = plant_data[4] if len(plant_data) > 4 else color
            sell_value = self.calculate_sell_value(cost, time)
            size = random.choice(rare_sizes)
            rare_plants[name] = PlantType(name, cost, sell_value, time, color, fruit_color, size)
        
        categories.append({
            'name': 'RARE SEEDS',
            'color': RARE_COLOR,
            'plants': rare_plants
        })
        
        # Mythic Seeds ($5000-$100000) - Anything except 4x4
        mythic_plants = {}
        mythic_sizes = [(1, 1), (2, 1), (1, 2), (2, 2), (3, 1), (1, 3), (3, 3), (4, 3), (3, 4)]  # No 4x4
        mythic_data = [
            ('Eternal Fruit', 5000, 1800, (255, 215, 0), (255, 223, 0)),
            ('Mystic Herb', 10000, 2400, (138, 43, 226), (147, 112, 219)),
            ('Cosmic Berry', 15000, 3000, (75, 0, 130), (123, 104, 238)),
            ('Divine Rose', 20000, 3600, (255, 20, 147), (255, 182, 193)),
            ('Celestial Apple', 25000, 4200, (255, 215, 0), (255, 255, 224)),
            ('Quantum Melon', 30000, 4800, (0, 255, 255), (224, 255, 255)),
            ('Infinity Bloom', 35000, 5400, (255, 105, 180), (255, 20, 147)),
            ('Galaxy Grape', 40000, 6000, (75, 0, 130), (138, 43, 226)),
            ('Universe Berry', 45000, 6600, (25, 25, 112), (72, 61, 139)),
            ('Reality Stone Fruit', 50000, 7200, (255, 0, 0), (220, 20, 60)),
            ('Time Crystal Plant', 55000, 7800, (173, 216, 230), (224, 255, 255)),
            ('Power Gem Flower', 60000, 8400, (255, 165, 0), (255, 215, 0)),
            ('Mind Stone Herb', 65000, 9000, (138, 43, 226), (147, 112, 219)),
            ('Soul Stone Berry', 70000, 9600, (255, 140, 0), (255, 165, 0)),
            ('Space Stone Vine', 75000, 10200, (0, 0, 255), (65, 105, 225)),
            ('Dimensional Fruit', 80000, 10800, (255, 20, 147), (255, 105, 180)),
            ('Multiverse Bloom', 85000, 11400, (255, 215, 0), (255, 255, 0)),
            ('Omniversal Plant', 90000, 12000, (255, 255, 255), (224, 255, 255)),
            ('Creator Seed', 95000, 12600, (255, 215, 0), (255, 223, 0)),
            ('God Tier Fruit', 100000, 13200, (255, 215, 0), (255, 255, 224))
        ]
        
        for i, plant_data in enumerate(mythic_data):
            name, cost, time, color = plant_data[:4]
            fruit_color = plant_data[4] if len(plant_data) > 4 else color
            sell_value = self.calculate_sell_value(cost, time)
            size = random.choice(mythic_sizes)
            mythic_plants[name] = PlantType(name, cost, sell_value, time, color, fruit_color, size)
        
        categories.append({
            'name': 'MYTHIC SEEDS',
            'color': MYTHIC_COLOR,
            'plants': mythic_plants
        })
        
        # Legendary Seeds ($200,000-$10,000,000) - All 4x4
        legendary_plants = {}
        legendary_data = [
            ('World Tree Sapling', 200000, 14400, (139, 69, 19), (0, 255, 0)),
            ('Universe Heart', 1000000, 25600, (255, 20, 147), (255, 105, 180)),
            ('Infinity Garden', 3000000, 106800, (255, 215, 0), (255, 255, 0)),
            ('Creation Essence', 5000000, 280000, (255, 255, 255), (224, 255, 255)),
            ('Omnipotent Bloom', 10000000, 1900200, (255, 215, 0), (255, 223, 0))
        ]
        
        for i, plant_data in enumerate(legendary_data):
            name, cost, time, color = plant_data[:4]
            fruit_color = plant_data[4] if len(plant_data) > 4 else color
            sell_value = self.calculate_sell_value(cost, time)
            # All legendary plants are 4x4
            legendary_plants[name] = PlantType(name, cost, sell_value, time, color, fruit_color, (4, 4))
        
        categories.append({
            'name': 'LEGENDARY SEEDS',
            'color': LEGENDARY_COLOR,
            'plants': legendary_plants
        })
        
        # Tools category
        tools = {
            'Iron Fertilizer': PlantType('Iron Fertilizer', 10000, 0, 0, (128, 128, 128)),
            'Gold Fertilizer': PlantType('Gold Fertilizer', 150000, 0, 0, (255, 215, 0)),
            'Diamond Fertilizer': PlantType('Diamond Fertilizer', 2500000, 0, 0, (185, 242, 255)),
            'Iron Hoe': PlantType('Iron Hoe', 5000, 0, 0, (128, 128, 128)),
            'Gold Hoe': PlantType('Gold Hoe', 50000, 0, 0, (255, 215, 0)),
            'Diamond Hoe': PlantType('Diamond Hoe', 250000, 0, 0, (185, 242, 255)),
            'Iron Shovel': PlantType('Iron Shovel', 20000, 0, 0, (128, 128, 128)),
            'Gold Shovel': PlantType('Gold Shovel', 100000, 0, 0, (255, 215, 0)),
            'Diamond Shovel': PlantType('Diamond Shovel', 500000, 0, 0, (185, 242, 255))
        }
        
        categories.append({
            'name': 'TOOLS',
            'color': TOOLS_COLOR,
            'plants': tools
        })
        
        return categories
        
    def get_all_plant_types(self) -> Dict[str, PlantType]:
        """Get all plant types from all categories"""
        all_plants = {}
        for category in self.plant_categories:
            all_plants.update(category['plants'])
        return all_plants
        
    def toggle_shop(self):
        """Toggle shop open/closed"""
        self.is_open = not self.is_open
        
    def next_page(self):
        """Go to next page"""
        if self.current_page < self.max_page:
            self.current_page += 1
            
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
        
    def buy_seeds(self, player: Player, plant_name: str, quantity: int = 1) -> bool:
        """Buy seeds or tools if player has enough money"""
        all_plants = self.get_all_plant_types()
        if plant_name not in all_plants:
            return False
        
        # Handle tool purchases
        if any(tool in plant_name for tool in ['Fertilizer', 'Hoe', 'Shovel']):
            tool_type = None
            if 'Fertilizer' in plant_name:
                tool_type = 'fertilizer'
                current_level = player.fertilizer_level
            elif 'Hoe' in plant_name:
                tool_type = 'hoe'
                current_level = player.hoe_level
            elif 'Shovel' in plant_name:
                tool_type = 'shovel'
                current_level = player.shovel_level
                
            level_name = plant_name.split()[0]  # Iron, Gold, or Diamond
            level_map = {'Iron': 1, 'Gold': 2, 'Diamond': 3}
            required_level = level_map[level_name]
            
            if current_level >= required_level:
                return False  # Already have this or higher
            if current_level != required_level - 1:
                return False  # Need to buy in order
                
            total_cost = all_plants[plant_name].seed_cost
            if player.money >= total_cost:
                player.money -= total_cost
                if tool_type == 'fertilizer':
                    player.fertilizer_level = required_level
                elif tool_type == 'hoe':
                    player.hoe_level = required_level
                else:  # shovel
                    player.shovel_level = required_level
                return True
            return False
        
        # Regular seed purchase
        total_cost = all_plants[plant_name].seed_cost * quantity
        if player.money >= total_cost:
            player.money -= total_cost
            player.inventory.add_seeds(plant_name, quantity)
            return True
        return False
        
    def sell_item(self, player: Player, item_name: str, quantity: int = 1) -> bool:
        """Sell harvested items"""
        all_plants = self.get_all_plant_types()
        if item_name not in all_plants:
            return False
            
        if player.inventory.remove_item(item_name, quantity):
            total_value = all_plants[item_name].sell_value * quantity
            player.money += total_value
            return True
        return False
        
    def sell_all_items(self, player: Player) -> float:
        """Sell all items in inventory, return total money earned"""
        all_plants = self.get_all_plant_types()
        total_earned = 0.0
        
        items_to_sell = list(player.inventory.items.items())
        for item_name, quantity in items_to_sell:
            if item_name in all_plants:
                value = all_plants[item_name].sell_value * quantity
                total_earned += value
                player.money += value
                del player.inventory.items[item_name]
        
        return total_earned
        
    def draw(self, screen: pygame.Surface, player: Player, font, small_font):
        """Draw shop interface when open"""
        if not self.is_open:
            return
            
        # Shop background with rounded corners effect - 0.75x width
        original_width = SCREEN_WIDTH - 200
        shop_width = int(original_width * 0.75)
        shop_rect = pygame.Rect((SCREEN_WIDTH - shop_width) // 2, 80, shop_width, SCREEN_HEIGHT - 160)
        pygame.draw.rect(screen, WHITE, shop_rect)
        pygame.draw.rect(screen, BLACK, shop_rect, 4)
        
        # Current category
        current_category = self.plant_categories[self.current_page]
        
        # Title with category color
        title_text = font.render(f"Garden Shop - {current_category['name']}", True, current_category['color'])
        screen.blit(title_text, (shop_rect.x + 30, shop_rect.y + 20))
        
        # Money display
        money_text = font.render(f"Money: ${player.money:,.2f}", True, BLACK)
        screen.blit(money_text, (shop_rect.right - 250, shop_rect.y + 20))
        
        # Remove top page navigation and arrows
        # Only keep bottom navigation elements
        
        # Navigation triangles at bottom with increased spacing
        bottom_y = shop_rect.bottom - 40
        
        if self.current_page > 0:
            # Left black filled triangle
            left_points = [
                (shop_rect.centerx - 100, bottom_y),
                (shop_rect.centerx - 80, bottom_y - 15),
                (shop_rect.centerx - 80, bottom_y + 15)
            ]
            pygame.draw.polygon(screen, BLACK, left_points)
            left_rect = pygame.Rect(shop_rect.centerx - 100, bottom_y - 15, 20, 30)
            self.nav_buttons.append(('prev', left_rect))
        
        # Page number text
        page_text = font.render(f"Page {self.current_page + 1}/{self.max_page + 1}", True, BLACK)
        page_rect = page_text.get_rect(center=(shop_rect.centerx, bottom_y))
        screen.blit(page_text, page_rect)
        
        if self.current_page < self.max_page:
            # Right black filled triangle
            right_points = [
                (shop_rect.centerx + 100, bottom_y),
                (shop_rect.centerx + 80, bottom_y - 15),
                (shop_rect.centerx + 80, bottom_y + 15)
            ]
            pygame.draw.polygon(screen, BLACK, right_points)
            right_rect = pygame.Rect(shop_rect.centerx + 80, bottom_y - 15, 20, 30)
            self.nav_buttons.append(('next', right_rect))
        
        # Item list with buy buttons
        y_offset = 70
        row_height = 35
        
        # Clear previous buttons
        self.buy_buttons = []
        
        for i, (name, plant_type) in enumerate(current_category['plants'].items()):
            y = shop_rect.y + y_offset + (i * row_height)
            if y > shop_rect.bottom - 100:  # Don't draw below shop area
                break
                
            # Handle all tools display (Fertilizer, Hoe, Shovel)
            if any(tool in name for tool in ['Fertilizer', 'Hoe', 'Shovel']):
                tool_type = None
                if 'Fertilizer' in name:
                    tool_type = 'fertilizer'
                    current_level = player.fertilizer_level
                elif 'Hoe' in name:
                    tool_type = 'hoe'
                    current_level = player.hoe_level
                elif 'Shovel' in name:
                    tool_type = 'shovel'
                    current_level = player.shovel_level
                    
                level_name = name.split()[0]  # Iron, Gold, or Diamond
                level_map = {'Iron': 1, 'Gold': 2, 'Diamond': 3}
                required_level = level_map[level_name]
                
                if current_level >= required_level:
                    info_text = f"{name}: PURCHASED"
                    color = GRAY
                elif current_level != required_level - 1:
                    info_text = f"{name}: ${plant_type.seed_cost:,.0f} (Need previous level)"
                    color = GRAY
                else:
                    info_text = f"{name}: ${plant_type.seed_cost:,.0f}"
                    color = BLACK if player.money >= plant_type.seed_cost else GRAY
            else:
                # Regular plant info display (unchanged)
                time_str = f"{plant_type.growth_time:.0f}s"
                size_str = f"{plant_type.size[0]}x{plant_type.size[1]}" if plant_type.size != (1, 1) else "1x1"
                
                if plant_type.seed_cost < 10:
                    cost_str = f"${plant_type.seed_cost:.2f}"
                else:
                    cost_str = f"${plant_type.seed_cost:,.0f}"
                
                if plant_type.sell_value < 10:
                    sell_str = f"${plant_type.sell_value:.2f}"
                else:
                    sell_str = f"${plant_type.sell_value:,.0f}"
                    
                info_text = f"{name}: {cost_str} -> {sell_str} ({time_str}) [{size_str}]"
                color = BLACK if player.money >= plant_type.seed_cost else GRAY
                    
            plant_text = small_font.render(info_text, True, color)
            screen.blit(plant_text, (shop_rect.x + 30, y))
                
            # Buy button
            if any(tool in name for tool in ['Fertilizer', 'Hoe', 'Shovel']):
                if current_level >= required_level:
                    button_color = GRAY
                    button_text = "OWNED"
                elif current_level != required_level - 1 or player.money < plant_type.seed_cost:
                    button_color = GRAY
                    button_text = "BUY"
                else:
                    button_color = GREEN
                    button_text = "BUY"
            else:
                button_color = GREEN if player.money >= plant_type.seed_cost else GRAY
                button_text = "BUY"
            
            button_rect = pygame.Rect(shop_rect.right - 120, y - 5, 80, 25)
            pygame.draw.rect(screen, button_color, button_rect)
            pygame.draw.rect(screen, BLACK, button_rect, 2)
            
            buy_text = small_font.render(button_text, True, BLACK)
            text_rect = buy_text.get_rect(center=button_rect.center)
            screen.blit(buy_text, text_rect)
            
            # Store button info for click detection
            button_info = (button_rect.copy(), name)  # Use copy() to ensure we get a new rect
            self.buy_buttons.append(button_info)

class GameWorld:
    def __init__(self):
        self.map = Map()
        self.player = Player(TILE_SIZE * MAP_WIDTH // 2, TILE_SIZE * MAP_HEIGHT // 2)
        self.plants: Dict[Tuple[int, int], Plant] = {}
        self.weather = Weather()
        self.day_night = DayNightCycle()
        self.shop = Shop()
        self.minimap = Minimap(self.map)
        self.help_dialog = HelpDialog()
        self.camera_x = 0
        self.camera_y = 0
        self.mouse_pos = (0, 0)
        self.error_message = ""
        self.error_timer = 0.0
        
    def update(self, dt: float, keys, events):
        """Update all game systems"""
        # Update error message timer
        if self.error_timer > 0:
            self.error_timer -= dt
            if self.error_timer <= 0:
                self.error_message = ""
        
        # Update player
        self.player.update(dt, keys, self.map)
        
        # Update camera to follow player smoothly
        target_camera_x = self.player.x - SCREEN_WIDTH // 2
        target_camera_y = self.player.y - SCREEN_HEIGHT // 2
        
        # Smooth camera movement
        self.camera_x += (target_camera_x - self.camera_x) * dt * 6
        self.camera_y += (target_camera_y - self.camera_y) * dt * 6
        
        # Clamp camera to map bounds
        self.camera_x = max(0, min(MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH, self.camera_x))
        self.camera_y = max(0, min(MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT, self.camera_y))
        
        # Update weather and day/night
        self.weather.update(dt)
        self.day_night.update(dt)
        
        # Update plants
        weather_multiplier = self.weather.get_growth_multiplier()
        fertilizer_multiplier = self.player.get_fertilizer_multiplier()
        for plant in self.plants.values():
            tile_type = self.map.tiles[plant.y][plant.x]  # Get tile type for plant location
            plant.update(weather_multiplier, fertilizer_multiplier, tile_type)
        
        # Handle events
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.help_dialog.is_open:
                        self.help_dialog.close()
                elif event.key == pygame.K_p:  # Plant key
                    self.handle_planting()
                elif event.key == pygame.K_h:  # Harvest key
                    self.handle_harvesting()
                elif event.key == pygame.K_e:
                    self.shop.toggle_shop()
                elif event.key == pygame.K_f and self.is_in_sell_area():
                    # Sell all items when in sell area (F key)
                    earned = self.shop.sell_all_items(self.player)
                    if earned > 0:
                        print(f"Sold all items for ${earned:,.2f}!")
                elif self.shop.is_open:
                    if event.key == pygame.K_LEFT:
                        self.shop.prev_page()
                    elif event.key == pygame.K_RIGHT:
                        self.shop.next_page()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check help button click first
                    help_button_rect = pygame.Rect(15, SCREEN_HEIGHT - 50, 35, 35)
                    if help_button_rect.collidepoint(event.pos):
                        self.help_dialog.toggle()
                    elif self.shop.is_open:
                        # Check navigation button clicks
                        for nav_type, nav_rect in self.shop.nav_buttons:
                            if nav_rect.collidepoint(event.pos):
                                if nav_type == 'prev':
                                    self.shop.prev_page()
                                elif nav_type == 'next':
                                    self.shop.next_page()
                                break
                        else:
                            # Check buy button clicks
                            self.handle_shop_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
                
    def can_plant_at(self, x: int, y: int, size: Tuple[int, int]) -> bool:
        """Check if a plant of given size can be placed at position"""
        width, height = size
        
        # Check if all tiles are within bounds and tillable
        for dy in range(height):
            for dx in range(width):
                check_x, check_y = x + dx, y + dy
                
                # Check bounds
                if check_x < 0 or check_x >= MAP_WIDTH or check_y < 0 or check_y >= MAP_HEIGHT:
                    return False
                
                # Check if tillable
                if not self.map.is_tillable(check_x, check_y):
                    return False
                
                # Check if already occupied by plant
                if (check_x, check_y) in self.plants:
                    return False
        
        return True
    
    def find_planting_spot(self, player_x: int, player_y: int, size: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find closest valid planting spot near player within planting range"""
        planting_range = self.player.get_planting_range()  # Get current hoe range
        
        # Try positions in expanding circles around player up to planting range
        for radius in range(planting_range + 1):
            positions = []
            
            if radius == 0:
                positions = [(player_x, player_y)]
            else:
                # Generate positions in a circle around player
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if abs(dx) == radius or abs(dy) == radius:  # Only edge of circle
                            positions.append((player_x + dx, player_y + dy))
            
            # Shuffle to avoid bias toward specific directions
            random.shuffle(positions)
            
            for x, y in positions:
                if self.can_plant_at(x, y, size):
                    return (x, y)
        
        return None
    
    def show_error(self, message: str):
        """Show error message for a few seconds"""
        self.error_message = message
        self.error_timer = 3.0  # Show for 3 seconds
                
    # Remove this duplicate method
    # def handle_harvesting(self):
    #     """Handle H key for harvesting"""
    #     player_tile_x, player_tile_y = self.player.get_tile_position()
    #     if (player_tile_x, player_tile_y) in self.plants:
    #         plant = self.plants[(player_tile_x, player_tile_y)]
    #         if plant.harvestable:
    #             # Harvest the plant - remove from all occupied tiles
    #             occupied_tiles = plant.get_occupied_tiles()
    #             for tile in occupied_tiles:
    #                 if tile in self.plants:
    #                     del self.plants[tile]
    #             # Add harvested item to inventory
    #             self.player.inventory.add_item(plant.plant_type.name, 1)

    # Keep this version which implements the shovel range
    def handle_harvesting(self):
        """Handle H key for harvesting with range support"""
        player_tile_x, player_tile_y = self.player.get_tile_position()
        harvest_range = self.player.get_harvest_range()  # Get current shovel range
        
        # Check all tiles within harvest range
        for dy in range(-harvest_range, harvest_range + 1):
            for dx in range(-harvest_range, harvest_range + 1):
                check_x = player_tile_x + dx
                check_y = player_tile_y + dy
                
                # Only check tiles within the circular range
                if math.sqrt(dx*dx + dy*dy) <= harvest_range:
                    if (check_x, check_y) in self.plants:
                        plant = self.plants[(check_x, check_y)]
                        if plant.harvestable:
                            # Harvest the plant - remove from all occupied tiles
                            occupied_tiles = plant.get_occupied_tiles()
                            for tile in occupied_tiles:
                                if tile in self.plants:
                                    del self.plants[tile]
                            
                            # Add harvested item to inventory
                            self.player.inventory.add_item(plant.plant_type.name, 1)
                    
    def is_in_sell_area(self) -> bool:
        """Check if player is in the selling area"""
        player_tile_x, player_tile_y = self.player.get_tile_position()
        return self.map.is_sell_area(player_tile_x, player_tile_y)
                
    def handle_shop_click(self, pos):
        """Handle clicks on shop buy buttons"""
        if not self.shop.is_open:
            return
            
        # Check each buy button
        for button_rect, plant_name in self.shop.buy_buttons:
            if button_rect.collidepoint(pos):
                # Try to buy the item
                success = self.shop.buy_seeds(self.player, plant_name)
                if not success:
                    # Show error message if purchase failed
                    all_plants = self.shop.get_all_plant_types()
                    if plant_name in all_plants:
                        plant_type = all_plants[plant_name]
                        if self.player.money < plant_type.seed_cost:
                            self.show_error(f"Not enough money! Need ${plant_type.seed_cost:,.2f}")
                        else:
                            self.show_error("Cannot purchase this item yet!")
                break

    def handle_planting(self):
        """Handle P key for planting with multi-tile support"""
        player_tile_x, player_tile_y = self.player.get_tile_position()
        
        # Find first available seed in inventory
        for plant_name, quantity in self.player.inventory.seeds.items():
            if quantity > 0:
                plant_type = self.shop.get_all_plant_types()[plant_name]
                
                # Find suitable planting location
                planting_spot = self.find_planting_spot(player_tile_x, player_tile_y, plant_type.size)
                
                if planting_spot is None:
                    self.show_error("Error: Not enough space to place that seed here")
                    return
                # Plant the seed at found location
                plant_x, plant_y = planting_spot
                new_plant = Plant(plant_type, plant_x, plant_y)
                
                # Add plant to all tiles it occupies
                for tile in new_plant.get_occupied_tiles():
                    self.plants[tile] = new_plant
                
                # Remove seed from inventory
                self.player.inventory.use_seed(plant_name)
                return
        
        self.show_error("No seeds in inventory!")

    def draw(self, screen: pygame.Surface, font, small_font):
        """Draw the game world"""
        # Fill background
        screen.fill(BLACK)
        
        # Draw map
        self.map.draw(screen, int(self.camera_x), int(self.camera_y))
        
        # Draw plants
        for plant in set(self.plants.values()):  # Use set to avoid drawing duplicates
            plant.draw(screen, int(self.camera_x), int(self.camera_y))
        
        # Draw player
        self.player.draw(screen, int(self.camera_x), int(self.camera_y))
        
        # Draw weather effects
        self.weather.draw_effects(screen)
        
        # Draw day/night overlay
        self.day_night.draw_overlay(screen)
        
        # Draw minimap
        self.minimap.draw(screen, self.player.x, self.player.y)
        
        # Draw UI elements
        self.draw_ui(screen, font, small_font)
        
        # Draw shop if open
        if self.shop.is_open:
            self.shop.draw(screen, self.player, font, small_font)
            
        # Draw help dialog if open
        self.help_dialog.draw(screen, font, small_font)

    def draw_ui(self, screen: pygame.Surface, font, small_font):
        """Draw UI elements"""
        # Create slightly larger font for info display (50% bigger instead of 70%)
        info_font = pygame.font.Font(None, int(24 * 1.5))  # Reduced from 1.7 to 1.5
        
        # Draw top-left info box
        info_box_x = 10
        info_box_y = 10
        info_box_width = 300
        info_box_height = 160
        
        # Info box with semi-transparent background
        info_surface = pygame.Surface((info_box_width, info_box_height), pygame.SRCALPHA)
        info_surface.fill((255, 255, 255, 128))  # White with 50% transparency
        screen.blit(info_surface, (info_box_x, info_box_y))
        pygame.draw.rect(screen, BLACK, (info_box_x, info_box_y, info_box_width, info_box_height), 2)
        
        # Draw weather indicator with larger font
        weather_text = info_font.render(f"Weather: {self.weather.current_weather.value.capitalize()}", True, BLACK)
        screen.blit(weather_text, (info_box_x + 10, info_box_y + 10))
        
        # Draw current buff info
        player_tile_x, player_tile_y = self.player.get_tile_position() # Get player's current tile to show soil buff
        weather_mult = self.weather.get_growth_multiplier()
        fert_mult = self.player.get_fertilizer_multiplier()
        soil_mult = 1.1 if self.map.tiles[player_tile_y][player_tile_x] == 'soil' else 1.0
        total_mult = weather_mult * fert_mult * soil_mult
        
        buff_text = info_font.render(f"Total Buff: {total_mult:.2f}x", True, BLACK)
        screen.blit(buff_text, (info_box_x + 10, info_box_y + 40))
        
        # Draw tool levels with simplified display
        tool_y = info_box_y + 70
        tools = [
            f"Fertilizer: {['Basic', 'Iron', 'Gold', 'Diamond'][self.player.fertilizer_level]}",
            f"Hoe: {['Basic', 'Iron', 'Gold', 'Diamond'][self.player.hoe_level]}",
            f"Shovel: {['Basic', 'Iron', 'Gold', 'Diamond'][self.player.shovel_level]}"
        ]
        
        for tool_info in tools:
            text = info_font.render(tool_info, True, BLACK)
            screen.blit(text, (info_box_x + 10, tool_y))
            tool_y += 28  # Reduced spacing from 35 to 28
        
        # Draw inventory box below info box
        inventory_x = 10
        inventory_y = info_box_y + info_box_height + 20  # 20px gap between boxes
        inventory_width = 187  # 10% wider than original 170
        inventory_height = 400
        
        # Background with semi-transparent white
        inventory_surface = pygame.Surface((inventory_width, inventory_height), pygame.SRCALPHA)
        inventory_surface.fill((255, 255, 255, 128))  # White with 50% transparency
        screen.blit(inventory_surface, (inventory_x, inventory_y))
        pygame.draw.rect(screen, BLACK, (inventory_x, inventory_y, inventory_width, inventory_height), 2)
        
        # Title
        inv_title = font.render("Inventory", True, BLACK)
        screen.blit(inv_title, (inventory_x + 10, inventory_y + 10))
        
        # Money display at top of inventory - using small_font now
        money_text = small_font.render(f"Money: ${self.player.money:,.2f}", True, BLACK)
        screen.blit(money_text, (inventory_x + 10, inventory_y + 40))
        
        # Seeds section
        y_offset = inventory_y + 80
        seeds_text = small_font.render("Seeds:", True, BLACK)
        screen.blit(seeds_text, (inventory_x + 10, y_offset))
        
        # Display seeds in inventory with limit
        y_offset += 20
        max_visible_items = 12  # Adjust this number based on your UI
        visible_seeds = list(self.player.inventory.seeds.items())
        hidden_seeds = len(visible_seeds) - max_visible_items
        
        for i, (seed_name, quantity) in enumerate(visible_seeds):
            if i < max_visible_items:
                text = small_font.render(f"{seed_name}: {quantity}", True, BLACK)
                screen.blit(text, (inventory_x + 20, y_offset))
                y_offset += 20
            else:
                text = small_font.render(f"and {hidden_seeds} others...", True, BLACK)
                screen.blit(text, (inventory_x + 20, y_offset))
                break
        
        # Items section with similar logic
        y_offset += 20
        items_text = small_font.render("Items:", True, BLACK)
        screen.blit(items_text, (inventory_x + 10, y_offset))
        
        y_offset += 20
        visible_items = list(self.player.inventory.items.items())
        hidden_items = len(visible_items) - max_visible_items
        
        for i, (item_name, quantity) in enumerate(visible_items):
            if i < max_visible_items:
                text = small_font.render(f"{item_name}: {quantity}", True, BLACK)
                screen.blit(text, (inventory_x + 20, y_offset))
                y_offset += 20
            else:
                text = small_font.render(f"and {hidden_items} others...", True, BLACK)
                screen.blit(text, (inventory_x + 20, y_offset))
                break
        
        # Help button (bottom left)
        help_button_rect = pygame.Rect(15, SCREEN_HEIGHT - 50, 35, 35)
        pygame.draw.rect(screen, WHITE, help_button_rect)
        pygame.draw.rect(screen, BLACK, help_button_rect, 2)
        
        # Question mark
        text = font.render("?", True, BLACK)
        text_rect = text.get_rect(center=help_button_rect.center)
        screen.blit(text, text_rect)
        
        # Draw error message if active
        if self.error_timer > 0:
            error_surface = font.render(self.error_message, True, RED)
            error_rect = error_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
            screen.blit(error_surface, error_rect)
        
        # Draw hover plant info with colored timer based on buff
        mouse_tile_x = int((self.mouse_pos[0] + self.camera_x) // TILE_SIZE)
        mouse_tile_y = int((self.mouse_pos[1] + self.camera_y) // TILE_SIZE)

        if (mouse_tile_x, mouse_tile_y) in self.plants:
            plant = self.plants[(mouse_tile_x, mouse_tile_y)]
            
            # Calculate total multiplier including soil
            weather_mult = self.weather.get_growth_multiplier()
            fert_mult = self.player.get_fertilizer_multiplier()
            soil_mult = 1.1 if self.map.tiles[plant.y][plant.x] == 'soil' else 1.0
            total_mult = weather_mult * fert_mult * soil_mult
            
            # Get base time remaining
            time_left = plant.time_remaining

            # Choose color based on total buff
            if total_mult > 1:
                timer_color = GREEN
            elif total_mult < 1:
                timer_color = RED
            else:
                timer_color = WHITE

            # Draw with larger info_font instead of small_font
            info_text = f"{plant.plant_type.name} - Time Remaining: {time_left:.1f}s"
            info_surface = info_font.render(info_text, True, timer_color)  # Using info_font instead of small_font
            screen.blit(info_surface, (10, SCREEN_HEIGHT - 80))

# Initialize and run game
async def main():
    """Main game loop (async for pygbag)"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Garden Simulator v4.1")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    world = GameWorld()
    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()
        dt = clock.tick(FPS) / 1000.0
        world.update(dt, keys, events)
        world.draw(screen, font, small_font)
        pygame.display.flip()
        await asyncio.sleep(0)  # Yield to browser

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
