
import HandtrackingModule as htm
import time
import numpy as np
import cv2 as cv
from collections import Counter

cap = cv.VideoCapture(0)
wcap, hcap = 800, 800
cap.set(4, wcap)
cap.set(3, hcap)
pTime = 0
detector = htm.handDetector(detectionCon=0.75, )
# setting the finger positions for each number
fingerlist = []
inputlist = []
num = 0
np.random.seed(0)
font = cv.FONT_HERSHEY_PLAIN

countdown = 3


def is_finger_closed(finger_list, direction=1, axis=1):
    return direction * finger_list[1][axis] < direction * finger_list[3][axis]


def get_closed_fingers(lmlist, direction=1, axis=1):
    finger_indexes = [
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16],
        [17, 18, 19, 20]
    ]

    if (lmlist[0][axis]-lmlist[9][axis])>0:
        direction = 1
    else:
        direction = -1
    

    finger_statuses = []
    for finger, indices in enumerate(finger_indexes):
        status = is_finger_closed([lmlist[x] for x in indices], direction=direction, axis=axis)
        finger_statuses.append(status)

    return finger_statuses


def finger_combo(lmlist):
    finger_statuses = get_closed_fingers(lmlist, 1, 1)

    if finger_statuses == [False, False, True, True]:
        return "Scissors"
    elif finger_statuses == [True, True, True, True]:
        return "Rock"

    elif finger_statuses == [False, False, False, False]:
        return "Paper"
    
    elif finger_statuses == [False, True, True, False]:
        return "Restart"
    else:
        # print(finger_statuses)
        return "Unknown"



def check_locked_gesture(past_gestures, limit=60):
    if not len(past_gestures) > limit:
        return False

    unique_gestures = {}
    for gesture in past_gestures[-limit:]:
        if gesture not in unique_gestures:
            unique_gestures[gesture] = 0
        else:
            unique_gestures[gesture] += 1

    if len(unique_gestures.keys()) > 1:
        return False
    else:
        return list(unique_gestures.keys())[0]

def bot_choice():
    return np.random.choice(["Rock", "Paper", "Scissors"])

def check_winner(player_choice, bot_choice):
    if player_choice == bot_choice:
        return "Draw"
    elif player_choice == "Rock" and bot_choice == "Scissors":
        return "Player"
    elif player_choice == "Scissors" and bot_choice == "Paper":
        return "Player"
    elif player_choice == "Paper" and bot_choice == "Rock":
        return "Player"
    else:
        return "Bot"
    
def play_round(player_choice, bot_choice):
    print(f"Player: {player_choice}")
    print(f"Bot: {bot_choice}")
    winner = check_winner(player_choice, bot_choice)
    print(f"Winner: {winner}")
    return winner


counter = 0
past_gestures = []
start_time = time.time()
_bot_choice = None
player_choice = None
player_score = 0
bot_score = 0
added_scores = False

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmlist = detector.findPosition(img, draw=False)

    if len(lmlist) != 0:
        counter += 1
        fingerpos1 = finger_combo(lmlist)
        fingerlist.append(fingerpos1)
        past_gestures.append(fingerpos1)

        # if counter % 10 == 0:
        #     print(check_locked_gesture(past_gestures, limit = 5))

        # print(fingerpos1)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    if 0<time.time() - start_time<countdown:
        cv.putText(img, f"Game starting in {countdown-1-int(time.time() - start_time)}", (50, 150), font, 3, (137, 0, 255), 2)  
    if time.time() - start_time > countdown:
        if not _bot_choice:
            _bot_choice = bot_choice()
        if not player_choice or player_choice == "Unknown":
            player_choice = check_locked_gesture(past_gestures, limit=5)
        if player_choice and player_choice != "Restart" and player_choice != "Unknown":
            
            winner = check_winner(player_choice, _bot_choice)
            if not added_scores:
                if winner == "Player":
                    player_score += 1
                elif winner == "Bot":
                    bot_score += 1
                added_scores = True
            cv.putText(img, f"P: {player_choice}", (200, 120), font, 2, (137, 0, 255), 2)
            cv.putText(img, f"B: {_bot_choice}", (200, 170), font, 2, (137, 0, 255), 2)
            if winner == "Draw":
                cv.putText(img, "Draw", (200, 250), font, 5, (137, 0, 255), 2)
            else:
                cv.putText(img, f"Winner: {winner}", (50, 250), font, 5, (137, 0, 255), 2)



    # if time.time() - start_time > 10:
    if check_locked_gesture(past_gestures, limit=5) == "Restart":
        _bot_choice = None
        player_choice = None
        added_scores = False
        start_time = time.time()
        past_gestures = []
        counter = 0
        fingerlist = []
        inputlist = []

        
        cv.putText(img, _bot_choice, (250, 150), font, 3, (137, 0, 255), 2)
    cv.putText(img, f"Player: {player_score}", (50, 350), font, 2, (137, 0, 255), 2)
    cv.putText(img, f"Bot: {bot_score}", (50, 400), font, 2, (137, 0, 255), 2)
    cv.putText(img, f'FPS: {int(fps)}', (50, 50), font, 2, (137, 0, 255), 2)
    cv.imshow('Image', img)
    key = cv.waitKey(1)
    if key == ord('v'):
        break
