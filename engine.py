import pygame
import json
import random
import time
from queue import Queue

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.load_assets()
        self.setup_game()
        self.player_move_delay = 0.25  # Player move delay (1/4 speed)
        self.last_player_move_time = time.time()

    def load_assets(self):
        # Load maps, NPCs, and dialogues
        self.maps = self.load_maps('data/maps.json')
        self.npcs = self.load_npcs('data/npcs.json')

        # Load images from the assets directory
        self.wall_image = pygame.image.load('assets/wall.png').convert_alpha()
        self.door_image = pygame.image.load('assets/door.png').convert_alpha()
        self.portal_image = pygame.image.load('assets/portal.png').convert_alpha()
        self.floor_image = pygame.image.load('assets/floor.png').convert_alpha()

    def load_maps(self, file_path):
        with open(file_path, 'r') as file:
            maps = json.load(file)
        return maps

    def load_npcs(self, file_path):
        with open(file_path, 'r') as file:
            npcs = json.load(file)
        return npcs

    def setup_game(self):
        # Initialize game state variables
        self.current_map = "map1"  # Start with the first map
        self.tile_map = self.maps[self.current_map]
        self.player_pos = [5, 5]  # Starting position of the player
        self.current_dialogue = None
        self.interacting = False
        self.camera_offset = [0, 0]  # Camera offset for scrolling

        # Initialize NPCs
        self.npc_data = {}
        for npc_id, npc_info in self.npcs.items():
            start_pos = self.find_nearest_non_wall(npc_info["start_pos"], npc_info["map"])
            movement_range = self.get_movement_range(npc_info["movement_level"])
            self.npc_data[npc_id] = {
                "pos": start_pos,
                "start_pos": start_pos[:],  # Store the starting position
                "last_move_time": time.time(),
                "move_interval": 2,  # NPC moves every 2 seconds
                "movement_level": npc_info["movement_level"],  # Movement level key
                "movement_range": movement_range,  # Dynamically generated movement range
                "dialogue": npc_info["dialogue"],
                "current_dialogue": "start",
                "color": npc_info["color"],
                "moving": True,  # Flag to control NPC movement
                "map": npc_info["map"],
                "move_count": 0,  # Count for tracking movements
                "conversation_active": False  # To track conversation state
            }

    def find_nearest_non_wall(self, start_pos, map_name):
        """Find the nearest non-wall tile to the starting position using BFS."""
        queue = Queue()
        queue.put(start_pos)
        visited = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while not queue.empty():
            x, y = queue.get()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            if self.maps[map_name][y][x] != '1':  # Not a wall
                return [x, y]

            for dx, dy in directions:
                new_x = x + dx
                new_y = y + dy
                if 0 <= new_x < len(self.maps[map_name][0]) and 0 <= new_y < len(self.maps[map_name]):
                    queue.put((new_x, new_y))

        # If no non-wall tile is found, return the original position (unlikely case)
        return start_pos

    def get_movement_range(self, movement_level):
        """Determine movement range based on the movement level."""
        if movement_level == "toodling":
            return 1
        elif movement_level == "restless":
            return 2
        elif movement_level == "roaming":
            return 3
        elif movement_level == "wandering":
            return 4
        else:
            return 1  # Default to toodling if undefined

    def update(self):
        # Handle player movement input
        keys = pygame.key.get_pressed()
        current_time = time.time()
        if not self.interacting and current_time - self.last_player_move_time >= self.player_move_delay:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.move_player(-1, 0)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.move_player(1, 0)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.move_player(0, -1)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.move_player(0, 1)
            self.last_player_move_time = current_time

        # Handle interaction input
        if keys[pygame.K_SPACE] and not self.interacting:
            self.activate()

        # Update NPC movement if not interacting
        if not self.interacting:
            self.update_npc_movement()

    def move_player(self, dx, dy):
        # Calculate new position
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        # Check if the new position is within bounds and not a wall (1 is a wall)
        if 0 <= new_x < len(self.tile_map[0]) and 0 <= new_y < len(self.tile_map):
            tile = self.tile_map[new_y][new_x]
            if tile[0] != '1':  # Assuming '1' represents a wall
                self.player_pos = [new_x, new_y]
                self.update_camera()

                # Handle map transitions
                if tile.startswith('D['):  # Door format D[map_name]
                    map_name = self.parse_map_transition(tile)
                    self.change_map(map_name, self.get_door_position(map_name, f'D[{self.current_map}]'))
                elif tile.startswith('P['):  # Portal format P[map_name]
                    map_name = self.parse_map_transition(tile)
                    self.change_map(map_name, self.get_door_position(map_name, f'P[{self.current_map}]'))

    def parse_map_transition(self, tile):
        # Extract the map name from the tile
        return tile[tile.index('[') + 1:tile.index(']')]

    def change_map(self, new_map, start_position):
        self.current_map = new_map
        self.tile_map = self.maps[new_map]
        self.player_pos = start_position
        self.update_camera()

    def get_door_position(self, map_name, door_type):
        # Find the position of the corresponding door or portal on the destination map
        for y, row in enumerate(self.maps[map_name]):
            for x, tile in enumerate(row):
                if tile == door_type:
                    return [x, y]
        return [1, 1]  # Default to [1, 1] if no corresponding door is found

    def update_camera(self):
        # Screen size
        screen_width, screen_height = self.screen.get_size()

        # Tile size
        tile_size = 32

        # Calculate the visible area in tiles
        visible_tiles_x = screen_width // tile_size
        visible_tiles_y = screen_height // tile_size

        # Calculate camera offsets
        half_visible_x = visible_tiles_x // 2
        half_visible_y = visible_tiles_y // 2

        # Center the camera on the player but within the map bounds
        self.camera_offset[0] = max(0, min(self.player_pos[0] - half_visible_x, len(self.tile_map[0]) - visible_tiles_x))
        self.camera_offset[1] = max(0, min(self.player_pos[1] - half_visible_y, len(self.tile_map) - visible_tiles_y))

    def activate(self):
        # Check if the player is interacting with an NPC
        for npc_id, npc in self.npc_data.items():
            if npc["map"] == self.current_map and self.player_pos == npc["pos"]:
                self.interacting = True
                if not npc["conversation_active"]:
                    self.current_dialogue = npc["dialogue"]["start"]  # Start the conversation
                    npc["current_dialogue"] = "start"
                else:
                    self.current_dialogue = npc["dialogue"][npc["current_dialogue"]]

                self.current_npc = npc_id
                npc["moving"] = False  # Stop NPC movement when interacting
                npc["conversation_active"] = True
                return

        # Reset interaction if there's no NPC or object to interact with
        self.interacting = False
        self.current_dialogue = None

    def update_npc_movement(self):
        current_time = time.time()
        for npc_id, npc in self.npc_data.items():
            if npc["map"] == self.current_map and npc["moving"] and current_time - npc["last_move_time"] > npc["move_interval"]:
                npc["move_count"] += 1
                if npc["move_count"] % 3 == 0:
                    # Move back toward the starting point every third move
                    dx = npc["start_pos"][0] - npc["pos"][0]
                    dy = npc["start_pos"][1] - npc["pos"][1]
                    if dx != 0:
                        dx = int(dx / abs(dx))  # Normalize to -1, 0, or 1
                    if dy != 0:
                        dy = int(dy / abs(dy))
                else:
                    # Normal movement based on the movement level
                    dx = random.randint(-npc["movement_range"], npc["movement_range"])
                    dy = random.randint(-npc["movement_range"], npc["movement_range"])

                new_x = npc["pos"][0] + dx
                new_y = npc["pos"][1] + dy

                # Check bounds and walls
                if (npc["start_pos"][0] - npc["movement_range"] <= new_x <= npc["start_pos"][0] + npc["movement_range"] and
                    npc["start_pos"][1] - npc["movement_range"] <= new_y <= npc["start_pos"][1] + npc["movement_range"] and
                    0 <= new_x < len(self.tile_map[0]) and 0 <= new_y < len(self.tile_map) and
                    self.tile_map[new_y][new_x][0] != '1'):  # Avoid walls
                    npc["pos"] = [new_x, new_y]

                npc["last_move_time"] = current_time

    def render(self):
        # Render the map and sprites
        self.screen.fill((0, 0, 0))
        self.draw_map()

        # Draw the player
        pygame.draw.rect(self.screen, (0, 255, 0), pygame.Rect(
            (self.player_pos[0] - self.camera_offset[0]) * 32,
            (self.player_pos[1] - self.camera_offset[1]) * 32,
            32, 32))

        # Draw the NPCs
        for npc_id, npc in self.npc_data.items():
            if npc["map"] == self.current_map:
                pygame.draw.rect(self.screen, npc["color"], pygame.Rect(
                    (npc["pos"][0] - self.camera_offset[0]) * 32,
                    (npc["pos"][1] - self.camera_offset[1]) * 32,
                    32, 32))

        # Render dialogue if any
        if self.current_dialogue and self.interacting:
            self.render_dialogue(self.current_dialogue)

        pygame.display.flip()

    def draw_map(self):
        for y in range(len(self.tile_map)):
            for x in range(len(self.tile_map[y])):  # Ensure we're within the current row's bounds
                tile = self.tile_map[y][x]
                draw_x = (x - self.camera_offset[0]) * 32
                draw_y = (y - self.camera_offset[1]) * 32

                if 0 <= draw_x < self.screen.get_width() and 0 <= draw_y < self.screen.get_height():
                    if tile == '1':  # Wall tile
                        self.screen.blit(self.wall_image, (draw_x, draw_y))
                    elif tile == '0':  # Floor tile
                        self.screen.blit(self.floor_image, (draw_x, draw_y))
                    elif tile.startswith('D['):  # Door tile
                        self.screen.blit(self.door_image, (draw_x, draw_y))
                    elif tile.startswith('P['):  # Portal tile
                        self.screen.blit(self.portal_image, (draw_x, draw_y))

    def render_dialogue(self, dialogue):
        font = pygame.font.Font(None, 36)
        # Draw background box
        pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(40, 380, 700, 180))
        pygame.draw.rect(self.screen, (255, 255, 255), pygame.Rect(40, 380, 700, 180), 2)  # White border

        # Render dialogue text with wrapping
        wrapped_text = self.wrap_text(dialogue["text"], font, 680)
        for i, line in enumerate(wrapped_text):
            text_surface = font.render(line, True, (255, 255, 255))
            self.screen.blit(text_surface, (50, 400 + i * 30))

        # Render dialogue options
        for i, option in enumerate(dialogue["options"]):
            option_text = f"{i + 1}. {option['response']}"
            option_surface = font.render(option_text, True, (200, 200, 200))
            self.screen.blit(option_surface, (50, 450 + (len(wrapped_text) + i) * 30))

        leave_text = f"{len(dialogue["options"]) + 1}. Smell you later"
        leave_surface = font.render(leave_text, True, (200, 200, 200))
        self.screen.blit(leave_surface, (50, 450 + (len(wrapped_text) + len(dialogue["options"])) * 30))

        # Check for dialogue option selection
        keys = pygame.key.get_pressed()
        for i in range(len(dialogue["options"])):
            if keys[pygame.K_1 + i]:
                self.select_dialogue_option(i)

        if keys[pygame.K_1 + len(dialogue["options"])]:
            self.leave_conversation()

    def wrap_text(self, text, font, max_width):
        """Wrap text to fit within a given width."""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = current_line + [word]
            width, _ = font.size(' '.join(test_line))
            if width <= max_width:
                current_line = test_line
            else:
                lines.append(' '.join(current_line))
                current_line = [word]

        lines.append(' '.join(current_line))  # Add the last line
        return lines

    def select_dialogue_option(self, option_index):
        npc = self.npc_data[self.current_npc]
        next_dialogue_key = self.current_dialogue["options"][option_index]["next"]
        npc["current_dialogue"] = next_dialogue_key
        self.current_dialogue = npc["dialogue"][next_dialogue_key]
        if not self.current_dialogue["options"]:
            self.interacting = False
            npc["moving"] = True  # Resume NPC movement after final dialogue
        else:
            self.render_dialogue(self.current_dialogue)  # Immediately transition to the next dialogue

    def leave_conversation(self):
        self.interacting = False
        self.current_dialogue = None
        self.npc_data[self.current_npc]["moving"] = True  # Resume NPC movement after leaving conversation
        self.npc_data[self.current_npc]["conversation_active"] = False  # Reset conversation

    def play_cutscene(self, images, fps=3):
        for image in images:
            self.screen.blit(image, (0, 0))
            pygame.display.flip()
            pygame.time.delay(int(1000 / fps))

class Inventory:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def render(self, screen):
        # Render the inventory UI
        font = pygame.font.Font(None, 36)
        for i, item in enumerate(self.items):
            item_text = font.render(item, True, (255, 255, 255))
            screen.blit(item_text, (10, 10 + i * 30))
