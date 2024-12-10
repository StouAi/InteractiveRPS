import cv2
import numpy as np
import pygame as pg
import time
import camera_comm as cc

np.random.seed(0)
font = cv2.FONT_HERSHEY_PLAIN

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
    counter = 0
    past_gestures = []
    start_time = time.time()
    countdown = 3
    pTime = 0
    _bot_choice = None
    player_choice = None
    player_score = 0
    bot_score = 0
    added_scores = False

    while running:
        ret, img = cap.read()
        if not ret:
            print("Error: Failed to capture video.")
            break

        img = cv2.flip(img, 1)  # Reverse the image horizontally
        
        img = cc.detector.findHands(img)
        lmlist = cc.detector.findPosition(img, draw=False)

        for event in pg.event.get():
            if event.type == pg.QUIT:  # Quit event
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_q:  # Press 'Q' to quit
                    running = False
        
        if len(lmlist) != 0:
            counter += 1
            fingerpos1 = cc.finger_combo(lmlist)
            cc.fingerlist.append(fingerpos1)
            past_gestures.append(fingerpos1)
        
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        # Draw the background
        gui.screen.blit(home_screen, [0, 0])
        
        # add the title
        add_title(gui)
        
        # add "vs" title.
        add_title(gui, title = "vs", pos = (gui.width//2, gui.height//2), font_size=50)
        
        if time.time() - start_time<countdown: # TODO add this to general gui
            cv2.putText(img, f"Game starting in {countdown-1-int(time.time() - start_time)}", (50, 150), font, 3, (137, 0, 255), 2) 

        if time.time() - start_time > countdown:
            if not _bot_choice:
                _bot_choice = cc.bot_choice()

            if not player_choice or player_choice == "Unknown" or player_choice == "Explicit":
                player_choice = cc.check_locked_gesture(past_gestures, limit=5)

            if player_choice and player_choice != "Restart" and player_choice != "Unknown" and player_choice != "Explicit":
                
                winner = cc.check_winner(player_choice, _bot_choice)
                if not added_scores:
                    if winner == "Player":
                        player_score += 1
                    elif winner == "Bot":
                        bot_score += 1
                    added_scores = True
                cv2.putText(img, f"P: {player_choice}", (200, 120), font, 2, (137, 0, 255), 2) # TODO add this to general gui
                cv2.putText(img, f"B: {_bot_choice}", (200, 170), font, 2, (137, 0, 255), 2) # TODO add this to general gui
                if winner == "Draw":
                    cv2.putText(img, "Draw", (200, 250), font, 5, (137, 0, 255), 2) # TODO add this to general gui
                else:
                    cv2.putText(img, f"Winner: {winner}", (50, 250), font, 5, (137, 0, 255), 2) # TODO add this to general gui


        if cc.check_locked_gesture(past_gestures, limit=5) == "Explicit":
            # print("Explicit gesture detected")
            explicit = cv2.imread("explicit.png")
            try:
                finger_size = np.sqrt((lmlist[12][1]- lmlist[9][1])**2 + (lmlist[12][2]- lmlist[9][2])**2)
            except IndexError:
                finger_size = 100
                # print("error")
            scale_factor = explicit.shape[0] / finger_size
            explicit_size = [int(explicit.shape[1] / scale_factor), int(explicit.shape[0] / scale_factor)]
            # explicit_size = [120, 75]
            
            explicit = cv2.resize(explicit, explicit_size)


            coords = lmlist[11][1], lmlist[11][2]
            coords = [int(coords[0] - explicit_size[0]//2), int(coords[1] - explicit_size[1]//2)]
            x, y = coords[0], coords[1]
            y_limit_high = min(y+explicit_size[1], img.shape[0])
            x_limit_high = min(x+explicit_size[0], img.shape[1])
            y_limit_low = max(y, 0)
            x_limit_low = max(x, 0)
            img[y_limit_low:y_limit_high, x_limit_low:x_limit_high] = explicit[:y_limit_high-y_limit_low, :x_limit_high-x_limit_low]




            

            
        
        if cc.check_locked_gesture(past_gestures, limit=5) == "Restart":
            _bot_choice = None
            player_choice = None
            added_scores = False
            start_time = time.time()
            past_gestures = []
            counter = 0
            fingerlist = []
            inputlist = []

            
            cv2.putText(img, _bot_choice, (250, 150), font, 3, (137, 0, 255), 2)
        cv2.putText(img, f"Player: {player_score}", (50, 350), font, 2, (137, 0, 255), 2)
        cv2.putText(img, f"Bot: {bot_score}", (50, 400), font, 2, (137, 0, 255), 2)
        cv2.putText(img, f'FPS: {int(fps)}', (50, 50), font, 2, (137, 0, 255), 2)
        # cv.imshow('Image', img)

        # Display the webcam feed
        img = cv2.flip(img, 1)  # Reverse the image horizontally
        add_camera(gui, img)
        
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
