import os
import pickle
import cv2
import face_recognition
import numpy as np
from datetime import datetime

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
cap = cv2.VideoCapture(0)
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
id = -1
imgStudent = []
cachedStudentInfo = {}  # Caching student info
cachedStudentImages = {}  # Caching student images
slot_height = 150  # Height of each user slot in the right panel
frame_skip = 2  # Process every 2 frames to improve performance
marked_present = set()  # Set to keep track of IDs marked as present

# Fetch all student IDs from Firebase
ref = db.reference('Students')
all_students = ref.get()
all_student_ids = list(all_students.keys()) if all_students else []

frame_count = 0

while True:
    success, img = cap.read()
    if not success:
        print("Unable to load the frame.")
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue  # Skip frames

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)  # Smaller frame for faster face recognition
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Detect faces and encodings in the current frame
    faceCurrFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurrFrame)

    img = cv2.resize(img, (640, 480))  # Resize the video frame to fit the background
    imgBackground[162:162 + 480, 55:55 + 640] = img  # Insert video frame into background

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

            # Mark the student as present if not already marked
            if id not in marked_present:
                marked_present.add(id)

                # Mark attendance in Firebase
                today_date = datetime.now().strftime("%Y-%m-%d")
                ref = db.reference(f'Students/{id}/Attendance')
                ref.child(today_date).set("Present")

            # Store detected face details for organized display
            detected_faces.append({
                "id": id,
                "name": studentInfo.get("name", "Unknown"),
                "major": studentInfo.get("major", "Unknown"),
                "starting_year": studentInfo.get("starting_year", "Unknown"),
                "image": imgStudent,
                "present": id in marked_present
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
        cv2.putText(imgBackground, f"Year: {face['starting_year']}", (930, y_offset + 110),
                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (50, 50, 50), 1)

        # Display "Present" if the student has been marked as present
        if face["present"]:
            cv2.putText(imgBackground, "Present", (930, y_offset + 140),
                        cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 255, 0), 1)

    # Display the updated background
    cv2.imshow("Face Recognition", imgBackground)

    # Keyboard controls for quitting
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Mark absent students
today_date = datetime.now().strftime("%Y-%m-%d")
for student_id in all_student_ids:
    if student_id not in marked_present:
        ref = db.reference(f'Students/{student_id}/Attendance')
        ref.child(today_date).set("Absent")

cap.release()
cv2.destroyAllWindows()