from pygame import sprite, Surface, draw


def create_rect(width: int, height: int, fill_color, border_color=None, border_width=1):
    rect_sprite = sprite.Sprite()
    rect_sprite.image = Surface((width, height))
    rect_sprite.image.fill(fill_color)
    rect_sprite.rect = rect_sprite.image.get_rect()
    if border_color is not None:
        draw.rect(rect_sprite.image, border_color, (0, 0, width, height), border_width)
    return rect_sprite
