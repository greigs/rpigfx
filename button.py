import pygame
import sys
import struct
# Button is a simple tappable screen region.  Each has:
#  - bounding rect ((X,Y,W,H) in pixels)
#  - optional background color and/or Icon (or None), always centered
#  - optional foreground Icon, always centered
#  - optional single callback function
#  - optional single value passed to callback
# Occasionally Buttons are used as a convenience for positioning Icons
# but the taps are ignored.  Stacking order is important; when Buttons
# overlap, lowest/first Button in list takes precedence when processing
# input, and highest/last Button is drawn atop prior Button(s).  This is
# used, for example, to center an Icon by creating a passive Button the
# width of the full screen, but with other buttons left or right that
# may take input precedence (e.g. the Effect labels & buttons).
# After Icons are loaded at runtime, a pass is made through the global
# buttons[] list to assign the Icon objects (from names) to each Button.
class Button:
  def __init__(self, **kwargs):
    self.key = None # the key
    self.color = None # Background fill color, if any
    self.iconBg = None # Background Icon (atop color fill)
    self.staticBg = None
    self.animating = False
    self.iconFg = None # Foreground Icon (atop background)
    self.bg = None # Background Icon name
    self.fg = None # Foreground Icon name
    self.callback = None # Callback function
    self.value = None # Value passed to callback
    self.w = None
    self.h = None
    self.shift = None
    self.shiftimg = None
    self.rect = []
    for key, value in kwargs.iteritems():
      if key == 'color': self.color = value
      elif key == 'bg': self.bg = value
      elif key == 'fg': self.fg = value
      elif key == 'cb': self.callback = value
      elif key == 'value': self.value = value
      elif key == 'key': self.key = value
      elif key == 'shift': self.shift = value


  def selected(self, pos):
    x1 = self.rect[0]
    y1 = self.rect[1]
    x2 = x1 + self.rect[2] - 1
    y2 = y1 + self.rect[3] - 1
    if ((pos[0] >= x1) and (pos[0] <= x2) and
        (pos[1] >= y1) and (pos[1] <= y2)):
      if self.callback:
        if self.value is None: self.callback()
        else: self.callback(self.value)
      return True
    return False

  def draw(self, screen, iconPathLocal, loadSet, shift):
    #if self.shiftimg is None and self.shift is not None:
      #self.shiftimg = pygame.image.load(iconPathLocal + '/' + self.iconBg.name.split('.')[0] + '_shift.png').convert(16)
      #self.shiftimg = pygame.transform.scale(self.shiftimg, (self.w,self.h))
    if self.color:
      screen.fill(self.color, self.rect)
    if self.iconBg:
      if shift and self.shift is not None:
        img = self.shiftimg
      else:
        if self.staticBg is None or loadSet:
          self.staticBg = pygame.transform.smoothscale(self.iconBg.bitmap.convert(24), (self.w,self.h)).convert(16)
        if self.animating:
          img = pygame.transform.scale(self.iconBg.bitmap, (self.w,self.h))
        else:
          img = self.staticBg
      #img = self.iconBg.bitmap
      #img.set_alpha(255)
      screen.blit(img,(self.rect[0],self.rect[1]))
    if self.iconFg:
      img = pygame.transform.scale(self.iconFg.bitmap, (self.w,self.h))
      #img.set_alpha(255)
      screen.blit(img, (self.rect[0], self.rect[1]))