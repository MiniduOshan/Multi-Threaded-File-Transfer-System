import socket
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from encryption import encrypt_data, decrypt_data, KEY_FILE, generate_key

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

HOST = '0.0.0.0'
PORT = 5001
BUFFER_SIZE = 8192
HEADER_MAX_SIZE = 8192
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
if not os.path.exists(KEY_FILE):
    logging.info("Secret key not found, generating new key...")
    generate_key()

executor = ThreadPoolExecutor(max_workers=10)


def recv_header(conn, max_size=HEADER_MAX_SIZE):
    """Read a newline-terminated command header and return (parts, remaining_bytes)."""
    data = bytearray()
    while b"\n" not in data:
        chunk = conn.recv(1024)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > max_size:
            raise ValueError("Header too large")

    if b"\n" not in data:
        raise ValueError("Incomplete command header")

    header, remainder = bytes(data).split(b"\n", 1)
    parts = header.decode("utf-8").strip().split()
    if not parts:
        raise ValueError("Empty command header")

    return parts, remainder

def handle_client(conn, addr):
    logging.info(f"New connection from {addr}")

    try:
        parts, initial_data = recv_header(conn)
        command = parts[0]

        if command == "UPLOAD":
            if len(parts) < 3:
                logging.error(f"Malformed UPLOAD command from {addr}")
                conn.sendall(b"ERROR MALFORMED_UPLOAD\n")
                return
                
            filename = os.path.basename(parts[1])
            filesize = int(parts[2])
            if filesize < 0:
                conn.sendall(b"ERROR INVALID_FILE_SIZE\n")
                return

            filepath = os.path.join(UPLOAD_DIR, filename)
            logging.info(f"Receiving {filename} ({filesize} bytes) from {addr}")

            file_data = bytearray(initial_data[:filesize])
            received = len(file_data)

            while received < filesize:
                chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
                if not chunk:
                    break
                file_data.extend(chunk)
                received += len(chunk)

            if received == filesize:
                encrypted = encrypt_data(bytes(file_data))
                with open(filepath, "wb") as f:
                    f.write(encrypted)
                logging.info(f"File {filename} received, encrypted, and saved.")
                conn.sendall(b"OK UPLOAD_COMPLETE\n")
            else:
                logging.warning(f"File {filename} transfer incomplete ({received}/{filesize} bytes received).")
                conn.sendall(b"ERROR INCOMPLETE_UPLOAD\n")

        elif command == "DOWNLOAD":
            if len(parts) < 2:
                logging.error(f"Malformed DOWNLOAD command from {addr}")
                conn.sendall(b"ERROR MALFORMED_DOWNLOAD\n")
                return
                
            filename = os.path.basename(parts[1])
            filepath = os.path.join(UPLOAD_DIR, filename)

            if not os.path.exists(filepath):
                conn.sendall(b"ERROR FILE_NOT_FOUND\n")
                logging.warning(f"Client requested non-existent file: {filename}")
                return

            with open(filepath, "rb") as f:
                encrypted = f.read()

            try:
                decrypted = decrypt_data(encrypted)
            except Exception as e:
                logging.error(f"Failed to decrypt file {filename}: {e}")
                conn.sendall(b"ERROR DECRYPTION_FAILED\n")
                return

            conn.sendall(f"OK {len(decrypted)}\n".encode("utf-8"))
            
            sent = 0
            while sent < len(decrypted):
                chunk = decrypted[sent:sent+BUFFER_SIZE]
                conn.sendall(chunk)
                sent += len(chunk)

            logging.info(f"File {filename} decrypted and sent to {addr}")
        else:
            logging.warning(f"Unknown command from {addr}: {command}")
            conn.sendall(b"ERROR UNKNOWN_COMMAND\n")

    except Exception as e:
        logging.error(f"Error handling client {addr}: {e}")

    finally:
        conn.close()
        logging.info(f"Connection with {addr} closed")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(128)

    logging.info(f"🚀 Socket server listening on {HOST}:{PORT}")

    while True:
        try:
            conn, addr = server.accept()
            executor.submit(handle_client, conn, addr)
        except KeyboardInterrupt:
            logging.info("Shutting down server...")
            break
        except Exception as e:
            logging.error(f"Server accept error: {e}")

if __name__ == "__main__":
    start_server()
