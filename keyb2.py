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


# Init pygame and screen

#os.putenv('SDL_VIDEODRIVER', 'fbcon')
pygame.display.init()
size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
pygame.init()
pygame.mixer.quit()
screenhw = pygame.display.set_mode((1300,540),pygame.HWSURFACE,32)
screen = screenhw.convert_alpha()
#screenPrescaled = pygame.Surface((800, 480), flags=pygame.HWSURFACE, depth=16)
windoww = pygame.display.Info().current_w
windowh = pygame.display.Info().current_h

while(True):


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
  
  pygame.display.update()

