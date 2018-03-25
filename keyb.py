import atexit
import cPickle as pickle
import errno
import fnmatch
import io
import os
import os.path
import pygame
import stat
import threading
import re
import time
import sys
import struct
import pytweening
from pygame.locals import *
from subprocess import call
from threading import Thread
from pipes import Pipes





# UI classes ---------------------------------------------------------------

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
    self.key      = None # the key
    self.color    = None # Background fill color, if any
    self.iconBg   = None # Background Icon (atop color fill)
    self.staticBg = None # 
    self.animating= False
    self.iconFg   = None # Foreground Icon (atop background)
    self.bg       = None # Background Icon name
    self.fg       = None # Foreground Icon name
    self.callback = None # Callback function
    self.value    = None # Value passed to callback
    self.w        = None
    self.h        = None
    self.shift    = None
    self.shiftimg = None
    for key, value in kwargs.iteritems():
      if   key == 'color': self.color    = value
      elif key == 'bg'   : self.bg       = value
      elif key == 'fg'   : self.fg       = value
      elif key == 'cb'   : self.callback = value
      elif key == 'value': self.value    = value
      elif key == 'key'  : self.key      = value
      elif key == 'shift': self.shift    = value


  def selected(self, pos):
    x1 = self.rect[0]
    y1 = self.rect[1]
    x2 = x1 + self.rect[2] - 1
    y2 = y1 + self.rect[3] - 1
    if ((pos[0] >= x1) and (pos[0] <= x2) and
        (pos[1] >= y1) and (pos[1] <= y2)):
      if self.callback:
        if self.value is None: self.callback()
        else:                  self.callback(self.value)
      return True
    return False

  def draw(self, screen, iconPathLocal, loadSet):
    if self.shiftimg is None and self.shift is not None:
      self.shiftimg = pygame.image.load(iconPathLocal + '/' + self.iconBg.name.split('.')[0] + '_shift.png').convert(16)
      self.shiftimg = pygame.transform.scale(self.shiftimg, (self.w,self.h))
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
      screen.blit(img,
        (self.rect[0],
         self.rect[1]))

  def setBg(self, name):
    if name is None:
      self.iconBg = None
    else:
      for i in icons:
        if name == i.name:
          self.iconBg = i
          break


# UI callbacks -------------------------------------------------------------
# These are defined before globals because they're referenced by items in
# the global buttons[] list.


# Global stuff -------------------------------------------------------------

screenMode      =  9      # Current screen mode; default = viewfinder
screenModePrior = -1      # Prior screen mode (for detecting changes)
settingMode     =  4      # Last-used settings mode (default = storage)
storeMode       =  0      # Storage mode; default = Photos folder
storeModePrior  = -1      # Prior storage mode (for detecting changes)
sizeMode        =  0      # Image size; default = Large
fxMode          =  0      # Image effect; default = Normal
isoMode         =  0      # ISO settingl default = Auto
#iconPath        = 'icons' # Subdirectory containing UI bitmaps (PNG format)
saveIdx         = -1      # Image index for saving (-1 = none set yet)
loadIdx         = -1      # Image index for loading
scaled          = None    # pygame Surface w/last-loaded image
global selectedKeyset
selectedKeyset = 0
loadedKeyset    = -1
enableFifoLoop = False
rowNums = [15,15,15,14,15,11]

shift           = False
msg             = ""

#icons = [] # This list gets populated at startup

# buttons[] is a list of lists; each top-level list element corresponds
# to one screen mode (e.g. viewfinder, image playback, storage settings),
# and each element within those lists corresponds to one UI button.
# There's a little bit of repetition (e.g. prev/next buttons are
# declared for each settings screen, rather than a single reusable
# set); trying to reuse those few elements just made for an ugly
# tangle of code elsewhere.
keysets = ["standard", "premiere"]

buttons = []
rowNum = 0
for row in rowNums:
  thisrow = []
  for key in range(0,row):
    butName = str(rowNum) + "_" + str(key)
    thisrow.append(Button(bg = butName))
  buttons.append(thisrow)
  rowNum += 1

iconsets = []

def fifoLoop():
  global selectedKeyset
  msg = ""
  pipes = Pipes()
  while True:
    pipes.run()
    if pipes.msgcomplete:
      if msg != pipes.msg:
        if selectedKeyset == 1:
          selectedKeyset = 0
        else:
          selectedKeyset = 1
      msg = pipes.msg
      print(msg)
      pipes.reset_msg()




# Scan files in a directory, locating JPEGs with names matching the
# software's convention (IMG_XXXX.JPG), returning a tuple with the
# lowest and highest indices (or None if no matching files).
def imgRange(path):
  min = 9999
  max = 0
  try:
    for file in os.listdir(path):
      if fnmatch.fnmatch(file, 'IMG_[0-9][0-9][0-9][0-9].JPG'):
        i = int(file[4:8])
        if(i < min): min = i
        if(i > max): max = i
  finally:
    return None if min > max else (min, max)


def draw_text(screen, font, text, surfacewidth, surfaceheight):
  """Center text in window
  """
  fw, fh = font.size(text) # fw: font width,  fh: font height
  surface = font.render(text, True, (0, 0, 255))
  # // makes integer division in python3 
  screen.blit(surface, (0,0))

