import openai
import os
from prompt.staging.staging import Staging
from prompt.staging.basic_staging import BasicStaging

openai.api_key = os.getenv("OPENAI_API_KEY")
