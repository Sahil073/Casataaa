# models/network.py (Updated)
import socket
import threading
import logging
import os
import time
from datetime import datetime, timedelta
from models.encryption import EncryptionModel

# Configure logging
logging.basicConfig(filename='logs/chat.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NetworkModel:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        self.clients = []
        self.lock = threading.Lock()
        self.encryption = EncryptionModel()
        self.history_file = 'chat_history.txt'
        self.files_dir = 'files/'  # Directory to store received files
        os.makedirs(self.files_dir, exist_ok=True)  # Create files directory if it doesn't exist
        self.cleanup_history()  # Clean up old messages on startup

    def cleanup_history(self):
        """Remove messages older than 48 hours from chat_history.txt."""
        if os.path.exists(self.history_file):
            current_time = time.time()
            history = []
            try:
                with open(self.history_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            encrypted_line = line.strip().encode()
                            decrypted_line = self.encryption.decrypt(encrypted_line).decode()
                            timestamp = float(decrypted_line.split(' [')[1].split(']')[0])  # Extract timestamp
                            if current_time - timestamp < 172800:  # 48 hours in seconds
                                history.append(line)
            except Exception as e:
                logging.error("Error cleaning history: %s", e)
            with open(self.history_file, 'w') as f:
                for line in history:
                    f.write(line)
            logging.info("Cleaned up chat history, removed messages older than 48 hours")

    def start(self):
        logging.info("Server started on %s:%s", self.host, self.port)
        print(f"Server started on {self.host}:{self.port}...")
        self.load_and_send_history()
        while True:
            try:
                client, addr = self.server.accept()
                with self.lock:
                    self.clients.append(client)
                logging.info("New connection from %s", addr)
                print(f"New connection from {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(client, addr))
                client_thread.start()
            except Exception as e:
                logging.error("Error accepting client connection: %s", e)
                print(f"Error accepting client connection: {e}")
                break

    def handle_client(self, client, addr):
        self.send_history(client)
        while True:
            try:
                message = client.recv(1024)
                if not message:
                    break
                decoded_message = self.encryption.decrypt(message).decode()
                logging.info("Message received from %s: %s", addr, decoded_message)
                print(f"Message received from {addr}: {decoded_message}")
                if decoded_message.startswith('/download '):
                    self.handle_download_request(client, decoded_message.split(' ')[1])
                else:
                    timestamp = time.time()
                    full_message = f"{addr}: {decoded_message} [{timestamp}]"
                    self.save_message(full_message)
                    self.broadcast(self.encryption.encrypt(full_message.encode()), client)
            except Exception as e:
                logging.error("Error handling client %s: %s", addr, e)
                print(f"Error handling client {addr}: {e}")
                break
        with self.lock:
            if client in self.clients:
                self.clients.remove(client)
        client.close()
        logging.info("Client disconnected: %s", addr)
        print(f"Client disconnected: {addr}")

    def broadcast(self, message, sender):
        with self.lock:
            for client in self.clients:
                if client != sender:
                    try:
                        client.send(message)
                    except Exception as e:
                        logging.error("Error broadcasting to client: %s", e)
                        print(f"Error broadcasting to client: {e}")
                        client.close()
                        self.clients.remove(client)

    def save_message(self, message):
        """Save message to chat history file with encryption and timestamp."""
        with open(self.history_file, 'a') as f:
            encrypted_message = self.encryption.encrypt(message.encode())
            f.write(encrypted_message.decode() + '\n')

    def load_history(self):
        """Load encrypted history from file."""
        history = []
        try:
            with open(self.history_file, 'r') as f:
                for line in f:
                    if line.strip():
                        history.append(self.encryption.encrypt(line.strip().encode()))
        except FileNotFoundError:
            logging.info("No chat history file found, creating new one.")
        return history

    def send_history(self, client):
        """Send chat history to a new client."""
        history = self.load_history()
        for message in history:
            try:
                client.send(message)
            except Exception as e:
                logging.error("Error sending history to client: %s", e)

    def load_and_send_history(self):
        """Load history and send to all existing clients on server start."""
        history = self.load_history()
        with self.lock:
            for client in self.clients:
                for message in history:
                    try:
                        client.send(message)
                    except Exception as e:
                        logging.error("Error sending history to client: %s", e)

    def handle_download_request(self, client, file_id):
        """Handle file download request from client."""
        file_path = os.path.join(self.files_dir, f"file_{file_id}.bin")
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_data = f.read()
                encrypted_data = self.encryption.encrypt(file_data)
                client.send(encrypted_data)
        else:
            client.send(self.encryption.encrypt("File not found".encode()))

    def save_file(self, data, timestamp):
        """Save received file with a unique name."""
        file_path = os.path.join(self.files_dir, f"file_{timestamp}.bin")
        with open(file_path, 'wb') as f:
            f.write(data)
        return timestamp

    def shutdown(self):
        with self.lock:
            for client in self.clients:
                client.close()
        self.server.close()
        logging.info("Server shut down")
        print("Server shut down")