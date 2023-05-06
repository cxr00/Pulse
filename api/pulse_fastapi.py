from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from starlette.responses import JSONResponse

from api.prompt import Prompt

db_url = "sqlite:///./pulse.db"
engine = create_engine(db_url)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PromptModel(Base):
    __tablename__ = 'prompts'
    prompt_id = Column(Integer, primary_key=True)
    u_id = Column(String(50), nullable=False)
    completion_type = Column(String(32), nullable=False)
    time = Column(DateTime, nullable=False)
    prompt = Column(String(8192), nullable=False)
    risk_score = Column(Integer, nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    vaccinated_prompt_tokens = Column(Integer, nullable=False)
    overhead = Column(Integer, nullable=False)
    layering_input_tokens = Column(Integer, nullable=False)
    layering_overhead = Column(Integer, nullable=False)
    layering_to_vaccinated_overhead = Column(Integer, nullable=False)
    gating = Column(String(255), nullable=False)
    annotation_verification = Column(String(255), nullable=False)
    layering = Column(String(255), nullable=False)
    layering_output = Column(String(8192), nullable=False)
    layering_output_tokens = Column(Integer, nullable=False)
    vaccination = Column(String(255), nullable=False)
    vaccinated_prompt = Column(String(8192), nullable=False)
    output = Column(JSON, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    model_parameters = Column(JSON, nullable=False)

    def as_dict(self):
        return {
            'u_id': self.u_id,
            'prompt_id': self.prompt_id,
            "completion_type": self.completion_type,
            'time': self.time,
            'prompt': self.prompt,
            'risk_score': self.risk_score,
            'prompt_tokens': self.prompt_tokens,
            'vaccinated_prompt_tokens': self.vaccinated_prompt_tokens,
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
            'vaccinated_prompt': self.vaccinated_prompt,
            'output': self.output,
            'output_tokens': self.output_tokens,
            "cost": self.cost,
            'model_parameters': self.model_parameters
        }


Base.metadata.create_all(bind=engine)
app = FastAPI()

db = session()
prompts = db.query(PromptModel).all()
db.close()

CURRENT_PROMPT_ID = max([-1] + [prompt.prompt_id for prompt in prompts]) + 1
users = list(set([prompt.u_id for prompt in prompts]))


@app.get("/prompts")
def get_prompts():
    return {"prompts": [prompt.as_dict() for prompt in prompts]}


@app.get("/prompts/{prompt_id}")
def get_prompt(prompt_id):
    db = session()
    prompt = db.query(PromptModel).filter(PromptModel.prompt_id == prompt_id)
    db.close()
    return {"prompt": prompt.as_dict()}


@app.get("/prompts/users/{user_id}")
def get_users_prompts(user_id):
    if user_id == "all":
        return {"prompts": [prompt.as_dict() for prompt in prompts]}
    elif user_id in users:
        output_prompts = [prompt.as_dict() for prompt in prompts if prompt.u_id == user_id]
        return {"prompts": output_prompts}
    else:
        return {"error": "User id not found"}, 404


@app.post("/prompts")
def stage_prompt(prompt: dict):
    global CURRENT_PROMPT_ID, prompts
    new_prompt = Prompt(prompt_id=CURRENT_PROMPT_ID, **prompt)
    CURRENT_PROMPT_ID += 1
    new_prompt.stage()
    if new_prompt["u_id"] not in users:
        users.append(new_prompt["u_id"])
    sess = session()
    sess.add(PromptModel(**new_prompt.dict()))
    sess.commit()
    prompts = sess.query(PromptModel).all()
    sess.close()
    return new_prompt.dict()


@app.delete('/prompts/{prompt_id}')
def delete_prompt(prompt_id):
    global prompts
    sess = session()
    sess.query(PromptModel).filter(PromptModel.prompt_id == int(prompt_id)).delete()
    sess.commit()
    prompts = sess.query(PromptModel).all()
    sess.close()
    return {'success': True}, 200
