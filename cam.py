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
import time
import sys
import pytweening
from pygame.locals import *
from subprocess import call  


# UI classes ---------------------------------------------------------------

# Icon is a very simple bitmap class, just associates a name and a pygame
# image (PNG loaded from icons directory) for each.
# There isn't a globally-declared fixed list of Icons.  Instead, the list
# is populated at runtime from the contents of the 'icons' directory.

class Icon:

	def __init__(self, name):
	  self.name = name
	  self.originalbitmap = pygame.image.load(iconPath + '/' + name + '.png').convert(24)
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

	def __init__(self, rect, **kwargs):
	  self.rect     = rect # Bounds
	  self.key      = None # the key
	  self.color    = None # Background fill color, if any
	  self.iconBg   = None # Background Icon (atop color fill)
	  self.iconFg   = None # Foreground Icon (atop background)
	  self.bg       = None # Background Icon name
	  self.fg       = None # Foreground Icon name
	  self.callback = None # Callback function
	  self.value    = None # Value passed to callback
	  self.w        = None
	  self.h        = None
	  for key, value in kwargs.iteritems():
	    if   key == 'color': self.color    = value
	    elif key == 'bg'   : self.bg       = value
	    elif key == 'fg'   : self.fg       = value
	    elif key == 'cb'   : self.callback = value
	    elif key == 'value': self.value    = value
	    elif key == 'key'  : self.key      = value

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

	def draw(self, screen):
	  if self.color:
	    screen.fill(self.color, self.rect)
	  if self.iconBg:
	    img = pygame.transform.scale(self.iconBg.bitmap, (self.w,self.h))
	    #img = self.iconBg.bitmap
	    #img.set_alpha(255)
	    screen.blit(img,
	      (self.rect[0],
	       self.rect[1]))
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
iconPath        = 'icons' # Subdirectory containing UI bitmaps (PNG format)
saveIdx         = -1      # Image index for saving (-1 = none set yet)
loadIdx         = -1      # Image index for loading
scaled          = None    # pygame Surface w/last-loaded image

icons = [] # This list gets populated at startup

# buttons[] is a list of lists; each top-level list element corresponds
# to one screen mode (e.g. viewfinder, image playback, storage settings),
# and each element within those lists corresponds to one UI button.
# There's a little bit of repetition (e.g. prev/next buttons are
# declared for each settings screen, rather than a single reusable
# set); trying to reuse those few elements just made for an ugly
# tangle of code elsewhere.

