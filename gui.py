import paho.mqtt.client as mqtt_client
import pygame as pg
import numpy as np
import cv2, time, utils

# MQTT settings
broker = '150.140.186.118'
port = 1883
topic = "hci_2024"  
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

def mqtt_publish(values, message):
    try:
        client = connect_mqtt()
        out = ",".join([str(x) for x in values])
        out += f",{message}"
        client.publish(topic, out)
    except:
        print("Mqtt error: Could not publish message.")
        return

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
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.rot90(img)
        img = pg.surfarray.make_surface(img)
        self.screen.blit(img, (0, 0))
        pg.display.flip()
        self.clock.tick(60)

    def close(self):
        pg.quit()


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
    return {
        "home_screen": pg.image.load("images/bg.jpg"),
        "animated_image": pg.image.load('images/hands.png'),
        "start_button_image": pg.image.load('images/start_btn.jpg'),
        "exit_button_image": pg.image.load('images/exit_btn.jpg'),
        "question_button_image": pg.transform.scale(pg.image.load('images/question.png'), (100, 120)),
        "qr_button_image": pg.transform.scale(pg.image.load('images/qr.png'), (100, 100)),
        "qr_code_image": pg.transform.scale(pg.image.load("images/scan.png"), (300, 300)),
        "rock": pg.image.load("images/rock.png"),
        "rock_lose": pg.image.load("images/rock_lose.png"),
        "rock_win": pg.image.load("images/rock_win.png"),
        "paper": pg.image.load("images/paper.png"),
        "paper_lose": pg.image.load("images/paper_lose.png"),
        "paper_win": pg.image.load("images/paper_win.png"),
        "scissors": pg.image.load("images/scissors.png"),
        "scissors_lose": pg.image.load("images/scissors_lose.png"),
        "scissors_win": pg.image.load("images/scissors_win.png")
    }

def open_camera():
    print("Opening camera...")
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("Camera opened successfully.")
        return cap
    
    print("Error: Could not open camera.")
    return


def show_qr_popup(gui):
    """Show a pop-up window with QR code for the game."""
    popup_width, popup_height = 500, 500
    popup_x = (gui.width - popup_width) // 2
    popup_y = (gui.height - popup_height) // 2
    
    # Create the pop-up surface with rounded corners
    popup_surface = pg.Surface((popup_width, popup_height), pg.SRCALPHA)
    pg.draw.rect(popup_surface, (230, 240, 255, 240), (0, 0, popup_width, popup_height), border_radius=20)  # Light blue background
    
    # Add a border around the pop-up
    pg.draw.rect(popup_surface, (50, 100, 200), (0, 0, popup_width, popup_height), width=4, border_radius=20)  # Blue border
    
    # Add QR code image
    qr_code_image = images["qr_code_image"]

    qr_code_x = (popup_width - qr_code_image.get_width()) // 2
    qr_code_y = (popup_height - qr_code_image.get_height()) // 2
    popup_surface.blit(qr_code_image, (qr_code_x, qr_code_y))
    
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
        gui.screen.blit(popup_surface, (popup_x, popup_y))
        draw_close_button()
        pg.display.update()

    # Close the popup and return to the home screen
    pg.display.update()
    
def show_instructions_popup(gui):
    """Show a pop-up window with game instructions."""
    popup_width, popup_height = 600, 400
    popup_x = (gui.width - popup_width) // 2
    popup_y = (gui.height - popup_height) // 2

    # Create the pop-up surface with rounded corners
    popup_surface = pg.Surface((popup_width, popup_height), pg.SRCALPHA)
    pg.draw.rect(popup_surface, (230, 240, 255, 240), (0, 0, popup_width, popup_height), border_radius=20)  # Light blue background

    # Add a border around the pop-up
    pg.draw.rect(popup_surface, (50, 100, 200), (0, 0, popup_width, popup_height), width=4, border_radius=20)  # Blue border

    # Add instructions text
    font = pg.font.Font('font.ttf', 30)
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
        gui.screen.blit(popup_surface, (popup_x, popup_y))
        draw_close_button()
        pg.display.update()

    # Close the popup and return to the home screen
    pg.display.update()


