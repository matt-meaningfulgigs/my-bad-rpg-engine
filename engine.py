import pygame
import json
import random
import time
from queue import Queue

# Import the conversation, combat, menu, and credits engines
from conversation_engine import ConversationEngine
from combat_engine import CombatEngine
from menu_engine import MenuEngine
from credits_engine import CreditsEngine

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.menu_engine = MenuEngine(screen)
        self.conversation_engine = ConversationEngine(screen, self)  # Pass self as game_instance
        self.combat_engine = CombatEngine(screen)
        self.credits_engine = CreditsEngine(screen)
        self.current_state = "menu"
        self.player_move_delay = 0.25
        self.last_player_move_time = time.time()

        # Emojis for heart and smoke effects
        self.heart_emoji = pygame.font.Font(None, 50).render("❤️", True, (255, 0, 0))
        self.smoke_emoji = pygame.font.Font(None, 50).render("🌩️", True, (169, 169, 169))

        self.current_npc = None  # To track the current NPC being interacted with
        self.run_game()

    def run_game(self):
        if self.current_state == "menu":
            self.menu_engine.start_menu()
            self.current_state = "exploring"
            self.load_assets()
            self.setup_game()

    def load_assets(self):
        self.maps = self.load_maps('data/maps.json')
        self.npcs = self.load_npcs('data/npcs.json')
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
        self.current_map = "map1"
        self.tile_map = self.maps[self.current_map]
        self.player_pos = [5, 5]
        self.current_dialogue = None
        self.interacting = False
        self.camera_offset = [0, 0]

        self.npc_data = {}
        for npc_id, npc_info in self.npcs.items():
            start_pos = self.find_nearest_non_wall(npc_info["start_pos"], npc_info["map"])
            movement_range = self.get_movement_range(npc_info["movement_level"])
            first_name = npc_info["name"].split()[0]  # Extract the first name

            # Handle seduction_level, converting it to an integer or None
            seduction_level = npc_info.get("seduction_level", None)
            if seduction_level is not None and seduction_level != 'None':
                try:
                    seduction_level = int(seduction_level)
                except ValueError:
                    seduction_level = None  # Fallback if conversion fails

            self.npc_data[npc_id] = {
                "name": first_name,
                "pos": start_pos,
                "start_pos": start_pos[:],
                "last_move_time": time.time(),
                "move_interval": random.uniform(2, 4),  # Random interval between 2 to 4 seconds
                "movement_level": npc_info["movement_level"],
                "movement_range": movement_range,
                "dialogue": npc_info["dialogue"],
                "current_dialogue": "start",
                "color": npc_info["color"],
                "moving": True,
                "map": npc_info["map"],
                "move_count": 0,
                "return_to_start": False,
                "seduction_level": seduction_level,
                "effect_start_time": None,
                "effect_type": None
            }

    def update(self):
        if self.current_state == "exploring":
            self.handle_exploration()
            self.handle_npc_movement()

    def handle_exploration(self):
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

        if keys[pygame.K_SPACE] and not self.interacting:
            npc = self.check_for_npc_interaction()
            if npc:
                self.current_npc = npc  # Track the current NPC
                self.current_state = "conversation"
                self.conversation_engine.start_conversation(npc, self.end_conversation)

    def check_for_npc_interaction(self):
        # Check if the player is adjacent to any NPC
        adjacent_positions = [
            (self.player_pos[0] - 1, self.player_pos[1]),
            (self.player_pos[0] + 1, self.player_pos[1]),
            (self.player_pos[0], self.player_pos[1] - 1),
            (self.player_pos[0], self.player_pos[1] + 1)
        ]
        for npc_id, npc in self.npc_data.items():
            if npc["map"] == self.current_map and tuple(npc["pos"]) in adjacent_positions:
                full_npc_data = {
                    "id": npc_id,
                    "name": npc_id.replace("_", " ").title(),
                    **npc
                }
                return full_npc_data
        return None

    def handle_npc_movement(self):
        current_time = time.time()
        for npc_id, npc in self.npc_data.items():
            if current_time - npc["last_move_time"] >= npc["move_interval"]:
                if npc["return_to_start"]:
                    self.move_npc_towards_start(npc)
                else:
                    self.move_npc_randomly(npc)

                npc["last_move_time"] = current_time
                npc["move_count"] += 1

                if npc["move_count"] >= 3:
                    npc["return_to_start"] = True
                else:
                    npc["move_interval"] = random.uniform(2, 4)

    def move_npc_randomly(self, npc):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        valid_directions = []
        start_x, start_y = npc["start_pos"]
        max_distance = npc["movement_range"]

        for dx, dy in directions:
            new_x, new_y = npc["pos"][0] + dx, npc["pos"][1] + dy
            if (0 <= new_x < len(self.tile_map[0]) and
                0 <= new_y < len(self.tile_map) and
                self.tile_map[new_y][new_x] != '1' and  # Not a wall
                (new_x, new_y) != tuple(self.player_pos) and  # Not the player's position
                not any((new_x, new_y) == tuple(other_npc["pos"]) for other_npc in self.npc_data.values())):  # Not another NPC
                distance_from_start = abs(new_x - start_x) + abs(new_y - start_y)
                if distance_from_start <= max_distance:
                    valid_directions.append((dx, dy))

        if valid_directions:
            direction = random.choice(valid_directions)
            npc["pos"][0] += direction[0]
            npc["pos"][1] += direction[1]

    def move_npc_towards_start(self, npc):
        start_x, start_y = npc["start_pos"]
        npc_x, npc_y = npc["pos"]

        dx = 0 if npc_x == start_x else (1 if start_x > npc_x else -1)
        dy = 0 if npc_y == start_y else (1 if start_y > npc_y else -1)

        new_x = npc["pos"][0] + dx
        new_y = npc["pos"][1] + dy

        if (0 <= new_x < len(self.tile_map[0]) and
            0 <= new_y < len(self.tile_map) and
            self.tile_map[new_y][new_x] != '1' and  # Not a wall
            (new_x, new_y) != tuple(self.player_pos) and  # Not the player's position
            not any((new_x, new_y) == tuple(other_npc["pos"]) for other_npc in self.npc_data.values())):  # Not another NPC
            npc["pos"][0] = new_x
            npc["pos"][1] = new_y
        else:
            npc["move_count"] = 0
            npc["return_to_start"] = False

    def find_nearest_non_wall(self, start_pos, map_name):
        queue = Queue()
        queue.put(start_pos)
        visited = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while not queue.empty():
            x, y = queue.get()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            if self.maps[map_name][y][x] != '1':
                return [x, y]

            for dx, dy in directions:
                new_x = x + dx
                new_y = y + dy
                if 0 <= new_x < len(self.maps[map_name][0]) and 0 <= new_y < len(self.maps[map_name]):
                    queue.put((new_x, new_y))

        return start_pos

    def get_movement_range(self, movement_level):
        if movement_level == "toodling":
            return 5  # Max range for toodling is 5 tiles
        elif movement_level == "restless":
            return 10  # Max range for restless is 10 tiles
        elif movement_level == "wandering":
            return 20  # Max range for wandering is 20 tiles
        else:
            return 5  # Default to 5 tiles if undefined

    def move_player(self, dx, dy):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        if (0 <= new_x < len(self.tile_map[0]) and
            0 <= new_y < len(self.tile_map) and
            self.tile_map[new_y][new_x] != '1' and  # Not a wall
            not any((new_x, new_y) == tuple(npc["pos"]) for npc in self.npc_data.values())):  # Not an NPC
            self.player_pos = [new_x, new_y]
            self.update_camera()

            tile = self.tile_map[new_y][new_x]
            if tile.startswith('D['):
                map_name = self.parse_map_transition(tile)
                self.change_map(map_name, self.get_door_position(map_name, f'D[{self.current_map}]'))
            elif tile.startswith('P['):
                map_name = self.parse_map_transition(tile)
                self.change_map(map_name, self.get_door_position(map_name, f'P[{self.current_map}]'))

    def parse_map_transition(self, tile):
        return tile[tile.index('[') + 1:tile.index(']')]

    def change_map(self, new_map, start_position):
        self.current_map = new_map
        self.tile_map = self.maps[new_map]
        self.player_pos = start_position
        self.update_camera()

    def get_door_position(self, map_name, door_type):
        for y, row in enumerate(self.maps[map_name]):
            for x, tile in enumerate(row):
                if tile == door_type:
                    return [x, y]
        return [1, 1]

    def update_camera(self):
        screen_width, screen_height = self.screen.get_size()
        tile_size = 32
        visible_tiles_x = screen_width // tile_size
        visible_tiles_y = screen_height // tile_size

        half_visible_x = visible_tiles_x // 2
        half_visible_y = visible_tiles_y // 2

        self.camera_offset[0] = max(0, min(self.player_pos[0] - half_visible_x, len(self.tile_map[0]) - visible_tiles_x))
        self.camera_offset[1] = max(0, min(self.player_pos[1] - half_visible_y, len(self.tile_map) - visible_tiles_y))

    def render(self):
        if self.current_state == "exploring":
            self.render_exploration()
        elif self.current_state == "conversation":
            self.conversation_engine.render_conversation()
        elif self.current_state == "combat":
            self.combat_engine.render()
        elif self.current_state == "menu":
            self.menu_engine.render()
        elif self.current_state == "credits":
            self.credits_engine.render()

    def render_exploration(self):
        self.screen.fill((0, 0, 0))
        self.draw_map()

        # Draw the player
        pygame.draw.rect(self.screen, (0, 255, 0), pygame.Rect(
            (self.player_pos[0] - self.camera_offset[0]) * 32,
            (self.player_pos[1] - self.camera_offset[1]) * 32,
            32, 32))

        # Font for NPC names
        font = pygame.font.Font(None, 24)

        # Draw the NPCs with their names
        for npc_id, npc in self.npc_data.items():
            if npc["map"] == self.current_map:
                # Draw the NPC
                npc_rect = pygame.Rect(
                    (npc["pos"][0] - self.camera_offset[0]) * 32,
                    (npc["pos"][1] - self.camera_offset[1]) * 32,
                    32, 32
                )
                pygame.draw.rect(self.screen, npc["color"], npc_rect)

                # Render the NPC's first name
                name_surface = font.render(npc["name"], True, (255, 255, 255))
                name_rect = name_surface.get_rect(center=npc_rect.center)

                # Blit the name onto the NPC's sprite
                self.screen.blit(name_surface, name_rect)

                # Render the effects (hearts or smoke)
                self.render_effects(npc, npc_rect)

        pygame.display.flip()

    def render_effects(self, npc, npc_rect):
        current_time = time.time()

        # Skip rendering effects if seduction level is None
        seduction_level = npc.get("seduction_level", None)
        
        if seduction_level is None:
            return
        
        # Ensure seduction_level is an integer
        try:
            seduction_level = int(seduction_level)
        except (ValueError, TypeError):
            return  # Skip rendering if seduction_level can't be converted to an integer

        if seduction_level >= 3:
            # Render hearts when fully seduced
            if "effect_start_time" not in npc or current_time - npc["effect_start_time"] > random.uniform(1.5, 2.5):
                npc["effect_start_time"] = current_time
                npc["effect_type"] = "heart"
                self.create_rising_effect(npc_rect, self.heart_emoji)
        elif seduction_level < 0:
            # Render smoke when seduction level is below 0
            if "effect_start_time" not in npc or current_time - npc["effect_start_time"] > random.uniform(1.5, 2.5):
                npc["effect_start_time"] = current_time
                npc["effect_type"] = "smoke"
                self.create_rising_effect(npc_rect, self.smoke_emoji)

    def create_rising_effect(self, npc_rect, emoji_surface):
        start_x = npc_rect.centerx
        start_y = npc_rect.top - 10
        effect_surface = emoji_surface.copy()
        effect_start_time = time.time()

        while time.time() - effect_start_time < 2:  # The effect lasts 2 seconds
            current_time = time.time()
            elapsed_time = current_time - effect_start_time
            fade = max(0, int(255 * (1 - elapsed_time / 2)))
            effect_surface.set_alpha(fade)

            self.screen.blit(effect_surface, (start_x, start_y - int(elapsed_time * 20)))
            pygame.display.flip()
            pygame.time.delay(50)  # Delay to create the floating effect

    def end_conversation(self):
        print("[Game] Conversation ended, returning to exploration mode.")
        
        if self.current_npc and self.current_npc.get("seduction_level") is not None:
            try:
                # Convert seduction_level to an integer if it is not already
                current_level = int(self.current_npc.get("seduction_level", 0))
            except ValueError:
                current_level = 0  # Default to 0 if the conversion fails

            # Adjust seduction level based on player's choices
            seduction_change = self.conversation_engine.npc.get("seduction_change", 0)
            new_seduction_level = current_level + seduction_change
            self.current_npc["seduction_level"] = min(max(new_seduction_level, -1), 3)  # Clamp between -1 and 3

            # Update the NPC's dialogue level based on the new seduction level
            self.current_npc["current_dialogue"] = f"seduction_{self.current_npc['seduction_level']}"
            if seduction_change > 0:
                print(f"[Game] Seduction level increased to {self.current_npc['seduction_level']}.")
            elif seduction_change < 0:
                print(f"[Game] Seduction level decreased to {self.current_npc['seduction_level']}.")

        self.current_npc = None  # Clear the current NPC after the conversation ends
        self.current_state = "exploring"
        self.interacting = False

    def draw_map(self):
        for y in range(len(self.tile_map)):
            for x in range(len(self.tile_map[y])):
                tile = self.tile_map[y][x]
                draw_x = (x - self.camera_offset[0]) * 32
                draw_y = (y - self.camera_offset[1]) * 32

                if 0 <= draw_x < self.screen.get_width() and 0 <= draw_y < self.screen.get_height():
                    if tile == '1':
                        self.screen.blit(self.wall_image, (draw_x, draw_y))
                    elif tile == '0':
                        self.screen.blit(self.floor_image, (draw_x, draw_y))
                    elif tile.startswith('D['):
                        self.screen.blit(self.door_image, (draw_x, draw_y))
                    elif tile.startswith('P['):
                        self.screen.blit(self.portal_image, (draw_x, draw_y))
