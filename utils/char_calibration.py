import pygame


def build_char_ramp(chars, font):
    brightness = []

    for c in chars:
        surf = font.render(c, False, (255, 255, 255))
        arr = pygame.surfarray.array3d(surf)

        # считаем среднюю яркость
        value = arr.mean()
        brightness.append((value, c))

    # сортируем от тёмного к светлому
    brightness.sort(key=lambda x: x[0])

    return "".join([c for _, c in brightness])