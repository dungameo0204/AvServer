import tkinter as tk
from tkinter import messagebox
import subprocess
import os

def run_release_builder():
    try:
        # Chạy file Python xử lý logic của bạn
        subprocess.run(["python", "ReleaseBuilder.py"], check=True)
        log_text.insert(tk.END, "Successfully ran ReleaseBuilder.py\n")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run builder: {e}")

def git_push():
    try:
        commands = [
            ["git", "add", "."],
            ["git", "commit", "-m", "Manual update via Dashboard"],
            ["git", "push", "origin", "main"]
        ]
        for cmd in commands:
            subprocess.run(cmd, check=True)
        log_text.insert(tk.END, "Successfully pushed to GitHub!\n")
        messagebox.showinfo("Success", "Server updated successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Git error: {e}")

# Giao diện
root = tk.Tk()
root.title("AvServer Manager Dashboard")
root.geometry("400x300")

tk.Label(root, text="Server Management", font=("Arial", 14, "bold")).pack(pady=10)

tk.Button(root, text="1. Build Manifest (Python)", command=run_release_builder, 
          bg="#e1e1e1", width=25).pack(pady=5)

tk.Button(root, text="2. Push to GitHub", command=git_push, 
          bg="#4CAF50", fg="white", width=25).pack(pady=5)

log_text = tk.Text(root, height=8, width=45)
log_text.pack(pady=10)

root.mainloop()