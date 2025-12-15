import os

from app import create_app

env = os.getenv("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=(env == "development")
    )
