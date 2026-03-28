import subprocess
import time
import sys

def run_app():
    print("🚀 Starting FileFlow System...")
    
    # Start Socket Server
    server_process = subprocess.Popen([sys.executable, "server.py"])
    print("✅ Socket Server started on port 5001")
    
    # Give the server a moment to start
    time.sleep(1)
    
    # Start Flask Web App
    try:
        print("✅ Flask Web App starting on http://127.0.0.1:5000")
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        server_process.terminate()

if __name__ == "__main__":
    run_app()
