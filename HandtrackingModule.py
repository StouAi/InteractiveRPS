import cv2 as cv
import mediapipe as mp
import time

class handDetector():
    def __init__(self,mode=False,maxHands=2,complexity = 1,detectionCon=0.5,trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.complexity = complexity
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.mphand = mp.solutions.hands
        self.hands = self.mphand.Hands(self.mode,self.maxHands,self.complexity,
                                       self.detectionCon,self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self,img,draw=True):
        imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        #print(results.multi_hand_landmarks)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,self.mphand.HAND_CONNECTIONS)
        return img


    def findPosition(self,img,handNo=0,draw=True):
        lmlist=[]
        if self.results.multi_hand_landmarks:
            myhand  = self.results.multi_hand_landmarks[handNo]
            for id,lm in enumerate(myhand.landmark):
                #print(id,lm)
                h,w,c = img.shape
                cx,cy = int(lm.x*w),int(lm.y*h)
                #print(id,cx,cy)
                lmlist.append([id,cx,cy])
                if draw:
                    cv.circle(img,(cx,cy),15,(255,0,255),cv.FILLED)
        return lmlist

def main():
    ptime=0
    ctime =0
    cap = cv.VideoCapture(0)
    detector = handDetector()
    while True:
        success, img = cap.read()
        img = detector.findHands(img)
        lmlist = detector.findPosition(img)
        if len(lmlist)!=0:
            print(lmlist[4])
        ctime = time.time()
        fps = 1/(ctime-ptime)
        ptime = ctime
        cv.putText(img,str(int(fps)),(10,70),cv.FONT_HERSHEY_PLAIN,3,(255,0,255),3)


        cv.imshow("Image", img)
        key = cv.waitKey(1)
        if key ==ord('v'):
            break


if __name__ == "__main__":
    main()