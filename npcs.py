class NPCManager:
    def __init__(self):
        self.npcs = {
            "homer": {"name": "Homer Simpson", "seduction_level": -99},
            "marge": {"name": "Marge Simpson", "seduction_level": 0},
            "bart": {"name": "Bart Simpson", "seduction_level": -99},
            "edna": {"name": "Edna Krabappel", "seduction_level": 0},
            "moe": {"name": "Moe Szyslak", "seduction_level": -99},
            "selma": {"name": "Selma Bouvier", "seduction_level": 0},
            "lisa": {"name": "Lisa Simpson", "seduction_level": -99},
            "maggie": {"name": "Maggie Simpson", "seduction_level": -99},
            "agnes": {"name": "Agnes Skinner", "seduction_level": 0},
            "maude": {"name": "Maude Flanders", "seduction_level": 0},
            "kirk": {"name": "Kirk Van Houten", "seduction_level": -99},
            "luanne": {"name": "Luanne Van Houten", "seduction_level": 0},
            "mr_burns": {"name": "Mr. Burns", "seduction_level": -99},
            "milhouse": {"name": "Milhouse Van Houten", "seduction_level": -99},
            "apu": {"name": "Apu Nahasapeemapetilon", "seduction_level": -99},
            "nelson": {"name": "Nelson Muntz", "seduction_level": -99},
            "ralph": {"name": "Ralph Wiggum", "seduction_level": -99},
            "smithers": {"name": "Waylon Smithers", "seduction_level": 0},
        }

    def get_npc(self, npc_name):
        """Retrieve the NPC's full data by their name."""
        return self.npcs.get(npc_name, None)

    def get_seduction_level(self, npc_name):
        return self.npcs.get(npc_name, {}).get("seduction_level", 0)

    def update_seduction_level(self, npc_name, change):
        if npc_name in self.npcs:
            self.npcs[npc_name]["seduction_level"] += change
            # Optional: Add bounds to seduction levels (e.g., -99 to 3)
            self.npcs[npc_name]["seduction_level"] = max(-99, min(3, self.npcs[npc_name]["seduction_level"]))
            # Log the updated seduction level
            print(f"[NPCManager] {self.npcs[npc_name]['name']}'s seduction level updated to {self.npcs[npc_name]['seduction_level']}")

    def save_state(self):
        # Implement saving to a file if needed
        pass

    def load_state(self):
        # Implement loading from a file if needed
        pass
