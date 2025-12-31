"""Application entrypoint.

- Creates the Flask app via app.create_app()
- Supports HOST/PORT/FLASK_RUN_PORT and DEBUG/FLASK_DEBUG env overrides
- Exposes `app` for WSGI servers (gunicorn/uwsgi)
"""

import os

from app import create_app


def _str_to_bool(value: str) -> bool:
	return str(value).lower() in {"1", "true", "t", "yes", "y", "on"}


app = create_app()


if __name__ == "__main__":
	host = os.getenv("HOST", "0.0.0.0")
	port = int(os.getenv("PORT", os.getenv("FLASK_RUN_PORT", 5000)))
	debug = True  # 强制启用调试模式

	app.run(host=host, port=port, debug=debug)
