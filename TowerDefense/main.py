import pygame as pg
import json
from enemy import Enemy
from world import World
from turret import Turret
from button import Button
import constants as c

pg.init()

clock = pg.time.Clock()

#game window
screen = pg.display.set_mode((c.SCREEN_WIDTH + c.SIDE_PANEL, c.SCREEN_HEIGHT))
pg.display.set_caption("Tower Defense")

#game variables
game_over = False
game_outcome = 0 #-1 = loss, 1 = win
last_enemy_spawn = pg.time.get_ticks()
placing_turrets = False
selected_turret = None
level_started = False

#load images
map_image = pg.image.load("assets/levels/level.png").convert_alpha()
cursor_turret_image = pg.image.load("assets/turrets/cursor_turret.png").convert_alpha()
turret_spritesheets = []
for x in range(1, c.TURRET_LEVELS + 1):
    turret_sheet = pg.image.load(f'assets/turrets/turret_{x}.png').convert_alpha()
    turret_spritesheets.append(turret_sheet)
enemy_images = {
    "weak": pg.image.load("assets/enemies/enemy_1.png").convert_alpha(),
    "medium": pg.image.load("assets/enemies/enemy_2.png").convert_alpha(),
    "strong": pg.image.load("assets/enemies/enemy_3.png").convert_alpha(),
    "elite": pg.image.load("assets/enemies/enemy_4.png").convert_alpha()
}
buy_turret_image = pg.image.load("assets/buttons/buy_turret.png").convert_alpha()
cancel_image = pg.image.load("assets/buttons/cancel.png").convert_alpha()
upgrade_turret_image = pg.image.load("assets/buttons/upgrade_turret.png").convert_alpha()
begin_image = pg.image.load("assets/buttons/begin.png").convert_alpha()
restart_image = pg.image.load("assets/buttons/restart.png").convert_alpha()


#load json data
with open('assets/levels/level.tmj') as file:
    world_data = json.load(file)

#load fonts
text_font = pg.font.SysFont("Consolas", 24, bold = True)
large_font = pg.font.SysFont("Consolas", 36)

def display_data():
    pg.draw.rect(screen, "maroon", (c.SCREEN_WIDTH, 0,  c.SIDE_PANEL, c.SCREEN_HEIGHT))
    pg.draw.rect(screen, "grey0", (c.SCREEN_WIDTH, 0,  c.SIDE_PANEL, 400), 2)

    draw_text("Health: " + str(world.health), text_font, "black", 0, 0)
    draw_text("Money: " + str(world.money), text_font, "black", 0, 30)
    draw_text("Wave " + str(world.level), text_font, "black", 0, 60)

#output text
def draw_text(text, font, text_color, x, y):
    img = font.render(text, True, text_color)
    screen.blit(img, (x,y))

def create_turret(mouse_pos):
    mouse_tile_x = mouse_pos[0] // c.TILE_SIZE
    mouse_tile_y = mouse_pos[1] // c.TILE_SIZE
    #calc row and col
    mouse_tile_num = (mouse_tile_y * c.COLS) + mouse_tile_x
    #check grass
    if world.tile_map[mouse_tile_num] == 7:
        #check free space
        space_is_free = True
        for turret in turret_group:
            if (mouse_tile_x, mouse_tile_y) == (turret.tile_x, turret.tile_y):
                space_is_free = False
        if space_is_free == True:
            new_turret = Turret(turret_spritesheets, mouse_tile_x, mouse_tile_y)
            turret_group.add(new_turret)
            world.money -= c.BUY_COST

def select_turret(mouse_pos):
    mouse_tile_x = mouse_pos[0] // c.TILE_SIZE
    mouse_tile_y = mouse_pos[1] // c.TILE_SIZE
    for turret in turret_group:
        if (mouse_tile_x, mouse_tile_y) == (turret.tile_x, turret.tile_y):
            return turret

def clear_selection():
    for turret in turret_group:
        turret.selected = False

#create world
world = World(world_data, map_image)
world.process_data()
world.process_enemies()

#create groups
enemy_group = pg.sprite.Group()
turret_group = pg.sprite.Group()

