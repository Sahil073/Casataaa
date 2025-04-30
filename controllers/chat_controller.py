import threading
import socket
import os
from models.network import NetworkModel
from models.encryption import EncryptionModel
import time

class ChatController:
    def __init__(self, view, host='127.0.0.1', port=5000):
        """
        Initialize the controller with a view and network settings.
        Args:
            view: ChatGUI instance for displaying messages.
            host: Server host IP.
            port: Server port.
        """
        self.view = view
        self.host = host
        self.port = port
        self.encryption = EncryptionModel()
        self.client = None

    def start(self):
        """Connect to the server and start receiving messages."""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def send_message(self, message):
        """
        Send a message to the server.
        Args:
            message: String message to send.
        """
        if message.startswith('/download '):
            encrypted_message = self.encryption.encrypt(message)
            self.client.send(encrypted_message)
        else:
            encrypted_message = self.encryption.encrypt(f"{self.client.getsockname()[0]}: {message}")
            self.client.send(encrypted_message)

    def send_file(self, file_path):
        """
        Send a file to the server.
        Args:
            file_path: Path to the file to upload.
        """
        with open(file_path, 'rb') as f:
            file_data = f.read()
            timestamp = str(int(time.time()))
            encrypted_data = self.encryption.encrypt(file_data)
            self.client.send(encrypted_data)
            # Send timestamp as file_id (simplified for now)
            self.client.send(self.encryption.encrypt(timestamp.encode()))
            self.view.display_message("System", f"File {os.path.basename(file_path)} uploaded, ID: {timestamp}")

    def receive_messages(self):
        """Receive messages from the server in a loop."""
        while True:
            try:
                message = self.client.recv(1024 * 1024)  # Larger buffer for files
                if not message:
                    break
                decrypted_message = self.encryption.decrypt(message).decode()
                if decrypted_message.startswith("File not found"):
                    self.view.display_message("System", decrypted_message)
                elif "uploaded" in decrypted_message:
                    self.view.display_message("System", decrypted_message)
                elif decrypted_message.startswith('/download '):
                    self.handle_download(decrypted_message.split(' ')[1])
                else:
                    self.view.display_message("Server", decrypted_message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def handle_download(self, file_id):
        """
        Handle file download by saving the received file locally.
        Args:
            file_id: File identifier (timestamp).
        """
        try:
            response = self.client.recv(1024 * 1024)  # Receive file data
            decrypted_data = self.encryption.decrypt(response)
            with open(f"downloaded_file_{file_id}.bin", 'wb') as f:
                f.write(decrypted_data)
            self.view.display_message("System", f"File {file_id} downloaded successfully")
        except Exception as e:
            self.view.display_message("System", f"Error downloading file {file_id}: {e}")

    def shutdown(self):
        """Close the client socket."""
        if self.client:
            self.client.close()