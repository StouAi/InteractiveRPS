import cv2
import numpy as np
import pygame as pg
import time


class GUI:
    def __init__(self, width, height, title):
        pg.init()
        self.width = width
        self.height = height
        self.title = title
        self.screen = pg.display.set_mode((width, height))
        pg.display.set_caption(title)
        self.clock = pg.time.Clock()

    def draw(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        img = np.rot90(img)  # Rotate image for proper orientation
        img = pg.surfarray.make_surface(img)  # Create a surface from the image
        self.screen.blit(img, (0, 0))  # Blit the image on the screen
        pg.display.flip()  # Update the display
        self.clock.tick(60)  # Control the frame rate (60 FPS)

    def close(self):
        pg.quit()  # Quit pygame


class Button:
    def __init__(self, x, y, image, screen):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.screen = screen
        
    def draw(self):
        self.screen.blit(self.image, (self.rect.x, self.rect.y))
        
    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)
        
    def is_clicked(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class Animation:
    def __init__(self, x, y, image, screen):
        self.image = image
        self.original_image = image  # Save the original image for resizing
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.screen = screen
        self.scale_factor = 0.8  # Initial scale factor (normal size)
        self.enlarging = True  # Flag to track whether the image is enlarging or shrinking

    def draw(self):
        """Draw the animation (image) to the screen with current scaling."""
        # Scale the image based on the scale factor
        scaled_image = pg.transform.scale(self.original_image, 
                                          (int(self.original_image.get_width() * self.scale_factor), 
                                           int(self.original_image.get_height() * self.scale_factor)))
        # Get the new rectangle for the scaled image
        new_rect = scaled_image.get_rect()
        new_rect.center = self.rect.center  # Set the center of the scaled image to the original center
        self.screen.blit(scaled_image, new_rect.topleft)

    def update(self):
        """Update the scale factor for enlarging and shrinking."""
        if self.enlarging:
            self.scale_factor += 0.0003  # Increase scale slowly
            if self.scale_factor >= 0.85:  
                self.enlarging = False
        else:
            self.scale_factor -= 0.0003  # Decrease scale slowly
            if self.scale_factor <= 0.75:  # When the image reaches its original size, start enlarging
                self.enlarging = True


def load_images():
    start_button_image = pg.image.load('start_btn.jpg').convert_alpha()
    exit_button_image = pg.image.load('exit_btn.jpg').convert_alpha()
    
    if not start_button_image or not exit_button_image:
        print("Error: Could not load images.")
        exit()

    return start_button_image, exit_button_image


def home_screen(gui):
    """Home screen showing the title and buttons."""
    home_screen = pg.image.load("bg.jpg").convert()
    start_button_image, exit_button_image = load_images()
    
    start_btn = Button(640 - start_button_image.get_width() - 50, 500, start_button_image, gui.screen)
    exit_btn = Button(640 + 50, 500, exit_button_image, gui.screen)
    
    animated_image = pg.image.load('hands.png').convert_alpha()
    animation = Animation(640 - animated_image.get_width() // 2, 150, animated_image, gui.screen)  # Position above the buttons


    running = True
    while running:
        mouse_pos = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                if start_btn.is_hovered(mouse_pos):  # Start button clicked
                    return 'game'
                elif exit_btn.is_hovered(mouse_pos):  # Exit button clicked
                    running = False
                    return 'exit'
            if start_btn.is_hovered(mouse_pos) or exit_btn.is_hovered(mouse_pos):
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            else:
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)

        
        gui.screen.blit(home_screen, (0, 0))
        
        # Add the title
        add_title(gui)
        
        start_btn.draw()
        exit_btn.draw()
        
        # Update and draw the animated image
        animation.update()
        animation.draw()
        
        pg.display.update()

    return 'exit'


def open_camera(gui):
    """Open webcam feed and display on the GUI."""
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        gui.draw(frame)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                gui.close()
                cap.release()
                exit()

    cap.release()
    gui.close()


def game_screen(gui):
    """Game screen to show webcam feed during the game."""
    home_screen = pg.image.load("bg.jpg").convert()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return 'exit'

    running = True
    while running:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture video.")
            break

        for event in pg.event.get():
            if event.type == pg.QUIT:  # Quit event
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_q:  # Press 'Q' to quit
                    running = False

        # Draw the background
        gui.screen.blit(home_screen, [0, 0])
        
        # add the title
        add_title(gui)
        
        # add "vs" title.
        add_title(gui, title = "vs", pos = (gui.width//2, gui.height//2), font_size=50)
        
        # Display the webcam feed
        add_camera(gui, frame)
        
        # Display bot choice
        

        pg.display.update()

    cap.release()
    return 'exit'

def add_title(gui, title="Rock-Paper-Scissors Shoot!", pos = [640, 50], font_size=100):
    font = pg.font.Font('font.ttf', font_size)
    text = pg.font.Font.render(font, title, True, (168, 83, 76))
    gui.screen.blit(text, (int(pos[0]) - text.get_width() // 2, int(pos[1])))
    
def add_camera(gui, frame):
    # Resize and draw the camera feed
    frame = cv2.resize(frame, (450, 350))  # Resize the frame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    camera_surface = pg.surfarray.make_surface(frame)

    camera_x = gui.width - camera_surface.get_width() - 50
    camera_y = 150

    draw_border(gui, camera_surface, camera_x, camera_y)

    # Draw the camera feed
    gui.screen.blit(camera_surface, (camera_x, camera_y))

def draw_border(gui, camera_surface, camera_x, camera_y):
    # Draw border around the camera feed
    border_rect = pg.Rect(camera_x - 5, camera_y - 5, camera_surface.get_width() + 10, camera_surface.get_height() + 10)
    pg.draw.rect(gui.screen, (255, 255, 255), border_rect)
    
def add_score(winner):
    if winner == "Player":
        player_score += 1
    elif winner == "Bot":
        bot_score += 1

    return player_score, bot_score

def main():
    home_gui = GUI(1280, 720, "Rock-Paper-Scissors Shoot!")
    gameplay_gui = GUI(1280, 720, "Rock-Paper-Scissors Shoot!")

    screen_status = 'home'

    if screen_status == 'home':
        screen_status = home_screen(home_gui)
    
    if screen_status == 'game':
        game_screen(gameplay_gui)
    
    elif screen_status == 'exit':
        home_gui.close()


if __name__ == "__main__":
    main()
