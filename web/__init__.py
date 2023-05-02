from web.flask_api import app

host = "127.0.0.1"
port = 3553
pulse_api_url = f"http://{host}:{port}/prompts"
pulse_user_api_url = f"{pulse_api_url}/users/"
