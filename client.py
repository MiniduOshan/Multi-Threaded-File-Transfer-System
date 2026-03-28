import socket
import os

SERVER_IP = "127.0.0.1"
PORT = 5001
BUFFER_SIZE = 4096
HEADER_MAX_SIZE = 8192


def recv_line(sock, max_size=HEADER_MAX_SIZE):
    data = bytearray()
    while b"\n" not in data:
        chunk = sock.recv(1024)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > max_size:
            raise ValueError("Header too large")

    if b"\n" not in data:
        raise ConnectionError("Socket closed before header was fully received")

    line, remainder = bytes(data).split(b"\n", 1)
    return line.decode("utf-8").strip(), remainder


def upload(file_path):
    filename = os.path.basename(file_path)
    filesize = os.path.getsize(file_path)

    s = socket.socket()
    s.connect((SERVER_IP, PORT))
    s.sendall(f"UPLOAD {filename} {filesize}\n".encode("utf-8"))

    with open(file_path, "rb") as f:
        sent = 0
        while chunk := f.read(BUFFER_SIZE):
            s.sendall(chunk)
            sent += len(chunk)
            print(f"Uploading: {round(sent/filesize*100,2)}%")

    status, _ = recv_line(s)
    if not status.startswith("OK"):
        print(f"Upload failed: {status}")
        s.close()
        return

    s.close()
    print("Upload complete!")


def download(filename):
    s = socket.socket()
    s.connect((SERVER_IP, PORT))

    s.sendall(f"DOWNLOAD {filename}\n".encode("utf-8"))

    response, initial_data = recv_line(s)

    if response.startswith("ERROR"):
        print(f"Download failed: {response}")
        s.close()
        return

    parts = response.split()
    if len(parts) != 2 or parts[0] != "OK":
        print(f"Invalid server response: {response}")
        s.close()
        return

    filesize = int(parts[1])

    with open(filename, "wb") as f:
        received = len(initial_data)
        if initial_data:
            f.write(initial_data)

        while received < filesize:
            data = s.recv(BUFFER_SIZE)
            if not data:
                break
            f.write(data)
            received += len(data)
            print(f"Downloading: {round(received/filesize*100,2)}%")

    s.close()
    print("Download complete!")


# Example usage
# upload("example.txt")
# download("example.txt")