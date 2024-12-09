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
    # Load the home screen image
    home_screen = cv2.imread("bg.jpg")
    
    if home_screen is None:
        print("Error: Could not load the home screen image.")
        exit()

    # Display the home screen image
    gui.draw(home_screen)

    

# Initialize the GUI
gui = GUI(1280, 720, "Rock-Paper-Scissors Shoot!")
# homeScreen(gui)
openCamera(gui)