#create buttons
turret_button = Button(c.SCREEN_WIDTH + 30, 120, buy_turret_image, True)
cancel_button = Button(c.SCREEN_WIDTH + 50, 180, cancel_image, True)
upgrade_button = Button(c.SCREEN_WIDTH + 5, 180, upgrade_turret_image, True)
begin_button = Button(c.SCREEN_WIDTH + 60, 300, begin_image, True)
restart_button = Button(310, 300, restart_image, True)

#game
run = True
while run:

    clock.tick(c.FPS)

    ########################
    # UPDATING SECTION
    ########################

    if game_over == False:
        #lost
        if world.health <= 0:
            game_over = True
            game_outcome = -1 
        #won
        if world.level > c.TOTAL_LEVELS:
            game_over = True
            game_outcome = 1

    #update groups
    enemy_group.update(world)
    turret_group.update(enemy_group)

    #highlight selected turret
    if selected_turret:
        selected_turret.selected = True

    ########################
    # DRAWING SECTION
    ########################

    screen.fill("grey100")

    #draw world
    world.draw(screen)

    #draw groups
    enemy_group.draw(screen)
    for turret in turret_group:
        turret.draw(screen)

    display_data()

    if game_over == False:
        #check level start
        if level_started ==  False:
            if begin_button.draw(screen):
                level_started = True
        else:
            #spawn enemies
            if pg.time.get_ticks() - last_enemy_spawn > c.SPAWN_COOLDOWN:
                if  world.spawned_enemies < len(world.enemy_list):
                    enemy_type = world.enemy_list[world.spawned_enemies]
                    enemy = Enemy(enemy_type, world.waypoints, enemy_images.get(enemy_type))
                    enemy_group.add(enemy)        
                    world.spawned_enemies += 1
                    last_enemy_spawn = pg.time.get_ticks()

        if world.check_level_complete() == True:
            world.money += c.LEVEL_COMPLETE_REWARD
            world.level += 1
            level_started = False
            last_enemy_spawn = pg.time.get_ticks()
            world.reset_level()
            world.process_enemies()

        #draw buttons
        if turret_button.draw(screen):
            placing_turrets = True
        if placing_turrets == True:
            #show cursor turret
            cursor_rect = cursor_turret_image.get_rect()
            cursor_pos = pg.mouse.get_pos()
            cursor_rect.center = cursor_pos
            if cursor_pos[0] <= c.SCREEN_WIDTH:
                screen.blit(cursor_turret_image, cursor_rect)
            if cancel_button.draw(screen):
                placing_turrets = False
        if selected_turret:
            if selected_turret.upgrade_level < c.TURRET_LEVELS:
                if upgrade_button.draw(screen):
                    if world.money >= c.UPGRADE_COST:
                        selected_turret.upgrade()
                        world.money -= c.UPGRADE_COST
    else:
        pg.draw.rect(screen, "dodgerblue", (200, 200, 400, 200), border_radius = 30)
        if game_outcome == -1:
            draw_text("GAME OVER". large_font, "grey0", 310, 230)
        elif game_outcome == 1:
            draw_text("YOU WIN!", large_font, "grey0", 315, 230)
        if restart_button.draw(screen):
            game_over = False
            level_started = False
            placing_turrets = False
            selected_turret = None
            last_enemy_spawn = pg.time.get_ticks()
            world = World(world_data, map_image)
            world.process_data()
            world.process_enemies()
            enemy_group.empty()
            turret_group.empty()

    #EVENT HANDLER
    for event in pg.event.get():
        
        #quit
        if event.type == pg.QUIT:
            run = False
        #mouse click
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pg.mouse.get_pos()
            #check mouse area
            if mouse_pos[0] < c.SCREEN_WIDTH and mouse_pos[1] < c.SCREEN_HEIGHT:
                #clear selected turret
                selected_turret = None
                clear_selection()
                if placing_turrets == True:
                    if world.money >= c.BUY_COST:
                        create_turret(mouse_pos)
                else:
                    selected_turret = select_turret(mouse_pos)
    
    #update display
    pg.display.flip()

pg.quit()