buttons = [
   #row 1
   [Button((  0,  0, 128, 128), bg='adobe_Ai'),
   Button((  0,  0, 128, 128), bg='adobe_Dw'),
   Button((  0,  0, 128, 128), bg='adobe_Fl'),
   Button((  0,  0, 128, 128), bg='adobe_Fw'),
   Button((  0,  0, 128, 128), bg='adobe_Id'),
   Button((  0,  0, 128, 128), bg='adobe_Ps'),
   Button((  0,  0, 128, 128), bg='axialis'),
   Button((  0,  0, 128, 128), bg='adobe_Ai'),
   Button((  0,  0, 128, 128), bg='adobe_Dw'),
   Button((  0,  0, 128, 128), bg='adobe_Fl'),
   Button((  0,  0, 128, 128), bg='adobe_Fw'),
   Button((  0,  0, 128, 128), bg='adobe_Id'),
   Button((  0,  0, 128, 128), bg='adobe_Ps'),
   Button((  0,  0, 128, 128), bg='axialis')
   ],
   
   #row 2
   [Button((  0,  0, 128, 128), bg='chrome'),
   Button((  0,  0, 128, 128), bg='dropbox', key=pygame.K_q),
   Button((  0,  0, 128, 128), bg='email', key=pygame.K_w),
   Button((  0,  0, 128, 128), bg='explorer', key=pygame.K_e),
   Button((  0,  0, 128, 128), bg='firefox', key=pygame.K_r),
   Button((  0,  0, 128, 128), bg='flashget', key=pygame.K_t),
   Button((  0,  0, 128, 128), bg='foobar', key=pygame.K_y),
   Button((  0,  0, 128, 128), bg='chrome'),
   Button((  0,  0, 128, 128), bg='dropbox'),
   Button((  0,  0, 128, 128), bg='email'),
   Button((  0,  0, 128, 128), bg='explorer'),
   ],
   
   #row 3
   [Button((  0,  0, 128, 128), bg='games'),
   Button((  0,  0, 128, 128), bg='googleEarth'),
   Button((  0,  0, 128, 128), bg='handbrake'),
   Button((  0,  0, 128, 128), bg='mediaPlayer'),
   Button((  0,  0, 128, 128), bg='notepad'),
   Button((  0,  0, 128, 128), bg='opera'),
   Button((  0,  0, 128, 128), bg='safari'),
   Button((  0,  0, 128, 128), bg='games'),
   Button((  0,  0, 128, 128), bg='googleEarth'),
   Button((  0,  0, 128, 128), bg='handbrake'),
   Button((  0,  0, 128, 128), bg='mediaPlayer'),
   Button((  0,  0, 128, 128), bg='notepad'),
   ],
   
   #row 4
   [Button((  0,  0, 128, 128), bg='sonyericsson'),
   Button((  0,  0, 128, 128), bg='totalCommander'),
   Button((  0,  0, 128, 128), bg='uTorrent'),
   Button((  0,  0, 128, 128), bg='vlcPlayer'),
   Button((  0,  0, 128, 128), bg='webcam'),
   Button((  0,  0, 128, 128), bg='xbmc'),
   Button((  0,  0, 128, 128), bg='safari'),
   Button((  0,  0, 128, 128), bg='sonyericsson'),
   Button((  0,  0, 128, 128), bg='totalCommander'),
   Button((  0,  0, 128, 128), bg='uTorrent'),
   Button((  0,  0, 128, 128), bg='vlcPlayer'),
   Button((  0,  0, 128, 128), bg='webcam'),
   ],
   
   #row 5
   [Button((  0,  0, 128, 128), bg='adobe_Ai'),
   Button((  0,  0, 128, 128), bg='adobe_Dw'),
   Button((  0,  0, 128, 128), bg='adobe_Fl'),
   Button((  0,  0, 128, 128), bg='adobe_Fw'),
   Button((  0,  0, 128, 128), bg='adobe_Id'),
   Button((  0,  0, 128, 128), bg='adobe_Ps'),
   Button((  0,  0, 128, 128), bg='axialis'),
   Button((  0,  0, 128, 128), bg='adobe_Ai'),
   Button((  0,  0, 128, 128), bg='adobe_Dw'),
   Button((  0,  0, 128, 128), bg='adobe_Fl'),
   Button((  0,  0, 128, 128), bg='adobe_Fw'),
   Button((  0,  0, 128, 128), bg='adobe_Id'),
   ],
   
   #row 6
   [Button((  0,  0, 128, 128), bg='chrome'),
   Button((  0,  0, 128, 128), bg='dropbox'),
   Button((  0,  0, 128, 128), bg='email'),
   Button((  0,  0, 128, 128), bg='explorer'),
   Button((  0,  0, 128, 128), bg='firefox'),
   Button((  0,  0, 128, 128), bg='flashget'),
   Button((  0,  0, 128, 128), bg='foobar'),
   Button((  0,  0, 128, 128), bg='chrome'),
   ]
   
]


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
	surface = font.render(text, True, (255, 255, 255))
	# // makes integer division in python3 
	screen.blit(surface, (0,0))

def apply_animation(b,keys,w,h, reverseanimation):
    if keys is not None and b.key is not None and len(keys) > 0 and keys[b.key]:
      if reverseanimation:
        b.w = w + int(pytweening.linear(1.0 - millis ) * 100)
        b.h = h + int(pytweening.linear(1.0 - millis ) * 100)      
      else:
        b.w = w + int(pytweening.linear( (millis )) * 100)
        b.h = h + int(pytweening.linear((millis )) * 100)
    else:
      b.h = h
      b.w = w

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
screen = pygame.display.set_mode(size,pygame.HWSURFACE|pygame.FULLSCREEN,16)
#screen = pygame.display.set_mode((800,480),pygame.HWSURFACE,16)
screenPrescaled = screen
#screenPrescaled = pygame.Surface((800, 480), flags=pygame.HWSURFACE, depth=16)
clock=pygame.time.Clock()
windoww = pygame.display.Info().current_w
windowh = pygame.display.Info().current_h
#pygame.mouse.set_visible(False)
font = pygame.font.SysFont('mono', 24, bold=True)



# Load all icons at startup.
for file in os.listdir(iconPath):
  if fnmatch.fnmatch(file, '*.png'):
    icons.append(Icon(file.split('.')[0]))

# Assign Icons to Buttons, now that they're loaded
for s in buttons:        # For each screenful of buttons...
  for b in s:            #  For each button on screen...
    for i in icons:      #   For each icon...
      if b.bg == i.name: #    Compare names; match?
        b.iconBg = i     #     Assign Icon to Button
        b.bg     = None  #     Name no longer used; allow garbage collection
      if b.fg == i.name:
        b.iconFg = i
        b.fg     = None


