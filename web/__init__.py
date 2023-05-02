from web.flask_api import app, host, port

pulse_api_url = f"http://{host}:{port}/prompts"
pulse_user_api_url = f"{pulse_api_url}/users/"
