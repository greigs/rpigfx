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
import gradients
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
	  self.originalbitmap = pygame.image.load(iconPath + '/' + name + '.png').convert(16)
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

	def draw(self, screen):
	  if self.shiftimg is None and self.shift is not None:
	    self.shiftimg = pygame.image.load(iconPath + '/' + self.shift + '.png').convert(24)
	    self.shiftimg = pygame.transform.scale(self.shiftimg, (self.w,self.h))
	  if self.color:
	    screen.fill(self.color, self.rect)
	  if self.iconBg:
	    if shift and self.shift is not None:
	      img = self.shiftimg
	    else:
	      if self.staticBg is None:
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
iconPath        = 'icons' # Subdirectory containing UI bitmaps (PNG format)
saveIdx         = -1      # Image index for saving (-1 = none set yet)
loadIdx         = -1      # Image index for loading
scaled          = None    # pygame Surface w/last-loaded image

shift           = False

icons = [] # This list gets populated at startup

# buttons[] is a list of lists; each top-level list element corresponds
# to one screen mode (e.g. viewfinder, image playback, storage settings),
# and each element within those lists corresponds to one UI button.
# There's a little bit of repetition (e.g. prev/next buttons are
# declared for each settings screen, rather than a single reusable
# set); trying to reuse those few elements just made for an ugly
# tangle of code elsewhere.

buttonsold = [
   #row 1
   [Button( bg='adobe_Ai'),
   Button( bg='adobe_Dw'),
   Button( bg='adobe_Fl'),
   Button( bg='adobe_Fw'),
   Button( bg='adobe_Id'),
   Button( bg='adobe_Ps'),
   Button( bg='axialis'),
   Button( bg='adobe_Ai'),
   Button( bg='adobe_Dw'),
   Button( bg='adobe_Fl'),
   Button( bg='adobe_Fw'),
   Button( bg='adobe_Id'),
   Button( bg='adobe_Ps'),
   Button( bg='axialis')
   ],
   
   #row 2
   [Button( bg='chrome'),
   Button( bg='dropbox', key=pygame.K_1),
   Button( bg='email', key=pygame.K_2),
   Button( bg='explorer', key=pygame.K_3),
   Button( bg='firefox', key=pygame.K_4),
   Button( bg='flashget', key=pygame.K_5),
   Button( bg='foobar', key=pygame.K_6),
   Button( bg='chrome', key=pygame.K_7),
   Button( bg='dropbox', key=pygame.K_8),
   Button( bg='email', key=pygame.K_9),
   Button( bg='explorer', key=pygame.K_0),
   ],
   
   #row 3
   [Button( bg='games'),
   Button( bg='googleEarth', key=pygame.K_q),
   Button( bg='handbrake', key=pygame.K_w),
   Button( bg='mediaPlayer', key=pygame.K_e),
   Button( bg='notepad', key=pygame.K_r),
   Button( bg='opera', key=pygame.K_t),
   Button( bg='safari', key=pygame.K_y),
   Button( bg='games', key=pygame.K_u),
   Button( bg='googleEarth', key=pygame.K_i),
   Button( bg='handbrake', key=pygame.K_o),
   Button( bg='mediaPlayer', key=pygame.K_p),
   Button( bg='notepad'),
   ],
   
   #row 4
   [Button( bg='sonyericsson'),
   Button( bg='totalCommander', key=pygame.K_a),
   Button( bg='uTorrent', key=pygame.K_s),
   Button( bg='vlcPlayer', key=pygame.K_d),
   Button( bg='webcam', key=pygame.K_f),
   Button( bg='xbmc', key=pygame.K_g),
   Button( bg='safari', key=pygame.K_h),
   Button( bg='sonyericsson', key=pygame.K_j),
   Button( bg='totalCommander', key=pygame.K_k),
   Button( bg='uTorrent', key=pygame.K_l),
   Button( bg='vlcPlayer'),
   Button( bg='webcam',),
   ],
   
   #row 5
   [Button( bg='adobe_Ai'),
   Button( bg='adobe_Dw', key=pygame.K_z),
   Button( bg='adobe_Fl', key=pygame.K_x),
   Button( bg='adobe_Fw', key=pygame.K_c),
   Button( bg='adobe_Id', key=pygame.K_v),
   Button( bg='adobe_Ps', key=pygame.K_b),
   Button( bg='axialis', key=pygame.K_n),
   Button( bg='adobe_Ai', key=pygame.K_m),
   Button( bg='adobe_Dw'),
   Button( bg='adobe_Fl'),
   Button( bg='adobe_Fw'),
   Button( bg='adobe_Id'),
   ],
   
   #row 6
   [Button( bg='chrome'),
   Button( bg='dropbox'),
   Button( bg='email'),
   Button( bg='explorer'),
   Button( bg='firefox'),
   Button( bg='flashget'),
   Button( bg='foobar'),
   Button( bg='chrome'),
   ]
   
]

