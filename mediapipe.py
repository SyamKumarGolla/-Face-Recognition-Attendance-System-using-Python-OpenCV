import os
import pickle
import cv2
import cvzone
import face_recognition
import numpy as np
import mediapipe as mp  # Importing mediapipe

import firebase_admin
from firebase_admin import credentials, db, storage

# Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://faceatten-95927-default-rtdb.firebaseio.com/",
        'storageBucket': "faceatten-95927.appspot.com"
    })

bucket = storage.bucket()

# Mediapipe Face Detection Initialization
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# Video Capture
cap = cv2.VideoCapture('sample.mp4')
cap.set(3, 640)
cap.set(4, 480)

# Load Background
imgBackground = cv2.imread('Resources/background.png')

# Import Mode Images
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]

# Load Encodings
print("Loading Encode File...")
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded...")

# Variables
modeType = 0
counter = 0
id = -1
imgStudent = []
cachedStudentInfo = {}  # Caching student info
cachedStudentImages = {}  # Caching student images

# Video Playback Control Settings
frame_skip = 1  # Process every frame by default
playback_speed = 1
paused = False
skip_frames = 30  # Number of frames to skip forward or backward

# Initialize Mediapipe Face Detection
with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
    while True:
        if not paused:
            for _ in range(frame_skip):  # Skip frames for faster processing
                success, img = cap.read()
                if not success:
                    print("Video finished or unable to load the frame.")
                    break

        if not success:
            break  # Exit if the video ends or there is an error in reading the video

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert image to RGB for mediapipe
        results = face_detection.process(img_rgb)  # Use Mediapipe for face detection

        img = cv2.resize(img, (640, 480))  # Resize the video frame to fit the background
        imgBackground[162:162 + 480, 55:55 + 640] = img  # Insert video frame into background
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]  # Mode display

        # Reset studentInfo and id for each frame
        studentInfo = None
        id = -1

        # Process detections from Mediapipe
        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, _ = img.shape
                bbox = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                       int(bboxC.width * iw), int(bboxC.height * ih)

                # Draw bounding box
                bbox_x1 = 55 + bbox[0]
                bbox_y1 = 162 + bbox[1]
                bbox_x2 = 55 + bbox[0] + bbox[2]
                bbox_y2 = 162 + bbox[1] + bbox[3]

                bbox_x1 = max(55, min(bbox_x1, 55 + 640))
                bbox_y1 = max(162, min(bbox_y1, 162 + 480))
                bbox_x2 = max(55, min(bbox_x2, 55 + 640))
                bbox_y2 = max(162, min(bbox_y2, 162 + 480))

                bbox = (bbox_x1, bbox_y1, bbox_x2 - bbox_x1, bbox_y2 - bbox_y1)
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

                # Face Recognition
                imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)  # Smaller frame for face encoding
                imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
                encodeCurFrame = face_recognition.face_encodings(imgS)

                if encodeCurFrame:
                    matches = face_recognition.compare_faces(encodeListKnown, encodeCurFrame[0])
                    faceDis = face_recognition.face_distance(encodeListKnown, encodeCurFrame[0])

                    # Find the best match index
                    matchIndex = np.argmin(faceDis)

                    if matches[matchIndex]:
                        print("Known Face Detected")
                        id = studentIds[matchIndex]  # Update recognized person's ID
                        print(f"Detected ID: {id}")

                        if counter == 0:
                            counter = 1
                            modeType = 1

                        # Check if student info is already cached
                        if id in cachedStudentInfo:
                            studentInfo = cachedStudentInfo[id]
                            imgStudent = cachedStudentImages.get(id)
                        else:
                            print(f"Fetching data for ID: {id}")  # Fetching data if not cached
                            studentInfo = db.reference(f'Students/{id}').get()

                            if studentInfo:
                                cachedStudentInfo[id] = studentInfo  # Cache student info
                                print(f"Student Info for ID {id}: {studentInfo}")

                                blob = bucket.get_blob(f'Images/{id}.png')
                                if blob:
                                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                                    imgStudent = cv2.imdecode(array, cv2.IMREAD_COLOR)
                                    cachedStudentImages[id] = imgStudent  # Cache student image
                                else:
                                    print(f"No image found for ID {id}")
                            else:
                                print(f"Student info not found for ID {id}")
                                continue  # Skip if no student info found

                        # Display student info on the background
                        if studentInfo:
                            cv2.putText(imgBackground, str(studentInfo['name']), (808, 445),
                                        cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)
                            cv2.putText(imgBackground, str(studentInfo['major']), (1006, 550),
                                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                            cv2.putText(imgBackground, str(studentInfo['starting_year']), (1125, 625),
                                        cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                            cv2.putText(imgBackground, str(id), (1006, 493),
                                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                            # Resize and display the student's image
                            if imgStudent is not None:
                                imgStudent = cv2.resize(imgStudent, (216, 216))
                                imgBackground[175:175 + 216, 909:909 + 216] = imgStudent

                        counter += 1

        # Display the updated background
        cv2.imshow("Face Attendance", imgBackground)

        # Keyboard controls for playback and frame skipping
        key = cv2.waitKey(playback_speed) & 0xFF
        if key == ord('q'):  # Quit
            break
        elif key == ord('p'):  # Pause or resume
            paused = not paused
        elif key == ord('f'):  # Skip forward
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES) + skip_frames)
        elif key == ord('b'):  # Skip backward
            current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(current_frame - skip_frames, 0))

cap.release()
cv2.destroyAllWindows()
