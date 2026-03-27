import pygame

class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.clicked = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.clicked = True

    def draw(self, surface, font):
        pygame.draw.rect(surface, (120, 120, 120), self.rect)
        text = font.render(self.text, True, (255, 255, 255))
        surface.blit(text, (self.rect.x + 10, self.rect.y + 5))

class Slider:
    def __init__(self, x, y, w, min_val, max_val, value, label, is_int=False):
        self.rect = pygame.Rect(x, y, w, 10)
        self.min = min_val
        self.max = max_val
        self.value = value
        self.label = label
        self.dragging = False
        self.is_int = is_int  # 🔥 тип значения

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True

        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        if event.type == pygame.MOUSEMOTION and self.dragging:
            x = event.pos[0]
            t = (x - self.rect.x) / self.rect.w
            t = max(0, min(1, t))

            value = self.min + t * (self.max - self.min)

            if self.is_int:
                self.value = int(value)
            else:
                self.value = value

    def draw(self, surface, font):
        pygame.draw.rect(surface, (80, 80, 80), self.rect)

        t = (self.value - self.min) / (self.max - self.min)
        knob_x = self.rect.x + t * self.rect.w

        pygame.draw.circle(surface, (200, 200, 200), (int(knob_x), self.rect.y + 5), 6)

        # 🔥 отображение
        if self.is_int:
            text = font.render(f"{self.label}: {int(self.value)}", True, (255, 255, 255))
        else:
            text = font.render(f"{self.label}: {self.value:.2f}", True, (255, 255, 255))

        surface.blit(text, (self.rect.x, self.rect.y - 20))