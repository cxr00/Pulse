from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from prompt import Prompt

app = Flask(__name__)
host = "127.0.0.1"
port = 3553
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pulse.db"
db = SQLAlchemy(app)

class PromptModel(db.Model):
    __tablename__ = 'prompts'
    prompt_id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.String(50), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    prompt = db.Column(db.String(8192), nullable=False)
    risk_score = db.Column(db.Integer, nullable=False)
    prompt_tokens = db.Column(db.Integer, nullable=False)
    vaccinated_tokens = db.Column(db.Integer, nullable=False)
    overhead = db.Column(db.Integer, nullable=False)
    layering_input_tokens = db.Column(db.Integer, nullable=False)
    layering_overhead = db.Column(db.Integer, nullable=False)
    layering_to_vaccinated_overhead = db.Column(db.Integer, nullable=False)
    gating = db.Column(db.String(255), nullable=False)
    annotation_verification = db.Column(db.String(255), nullable=False)
    layering = db.Column(db.String(255), nullable=False)
    layering_output = db.Column(db.String(8192), nullable=False)
    layering_output_tokens = db.Column(db.Integer, nullable=False)
    vaccination = db.Column(db.String(255), nullable=False)
    vaccinated = db.Column(db.String(8192), nullable=False)
    output = db.Column(db.String(32768), nullable=False)
    output_tokens = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    model_parameters = db.Column(db.JSON, nullable=False)

    def as_dict(self):
        return {
            'u_id': self.u_id,
            'prompt_id': self.prompt_id,
            'time': self.time,
            'prompt': self.prompt,
            'risk_score': self.risk_score,
            'prompt_tokens': self.prompt_tokens,
            'vaccinated_tokens': self.vaccinated_tokens,
            'overhead': self.overhead,
            'layering_input_tokens': self.layering_input_tokens,
            'layering_overhead': self.layering_overhead,
            'layering_to_vaccinated_overhead': self.layering_to_vaccinated_overhead,
            'gating': self.gating,
            'annotation_verification': self.annotation_verification,
            'layering': self.layering,
            'layering_output': self.layering_output,
            'layering_output_tokens': self.layering_output_tokens,
            'vaccination': self.vaccination,
            'vaccinated': self.vaccinated,
            'output': self.output,
            'output_tokens': self.output_tokens,
            "cost": self.cost,
            'model_parameters': self.model_parameters
        }

with app.app_context():
    db.create_all()
    prompts = PromptModel.query.with_for_update().all()

CURRENT_PROMPT_ID = max([-1] + [prompt.prompt_id for prompt in prompts]) + 1
users = list(set([prompt.u_id for prompt in prompts]))

# GET endpoints
@app.route('/prompts')
def get_prompts():
    return jsonify([prompt.as_dict() for prompt in prompts])

@app.route('/prompts/<prompt_id>')
def get_prompt(prompt_id):
    prompt = PromptModel.query.filter(PromptModel.prompt_id == prompt_id).all()
    if prompt:
        return jsonify(prompt[0].as_dict())
    else:
        return jsonify({'error': 'Prompt not found'}), 404

@app.route('/prompts/users/<user_id>')
def get_users_prompts(user_id):
    if user_id == "all":
        return jsonify([prompt.as_dict() for prompt in prompts])
    elif user_id in users:
        output_prompts = [prompt.as_dict() for prompt in prompts if prompt.u_id == user_id]
        return jsonify(output_prompts)
    else:
        return jsonify({"error": "User id not found"}), 404

# POST endpoints
@app.route('/prompts', methods=['POST'])
def stage_prompt():
    global CURRENT_PROMPT_ID, prompts
    prompt = Prompt(prompt_id=CURRENT_PROMPT_ID, **request.json)
    CURRENT_PROMPT_ID += 1
    prompt.stage()
    new_prompt = PromptModel(**prompt.triage)
    if new_prompt.u_id not in users:
        users.append(new_prompt.u_id)
    db.session.add(new_prompt)
    db.session.commit()
    prompts = PromptModel.query.all()
    return jsonify(prompt.triage)

# DELETE endpoints
@app.route('/prompts/<prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    global prompts
    db.session.query(PromptModel).filter(PromptModel.prompt_id == int(prompt_id)).delete()
    db.session.commit()
    prompts = PromptModel.query.all()
    return jsonify({'success': True})
