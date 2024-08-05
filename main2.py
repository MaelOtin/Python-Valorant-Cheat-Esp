import pymem
import pymem.process
import imgui
from imgui.integrations.pygame import PygameRenderer
import pygame
from pygame.locals import *
from OpenGL.GL import *

def get_valorant_process():
    try:
        return pymem.Pymem("VALORANT-Win64-Shipping.exe")
    except pymem.exceptions.PymemError as e:
        print(f"Error finding Valorant process: {e}")
        return None

def read_int(memory, address):
    try:
        return memory.read_int(address)
    except pymem.exceptions.PymemError as e:
        print(f"Error reading int from address {address}: {e}")
        return 0

def read_float(memory, address):
    try:
        return memory.read_float(address)
    except pymem.exceptions.PymemError as e:
        print(f"Error reading float from address {address}: {e}")
        return 0.0

def init_open_gl():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glViewport(0, 0, 1024, 768)

def main():
    pygame.init()
    size = 1024, 768
    screen = pygame.display.set_mode(size, pygame.RESIZABLE | OPENGL)
    imgui.create_context()
    impl = PygameRenderer()

    init_open_gl()

    valorant = get_valorant_process()
    if valorant is None:
        print("Valorant process not found. Exiting.")
        pygame.quit()
        return

    unity_player = pymem.process.module_from_name(valorant.process_handle, "UnityPlayer.dll")
    if unity_player is None:
        print("UnityPlayer.dll module not found in the Valorant process. Exiting.")
        pygame.quit()
        return

    base_address = unity_player.lpBaseOfDll

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            impl.process_event(event)

        imgui.new_frame()

        local_player_address = valorant.read_int(base_address + 0x017DDA20)

        for i in range(1, 32):
            entity_address = valorant.read_int(base_address + 0x017DDA20 + i * 0x10)
            if entity_address:
                entity_health = read_int(valorant, entity_address + 0x20)
                entity_x = read_float(valorant, entity_address + 0x90)
                entity_y = read_float(valorant, entity_address + 0x94)

                if entity_health > 0:
                    imgui.set_next_window_position(entity_x, entity_y)
                    imgui.begin(f'Enemy {i}', flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_BACKGROUND)
                    imgui.text_colored(f'HP: {entity_health}', 1.0, 0.0, 0.0, 1.0)
                    imgui.end()

        imgui.render()
        impl.render(imgui.get_draw_data())
        pygame.display.flip()
        pygame.time.wait(10)

    impl.shutdown()
    pygame.quit()

if __name__ == '__main__':
    main()
