import tkinter as tk
from views.gui import ChatGUI
from controllers.chat_controller import ChatController

def main():
    """Start the chat client."""
    root = tk.Tk()
    controller = ChatController(None, host='127.0.0.1', port=5000)  # Update host/port as needed
    view = ChatGUI(root, controller)
    controller.view = view
    controller.start()
    root.protocol("WM_DELETE_WINDOW", controller.shutdown)  # Handle window close
    root.mainloop()

if __name__ == "__main__":
    main()