def apply_animation(b,keys,w,h, reverseanimation):
    if keys is not None and b.key is not None and len(keys) > 0 and keys[b.key]:
      b.animating = True
      if reverseanimation:
        b.w = w + int(pytweening.linear(1.0 - millis ) * 100)
        b.h = h + int(pytweening.linear(1.0 - millis ) * 100)      
      else:
        b.w = w + int(pytweening.linear( (millis )) * 100)
        b.h = h + int(pytweening.linear((millis )) * 100)
    else:
      b.h = h
      b.w = w
      b.animating = False

# Initialization -----------------------------------------------------------

# Init framebuffer/touchscreen environment variables
#os.putenv('SDL_VIDEODRIVER', 'windlib')
#os.putenv('SDL_FBDEV'      , '/dev/fb0')
#os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
#os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')

# Get user & group IDs for file & folder creation
# (Want these to be 'pi' or other user, not root)
#s = os.getenv("SUDO_UID")
#uid = int(s)
#s = os.getenv("SUDO_GID")
#gid = int(s) 

# Init pygame and screen

#os.putenv('SDL_VIDEODRIVER', 'fbcon')
pygame.display.init()
size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
pygame.init()
pygame.mixer.quit()
if pygame.display.Info().current_h == 480:
  screen = pygame.display.set_mode(size,pygame.HWSURFACE|pygame.FULLSCREEN,16)
else:
  screen = pygame.display.set_mode((1300,540),pygame.HWSURFACE,16)
screenPrescaled = screen
overlay = pygame.Surface( screen.get_size(), pygame.SRCALPHA, 16)
#screenPrescaled = pygame.Surface((800, 480), flags=pygame.HWSURFACE, depth=16)
clock=pygame.time.Clock()
windoww = pygame.display.Info().current_w
windowh = pygame.display.Info().current_h
pygame.mouse.set_visible(False)
font = pygame.font.SysFont('mono', 24, bold=True)
pygame.display.set_caption('')


# Load all icons at startup.
for iconPathLocal in keysets:
  icons = []
  for file in os.listdir('keysets/' + iconPathLocal):
    if fnmatch.fnmatch(file, '*.png'):
      icons.append(Icon(file.split('.')[0], 'keysets/' + iconPathLocal))
  iconsets.append(icons)

# Assign Icons to Buttons, now that they're loaded

# Main loop ----------------------------------------------------------------
framecount = 0
# Desired framerate in frames per second. Try out other values.              
FPS = 4
# How many seconds the "game" is played.
playtime = 0.0
loadset = False


if enableFifoLoop:
  t = Thread(target=fifoLoop)
  t.start()

while(True):  
  
  if selectedKeyset != loadedKeyset:
    for s in buttons:        # For each screenful of buttons...
      for b in s:            #  For each button on screen...
        for i in iconsets[selectedKeyset]:      #   For each icon...
          if b.bg == i.name: #    Compare names; match?
            b.iconBg = i     #     Assign Icon to Button
            #b.bg     = None  #     Name no longer used; allow garbage collection # TODO GrS - decide to remove or not
          if b.fg == i.name:
            b.iconFg = i
            #b.fg     = None
    loadset = True
    loadedKeyset = selectedKeyset
  else:
    loadset = False

  # Do not go faster than this framerate.
  milliseconds = clock.tick(FPS) 
  playtime += milliseconds / 1000.0 
  keys = None

  framecount = framecount + 1

  for event in pygame.event.get():
    if event.type is KEYDOWN:
      keys = pygame.key.get_pressed()
      if keys[pygame.K_ESCAPE]:
        pygame.quit()
        sys.exit()
      if keys[pygame.K_LSHIFT]:
        shift = True
    elif event.type is KEYUP:
      keys = pygame.key.get_pressed()
      if not keys[pygame.K_LSHIFT]:
        shift = False
  
  keys = pygame.key.get_pressed()
  # Overlay buttons on display and update
  screenPrescaled.fill(0)
  
  lft = 0

  millis = ((round(time.time() * 1000)) % 1000)
  reverseanimation = (millis > 500)
  millis = millis / 1000

  with open('keysets/' + keysets[0]  + '/out.txt') as f:
    lines = [line.rstrip('\n') for line in f]
  keycount = 0
  scale = 0.3


  for row in range(6):
    for i,b in enumerate(buttons[row]):
      k = lines[keycount].split(',')
      w = int(round( int(k[2]) * scale ))
      h = int(round(int(k[3]) * scale))
      lft = int(round(int(k[0]) * scale))
      tp = int(round(int(k[1]) * scale))
      b.rect = ( lft, tp, w, h)
      apply_animation(b,keys,w,h, reverseanimation)
      keycount += 1
    
  for row in range(5, -1, -1):
    for i,b in enumerate(reversed(buttons[row])):
      b.draw(screenPrescaled, 'keysets/' + keysets[selectedKeyset], loadset)


  draw_text(screenPrescaled, font, "FPS: {:6.3}{}TIME: {:6.3} SECONDS".format(
                           clock.get_fps(), " "*5, playtime), windoww, windowh)

  #pygame.transform.scale(screenPrescaled, (windoww, windowh), screen)
  
  
  overlay.fill((int(pytweening.linear(millis ) * 100),int(pytweening.linear(1.0 - millis ) * 100),int(pytweening.linear(1.0 - millis ) * 50),0))
  #screen.blit(overlay, (0,0), None, BLEND_MIN)
  
  pygame.display.update()
 


  screenModePrior = screenMode
