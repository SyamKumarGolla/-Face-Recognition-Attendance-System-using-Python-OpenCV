import tkinter as tk
from tkinter import messagebox, ttk
import firebase_admin
from firebase_admin import credentials, db
import subprocess  # For running main.py after login
import os

# Firebase initialization
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceatten-95927-default-rtdb.firebaseio.com/"
})

# Function to create a new user registration window
def open_register_window():
    register_window = tk.Toplevel(root)
    register_window.title("Create Account")
    register_window.geometry("300x200")

    # Center the register window after it's fully initialized
    register_window.after(100, lambda: register_window.eval(
        'tk::PlaceWindow %s center' % register_window.winfo_pathname(register_window.winfo_id())))

    # Adding labels and entry fields
    label_username = ttk.Label(register_window, text="Username:", font=("Arial", 10))
    label_username.pack(pady=(20, 5))
    entry_new_username = ttk.Entry(register_window, width=25)
    entry_new_username.pack(pady=5)

    label_password = ttk.Label(register_window, text="Password:", font=("Arial", 10))
    label_password.pack(pady=5)
    entry_new_password = ttk.Entry(register_window, width=25, show="*")
    entry_new_password.pack(pady=5)

    # Register Button
    btn_register = ttk.Button(register_window, text="Create Account",
                              command=lambda: register(entry_new_username, entry_new_password))
    btn_register.pack(pady=20)

# Function to register a new user
def register(username_entry, password_entry):
    username = username_entry.get()
    password = password_entry.get()

    if not username or not password:
        messagebox.showwarning("Input Error", "Please enter both username and password.")
        return

    # Check if user already exists
    ref = db.reference(f'users/{username}')
    if ref.get():
        messagebox.showerror("Registration Error", "Username already exists. Try another one.")
        return

    # Store new user credentials
    ref.set({
        'username': username,
        'password': password
    })
    messagebox.showinfo("Success", "Account created successfully! You can now log in.")
    username_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)

# Function to login an existing user
def login():
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        messagebox.showwarning("Input Error", "Please enter both username and password.")
        return

    # Fetch user credentials from Firebase
    ref = db.reference(f'users/{username}')
    user_data = ref.get()

    if user_data and user_data['password'] == password:
        messagebox.showinfo("Login Success", "You are logged in!")

        main_script_path = r"C:\Users\chett\PycharmProjects\pythonProject1\main.py"
        python_executable = r"C:\Users\chett\AppData\Local\Programs\Python\Python310\python.exe"

        if os.path.exists(main_script_path):
            try:
                # Launch main.py using subprocess
                subprocess.Popen([python_executable, main_script_path], shell=True)
                print("Running main.py...")
                print(f"Using Python: {python_executable}")
                print(f"Running script: {main_script_path}")

                root.destroy()  # Close the login window if applicable
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print(f"File not found: {main_script_path}")

    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")

# Function to toggle password visibility
def toggle_password():
    if entry_password.cget('show') == '*':
        entry_password.config(show='')
    else:
        entry_password.config(show='*')

# Setting up the main login GUI
root = tk.Tk()
root.title("Login Panel")
root.geometry("400x250")
root.configure(bg="#006d77")

# Title label
label_title = ttk.Label(root, text="Login Form", font=("Arial", 16, "bold"), background="#006d77", foreground="white")
label_title.pack(pady=(20, 10))

# Username and Password fields
label_username = ttk.Label(root, text="Username:", background="#006d77", foreground="white", font=("Arial", 10))
label_username.pack(pady=(5, 0))
entry_username = ttk.Entry(root, width=30)
entry_username.pack(pady=5)

label_password = ttk.Label(root, text="Password:", background="#006d77", foreground="white", font=("Arial", 10))
label_password.pack(pady=(5, 0))
entry_password = ttk.Entry(root, width=30, show="*")
entry_password.pack(pady=5)

# Show/Hide Password Checkbox
check_show_password = ttk.Checkbutton(root, text="Show Password", command=toggle_password)
check_show_password.pack(pady=5)

# Login and Register Buttons
btn_login = ttk.Button(root, text="Login", command=login)
btn_login.pack(pady=(10, 5))
btn_register = ttk.Button(root, text="Create Account", command=open_register_window)
btn_register.pack()

root.mainloop()
