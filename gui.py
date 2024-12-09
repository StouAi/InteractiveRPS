import cv2
import numpy as np
import pygame as pg


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

def load_images():
    start_button_image = pg.image.load('start_btn.jpg').convert_alpha()
    if start_button_image is None:
        print("Error: Could not load the start button image.")
        exit()
    exit_button_image = pg.image.load('exit_btn.jpg').convert_alpha()
    if exit_button_image is None:
        print("Error: Could not load the exit button image.")
        exit()
    return start_button_image, exit_button_image

class Button():
    def __init__(self, x, y, image, screen):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.screen = screen
        
    def draw(self):
        self.screen.blit(self.image, (self.rect.x, self.rect.y))
        
def openCamera(gui):
    # Open the webcam using OpenCV
    cap = cv2.VideoCapture(0)

    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        exit()
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("Error: Failed to capture image.")
            break

        # Draw the frame on the pygame screen
        gui.draw(frame)

        # Event handling (e.g., quit the window when clicking the close button)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                gui.close()
                cap.release()
                exit()

    # Release the camera and close the window
    cap.release()
    gui.close()
    
def homeScreen(gui):
    # Load the home screen image as a Pygame surface
    home_screen = pg.image.load("bg.jpg").convert()
    start_button_image, exit_button_image = load_images()
    start_btn = Button(640-300, 500, start_button_image, gui.screen)
    exit_btn = Button(640+100, 500, exit_button_image, gui.screen)

    if home_screen is None:
        print("Error: Could not load the home screen image.")
        exit()

    running = True
    while running:
        # Handle events
        for event in pg.event.get():
            if event.type == pg.QUIT:  # Quit event
                running = False

        # Blit the background and buttons to the screen
        gui.screen.blit(home_screen, (0, 0))  # Draw the background
        start_btn.draw()       # Draw the start button
        exit_btn.draw()        # Draw the exit button

        # Update the display
        pg.display.update()

    # Close the GUI after the loop ends
    gui.close()


# Initialize the GUI
gui = GUI(1280, 720, "Rock-Paper-Scissors Shoot!")
homeScreen(gui)
