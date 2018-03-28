import pygame

# Icon is a very simple bitmap class, just associates a name and a pygame
# image (PNG loaded from icons directory) for each.
# There isn't a globally-declared fixed list of Icons.  Instead, the list
# is populated at runtime from the contents of the 'icons' directory.
class Icon:
  def __init__(self, name, iconPathLocal):
    self.name = name
    self.originalbitmap = pygame.image.load(iconPathLocal + '/' + name + '.png').convert(24)
    #self.bitmap = pygame.transform.smoothscale(self.originalbitmap, (self.originalbitmap.get_width(),self.originalbitmap.get_height()))
    self.bitmap = self.originalbitmap.convert(16)