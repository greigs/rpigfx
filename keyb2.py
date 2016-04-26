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

class Icon:

	def __init__(self, name):
	  self.name = name
	  self.originalbitmap = pygame.image.load(iconPath + '/' + name + '.png').convert(16)
	  self.bitmap = self.originalbitmap.convert(16)
 


# Init pygame and screen

iconPath = 'icons'
#os.putenv('SDL_VIDEODRIVER', 'fbcon')
pygame.display.init()
size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
pygame.init()
pygame.mixer.quit()
screenhw = pygame.display.set_mode((1280,720),pygame.HWSURFACE,32)
screen = screenhw.convert_alpha()
#screenPrescaled = pygame.Surface((800, 480), flags=pygame.HWSURFACE, depth=16)
windoww = pygame.display.Info().current_w
windowh = pygame.display.Info().current_h

icons = [] # This list gets populated at startup

# Load all icons at startup.
for file in os.listdir(iconPath):
  if fnmatch.fnmatch(file, '*.png'):
    icons.append(Icon(file.split('.')[0]))

while(True):

  keys = None


  for event in pygame.event.get():
    if event.type is KEYDOWN:
      keys = pygame.key.get_pressed()
      if keys[pygame.K_ESCAPE]:
        pygame.quit()
        sys.exit()

  #pygame.transform.scale(screenPrescaled, (windoww, windowh), screen)
  
  screen.set_alpha(0)
  screen.fill((0,0,0,0))
  screen.fill(
   (255,255,255,100)
   #int(pytweening.linear(1.0 - millis ) * 100),
   #int(pytweening.linear(1.0 - millis ) * 50) ,10)
  )
  #screen.set_alpha(20)
  #screen.fill((0,0,0,0))
  #screen.blit(overlay, (0,0), None, special_flags=BLEND_RGBA_ADD)
  #screen.set_alpha(20)
  screenhw.fill((0,0,0,0))
  screenhw.blit(screen,(0,0), None)
  
  img = pygame.transform.scale(icons[0].bitmap, (1280,720))
  screenhw.blit(img,(0,0))
  
  pygame.display.update()

