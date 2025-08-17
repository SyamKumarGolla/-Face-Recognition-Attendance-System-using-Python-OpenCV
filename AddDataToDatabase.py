import tkinter as tk
from tkinter import filedialog, messagebox, font, ttk
import os
import firebase_admin
from firebase_admin import credentials, db, storage

# Firebase initialization
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceatten-95927-default-rtdb.firebaseio.com/",
    'storageBucket': "faceatten-95927.appspot.com"
})

bucket = storage.bucket()

# Function to add student data and upload the image
def add_student_data():
    student_id = entry_id.get()
    name = entry_name.get()
    major = entry_major.get()
    starting_year = entry_year.get()

    if student_id and name and major and starting_year and selected_image_path:
        ref = db.reference('Students')
        data = {
            "name": name,
            "major": major,
            "starting_year": int(starting_year)
        }
        ref.child(student_id).set(data)

        # Upload the image to Firebase storage
        blob = bucket.blob(f'Images/{student_id}.png')
        blob.upload_from_filename(selected_image_path)
        messagebox.showinfo("Success", f"Student {name} added successfully with image!")

        # Clear the fields after adding data
        entry_id.delete(0, tk.END)
        entry_name.delete(0, tk.END)
        entry_major.delete(0, tk.END)
        entry_year.delete(0, tk.END)
        label_image_path.config(text="No image selected")
    else:
        messagebox.showwarning("Input Error", "Please fill all fields and select an image")

# Function to select an image file
def select_image():
    global selected_image_path
    selected_image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    if selected_image_path:
        label_image_path.config(text=os.path.basename(selected_image_path))

# Create the main window
root = tk.Tk()
root.title("Add Student Data with Image")
root.geometry("600x400")
root.config(bg="#f0f4f8")

# Center the window
root.eval('tk::PlaceWindow . center')

# Define fonts
title_font = font.Font(family="Helvetica", size=16, weight="bold")
label_font = font.Font(family="Helvetica", size=12)
button_font = font.Font(family="Helvetica", size=12, weight="bold")

# Frame for left side (Upload area)
frame_upload = tk.Frame(root, bg="#f8f8f8", bd=2, relief="solid")
frame_upload.place(x=20, y=20, width=250, height=360)

# Upload area design
label_upload = tk.Label(frame_upload, text="Drag and Drop files to upload\nor", font=label_font, bg="#f8f8f8", fg="#333")
label_upload.pack(pady=(30, 5))
button_browse = tk.Button(frame_upload, text="Browse", font=button_font, bg="#4CAF50", fg="white", command=select_image)
button_browse.pack(pady=(5, 10))
label_supported = tk.Label(frame_upload, text="Supported files: PNG, JPG, JPEG", font=("Helvetica", 10), bg="#f8f8f8", fg="#666")
label_supported.pack()

label_image_path = tk.Label(frame_upload, text="No image selected", font=("Helvetica", 10), bg="#f8f8f8", fg="#999")
label_image_path.pack(pady=(10, 5))

# Frame for right side (Student details)
frame_details = tk.Frame(root, bg="#ffffff", bd=2, relief="solid")
frame_details.place(x=300, y=20, width=270, height=360)

# Title label
label_title = tk.Label(frame_details, text="Student Information", font=title_font, bg="#ffffff", fg="#333")
label_title.pack(pady=(20, 10))

# Labels and entry fields
label_id = tk.Label(frame_details, text="Student ID:", font=label_font, bg="#ffffff")
label_id.pack(pady=(5, 0))
entry_id = tk.Entry(frame_details, font=label_font, width=25)
entry_id.pack(pady=5)

label_name = tk.Label(frame_details, text="Name:", font=label_font, bg="#ffffff")
label_name.pack(pady=(5, 0))
entry_name = tk.Entry(frame_details, font=label_font, width=25)
entry_name.pack(pady=5)

label_major = tk.Label(frame_details, text="Major:", font=label_font, bg="#ffffff")
label_major.pack(pady=(5, 0))
entry_major = tk.Entry(frame_details, font=label_font, width=25)
entry_major.pack(pady=5)

label_year = tk.Label(frame_details, text="Starting Year:", font=label_font, bg="#ffffff")
label_year.pack(pady=(5, 0))
entry_year = tk.Entry(frame_details, font=label_font, width=25)
entry_year.pack(pady=5)

# Button to add data
button_add = tk.Button(root, text="Add Data with Image", font=button_font, bg="#2196F3", fg="white", command=add_student_data, width=30)
button_add.place(x=150, y=350)

# Run the main loop
root.mainloop()
