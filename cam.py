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
	  self.originalbitmap = pygame.image.load(iconPath + '/' + name + '.png')
	  self.originalbitmap = self.originalbitmap.convert_alpha()
	  self.bitmap = pygame.transform.smoothscale(self.originalbitmap, (self.originalbitmap.get_width(),self.originalbitmap.get_height()))


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
	    img = pygame.transform.smoothscale(self.iconBg.bitmap, (self.w,self.h))
	    #img.set_alpha(255)
	    screen.blit(img,
	      (self.rect[0],
	       self.rect[1]))
	  if self.iconFg:
	    img = pygame.transform.smoothscale(self.iconFg.bitmap, (self.w,self.h))
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
   Button((  0,  0, 128, 128), bg='axialis'	)
   ],
   
   #row 2
   [Button((  0,  0, 128, 128), bg='chrome'),
   Button((  0,  0, 128, 128), bg='dropbox'),
   Button((  0,  0, 128, 128), bg='email'),
   Button((  0,  0, 128, 128), bg='explorer'),
   Button((  0,  0, 128, 128), bg='firefox'),
   Button((  0,  0, 128, 128), bg='flashget'),
   Button((  0,  0, 128, 128), bg='foobar'),
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

# Busy indicator.  To use, run in separate thread, set global 'busy'
# to False when done.
def spinner():
	global busy, screenMode, screenModePrior

	buttons[screenMode][3].setBg('working')
	buttons[screenMode][3].draw(screen)
	pygame.display.update()

	busy = True
	n    = 0
	while busy is True:
	  buttons[screenMode][4].setBg('work-' + str(n))
	  buttons[screenMode][4].draw(screen)
	  pygame.display.update()
	  n = (n + 1) % 5
	  time.sleep(0.15)

	buttons[screenMode][3].setBg(None)
	buttons[screenMode][4].setBg(None)
	screenModePrior = -1 # Force refresh




# Initialization -----------------------------------------------------------

# Init framebuffer/touchscreen environment variables
#os.putenv('SDL_VIDEODRIVER', 'windlib')
os.putenv('SDL_FBDEV'      , '/dev/fb1')
os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')

# Get user & group IDs for file & folder creation
# (Want these to be 'pi' or other user, not root)
s = os.getenv("SUDO_UID")
#uid = int(s)
s = os.getenv("SUDO_GID")
#gid = int(s) 

# Init pygame and screen
#os.environ['SDL_VIDEODRIVER']='windlib'
pygame.init()
screen = pygame.display.set_mode([1280,800])
screenPrescaled = pygame.Surface((1280,800))
clock=pygame.time.Clock()
windoww = pygame.display.Info().current_w
windowh = pygame.display.Info().current_h
#pygame.mouse.set_visible(False)



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
while(True):
  framecount = framecount + 1
  # Process touchscreen input
  while True:
    for event in pygame.event.get():
      if(event.type is KEYDOWN):
        key = pygame.key.get_pressed()
        pos = pygame.mouse.get_pos()
        for b in buttons[screenMode]:
          if b.selected(pos): break
    # If in viewfinder or settings modes, stop processing touchscreen
    # and refresh the display to show the live preview.  In other modes
    # (image playback, etc.), stop and refresh the screen only when
    # screenMode changes.
    if screenMode >= 3 or screenMode != screenModePrior: break

  # Overlay buttons on display and update
  screenPrescaled.fill(0)
  
  lft = 0
  top = 0
  leftpadding = 0
  spacing = 4
  normalheight = 100
  normalwidth = 100
  topheight = 87
  topwidth = 87
  row2key0w = 100
  row2key10w = 230
  row3key0w = 100
  row3key11w = 130
  row4key0w = 130
  row5key0w = 130
  row6key0w = 130
  row6key3w = 516
  millis = ((round(time.time() * 1000)) % 1000)
  reverseanimation = (millis > 500)
  millis = millis / 1000

  for i,b in enumerate(buttons[0]):
    lft = leftpadding + (i * (spacing + topwidth))
    b.rect = ( lft, top, 0, 0)

    if reverseanimation:
      b.w = topwidth + int(pytweening.linear(1.0 - millis ) * 10)
      b.h = topheight + int(pytweening.linear(1.0 - millis ) * 10)      
    else:
      b.w = topwidth + int(pytweening.linear( (millis )) * 10)
      b.h = topheight + int(pytweening.linear((millis )) * 10)
    b.draw(screenPrescaled)

    
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
    if reverseanimation:
      b.w = w + int(pytweening.linear(1.0 - millis ) * 10)
      b.h = h + int(pytweening.linear(1.0 - millis ) * 10)      
    else:
      b.w = w + int(pytweening.linear( (millis )) * 10)
      b.h = h + int(pytweening.linear((millis )) * 10)
    b.draw(screenPrescaled)   

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
    if reverseanimation:
      b.w = w + int(pytweening.linear(1.0 - millis ) * 10)
      b.h = h + int(pytweening.linear(1.0 - millis ) * 10)      
    else:
      b.w = w + int(pytweening.linear( (millis )) * 10)
      b.h = h + int(pytweening.linear((millis )) * 10)
    b.draw(screenPrescaled)  

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
    if reverseanimation:
      b.w = w + int(pytweening.linear(1.0 - millis ) * 10)
      b.h = h + int(pytweening.linear(1.0 - millis ) * 10)      
    else:
      b.w = w + int(pytweening.linear( (millis )) * 10)
      b.h = h + int(pytweening.linear((millis )) * 10)
    b.draw(screenPrescaled)  

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
    if reverseanimation:
      b.w = w + int(pytweening.linear(1.0 - millis ) * 10)
      b.h = h + int(pytweening.linear(1.0 - millis ) * 10)      
    else:
      b.w = w + int(pytweening.linear( (millis )) * 10)
      b.h = h + int(pytweening.linear((millis )) * 10)
    b.draw(screenPrescaled)    

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
    if reverseanimation:
      b.w = w + int(pytweening.linear(1.0 - millis ) * 10)
      b.h = h + int(pytweening.linear(1.0 - millis ) * 10)      
    else:
      b.w = w + int(pytweening.linear( (millis )) * 10)
      b.h = h + int(pytweening.linear((millis )) * 10)
    b.draw(screenPrescaled)    

  pygame.transform.smoothscale(screenPrescaled, (windoww, windowh), screen)
  pygame.display.update()
  clock.tick(40)

  screenModePrior = screenMode
