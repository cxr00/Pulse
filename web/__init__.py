from web.flask_api import app, host, port

pulse_api_url = f"http://{host}:{port}/prompts"
pulse_user_api_url = f"{pulse_api_url}/users/"
pulse_risk_api_url = f"{pulse_api_url}/risk/"
pulse_overhead_api_url = f"{pulse_api_url}/overhead/"
pulse_model_params_api_url = f"{pulse_api_url}/params/"
