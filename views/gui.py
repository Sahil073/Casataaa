import tkinter as tk
from tkinter import filedialog, ttk
import datetime
import platform
import os

# Ensure pygame is installed for sound handling
try:
    import pygame
    pygame.mixer.init()
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

class ChatGUI:
    def __init__(self, root, controller):
        self.root = root
        self.root.title("💬 Encrypted Chat App")
        self.root.geometry("700x550")
        self.root.resizable(False, False)

        self.controller = controller  # Reference to ChatController for sending/receiving
        self.colors = {
            "dark": {
                "bg": "#1e1e1e", "fg": "#f5f5f5", "entry": "#2a2a2a",
                "button": "#4CAF50", "button_active": "#45a049", "chat_bg": "#262626",
                "bubble_user": "#3a8edb", "bubble_other": "#444", "emoji_bg": "#333333",
                "button_border": "#f5f5f5", "title_color": "#4CAF50"
            }
        }

        self.current_colors = self.colors["dark"]
        self.build_widgets()
        self.bind_events()  # Bind Enter key event

    def build_widgets(self):
        self.root.configure(bg=self.current_colors["bg"])
        
        # Top frame for title
        top_frame = tk.Frame(self.root, bg=self.current_colors["bg"])
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.title_label = tk.Label(top_frame, text="💬 Encrypted Chat App", font=("Segoe UI", 16, "bold"),
                                    bg=self.current_colors["bg"], fg=self.current_colors["title_color"])
        self.title_label.pack(side=tk.LEFT)

        # Chat area with Canvas + Scrollbar
        self.canvas_frame = tk.Frame(self.root, bg=self.current_colors["chat_bg"])
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        self.canvas = tk.Canvas(self.canvas_frame, bg=self.current_colors["chat_bg"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.current_colors["chat_bg"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bottom input area
        bottom_frame = tk.Frame(self.root, bg=self.current_colors["bg"])
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        self.entry_field = tk.Entry(bottom_frame, font=("Segoe UI", 10),
                                    bg=self.current_colors["entry"], fg=self.current_colors["fg"],
                                    insertbackground=self.current_colors["fg"], width=50, relief="flat")
        self.entry_field.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        self.emoji_button = tk.Button(bottom_frame, text="😄", width=3, command=self.open_emoji_picker,
                                      bg=self.current_colors["button"], fg=self.current_colors["fg"],
                                      relief="solid", bd=2, activebackground=self.current_colors["button_active"])
        self.emoji_button.pack(side=tk.LEFT)

        self.send_button = tk.Button(bottom_frame, text="📤 Send", command=self.send_message,
                                     bg=self.current_colors["button"], fg=self.current_colors["fg"],
                                     relief="solid", bd=2, activebackground=self.current_colors["button_active"])
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.upload_button = tk.Button(bottom_frame, text="📁 Upload", command=self.upload_file,
                                       bg=self.current_colors["button"], fg=self.current_colors["fg"],
                                       relief="solid", bd=2, activebackground=self.current_colors["button_active"])
        self.upload_button.pack(side=tk.LEFT)

        self.download_button = tk.Button(bottom_frame, text="⬇️ Download", command=self.download_file,
                                         bg=self.current_colors["button"], fg=self.current_colors["fg"],
                                         relief="solid", bd=2, activebackground=self.current_colors["button_active"])
        self.download_button.pack(side=tk.LEFT)

    def bind_events(self):
        """Bind Enter key to send message."""
        self.root.bind('<Return>', lambda event: self.send_message())
        self.entry_field.bind('<Return>', lambda event: self.send_message())

    def update_theme(self):
        c = self.current_colors
        self.root.configure(bg=c["bg"])
        self.title_label.configure(bg=c["bg"], fg=c["title_color"])
        self.canvas.configure(bg=c["chat_bg"])
        self.scrollable_frame.configure(bg=c["chat_bg"])
        self.entry_field.configure(bg=c["entry"], fg=c["fg"], insertbackground=c["fg"])
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=c["bg"])
        self.update_button_styles()

    def update_button_styles(self):
        c = self.current_colors
        buttons = [self.send_button, self.upload_button, self.emoji_button, self.download_button]
        for button in buttons:
            button.configure(bg=c["button"], fg=c["fg"], activebackground=c["button_active"],
                             relief="solid", bd=2)

    def send_message(self):
        msg = self.entry_field.get().strip()
        if msg:
            if msg.startswith('/download '):
                self.controller.send_message(msg)  # Handle download request
            else:
                self.controller.send_message(msg)  # Send regular message
                self.display_message("You", msg)
                self.entry_field.delete(0, tk.END)
                self.play_send_sound()

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.controller.send_file(file_path)
            self.display_message("System", f"📁 File uploaded: {os.path.basename(file_path)}")
            self.play_upload_sound()

    def download_file(self):
        file_id = self.entry_field.get().strip()
        if file_id and file_id.startswith('/download '):
            self.controller.send_message(file_id)  # Send download request
            self.entry_field.delete(0, tk.END)
        else:
            self.display_message("System", "Please enter /download <file_id> to download a file.")

    def display_message(self, sender, message):
        timestamp = datetime.datetime.now().strftime("%H:%M")
        is_user = sender == "You"
        color = self.current_colors["bubble_user"] if is_user else self.current_colors["bubble_other"]
        text_color = "#fff" if is_user else self.current_colors["fg"]

        wrapper = tk.Frame(self.scrollable_frame, bg=self.current_colors["chat_bg"])
        bubble = tk.Label(wrapper,
                          text=f"{'🧑' if is_user else '💻'} {sender} [{timestamp}]\n{message}",
                          bg=color, fg=text_color, wraplength=400, justify="left",
                          font=("Segoe UI", 10), padx=10, pady=5,
                          bd=0, relief="flat")
        bubble.pack(padx=10, pady=4, anchor="e" if is_user else "w")
        wrapper.pack(fill=tk.X)

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        self.play_receive_sound()

    def display_history(self, history):
        """Display chat history received from the server."""
        self.scrollable_frame.destroy()  # Clear existing content
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.current_colors["chat_bg"])
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        for line in history.split('\n'):
            if line.strip():
                sender, msg = line.split(': ', 1)
                msg = msg.split(' [')[0]  # Remove timestamp for display
                self.display_message(sender, msg)
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def open_emoji_picker(self):
        picker = tk.Toplevel(self.root)
        picker.title("Choose Emoji")
        picker.geometry("300x200")
        picker.configure(bg=self.current_colors["emoji_bg"])
        emojis = ["😀", "😂", "😍", "😎", "🤔", "🙄", "👍", "🎉", "😢", "😡", "🔥", "💯"]

        def insert_emoji(e):
            self.entry_field.insert(tk.END, e)
            picker.destroy()

        for i, emoji in enumerate(emojis):
            b = tk.Button(picker, text=emoji, font=("Segoe UI", 14), command=lambda e=emoji: insert_emoji(e),
                          bg=self.current_colors["emoji_bg"], relief="flat", bd=0)
            b.grid(row=i // 6, column=i % 6, padx=10, pady=10)

    def play_send_sound(self):
        if SOUND_AVAILABLE:
            try:
                pygame.mixer.music.load("send_message.mp3")  # Path to send sound file
                pygame.mixer.music.play()
            except:
                print("Send sound error.")

    def play_upload_sound(self):
        if SOUND_AVAILABLE:
            try:
                pygame.mixer.music.load("upload_file.mp3")  # Path to upload sound file
                pygame.mixer.music.play()
            except:
                print("Upload sound error.")

    def play_receive_sound(self):
        if SOUND_AVAILABLE:
            try:
                pygame.mixer.music.load("notification.mp3")  # Path to notification sound file
                pygame.mixer.music.play()
            except:
                pass
        elif platform.system() == "Windows":
            import winsound
            winsound.MessageBeep()

# Example usage (to be integrated with client.py)
if __name__ == "__main__":
    root = tk.Tk()
    # Placeholder for controller (to be provided by controllers/chat_controller.py)
    class DummyController:
        def send_message(self, msg):
            print(f"Sending: {msg}")
        def send_file(self, file_path):
            print(f"Uploading: {file_path}")

    app = ChatGUI(root, DummyController())
    root.mainloop()