buttons = [
   #row 1
   [Button( bg='escape'),
   Button( bg='f1'),
   Button( bg='f2'),
   Button( bg='f3'),
   Button( bg='f4'),
   Button( bg='f5'),
   Button( bg='f6'),
   Button( bg='f7'),
   Button( bg='f8'),
   Button( bg='f9'),
   Button( bg='f10'),
   Button( bg='f11'),
   Button( bg='f12'),
   Button( bg='#'),
   Button( bg='printscreen')
   ],
   
   #row 2
   [
   Button( bg='~'),
   Button( bg='1', key=pygame.K_1),
   Button( bg='2', key=pygame.K_2),
   Button( bg='3', key=pygame.K_3),
   Button( bg='4', key=pygame.K_4),
   Button( bg='5', key=pygame.K_5),
   Button( bg='6', key=pygame.K_6),
   Button( bg='7', key=pygame.K_7),
   Button( bg='8', key=pygame.K_8),
   Button( bg='9', key=pygame.K_9),
   Button( bg='0', key=pygame.K_0),
   Button( bg='-'),
   Button( bg='+'),
   Button( bg='oemclear'),
   ],
   
   #row 3
   [Button( bg='tab'),
   Button( bg='q', shift = 'qu', key=pygame.K_q),
   Button( bg='w', shift = 'wu', key=pygame.K_w),
   Button( bg='e', shift = 'eu', key=pygame.K_e),
   Button( bg='r', shift = 'ru', key=pygame.K_r),
   Button( bg='t', shift = 'tu', key=pygame.K_t),
   Button( bg='y', shift = 'yu', key=pygame.K_y),
   Button( bg='u', shift = 'uu', key=pygame.K_u),
   Button( bg='i', shift = 'iu', key=pygame.K_i),
   Button( bg='o', shift = 'ou', key=pygame.K_o),
   Button( bg='p', shift = 'pu', key=pygame.K_p),
   Button( bg='['),
   Button( bg=']'),
   Button( bg='forwardslash'),
   ],
   
   #row 4
   [Button( bg='capital'),
   Button( bg='a', shift = 'au', key=pygame.K_a),
   Button( bg='s', shift = 'su', key=pygame.K_s),
   Button( bg='d', shift = 'du', key=pygame.K_d),
   Button( bg='f', shift = 'fu', key=pygame.K_f),
   Button( bg='g', shift = 'gu', key=pygame.K_g),
   Button( bg='h', shift = 'hu', key=pygame.K_h),
   Button( bg='j', shift = 'ju', key=pygame.K_j),
   Button( bg='k', shift = 'ku', key=pygame.K_k),
   Button( bg='l', shift = 'lu', key=pygame.K_l),
   Button( bg=';'),
   Button( bg='#'),
   Button( bg='#'),
   Button( bg='return'),
   ],
   
   #row 5
   [Button( bg='lshiftkey'),
   Button( bg='forwardslash'),
   Button( bg='z', shift = 'zu', key=pygame.K_z),
   Button( bg='x', shift = 'xu', key=pygame.K_x),
   Button( bg='c', shift = 'cu', key=pygame.K_c),
   Button( bg='v', shift = 'vu', key=pygame.K_v),
   Button( bg='b', shift = 'bu', key=pygame.K_b),
   Button( bg='n', shift = 'nu', key=pygame.K_n),
   Button( bg='m', shift = 'mu', key=pygame.K_m),
   Button( bg=','),
   Button( bg='#'),  
   Button( bg='forwardslash'),   
   Button( bg='up'),
   Button( bg='rshiftkey'),
   Button( bg='delete')
   
   ],
   
   #row 6
   [
   Button( bg='#'),
   Button( bg='lcontrolkey'),
   Button( bg='lwin'),
   Button( bg='alt'),
   Button( bg='space'),
   Button( bg='alt'),
   Button( bg='left'),
   Button( bg='down'),
   Button( bg='right'),
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

def fill_gradient2(surface, color, gradient, rect=None, vertical=True, forward=True):
    """fill a surface with a gradient pattern
    Parameters:
    color -> starting color
    gradient -> final color
    rect -> area to fill; default is surface's rect
    vertical -> True=vertical; False=horizontal
    forward -> True=forward; False=reverse
    
    Pygame recipe: http://www.pygame.org/wiki/GradientCode
    """
    if rect is None: rect = surface.get_rect()
    x1,x2 = rect.left, rect.right
    y1,y2 = rect.top, rect.bottom

    c = Color(0,0,0)
    for j in range(360,-45,-45):
		for i in range(j,0,-1):
			c.hsla=(j-i,100,50,100)
			pygame.draw.circle(surface,c,(360,360),j-i)
			#__import__('time').sleep(0.01)
			#pygame.display.flip()

	  
def fill_gradient(surface, color, gradient, rect=None, vertical=True, forward=True):
    """fill a surface with a gradient pattern
    Parameters:
    color -> starting color
    gradient -> final color
    rect -> area to fill; default is surface's rect
    vertical -> True=vertical; False=horizontal
    forward -> True=forward; False=reverse
    
    Pygame recipe: http://www.pygame.org/wiki/GradientCode
    """
    if rect is None: rect = surface.get_rect()
    x1,x2 = rect.left, rect.right
    y1,y2 = rect.top, rect.bottom
    if vertical: h = y2-y1
    else:        h = x2-x1
    if forward: a, b = color, gradient
    else:       b, a = color, gradient
    rate = (
        float(b[0]-a[0])/h,
        float(b[1]-a[1])/h,
        float(b[2]-a[2])/h
    )
    fn_line = pygame.draw.line
    if vertical:
        for line in range(y1,y2):
            color = (
                min(max(a[0]+(rate[0]*(line-y1)),0),255),
                min(max(a[1]+(rate[1]*(line-y1)),0),255),
                min(max(a[2]+(rate[2]*(line-y1)),0),255)
            )
            fn_line(surface, color, (x1,line), (x2,line))
    else:
        for col in range(x1,x2):
            color = (
                min(max(a[0]+(rate[0]*(col-x1)),0),255),
                min(max(a[1]+(rate[1]*(col-x1)),0),255),
                min(max(a[2]+(rate[2]*(col-x1)),0),255)
            )
            fn_line(surface, color, (col,y1), (col,y2))
	  

	  
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
if pygame.display.Info().current_h == 720:
  screenhw = pygame.display.set_mode(size,pygame.HWSURFACE|pygame.FULLSCREEN|pygame.SRCALPHA,16)
else:
  screenhw = pygame.display.set_mode((1366,768),pygame.HWSURFACE,16)
  #screen = screenhw.convert_alpha()
screenPrescaled = screenhw
#overlay = pygame.Surface( screen.get_size(), pygame.SRCALPHA|pygame.HWSURFACE,16)
#overlay = overlay.convert_alpha()
#screenPrescaled = pygame.Surface((800, 480), flags=pygame.HWSURFACE, depth=16)
clock=pygame.time.Clock()
windoww = pygame.display.Info().current_w
windowh = pygame.display.Info().current_h
pygame.mouse.set_visible(False)
font = pygame.font.SysFont('mono', 24, bold=True)
pygame.display.set_caption('')


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
FPS = 60
# How many seconds the "game" is played.
playtime = 0.0
while(True):
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
  top = 0
  leftpadding = 0
  spacinghor = 20 
  spacingver = 30 
  normalheight = 60
  normalwidth = 60 
  topheight = 60
  topwidth = 60
  row2key0w = 60
  row2key13spacing = 60
  row2key13w = 100
  row3key0w = 90
  row3key13w = 130 
  row4key0w = 110 
  row4key13spacing = 40
  row4key13w = 90
  row5key0w = 70 
  row6key0w = 110 
  row6key3w = 403 
  millis = ((round(time.time() * 1000)) % 1000)
  reverseanimation = (millis > 500)
  millis = millis / 1000

  
  # Row 1
  for i,b in enumerate(buttons[0]):
    w = topwidth
    h = topheight
    lft = leftpadding + (i * (spacinghor + topwidth))
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation)
    
  # Row 2
  top = top + topheight + spacingver

  for i,b in enumerate(buttons[1]):
    w = normalwidth
    h = normalheight
    if i == 0:
      lft = 0
      w = row2key0w
    elif i == 13:
      w = row2key13w
      lft = ((i - 1) * (spacinghor + normalwidth)) + row2key0w + spacinghor + row2key13spacing  
    else:
      lft = ((i - 1) * (spacinghor + normalwidth)) + row2key0w + spacinghor
      
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation)

  # Row 3
  top = top + normalheight + spacingver

  for i,b in enumerate(buttons[2]):
    w = normalwidth
    h = normalheight
    if i == 0:
      lft = 0
      w = row3key0w
    elif i == 13:
      w = row3key13w
      lft = ((i - 1) * (spacinghor + normalwidth)) + row3key0w + spacinghor   
    else:
      lft = ((i - 1) * (spacinghor + normalwidth)) + row3key0w + spacinghor
      
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation)

  # Row 4
  top = top + normalheight + spacingver

  for i,b in enumerate(buttons[3]):
    w = normalwidth
    h = normalheight
    if i == 0:
      lft = 0
      w = row4key0w	
    elif i == 13:
      w = row4key13w
      lft = ((i - 1) * (spacinghor + normalwidth)) + row4key13w + spacinghor + row4key13spacing
    else:
      lft = ((i - 1) * (spacinghor + normalwidth)) + row4key0w + spacinghor
      
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation)
 
  # Row 5
  top = top + normalheight + spacingver

  for i,b in enumerate(buttons[4]):
    w = normalwidth
    h = normalheight
    if i == 0:
      lft = 0
      w = row5key0w
    else:
      lft = ((i - 1) * (spacinghor + normalwidth)) + row5key0w + spacinghor
      
    b.rect = ( lft, top, 0, 0)
    apply_animation(b,keys,w,h, reverseanimation) 

  # Row 6
  top = top + normalheight + spacingver

  for i,b in enumerate(buttons[5]):
    w = normalwidth
    h = normalheight
    if i == 0:
      lft = 0
      w = row6key0w
    elif i == 3:
      w = row6key3w
      lft = ((i - 1) * (spacinghor + normalwidth)) + row6key0w + spacinghor
    elif i > 3:
      lft = ((i - 2) * (spacinghor + normalwidth)) + row6key0w + spacinghor + row6key3w + spacinghor
    else:
      lft = ((i - 1) * (spacinghor + normalwidth)) + row6key0w + spacinghor
      
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

  draw_text(screenPrescaled, font, "FPS: {:6.3}{}TIME: {:6.3} SECONDS".format(
                           clock.get_fps(), " "*5, playtime), windoww, windowh)

  #pygame.transform.scale(screenPrescaled, (windoww, windowh), screen)
  
  
  #overlay.fill((255,0,0,100))
  
  #fill_gradient(overlay, ( int(pytweening.linear( (millis )) * 20),int(pytweening.linear( (millis )) * 40),int(pytweening.linear( #(millis )) * 60),0 ), (255,255,255,0))
  
  #overlay.blit(gradients.horizontal((screen.get_width(), screen.get_height()), (255,0,0,255), (0,255,255,255)),(0,0))
  
  #screen.fill(
   #(255,255,0,255),None, BLEND_RGBA_MULT
   #int(pytweening.linear(1.0 - millis ) * 100),
   #int(pytweening.linear(1.0 - millis ) * 50) ,10)
  #)
  #overlay.set_alpha(20)
  #screen.set_alpha(20)
  #screen.fill((0,0,0,0))
  #screen.blit(overlay, (0,0))
  #screen.set_alpha(20)
  #screenhw.fill((0,0,0,0))
  #screenhw.blit(screen,(0,0))
  #screenhw.blit(overlay,(0,0),None,BLEND_RGBA_MULT)
  
  pygame.display.update()
 


  screenModePrior = screenMode
