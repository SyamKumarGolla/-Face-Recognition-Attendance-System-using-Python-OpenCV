import os
import pickle
import cv2
import face_recognition
import numpy as np

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

# Video Capture
cap = cv2.VideoCapture('sampl 8.mp4')
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
cachedStudentInfo = {}  # Cache student info
cachedStudentImages = {}  # Cache student images
slot_height = 150  # Height of each user slot in the right panel

while True:
    success, img = cap.read()
    if not success:
        print("Video finished or unable to load the frame.")
        break

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Detect faces and encodings in the current frame
    faceCurrFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurrFrame)

    img = cv2.resize(img, (640, 480))
    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[0]

    detected_faces = []

    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurrFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            id = studentIds[matchIndex]
            y1, x2, y2, x1 = [coord * 4 for coord in faceLoc]
            bbox_x1, bbox_y1 = x1 + 55, y1 + 162
            bbox_x2, bbox_y2 = x2 + 55, y2 + 162

            # Draw bounding box on the face
            #cv2.rectangle(imgBackground, (bbox_x1, bbox_y1), (bbox_x2, bbox_y2), (0, 255, 0), 2)

            # Fetch student info if not already cached
            if id not in cachedStudentInfo:
                studentInfo = db.reference(f'Students/{id}').get()
                if studentInfo:
                    cachedStudentInfo[id] = studentInfo
                    blob = bucket.get_blob(f'Images/{id}.png')
                    if blob:
                        array = np.frombuffer(blob.download_as_string(), np.uint8)
                        imgStudent = cv2.imdecode(array, cv2.IMREAD_COLOR)
                        cachedStudentImages[id] = imgStudent

            # Get student info from the cache
            studentInfo = cachedStudentInfo.get(id, {})
            imgStudent = cachedStudentImages.get(id, None)

            # Store detected face details for organized display
            detected_faces.append({
                "id": id,
                "name": studentInfo.get("name", "Unknown"),
                "major": studentInfo.get("major", "Unknown"),
                "starting_year": studentInfo.get("starting_year", "Unknown"),
                "image": imgStudent
            })

    # Clear the right panel and display details for detected faces
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[0]

    for idx, face in enumerate(detected_faces[:4]):  # Limit to 4 slots (adjust as needed)
        y_offset = 50 + idx * slot_height

        # Draw student thumbnail
        if face["image"] is not None:
            imgResized = cv2.resize(face["image"], (100, 100))
            imgBackground[y_offset:y_offset + 100, 820:820 + 100] = imgResized

        # Display student details next to the thumbnail
        cv2.putText(imgBackground, f"ID: {face['id']}", (930, y_offset + 20),
                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (50, 50, 50), 1)
        cv2.putText(imgBackground, f"Name: {face['name']}", (930, y_offset + 50),
                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (50, 50, 50), 1)
        cv2.putText(imgBackground, f"Major: {face['major']}", (930, y_offset + 80),
                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (50, 50, 50), 1)

    # Show the video frame
    cv2.imshow("Face Recognition", imgBackground)

    # Keyboard controls
    key = cv2.waitKey(1)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
