from dotenv import load_dotenv
import os

from app import create_app


load_dotenv()
PORT = int(os.getenv("PORT")) if os.getenv("PORT", "").isdigit() else 5000
DEBUG = os.getenv("DEBUG", "false").lower() in {"true", "t", "1"}


if __name__ == "__main__":
    app, socketio = create_app()
    socketio.run(app, host="0.0.0.0", port=PORT, debug=DEBUG)