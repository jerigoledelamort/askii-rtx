import pygame


class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.clicked = False

    def handle(self, event, x_offset=0, mouse_pos=None, scroll_offset=0):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            source_pos = mouse_pos if mouse_pos is not None else event.pos
            local_pos = (source_pos[0] - x_offset, source_pos[1] + scroll_offset)
            if self.rect.collidepoint(local_pos):
                self.clicked = True

    def draw(self, surface, font, y_offset=0):
        rect = self.rect.move(0, y_offset)
        pygame.draw.rect(surface, (120, 120, 120), rect)
        text = font.render(self.text, True, (255, 255, 255))
        surface.blit(text, (rect.x + 10, rect.y + 5))


class Slider:
    def __init__(self, x, y, w, min_val, max_val, value, label, is_int=False):
        self.rect = pygame.Rect(x, y, w, 10)
        self.min = min_val
        self.max = max_val
        self.value = value
        self.label = label
        self.dragging = False
        self.is_int = is_int

    def handle(self, event, x_offset=0, mouse_pos=None, scroll_offset=0):
        source_pos = mouse_pos if mouse_pos is not None else getattr(event, "pos", None)

        if source_pos is None:
            return

        local_pos = (source_pos[0] - x_offset, source_pos[1] + scroll_offset)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(local_pos):
                self.dragging = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        if event.type == pygame.MOUSEMOTION and self.dragging:
            x = local_pos[0]
            t = (x - self.rect.x) / self.rect.w
            t = max(0, min(1, t))

            value = self.min + t * (self.max - self.min)
            self.value = int(value) if self.is_int else value

    def draw(self, surface, font, y_offset=0):
        rect = self.rect.move(0, y_offset)
        pygame.draw.rect(surface, (80, 80, 80), rect)

        t = (self.value - self.min) / (self.max - self.min)
        knob_x = rect.x + t * rect.w

        pygame.draw.circle(surface, (200, 200, 200), (int(knob_x), rect.y + 5), 6)

        if self.is_int:
            text = font.render(f"{self.label}: {int(self.value)}", True, (255, 255, 255))
        else:
            text = font.render(f"{self.label}: {self.value:.2f}", True, (255, 255, 255))

        surface.blit(text, (rect.x, rect.y - 20))


class Checkbox:
    def __init__(self, x, y, size, label, value):
        self.rect = pygame.Rect(x, y, size, size)
        self.label = label
        self.value = value

    def handle(self, event, x_offset=0, mouse_pos=None, scroll_offset=0):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            source_pos = mouse_pos if mouse_pos else event.pos
            local_pos = (source_pos[0] - x_offset, source_pos[1] + scroll_offset)
            if self.rect.collidepoint(local_pos):
                self.value = 1 - self.value

    def draw(self, surface, font, y_offset=0):
        rect = self.rect.move(0, y_offset)
        pygame.draw.rect(surface, (80, 80, 80), rect)
        if self.value:
            pygame.draw.rect(surface, (200, 200, 200), rect.inflate(-6, -6))
        text = font.render(self.label, True, (255, 255, 255))
        surface.blit(text, (rect.x + 30, rect.y))


class Dropdown:
    def __init__(self, x, y, w, h, options, selected_index, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.selected_index = selected_index
        self.label = label
        self.expanded = False
        self.changed = False

    def handle(self, event, x_offset=0, mouse_pos=None, scroll_offset=0):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        source_pos = mouse_pos if mouse_pos is not None else event.pos
        local_pos = (source_pos[0] - x_offset, source_pos[1] + scroll_offset)

        if self.rect.collidepoint(local_pos):
            self.expanded = not self.expanded
            return

        if self.expanded:
            for i in range(len(self.options)):
                option_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + self.rect.h * (i + 1),
                    self.rect.w,
                    self.rect.h,
                )
                if option_rect.collidepoint(local_pos):
                    if self.selected_index != i:
                        self.selected_index = i
                        self.changed = True
                    self.expanded = False
                    return

        self.expanded = False

    def draw(self, surface, font, y_offset=0):
        rect = self.rect.move(0, y_offset)
        label_text = font.render(self.label, True, (255, 255, 255))
        surface.blit(label_text, (rect.x, rect.y - 20))

        pygame.draw.rect(surface, (80, 80, 80), rect)
        value_text = font.render(self.options[self.selected_index], True, (255, 255, 255))
        surface.blit(value_text, (rect.x + 8, rect.y + 5))

        if self.expanded:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(
                    rect.x,
                    rect.y + rect.h * (i + 1),
                    rect.w,
                    rect.h,
                )
                color = (110, 110, 110) if i == self.selected_index else (60, 60, 60)
                pygame.draw.rect(surface, color, option_rect)
                option_text = font.render(option, True, (255, 255, 255))
                surface.blit(option_text, (option_rect.x + 8, option_rect.y + 5))