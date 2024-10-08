import pygame
from npcs import NPCManager

class ConversationEngine:
    def __init__(self, screen, game_instance):
        self.screen = screen
        self.game_instance = game_instance
        self.npc_manager = NPCManager()
        self.current_dialogue = None
        self.npc = None
        self.character_image = None
        self.font = pygame.font.Font(None, 36)
        self.conversation_active = False  # Track if a conversation is active
        self.on_end = None  # Callback for when the conversation ends

    def start_conversation(self, npc, on_end_callback):
        print(f"[ConversationEngine] Starting conversation with NPC: {npc['name']}")
        self.npc = npc

        # Retrieve the current seduction level from the NPCManager
        seduction_level = self.npc_manager.get_seduction_level(npc["id"])
        npc["seduction_level"] = seduction_level
        
        # Construct the correct dialogue key
        if seduction_level == -99:
            dialogue_key = "seduction_-99"
        else:
            dialogue_key = f"seduction_{seduction_level}"
        
        # Attempt to get the start dialogue under the correct key
        self.current_dialogue = npc["dialogue"].get(dialogue_key, {}).get("start", None)

        if self.current_dialogue is None:
            print(f"[ConversationEngine] No valid dialogue found for {npc['name']} with seduction level {seduction_level}. Falling back to start dialogue.")
            self.current_dialogue = npc["dialogue"].get("start", None)

        # If still no valid dialogue, end the conversation
        if self.current_dialogue is None:
            print(f"[ConversationEngine] No valid start dialogue found for {npc['name']}. Ending conversation.")
            self.conversation_active = False
            if on_end_callback:
                on_end_callback()
            return

        self.conversation_active = True
        self.on_end = on_end_callback

        # Attempt to load the character image
        try:
            self.character_image = pygame.image.load(f'assets/characters/{npc["name"].lower().replace(" ", "_")}.png').convert_alpha()
        except FileNotFoundError:
            # Create a large colored square as a placeholder using the NPC's color from the npcs.json file
            self.character_image = self.create_placeholder_image(npc["color"])

        self.handle_conversation()

    def create_placeholder_image(self, color):
        placeholder = pygame.Surface((200, 400))
        placeholder.fill(color)
        return placeholder

    def handle_conversation(self):
        print("[ConversationEngine] Handling conversation...")
        while self.conversation_active and self.current_dialogue:
            print(f"[ConversationEngine] Current Dialogue: {self.current_dialogue['text'] if self.current_dialogue else 'None'}")
            self.render_conversation()
            self.wait_for_player_input()
        print("[ConversationEngine] Exiting conversation loop.")

    def render_conversation(self):
        if self.current_dialogue is None:
            return  # Avoid rendering if there's no valid dialogue

        self.screen.fill((0, 0, 0), (0, 380, 800, 220))
        self.screen.blit(self.character_image, (600, 180))

        pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(40, 380, 700, 180))
        pygame.draw.rect(self.screen, (255, 255, 255), pygame.Rect(40, 380, 700, 180), 2)

        wrapped_text = self.wrap_text(self.current_dialogue["text"], self.font, 680)
        for i, line in enumerate(wrapped_text):
            text_surface = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(text_surface, (50, 400 + i * 30))

        for i, option in enumerate(self.current_dialogue["options"]):
            option_text = f"{i + 1}. {option['response']}"
            option_surface = self.font.render(option_text, True, (200, 200, 200))
            self.screen.blit(option_surface, (50, 450 + (len(wrapped_text) + i) * 30))

        leave_text = f"{len(self.current_dialogue['options']) + 1}. Smell you later"
        leave_surface = self.font.render(leave_text, True, (200, 200, 200))
        self.screen.blit(leave_surface, (50, 450 + (len(wrapped_text) + len(self.current_dialogue['options'])) * 30))

        pygame.display.flip()

    def wait_for_player_input(self):
        print("[ConversationEngine] Waiting for player input...")
        waiting_for_input = True
        total_options = len(self.current_dialogue["options"]) + 1  # Including "Smell you later"
        while waiting_for_input and self.conversation_active:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    print(f"[ConversationEngine] Key pressed: {pygame.key.name(event.key)}")
                    if pygame.K_1 <= event.key <= pygame.K_1 + total_options - 1:
                        option_index = event.key - pygame.K_1
                        if option_index < len(self.current_dialogue["options"]):
                            print(f"[ConversationEngine] Player selected option {option_index + 1}: {self.current_dialogue['options'][option_index]['response']}")
                            self.pending_seduction_change = self.current_dialogue["options"][option_index].get("seduction_change", None)
                            print(f"[ConversationEngine] Pending seduction change: {self.pending_seduction_change}")
                            self.select_dialogue_option(option_index)
                            waiting_for_input = False
                        elif option_index == len(self.current_dialogue["options"]):
                            print(f"[ConversationEngine] Player selected 'Smell you later' option.")
                            self.end_conversation()
                            waiting_for_input = False
                        else:
                            print(f"[ConversationEngine] Option {option_index + 1} is out of range.")
                    else:
                        print(f"[ConversationEngine] Key press not recognized for any option.")

    def select_dialogue_option(self, option_index):
        next_dialogue_key = self.current_dialogue["options"][option_index]["next"]
        print(f"[ConversationEngine] Selected dialogue option {option_index + 1}, moving to: {next_dialogue_key}")
        
        # Determine the current seduction level and branch
        seduction_level = self.npc_manager.get_seduction_level(self.npc["id"])
        if seduction_level == -99:
            seduction_key = "seduction_-99"
        else:
            seduction_key = f"seduction_{seduction_level}"
        
        # Access the dialogue branch
        dialogue_branch = self.npc["dialogue"].get(seduction_key, None)
        
        if dialogue_branch:
            self.current_dialogue = dialogue_branch.get(next_dialogue_key, None)
        else:
            self.current_dialogue = None

        # If this is the final dialogue with no options, apply seduction change if any
        if self.current_dialogue is None or not self.current_dialogue.get("options"):
            self.apply_seduction_change()  # Apply any pending seduction change
            print(f"[ConversationEngine] Ending conversation with final dialogue.")
            self.end_conversation()
        else:
            print(f"[ConversationEngine] Continuing conversation with dialogue: {self.current_dialogue['text']}")

    def apply_seduction_change(self):
        # Apply seduction change if defined in the current dialogue
        seduction_change = self.current_dialogue.get("seduction_change", None)
        if seduction_change is not None:
            self.npc_manager.update_seduction_level(self.npc["id"], seduction_change)
            print(f"[ConversationEngine] Seduction level for {self.npc['name']} updated to {self.npc_manager.get_seduction_level(self.npc['id'])} in NPCManager list")

    def end_conversation(self):
        # Apply any final seduction change if conversation ends with a seduction-changing dialogue
        self.apply_seduction_change()
        print("[ConversationEngine] Ending conversation.")
        self.current_dialogue = None
        self.conversation_active = False
        if self.on_end and self.on_end != self.end_conversation:
            self.on_end()

    def wrap_text(self, text, font, max_width):
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

        lines.append(' '.join(current_line))
        return lines