def draw_text(gui, text, pos, font_size):
    font = pg.font.Font('font.ttf', font_size)
    text = pg.font.Font.render(font, text, True, (168, 83, 76))
    gui.screen.blit(text, (int(pos[0]) - text.get_width() // 2, int(pos[1])))
    
def draw_camera_feed(gui, frame):
    # Resize and draw the camera feed
    frame = cv2.resize(frame, (320, 250))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    camera_surface = pg.surfarray.make_surface(frame)

    camera_x = (gui.width - camera_surface.get_width()) // 2  # Center horizontally
    camera_y = gui.height - camera_surface.get_height() - 50  # Offset from the bottom

    # Draw border around the camera feed
    border_rect = pg.Rect(camera_x - 5, camera_y - 5, camera_surface.get_width() + 10, camera_surface.get_height() + 10)
    pg.draw.rect(gui.screen, (255, 255, 255), border_rect)

    # Draw the camera feed
    gui.screen.blit(camera_surface, (camera_x, camera_y))


def home_screen(gui):
    """
    Home screen showing the title and buttons.
    """
    # Create home screen buttons 
    start_btn = Button(640 - images["start_button_image"].get_width() - 50, 500, images["start_button_image"], gui.screen)
    exit_btn = Button(640 + 50, 500, images["exit_button_image"], gui.screen)
    question_btn = Button(1140 , 600, images["question_button_image"], gui.screen)
    qr_btn = Button(50 , 620, images["qr_button_image"], gui.screen)
    
    # Create an animated image to display on the home screen 
    animation = Animation(640 - images["animated_image"].get_width() // 2, 150, images["animated_image"], gui.screen)  # Position above the buttons

    while True:
        mouse_pos = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                # Start game
                if start_btn.is_hovered(mouse_pos):
                    game_screen(gameplay_gui)
                    return
                # Exit
                elif exit_btn.is_hovered(mouse_pos):
                    home_gui.close()
                    return
                # Instructions
                elif question_btn.is_hovered(mouse_pos):
                    show_instructions_popup(gui)
                # QR code
                elif qr_btn.is_hovered(mouse_pos):
                    show_qr_popup(gui)
                    
            if start_btn.is_hovered(mouse_pos) or exit_btn.is_hovered(mouse_pos) or question_btn.is_hovered(mouse_pos) or qr_btn.is_hovered(mouse_pos):
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            else:
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)

        # Draw home screen components
        gui.screen.blit(images["home_screen"], (0, 0))
        draw_text(gui, text="Rock-Paper-Scissors Shoot!", pos=(gui.width // 2, 50), font_size=100)

        start_btn.draw()
        exit_btn.draw()
        question_btn.draw()
        qr_btn.draw()
        
        animation.update()
        animation.draw()
        
        # Update the display
        pg.display.update()

def game_screen(gui):
    """
    Game screen to show webcam feed during the game.
    """
    pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)

    past_gestures, counter = [], 0
    start_time, last_explicit_time = time.time(), time.time()
    player_choice, bot_choice = None, None
    player_score, bot_score = 0, 0
    added_scores = False

    while True:
        ret, img = cap.read()

        if not ret:
            print("Error: Failed to capture video.")

        img = cv2.flip(img, 1)  # Reverse the image horizontally
        
        img = utils.detector.find_hands(img)
        landmarks = utils.detector.find_position(img)

        for event in pg.event.get():
            if event.type == pg.QUIT:  # Quit event
                gameplay_gui.close()
                cap.release()
                return
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_q:  # Press 'Q' to quit
                    gameplay_gui.close()
                    cap.release()
                    return
        
        # Capture the hand landmarks and check for gestures
        if len(landmarks) != 0:
            counter += 1
            finger_pos = utils.finger_combo(landmarks)
            past_gestures.append(finger_pos)
        else:
            past_gestures.append("Unknown")
        
        # Draw the background
        gui.screen.blit(images["home_screen"], [0, 0])
        
        # Draw the player's and bot's scores
        draw_text(gui, text=f"Player's score:   {player_score}", pos=(gui.width//2 + 300, 50), font_size=50)
        draw_text(gui, text=f"Bot's score:   {bot_score}", pos=(gui.width//2 - 400, 50), font_size=50)

        current_time = time.time()
        
        # Countdown before the game starts (Rock, Paper, Scissors)
        if current_time - start_time < 1:
            draw_text(gui, text="Rock", pos=(gui.width//2, gui.height//2-100), font_size=100)
        elif current_time - start_time < 2:
            draw_text(gui, text="Paper", pos=(gui.width//2, gui.height//2-100), font_size=100)
        elif current_time - start_time < 3:
            draw_text(gui, text="Scissors", pos=(gui.width//2, gui.height//2-100), font_size=100)
        # Game has started
        else:
            # Bot's choice
            if not bot_choice:
                bot_choice = utils.bot_choice()

            # Player's choice
            if not player_choice or player_choice == "Unknown" or player_choice == "Explicit":
                player_choice = utils.check_locked_gesture(past_gestures, limit=5)
                draw_text(gui, text="Shoot!", pos=(gui.width//2, gui.height//2-100), font_size=100)

            if player_choice and player_choice != "Restart" and player_choice != "Unknown" and player_choice != "Explicit":
                draw_text(gui, text = "VS", pos = (gui.width//2, gui.height//2-100), font_size=100)
                
                # Check winner
                winner = utils.check_winner(player_choice, bot_choice)

                # Update scores and publish vibration message
                if not added_scores:
                    if winner == "Player":
                        player_score += 1
                        mqtt_publish([1001], "win")
                    elif winner == "Bot":
                        mqtt_publish([1001, 500, 1001], "lose")
                        bot_score += 1
                    else:
                        mqtt_publish([2000], "draw")
                    added_scores = True
                    
                # Display the choices made by the player and bot
                if winner == "Player":
                    bot_choice_image = images[bot_choice+"_lose"]
                    player_choice_image = images[player_choice+"_win"]
                    gui.screen.blit(bot_choice_image, (gui.width // 4 - bot_choice_image.get_width() // 2 -100, 100))
                    gui.screen.blit(player_choice_image, (gui.width // 4 - bot_choice_image.get_width() // 2+700, 100))
                elif winner == "Bot":
                    bot_choice_image = images[bot_choice+"_win"]
                    player_choice_image = images[player_choice+"_lose"]
                    gui.screen.blit(bot_choice_image, (gui.width // 4 - bot_choice_image.get_width() // 2 -100, 100))
                    gui.screen.blit(player_choice_image, (gui.width // 4 - bot_choice_image.get_width() // 2+700, 100))
                else:
                    bot_choice_image = images[bot_choice]
                    player_choice_image = images[player_choice]
                    gui.screen.blit(bot_choice_image, (gui.width // 4 - bot_choice_image.get_width() // 2 -100, 100))
                    gui.screen.blit(player_choice_image, (gui.width // 4 - bot_choice_image.get_width() // 2+700, 100))

        # Easter Egg!!
        if utils.check_locked_gesture(past_gestures, limit=5) == "Explicit":

            explicit = cv2.imread("images/explicit.png")
            if current_time - last_explicit_time > 1.3:
                last_explicit_time = current_time
                mqtt_publish([1001], "explicit")

            try:
                finger_size = np.sqrt((landmarks[12][1]- landmarks[9][1])**2 + (landmarks[12][2]- landmarks[9][2])**2)
            except IndexError:
                finger_size = 100
            
            scale_factor = explicit.shape[0] / finger_size
            explicit_size = [int(explicit.shape[1] / scale_factor), int(explicit.shape[0] / scale_factor)]
            explicit = cv2.resize(explicit, explicit_size)

            try:
                coords = landmarks[11][1], landmarks[11][2]
                coords = [int(coords[0] - explicit_size[0]//2), int(coords[1] - explicit_size[1]//2)]
                x, y = coords[0], coords[1]
                y_limit_high = min(y+explicit_size[1], img.shape[0])
                x_limit_high = min(x+explicit_size[0], img.shape[1])
                y_limit_low = max(y, 0)
                x_limit_low = max(x, 0)
                img[y_limit_low:y_limit_high, x_limit_low:x_limit_high] = explicit[:y_limit_high-y_limit_low, :x_limit_high-x_limit_low]
            except:
                pass
        
        # Restart the game if the player makes a rock-on gesture
        if utils.check_locked_gesture(past_gestures, limit=5) == "Restart":
            bot_choice = None
            player_choice = None
            added_scores = False
            start_time = current_time
            past_gestures = []
            counter = 0


        # Display the webcam feed
        img = cv2.flip(img, 1)  # Reverse the image horizontally
        draw_camera_feed(gui, img)
        
        # Update the display
        pg.display.update()


if __name__ == "__main__":
    # Load images and open the camera
    images = load_images()
    cap = open_camera()

    # Create GUI objects for the home and gameplay screens
    home_gui = GUI(1280, 720, "Rock-Paper-Scissors Shoot!")
    gameplay_gui = GUI(1280, 720, "Rock-Paper-Scissors Shoot!")

    # Start the game by displaying the home screen
    home_screen(home_gui)
