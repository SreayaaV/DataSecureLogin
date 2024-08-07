import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from datetime import datetime
import socket
import hashlib
import os
import serial
import time

# Global variables
unauthorized_count = 0
admin_device_ip = socket.gethostbyname(socket.gethostname())  # Get the device's IP address
upload_folder = "ADMIN_UPLOADS"
log_file = "logs.txt"
# Serial communication with Arduino
arduino = serial.Serial('COM6', 9600, timeout=1)
arduino.flush()


# Ensure the existence of the upload folder
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

# Dictionary to store regular user credentials and access permissions
regular_users = {
    "user1": {"password": "password1", "documents": [], "access": []},
    "user2": {"password": "password2", "documents": [], "access": []},
    "user3": {"password": "password3", "documents": [], "access": []},
    "user4": {"password": "password4", "documents": [], "access": []}
}

# Function to hash password using SHA-512
def hash_password(password):
    return hashlib.sha512(password.encode()).hexdigest()

# Function to log activity
def log_activity(activity, user_type):
    with open(log_file, 'a') as file:
        timestamp = str(datetime.now())
        file.write(f"{timestamp} [{user_type.upper()}]: {activity}\n")

# Function to read admin password
def read_admin_password():
    try:
        with open('admin_password.txt', 'r') as file:
            return file.readline().strip()
    except FileNotFoundError:
        return None

# Function to handle admin user login
def on_admin_user_login():
    admin_password = read_admin_password()
    if not admin_password:
        # If admin password file does not exist, prompt to set a new password
        set_admin_password()
    else:
        password = simpledialog.askstring("Admin Login", "Enter admin password:")
        if password:
            if hash_password(password) == admin_password:
                global unauthorized_count
                unauthorized_count = 0
                log_activity(f"Admin user login from IP address: {admin_device_ip}", "admin")
                messagebox.showinfo("Admin Login", "Admin login successful.")
                open_admin_panel()
                # Activate LED for 10 seconds
                send_to_arduino('1')
            else:
                unauthorized_count += 1
                if unauthorized_count >= 3:
                    messagebox.showwarning("Possible Attack", "Possible unauthorized access attempts detected. Change password now.")
                    unauthorized_count = 0
                    change_password()
                    send_to_arduino('3')
                else:
                    messagebox.showerror("Admin Login", "Incorrect admin password.")
                    # Activate buzzer for unauthorized login
                    send_to_arduino('3')

# Function to set admin password
def set_admin_password():
    new_password = simpledialog.askstring("Set Password", "Set admin password:")
    if new_password:
        save_admin_password(new_password)
        messagebox.showinfo("Password Set", "Admin password has been set successfully. Please login again.")

# Function to open admin panel
def open_admin_panel():
    admin_panel = tk.Toplevel()
    admin_panel.title("Admin Panel")
    admin_panel.geometry("300x200")

    # Buttons for admin actions
    manage_passwords_button = tk.Button(admin_panel, text="Manage Passwords", command=change_password)
    manage_passwords_button.pack(pady=5)

    view_logs_button = tk.Button(admin_panel, text="View Logs", command=view_logs)
    view_logs_button.pack(pady=5)

    upload_document_button = tk.Button(admin_panel, text="Upload Document", command=upload_document)
    upload_document_button.pack(pady=5)

# Function to change admin password
def change_password():
    new_password = simpledialog.askstring("Change Password", "Enter new admin password:")
    if new_password:
        save_admin_password(new_password)
        messagebox.showinfo("Password Changed", "Admin password has been changed successfully.")

# Function to save admin password
def save_admin_password(password):
    hashed_password = hash_password(password)
    with open('admin_password.txt', 'w') as file:
        file.write(hashed_password)

# Function to view logs
def view_logs():
    # Open logs file using default text editor
    try:
        with open(log_file, 'r') as file:
            logs_content = file.read()
            messagebox.showinfo("Log History", logs_content)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Function to upload document
def upload_document():
    file_path = filedialog.askopenfilename(initialdir="./", title="Select Document to Upload", 
                                           filetypes=(("All files", "*.*"),))
    if file_path:
        file_name = os.path.basename(file_path)
        selected_users = select_users_for_document()  # Prompt admin to select users to share the document with
        if selected_users:
            # Update access permissions for selected users
            for user in selected_users:
                regular_users[user]["documents"].append(file_name)
                regular_users[user]["access"].append(file_name)
            # Move the file to the ADMIN UPLOADS folder
            destination_path = os.path.join(upload_folder, file_name)
            os.rename(file_path, destination_path)
            log_activity(f"Admin uploaded '{file_name}'", "admin")
            messagebox.showinfo("Document Uploaded", f"Document uploaded successfully as '{destination_path}'")

# Function to prompt admin to select users for document sharing
def select_users_for_document():
    return simpledialog.askstring("Select Users", "Enter usernames (comma-separated) to share the document with:").split(",")

# Function to handle regular user login
def on_regular_user_login():
    username = simpledialog.askstring("Regular User Login", "Enter username:")
    password = simpledialog.askstring("Regular User Login", "Enter password:")
    if username in regular_users and password == regular_users[username]["password"]:
        log_activity(f"Regular user login as '{username}'", "regular")
        messagebox.showinfo("Regular User Login", "Regular user login successful.")
        open_document_viewer(username)  # Open document viewer for regular user
        # Activate LED for 10 seconds
        send_to_arduino('1')
    else:
        messagebox.showerror("Regular User Login", "Incorrect username or password.")
        # Activate buzzer for unauthorized login
        send_to_arduino('3')

# Function to open document viewer for regular user
def open_document_viewer(username):
    documents = regular_users[username]["documents"]
    access = regular_users[username]["access"]
    file_name = simpledialog.askstring("Enter Document Name", "Enter the name of the document you want to download:")
    if file_name in documents:
        file_path = os.path.join(upload_folder, file_name)
        if os.path.exists(file_path):
            # Check file extension to determine file type
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension in ('.mp4', '.avi', '.mkv', '.mov', '.wmv'):
                # If it's a video file, play it using a suitable player
                os.startfile(file_path)
            else:
                # Otherwise, open it as a regular file
                os.startfile(file_path)
        else:
            messagebox.showerror("File Not Found", f"Document '{file_name}' not found.")
            send_to_arduino('3')
    else:
        messagebox.showerror("Access Denied", "You do not have permission to view this document.")
        send_to_arduino('3')

def send_to_arduino(command):
    arduino.write(command.encode())

# GUI setup
root = tk.Tk()
root.title("Password Protected System")
root.geometry("400x150")

# Frame for buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=20)

# Button for admin user login
admin_user_button = tk.Button(button_frame, text="Admin User", command=on_admin_user_login, bg="blue", fg="white")
admin_user_button.grid(row=0, column=0, padx=5)

# Button for regular user login
regular_user_button = tk.Button(button_frame, text="Regular User", command=on_regular_user_login, bg="green", fg="white")
regular_user_button.grid(row=0, column=1, padx=5)

root.mainloop()
 