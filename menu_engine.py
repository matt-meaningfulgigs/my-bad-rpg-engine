import pygame

class MenuEngine:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 48)
        self.options = ["New Game", "Continue", "Exit"]
        self.selected_option = 0

    def start_menu(self):
        self.menu_loop()

    def menu_loop(self):
        running = True
        while running:
            self.render()
            running = self.handle_input()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.select_option()

        return True

    def select_option(self):
        if self.selected_option == 0:  # New Game
            return False  # Exiting the menu loop to start the game
        elif self.selected_option == 1:  # Continue (greyed out)
            pass  # No action, as continue is not implemented
        elif self.selected_option == 2:  # Exit
            pygame.quit()
            exit()

        return True

    def render(self):
        self.screen.fill((50, 50, 50))

        for i, option in enumerate(self.options):
            if i == self.selected_option:
                color = (255, 255, 255)
            else:
                color = (150, 150, 150)

            if option == "Continue":
                color = (100, 100, 100)  # Greyed out

            text_surface = self.font.render(option, True, color)
            x = self.screen.get_width() // 2 - text_surface.get_width() // 2
            y = self.screen.get_height() // 2 + i * 60
            self.screen.blit(text_surface, (x, y))

        pygame.display.flip()

    def end_menu(self):
        pass  # Exit menu and return to game
