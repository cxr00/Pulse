from flask import Flask, request, jsonify
from prompt import Prompt

app = Flask(__name__)
host = "127.0.0.1"
port = 3553
local_dir = "local"
save = True

# Data storage
prompts = {prompt["prompt_id"]: prompt for prompt in Prompt.load_folder(local_dir)}
CURRENT_PROMPT_ID = max([-1] + [int(prompt["prompt_id"]) for prompt in prompts.values()]) + 1
users = list(set([prompt.triage["u_id"] for prompt_id, prompt in prompts.items()]))

# GET endpoints
@app.route('/prompts')
def get_prompts():
    return jsonify([prompt.triage for prompt in prompts.values()])

@app.route('/prompts/<prompt_id>')
def get_prompt(prompt_id):
    prompt = prompts.get(prompt_id)
    if prompt:
        prompt = {key: value for key, value in prompt.triage.items() if key in request.args}
        return jsonify(prompt)
    else:
        return jsonify({'error': 'Prompt not found'}), 404

@app.route('/prompts/users/<user_id>')
def get_users_prompts(user_id):
    if user_id == "all":
        return jsonify([prompt.triage for prompt in prompts.values()])
    elif user_id in users:
        output_prompts = [prompt.triage for prompt in prompts.values() if prompt["u_id"] == user_id]
        return jsonify(output_prompts)
    else:
        return jsonify({"error": "User id not found"}), 404

@app.route('/prompts/overhead/<prompt_id>')
def get_overheads(prompt_id):
    prompt = prompts.get(prompt_id)
    if prompt:
        prompt = {key: value for key, value in prompt.triage.items() if "overhead" in key}
        return jsonify(prompt)
    else:
        return jsonify({'error': 'Prompt not found'}), 404

@app.route('/prompts/params/<prompt_id>')
def get_params(prompt_id):
    prompt = prompts.get(prompt_id).triage["model_parameters"]
    if prompt:
        return jsonify(prompt)
    else:
        return jsonify({'error': 'Prompt not found'}), 404

# POST endpoints
@app.route('/prompts', methods=['POST'])
def stage_prompt():
    global CURRENT_PROMPT_ID
    prompt_data = request.json
    prompt_id = str(CURRENT_PROMPT_ID)
    CURRENT_PROMPT_ID += 1
    prompt_data['prompt_id'] = prompt_id
    to_add = Prompt(**prompt_data)
    to_add.stage(save=save)
    prompts[prompt_id] = to_add
    if to_add.u_id not in users:
        users.append(to_add.u_id)
    return jsonify(to_add.triage)


# DELETE endpoints
@app.route('/prompts/<prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    if prompt_id in prompts:
        prompts[prompt_id].delete()
        del prompts[prompt_id]
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Prompt not found'}), 404
