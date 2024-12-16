import cv2
import numpy as np
import pygame as pg
import time
import camera_comm as cc
import paho.mqtt.client as mqtt_client

np.random.seed(0)
font = cv2.FONT_HERSHEY_PLAIN

broker = 'test.mosquitto.org'
port = 1883
topic = "hci_2024"  

# broker = '150.140.186.118'
# port = 1883
# topic = "hci_2024"  

client_id = 'rand_id' + str(np.random.randint(0,1000))


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}\n")

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)  # Uncomment if username/password is required
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(values, message):
    client = connect_mqtt()
    # values = [1001,1,1]
    out = ",".join([str(x) for x in values])
    out+=f",{message}"
    client.publish(topic, out)

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
    question_button_image = pg.image.load('question.png').convert_alpha()
    
    # resize question button
    question_button_image = pg.transform.scale(question_button_image, (question_button_image.get_width()//2, question_button_image.get_height()//2))
    
    if not start_button_image or not exit_button_image:
        print("Error: Could not load images.")
        exit()

    return start_button_image, exit_button_image, question_button_image

def show_instructions_popup(gui):
    """Show a pop-up window with game instructions."""
    popup_width, popup_height = 600, 400
    popup_x = (gui.width - popup_width) // 2
    popup_y = (gui.height - popup_height) // 2

    # # Create a shadow for the popup
    # shadow_surface = pg.Surface((popup_width + 20, popup_height + 20), pg.SRCALPHA, 32)
    # shadow_surface.fill((0, 0, 0, 10))  # Black with transparency
    # gui.screen.blit(shadow_surface, (popup_x - 10, popup_y - 10))

    # Create the pop-up surface with rounded corners
    popup_surface = pg.Surface((popup_width, popup_height), pg.SRCALPHA)
    pg.draw.rect(popup_surface, (230, 240, 255, 240), (0, 0, popup_width, popup_height), border_radius=20)  # Light blue background

    # Add a border around the pop-up
    pg.draw.rect(popup_surface, (50, 100, 200), (0, 0, popup_width, popup_height), width=4, border_radius=20)  # Blue border

    # Add instructions text
    font_size = 30
    font = pg.font.Font('font.ttf', font_size)
    instructions_text = [
        "FOLLOWING THE RULES IS PART OF ANY GAME!",
        " ",
        " Choose Rock, Paper, or Scissors.",
        " The bot will make its own random choice.",
        " The winner is determined based on the rules:",
        "   - Rock beats Scissors",
        "   - Scissors beats Paper",
        "   - Paper beats Rock",
        " To restart the game, make a rock-on gesture.",
    ]

    # Display the text centered inside the pop-up
    y_offset = 30
    for line in instructions_text:
        text_surface = font.render(line, True, (30, 30, 80))  # Dark blue text
        text_rect = text_surface.get_rect(center=(popup_width // 2, y_offset))
        popup_surface.blit(text_surface, text_rect.topleft)
        y_offset += 40  # Move down for the next line

    # Position of the close button (top-right of the pop-up)
    close_button_x = popup_x + popup_width - 40
    close_button_y = popup_y + 20

    def draw_close_button():
        mouse_pos = pg.mouse.get_pos()
        button_color = (100, 150, 255) if (close_button_x <= mouse_pos[0] <= close_button_x + 20 and \
                                           close_button_y <= mouse_pos[1] <= close_button_y + 20) else (200, 200, 255)
        pg.draw.circle(gui.screen, button_color, (close_button_x + 10, close_button_y + 10), 10)
        pg.draw.line(gui.screen, (255, 255, 255), (close_button_x + 5, close_button_y + 5), (close_button_x + 15, close_button_y + 15), 2)
        pg.draw.line(gui.screen, (255, 255, 255), (close_button_x + 15, close_button_y + 5), (close_button_x + 5, close_button_y + 15), 2)

    # Display the pop-up on the screen
    gui.screen.blit(popup_surface, (popup_x, popup_y))
    draw_close_button()
    pg.display.update()

    # Handle events for closing the pop-up
    pop_up_running = True
    while pop_up_running:
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                # Close the popup if the close button is clicked
                if close_button_x <= event.pos[0] <= close_button_x + 20 and \
                   close_button_y <= event.pos[1] <= close_button_y + 20:
                    pop_up_running = False
            elif event.type == pg.QUIT:
                pop_up_running = False

        # Ensure the popup and button remain visible
        # gui.screen.blit(shadow_surface, (popup_x - 10, popup_y - 10))
        gui.screen.blit(popup_surface, (popup_x, popup_y))
        draw_close_button()
        pg.display.update()

    # Close the popup and return to the home screen
    pg.display.update()

def home_screen(gui):
    """Home screen showing the title and buttons."""
    home_screen = pg.image.load("bg.jpg").convert()
    start_button_image, exit_button_image, question_button_image = load_images()

    start_btn = Button(640 - start_button_image.get_width() - 50, 500, start_button_image, gui.screen)
    exit_btn = Button(640 + 50, 500, exit_button_image, gui.screen)
    question_btn = Button(1140 , 600, question_button_image, gui.screen)
    
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
                elif question_btn.is_hovered(mouse_pos):
                    show_instructions_popup(gui)
                    
            if start_btn.is_hovered(mouse_pos) or exit_btn.is_hovered(mouse_pos) or question_btn.is_hovered(mouse_pos):
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            else:
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)

        
        gui.screen.blit(home_screen, (0, 0))
        
        # Add the title
        add_title(gui)
        
        start_btn.draw()
        exit_btn.draw()
        question_btn.draw()
        
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
    bot_animation_flag = True
    last_explicit = time.time()
    
    # Load images
    images = [
        pg.image.load("rock.png"),
        pg.image.load("paper.png"),
        pg.image.load("scissors.png"),
        pg.image.load("rock_lose.png"),
        pg.image.load("paper_lose.png"),
        pg.image.load("scissors_lose.png"),
        pg.image.load("rock_win.png"),
        pg.image.load("paper_win.png"),
        pg.image.load("scissors_win.png")
    ]
    
    # Scale images to fit desired size
    images = [pg.transform.scale(img, (350, 350)) for img in images]

    # Dictionary to map choices to images
    bot_choice_images = {
        "Rock": images[0],
        "Paper": images[1],
        "Scissors": images[2]
    }

    while running:
        
        ret, img = cap.read()
        if not ret:
            print("Error: Failed to capture video.")

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
        else:
            past_gestures.append("Unknown")
        
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        # Draw the background
        gui.screen.blit(home_screen, [0, 0])
        
        # add the title
        add_title(gui)
        
        # add "vs" title.
        add_title(gui, title = "vs", pos = (gui.width//2, gui.height//2+200), font_size=50)
        
        # add player and player's score title.
        add_title(gui, title = "Player's score: ", pos = (gui.width//2 +300, gui.height//2 + 200), font_size=50)
        add_title(gui, title = str(player_score), pos = (gui.width//2+500, gui.height//2 + 200), font_size=50)

        # add player's choice title.
        
        # Display the animation
        add_bot_animation(gui, bot_animation_flag)
        
        # add bot and bot's score title.
        add_title(gui, title = "Bot's score: ", pos = (gui.width//2 - 400, gui.height//2 + 200), font_size=50)
        add_title(gui, title = str(bot_score), pos = (gui.width//2-200, gui.height//2 + 200), font_size=50)
        
        if time.time() - start_time<countdown: # TODO add this to general gui
            cv2.putText(img, f"Game starting in {countdown-1-int(time.time() - start_time)}", (50, 150), font, 3, (137, 0, 255), 2) 

        if time.time() - start_time > countdown:
            bot_animation_flag = True
            if not _bot_choice:
                _bot_choice = cc.bot_choice()

            if not player_choice or player_choice == "Unknown" or player_choice == "Explicit":
                player_choice = cc.check_locked_gesture(past_gestures, limit=5)

            if player_choice and player_choice != "Restart" and player_choice != "Unknown" and player_choice != "Explicit":
                #Display Bot choice
                if _bot_choice in bot_choice_images:
                    bot_choice_image = bot_choice_images[_bot_choice]
                    gui.screen.blit(bot_choice_image, (gui.width // 4 - bot_choice_image.get_width() // 2, 200))  
                    bot_animation_flag = False       
                                   
                winner = cc.check_winner(player_choice, _bot_choice)
                if not added_scores:
                    if winner == "Player":
                        publish([1001], "win")
                        player_score += 1

                    elif winner == "Bot":
                        publish([1001, 500, 1001], "lose")
                        bot_score += 1
                    else:
                        publish([2000], "draw")
                    added_scores = True

                
                if winner == "Draw":
                    cv2.putText(img, "Draw", (200, 250), font, 5, (137, 0, 255), 2) # TODO add this to general gui
                else:
                    cv2.putText(img, f"Winner: {winner}", (50, 250), font, 5, (137, 0, 255), 2) # TODO add this to general gui


        if cc.check_locked_gesture(past_gestures, limit=5) == "Explicit":

            explicit = cv2.imread("explicit.png")
            if time.time() - last_explicit > 1.3:
                # print("sent explicit"+ str(time.time()))
                last_explicit = time.time()
                publish([1001, 1, 1], "explicit")
            try:
                finger_size = np.sqrt((lmlist[12][1]- lmlist[9][1])**2 + (lmlist[12][2]- lmlist[9][2])**2)
            except IndexError:
                finger_size = 100
                # print("error")
            scale_factor = explicit.shape[0] / finger_size
            explicit_size = [int(explicit.shape[1] / scale_factor), int(explicit.shape[0] / scale_factor)]
            # explicit_size = [120, 75]
            
            explicit = cv2.resize(explicit, explicit_size)

            try:
                coords = lmlist[11][1], lmlist[11][2]
                coords = [int(coords[0] - explicit_size[0]//2), int(coords[1] - explicit_size[1]//2)]
                x, y = coords[0], coords[1]
                y_limit_high = min(y+explicit_size[1], img.shape[0])
                x_limit_high = min(x+explicit_size[0], img.shape[1])
                y_limit_low = max(y, 0)
                x_limit_low = max(x, 0)
                img[y_limit_low:y_limit_high, x_limit_low:x_limit_high] = explicit[:y_limit_high-y_limit_low, :x_limit_high-x_limit_low]
            except:
                pass
        
        if cc.check_locked_gesture(past_gestures, limit=5) == "Restart":
            _bot_choice = None
            player_choice = None
            added_scores = False
            start_time = time.time()
            past_gestures = []
            counter = 0
            fingerlist = []
            inputlist = []
            bot_animation_flag = True

            
            cv2.putText(img, _bot_choice, (250, 150), font, 3, (137, 0, 255), 2)


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

def add_bot_animation(gui, flag = False):
    """Show three images sequentially every 1 second."""
    
    if flag:

        # Load images
        images = [
            pg.image.load("rock.png"),
            pg.image.load("paper.png"),
            pg.image.load("scissors.png")
        ]

        # Scale images to fit desired size
        images = [pg.transform.scale(img, (300, 300)) for img in images]

        # Determine the current image based on time
        elapsed_time = pg.time.get_ticks() // 500  # Convert milliseconds to seconds
        current_image = elapsed_time % len(images)  # Cycle through the images

        
        # Draw the current image
        bot_x = gui.width // 4 - images[current_image].get_width() // 2
        bot_y = 200
        gui.screen.blit(images[current_image], (bot_x, bot_y))
    
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
        
    elif screen_status == 'question':
        # pop up window with instructions
        print("question mark clicked")        
        screen_status = home_screen(home_gui)   


if __name__ == "__main__":
    main()
