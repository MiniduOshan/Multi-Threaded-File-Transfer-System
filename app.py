from flask import Flask, render_template, request, jsonify, send_file
import os
import socket
import threading
from io import BytesIO
from werkzeug.utils import secure_filename
import server as socket_server

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
SOCKET_HEADER_MAX = 8192

def list_upload_files():
    """Return only regular files from upload directory in sorted order."""
    try:
        names = os.listdir(UPLOAD_DIR)
    except Exception as e:
        app.logger.error(f"Error listing upload dir: {e}")
        return []

    files = []
    for name in names:
        full_path = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(full_path):
            files.append(name)

    files.sort()
    return files

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} P"

@app.route("/stats")
def stats():
    files = list_upload_files()
    total_size = 0
    for name in files:
        try:
            total_size += os.path.getsize(os.path.join(UPLOAD_DIR, name))
        except OSError as e:
            app.logger.warning(f"Could not read size for {name}: {e}")

    return jsonify({
        "storageUsed": format_size(total_size),
        "numFiles": len(files),
        "status": "Online"
    })

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5001


def recv_line(sock, max_size=SOCKET_HEADER_MAX):
    """Read a newline-terminated UTF-8 header and return (line, remaining_bytes)."""
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


def socket_server_is_running():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        return probe.connect_ex((SERVER_IP, SERVER_PORT)) == 0


def run_socket_server():
    try:
        socket_server.start_server()
    except OSError as e:
        app.logger.error(f"Socket server startup failed: {e}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"message": "Invalid filename"}), 400
    
    file.seek(0, os.SEEK_END)
    filesize = file.tell()
    file.seek(0)

    try:
        with socket.create_connection((SERVER_IP, SERVER_PORT), timeout=5) as s:
            s.sendall(f"UPLOAD {filename} {filesize}\n".encode("utf-8"))

            chunk_size = 8192
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                s.sendall(chunk)

            status_line, _ = recv_line(s)
            if not status_line.startswith("OK"):
                return jsonify({"message": f"Upload failed: {status_line}"}), 500

        return jsonify({"message": f"Successfully uploaded {filename}"})
    except Exception as e:
        return jsonify({"message": f"Upload failed: {str(e)}"}), 500


@app.route("/files")
def files():
    return render_template("partials/file_list.html",
                           files=list_upload_files())


@app.route("/download/<filename>")
def download(filename):
    safe_name = secure_filename(filename)
    if not safe_name:
        return "Invalid filename", 400

    try:
        with socket.create_connection((SERVER_IP, SERVER_PORT), timeout=5) as s:
            s.sendall(f"DOWNLOAD {safe_name}\n".encode("utf-8"))

            header_line, initial_data = recv_line(s)
            if header_line.startswith("ERROR"):
                if "FILE_NOT_FOUND" in header_line:
                    return "File not found", 404
                return f"Download error: {header_line}", 500

            parts = header_line.split()
            if len(parts) != 2 or parts[0] != "OK":
                return f"Invalid server response: {header_line}", 500

            filesize = int(parts[1])
            received = len(initial_data)
            file_data = bytearray(initial_data)

            while received < filesize:
                chunk = s.recv(min(8192, filesize - received))
                if not chunk:
                    break
                file_data.extend(chunk)
                received += len(chunk)

            if received != filesize:
                return "Download interrupted before completion", 500

        return send_file(
            BytesIO(file_data),
            download_name=safe_name,
            as_attachment=True
        )
    except Exception as e:
        return f"Download failed: {str(e)}", 500

@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    safe_name = secure_filename(filename)
    if not safe_name:
        return jsonify({"message": "Invalid filename"}), 400

    filepath = os.path.join(UPLOAD_DIR, safe_name)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return jsonify({"message": f"Deleted {safe_name}"})
        except Exception as e:
            return jsonify({"message": f"Delete failed: {str(e)}"}), 500
    return jsonify({"message": "File not found"}), 404


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    start_embedded_socket = os.environ.get("START_EMBEDDED_SOCKET", "0") == "1"

    # Keep embedded socket startup as an explicit opt-in for local/dev use.
    if start_embedded_socket:
        should_start_socket = (not debug_mode) or (os.environ.get("WERKZEUG_RUN_MAIN") == "true")
        if should_start_socket and not socket_server_is_running():
            threading.Thread(target=run_socket_server, daemon=True).start()

    app.run(host=host, port=port, debug=debug_mode, threaded=True)