# Main loop ----------------------------------------------------------------
framecount = 0
# Desired framerate in frames per second. Try out other values.              
FPS = 20
# How many seconds the "game" is played.
playtime = 0.0
while(True):
  # Do not go faster than this framerate.
  milliseconds = clock.tick(FPS) 
  playtime += milliseconds / 1000.0 
  keys = None

  framecount = framecount + 1
  # Process touchscreen input
  while True:
    for event in pygame.event.get():
      if(event.type is KEYDOWN):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_x]:
          pygame.quit()
          sys.exit()
        #pos = pygame.mouse.get_pos()
        #for b in buttons[screenMode]:
          #if b.selected(pos): break
    # If in viewfinder or settings modes, stop processing touchscreen
    # and refresh the display to show the live preview.  In other modes
    # (image playback, etc.), stop and refresh the screen only when
    # screenMode changes.
    if screenMode >= 3 or screenMode != screenModePrior: break

  
  keys = pygame.key.get_pressed()
  # Overlay buttons on display and update
  screenPrescaled.fill(0)
  
  lft = 0
  top = 0
  leftpadding = 0
  spacing = 2 
  normalheight = 82 
  normalwidth = 82 
  topheight = 56
  topwidth = 56
  row2key0w = 82
  row2key10w = 180
  row3key0w = 82
  row3key11w = 110 
  row4key0w = 110 
  row5key0w = 110 
  row6key0w = 110 
  row6key3w = 480 
  millis = ((round(time.time() * 1000)) % 1000)
  reverseanimation = (millis > 500)
  millis = millis / 1000

  
  # Row 1
  for i,b in enumerate(buttons[0]):
    w = topwidth
    h = topheight
    lft = leftpadding + (i * (spacing + topwidth))
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation)
    
  # Row 2
  top = top + topheight + spacing

  for i,b in enumerate(buttons[1]):
    w = normalwidth
    h = normalheight
    if i == 0:
      lft = 0
      w = row2key0w
    elif i == 10:
      w = row2key10w
      lft = ((i - 1) * (spacing + normalwidth)) + row2key0w + spacing   
    else:
      lft = ((i - 1) * (spacing + normalwidth)) + row2key0w + spacing
      
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation)

  # Row 3
  top = top + normalheight + spacing

  for i,b in enumerate(buttons[2]):
    w = normalwidth
    h = normalheight
    if i == 0:
      lft = 0
      w = row3key0w
    elif i == 11:
      w = row3key11w
      lft = ((i - 1) * (spacing + normalwidth)) + row3key0w + spacing   
    else:
      lft = ((i - 1) * (spacing + normalwidth)) + row3key0w + spacing
      
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation)

  # Row 4
  top = top + normalheight + spacing

  for i,b in enumerate(buttons[3]):
    w = normalwidth
    h = normalheight
    if i == 0:
      lft = 0
      w = row4key0w
    else:
      lft = ((i - 1) * (spacing + normalwidth)) + row4key0w + spacing
      
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation)
 
  # Row 5
  top = top + normalheight + spacing

  for i,b in enumerate(buttons[4]):
    w = normalwidth
    h = normalheight
    if i == 0:
      lft = 0
      w = row5key0w
    else:
      lft = ((i - 1) * (spacing + normalwidth)) + row5key0w + spacing
      
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation) 

  # Row 6
  top = top + normalheight + spacing

  for i,b in enumerate(buttons[5]):
    w = normalwidth
    h = normalheight
    if i == 0:
      lft = 0
      w = row6key0w
    elif i == 3:
      w = row6key3w
      lft = ((i - 1) * (spacing + normalwidth)) + row6key0w + spacing
    elif i > 3:
      lft = ((i - 2) * (spacing + normalwidth)) + row6key0w + spacing + row6key3w + spacing
    else:
      lft = ((i - 1) * (spacing + normalwidth)) + row6key0w + spacing
      
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation) 

  for i,b in enumerate(reversed(buttons[5])):
    b.draw(screenPrescaled)
  for i,b in enumerate(reversed(buttons[4])):
    b.draw(screenPrescaled)
  for i,b in enumerate(reversed(buttons[3])):
    b.draw(screenPrescaled)
  for i,b in enumerate(reversed(buttons[2])):
    b.draw(screenPrescaled)
  for i,b in enumerate(reversed(buttons[1])):
    b.draw(screenPrescaled)
  for i,b in enumerate(reversed(buttons[0])):
    b.draw(screenPrescaled)

  # Print framerate and playtime in titlebar.
  text = "FPS: {0:.2f}   Playtime: {1:.2f}".format(clock.get_fps(), playtime)
  pygame.display.set_caption(text)
  draw_text(screenPrescaled, font, "FPS: {:6.3}{}PLAYTIME: {:6.3} SECONDS".format(
                           clock.get_fps(), " "*5, playtime), windoww, windowh)

  #pygame.transform.scale(screenPrescaled, (windoww, windowh), screen)
  

  
  pygame.display.update()


  screenModePrior = screenMode
