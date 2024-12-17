import mediapipe as mp
import numpy as np
import cv2


class HandDetector():
    def __init__(self, mode=False, max_hands=2, complexity = 1, detection_con=0.5, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.complexity = complexity
        self.detection_con = detection_con
        self.track_con = track_con
        self.mphand = mp.solutions.hands
        self.hands = self.mphand.Hands(self.mode, self.max_hands, self.complexity,
                                       self.detection_con, self.track_con)
        self.mpDraw = mp.solutions.drawing_utils

    def find_hands(self, img):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            for landmark in self.results.multi_hand_landmarks:
                self.mpDraw.draw_landmarks(img, landmark, self.mphand.HAND_CONNECTIONS)
        return img

    def find_position(self, img, hand_No=0):
        landmarks = []
        if self.results.multi_hand_landmarks:
            myhand = self.results.multi_hand_landmarks[hand_No]
            for id, lm in enumerate(myhand.landmark):
                h, w, _ = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                landmarks.append([id, cx, cy])
        return landmarks


def is_finger_closed(finger_list, wrist):
    v1 = np.array(finger_list[1]) - np.array(wrist)
    v2 = np.array(finger_list[3]) - np.array(finger_list[1])
    cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    return cos_theta < 0


def get_closed_fingers(landmarks):
    finger_indexes = [
        [ 5,  6,  7,  8],
        [ 9, 10, 11, 12],
        [13, 14, 15, 16],
        [17, 18, 19, 20]
    ]

    finger_statuses = []
    for _, indices in enumerate(finger_indexes):
        status = is_finger_closed([landmarks[idx] for idx in indices], wrist = landmarks[0])
        finger_statuses.append(status)
    
    return finger_statuses


def finger_combo(landmarks):
    finger_statuses = get_closed_fingers(landmarks)

    if finger_statuses == [True, True, True, True]:
        return "rock"
    elif finger_statuses == [False, False, False, False]:
        return "paper"
    elif finger_statuses == [False, False, True, True]:
        return "scissors"
    elif finger_statuses == [False, True, True, False]:
        return "Restart"
    elif finger_statuses == [True, False, True, True]:
        return "Explicit"
    else:
        return "Unknown"


def check_locked_gesture(past_gestures, limit=60):
    if len(past_gestures) <= limit:
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
    return np.random.choice(["rock", "paper", "scissors"])


def check_winner(player_choice, bot_choice):
    if player_choice == bot_choice:
        return "Draw"
    elif player_choice == "rock" and bot_choice == "scissors":
        return "Player"
    elif player_choice == "scissors" and bot_choice == "paper":
        return "Player"
    elif player_choice == "paper" and bot_choice == "rock":
        return "Player"
    else:
        return "Bot"
    

detector = HandDetector(detection_con=0.75)
