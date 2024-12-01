
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


def is_finger_closed(finger_list, direction=1, axis=1):
    return direction * finger_list[1][axis] < direction * finger_list[3][axis]


def get_closed_fingers(lmlist, direction=1, axis=1):
    finger_indexes = [
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16],
        [17, 18, 19, 20]
    ]

    finger_statuses = []
    for finger, indices in enumerate(finger_indexes):
        status = is_finger_closed([lmlist[x] for x in indices], direction=direction, axis=axis)
        finger_statuses.append(status)

    return finger_statuses


def finger_combo(lmlist):
    finger_statuses = get_closed_fingers(lmlist, -1, 1)

    if finger_statuses == [False, False, True, True]:
        return "Scissors"
    elif finger_statuses == [True, True, True, True]:
        return "Rock"

    elif finger_statuses == [False, False, False, False]:
        return "Paper"
    else:
        print(finger_statuses)
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


counter = 0
past_gestures = []
while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmlist = detector.findPosition(img, draw=False)

    if len(lmlist) != 0:
        counter += 1
        # time.sleep(3)
        fingerpos1 = finger_combo(lmlist)
        fingerlist.append(fingerpos1)
        past_gestures.append(fingerpos1)

        if counter % 10 == 0:
            print(check_locked_gesture(past_gestures))

        # print(fingerpos1)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv.putText(img, "yolo", (150, 150), cv.FONT_HERSHEY_PLAIN, 2, (137, 0, 255), 2)
    cv.putText(img, f'FPS: {int(fps)}', (50, 50), cv.FONT_HERSHEY_PLAIN, 2, (137, 0, 255), 2)
    cv.imshow('Image', img)
    key = cv.waitKey(1)
    if key == ord('v'):
        break
