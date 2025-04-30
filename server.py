from models.network import NetworkModel

def main():
    """Start the chat server."""
    try:
        server = NetworkModel(host='0.0.0.0', port=5000)
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    main()