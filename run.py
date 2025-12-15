"""Development server entrypoint - for local development and containers only"""

import os
import sys

from app import create_app

env = os.getenv("FLASK_ENV", "development")

if env == "production":
    print(
        "ERROR: run.py is not intended for production use. "
        "Use Gunicorn or another production WSGI server instead."
    )
    sys.exit(1)

app = create_app(env)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=(env == "development")
    )
