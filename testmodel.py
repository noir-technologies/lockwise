import cv2 
from controller import doorAutomate
import time

video = cv2.VideoCapture(0)

if not video.isOpened():
    print("Error: Could not open video device")
    exit()

facedetect = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("Trainer.yml")

name_list = ["", "Gabriel"]

imgBackground = cv2.imread("background.png")

door_opened = False

while True:
    ret, frame = video.read()
    if not ret:
        print("Failed to capture image")
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)
    
    for (x, y, w, h) in faces:
        serial, conf = recognizer.predict(gray[y:y+h, x:x+w])
        if conf > 50 and not door_opened:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 1)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (50, 50, 255), 2)
            cv2.rectangle(frame, (x, y-40), (x+w, y), (50, 50, 255), -1)
            cv2.putText(frame, name_list[serial], (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # Open the door
            print("Face recognized: Opening the door")
            doorAutomate(0)
            time.sleep(10)
            doorAutomate(1)
            print("Door closed")
            door_opened = True  # Ensure the door only opens once

        else:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 1)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (50, 50, 255), 2)
            cv2.rectangle(frame, (x, y-40), (x+w, y), (50, 50, 255), -1)
            cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Reset the door_opened flag if the door is closed
    if door_opened:
        door_opened = False
    
    frame = cv2.resize(frame, (640, 480))
    imgBackground[162:162 + 480, 55:55 + 640] = frame
    cv2.imshow("Frame", imgBackground)
    
    k = cv2.waitKey(1)
    
    if k == ord("q"):
        break

video.release()
cv2.destroyAllWindows()
