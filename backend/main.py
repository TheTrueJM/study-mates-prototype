from app import create_app, socketio
import os

from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    app = create_app()
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=bool(os.environ.get("DEBUG", False))
    )
