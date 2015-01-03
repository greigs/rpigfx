import pygame, sys, random
from math import cos
from pygame.locals import *

FPS = 30
WINDOWWIDTH = 640
WINDOWHEIGHT = 480
FIRE = pygame.image.load('fire.png')
PIXEL = pygame.image.load('white.png')
FIRE_YELLOW = pygame.image.load('fire_yellow.png')

def main():
	global FPSCLOCK, DISPLAYSURF
	pygame.init()
	FPSCLOCK = pygame.time.Clock()
	DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
	pygame.mouse.set_visible(0)
	
	# particle_xysize Elements:
	# Its a List of Lists, where particle_xysize[element][0,1,2,3,4,5,6..]
	# x
	# y
	# size
	# direction
	# type
	# addition
	# color
	
	particles = 240
	particle_xysize = []
	while particles > 0:	
		particle_xysize.append([0,0,0,0,0,0,0,(0,0,0),(0,0)])
		particles -= 1
	
	for element in range(len(particle_xysize)):
		particle_xysize[element][2] = 10
		particle_xysize[element][4] = random.randint(0,1)
	velocity = []
	for particle in particle_xysize:
		velocity.append(random.randint(1, 10))
	
	mouse_x = 0
	mouse_y = 0
	random_numbers = [1, -1]
	
			# Reset Values
	for integer in velocity:
		integer *= random.sample(random_numbers, 1)[0]
					
	for direction in range(len(particle_xysize)):
		particle_xysize[direction][3] = random.sample(random_numbers, 1)[0]
		particle_xysize[direction][4] = random.sample(random_numbers, 1)[0]
		particle_xysize[direction][8] = (random.randint(1,2), random.randint(1,2))
		
	traegheit = 0
	
	while True:
	
		# Get Events of Game Loop
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
				pygame.quit()
				sys.exit()
			if event.type == MOUSEMOTION:
				mouse_x, mouse_y = event.pos
		# Fill the Display for new objects to be drawn
		DISPLAYSURF.fill((0, 0, 0))
		# Draw Elements
		for element in range(len(particle_xysize)):
			width = particle_xysize[element][2]
			height = particle_xysize[element][2]
			particle_x = particle_xysize[element][0]
			particle_y = particle_xysize[element][1]
			addition = particle_xysize[element][6]
			influence = particle_xysize[element][8]
			color = particle_xysize[element][7]
		
			particle_x += (velocity[element] + addition * influence[0] / 4) * particle_xysize[element][4]
			particle_y += (velocity[element] + addition * influence[1] / 4) * particle_xysize[element][3]
			
			if particle_xysize[element][5] == 0:
				firesmall = pygame.transform.scale(FIRE, (int(width), int(height)))
				#pygame.draw.rect(DISPLAYSURF, color, (particle_x - width / 2, particle_y - height / 2, width, height))
				DISPLAYSURF.blit(firesmall,[particle_x - width / 2,particle_y - height / 2])
			elif particle_xysize[element][5] == 1:
				#pygame.draw.circle(DISPLAYSURF, color, (particle_x - int(width / 2), particle_y - int(height / 2)), int(width))		
				white = pygame.transform.scale(PIXEL, (int(width / 4), int(height / 4)))
				DISPLAYSURF.blit(white,[particle_x - width / 2,particle_y - height / 2])
			elif particle_xysize[element][5] == 2:
				fire_yellow = pygame.transform.scale(FIRE_YELLOW, (int(width * 2), int(height * 2)))
				DISPLAYSURF.blit(fire_yellow,[particle_x - width,particle_y - height])
				
			if particle_xysize[element][2] > 0:
				particle_xysize[element][2] -= 0.5
				velocity[element] += 1
				if particle_xysize[element][6] < 50:
					particle_xysize[element][6] += 1
			else:
				while True:
					particle_xysize[element][3] = random.sample(random_numbers, 1)[0]
					particle_xysize[element][4] = random.sample(random_numbers, 1)[0]
					particle_xysize[element][5] = random.randint(0,2)
					particle_xysize[element][7] = (random.randint(1,255), random.randint(1,255), random.randint(1,255))
					particle_xysize[element][6] = 0
					particle_xysize[element][8] = (random.randint(1,20), random.randint(1,20))
					if random.randint(1, 10) > 4:
						particle_xysize[element][2] = random.randint(1, 20)
					velocity[element] = random.randint(1,5)
					particle_xysize[element][0], particle_xysize[element][1] = mouse_x, mouse_y
					break
					
		pygame.display.update()
		FPSCLOCK.tick(FPS)

if __name__ == '__main__':
	main()
	
	
	
	
	
	
	
