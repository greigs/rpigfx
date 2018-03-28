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
#from pipes import Pipes
from button import Button
from icon import Icon

# Global stuff -------------------------------------------------------------

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

shift           = True
msg             = ""

#icons = [] # This list gets populated at startup

# buttons[] is a list of lists; each top-level list element corresponds
# to one screen mode (e.g. viewfinder, image playback, storage settings),
# and each element within those lists corresponds to one UI button.
# There's a little bit of repetition (e.g. prev/next buttons are
# declared for each settings screen, rather than a single reusable
# set); trying to reuse those few elements just made for an ugly
# tangle of code elsewhere.
keysets = ["standard_lc", "premiere", "photoshop", "standard"]
keysetScales = [0.35, 0.344, 0.35, 0.35]
keysetXOffsets = [0, -20, 0, 0]

buttons = []
rowNum = 0
for row in rowNums:
  thisrow = []
  for key in range(0, row):
    butName = str(rowNum) + "_" + str(key)
    thisrow.append(Button(bg=butName))
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
      b.w = w + int(pytweening.linear(1.0 - millis) * 100)
      b.h = h + int(pytweening.linear(1.0 - millis) * 100)
    else:
      b.h = h + int(pytweening.linear((millis)) * 100)
      b.w = w + int(pytweening.linear((millis)) * 100)
  else:
    b.h = h
    b.w = w
    b.animating = False

# Initialization -----------------------------------------------------------
# Init pygame and screen
pygame.display.init()
size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
pygame.init()
pygame.mixer.quit()
if pygame.display.Info().current_h == 1366:
  #screen = pygame.display.set_mode(size, pygame.HWSURFACE|pygame.FULLSCREEN, 16)
  screen = pygame.display.set_mode((1366, 768), pygame.HWSURFACE|pygame.FULLSCREEN, 16)
else:
  screen = pygame.display.set_mode((1366, 768), pygame.HWSURFACE, 16)
screenPrescaled = screen
#overlay = pygame.Surface( screen.get_size(), pygame.SRCALPHA, 16)
clock = pygame.time.Clock()
windoww = pygame.display.Info().current_w
windowh = pygame.display.Info().current_h
pygame.mouse.set_visible(False)
font = pygame.font.SysFont('mono', 24, bold=True)
pygame.display.set_caption('Pio One')


# Load all icons at startup.
lines = []
for iconPathLocal in keysets:
  icons = []
  for file in os.listdir('keysets/' + iconPathLocal):
    if fnmatch.fnmatch(file, '*.png'):
      icons.append(Icon(file.split('.')[0], 'keysets/' + iconPathLocal))
  iconsets.append(icons)
  with open('keysets/' + iconPathLocal  + '/out.txt') as f:
    lines.append([line.rstrip('\n') for line in f])

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

while True:

  #if framecount > 0:
  #  if framecount % 20 == 0:
  #    selectedKeyset = 1
  #  if framecount % 30 == 0:
  #    selectedKeyset = 2

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
        selectedKeyset = 3
      if keys[pygame.K_z]:
        selectedKeyset = 0
      if keys[pygame.K_x]:
        selectedKeyset = 1
      if keys[pygame.K_c]:
        selectedKeyset = 2
    elif event.type is KEYUP:
      keys = pygame.key.get_pressed()
      if not keys[pygame.K_LSHIFT]:
        if shift:
          shift = False
          selectedKeyset = 0

  keys = pygame.key.get_pressed()
  # Overlay buttons on display and update
  screenPrescaled.fill(0)

  lft = 0

  millis = ((round(time.time() * 1000)) % 1000)
  reverseanimation = (millis > 500)
  millis = millis / 1000

  scale = keysetScales[selectedKeyset]

  keycount = 0
  for row in range(6):
    for i, b in enumerate(buttons[row]):
      k = lines[selectedKeyset][keycount].split(',')
      w = int(round(int(k[2]) * scale))
      h = int(round(int(k[3]) * scale))
      lft = int(round(int(k[0]) * scale))
      tp = int(round((int(k[1]) + keysetXOffsets[selectedKeyset]) * scale))
      b.rect = (lft, tp, w, h)
      b.key = int(k[4])
      apply_animation(b, keys, w, h, reverseanimation)
      keycount += 1

  for row in range(5, -1, -1):
    for i, b in enumerate(reversed(buttons[row])):
      b.draw(screenPrescaled, 'keysets/' + keysets[selectedKeyset], loadset, shift)

  draw_text(screenPrescaled, font, "FPS: {:6.3}{}TIME: {:6.3} SECONDS FRAMES:{:6}".format(
    clock.get_fps(), " "*5, playtime, framecount), windoww, windowh)

  #pygame.transform.scale(screenPrescaled, (windoww, windowh), screen)  

  # fill black
  #overlay.fill(0)

  # fill colour, attempt to use alpha
  #screen.fill(
  #  (int(pytweening.linear(millis ) * 55),
  #  int(pytweening.linear(1.0 - millis ) * 55),
  #  int(pytweening.linear(1.0 - millis ) * 55),
  #  10),
  #  None, BLEND_RGB_SUB )
  #screen.blit(overlay, (0,0), None, BLEND_RGBA_SUB)
  
  pygame.display.update()
 
  # Do not go faster than this framerate.
  milliseconds = clock.tick(FPS) 
  playtime += milliseconds / 1000.0