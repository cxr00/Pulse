import datetime
import json

import nltk
from nltk.tokenize import word_tokenize
import random
from prompt import gpt_35_turbo, completion_default_params, per
from prompt.staging import BasicStaging
# nltk.download("punkt")  # It's already downloaded rn


def failed_gating_prompt():
    return "Inform the user that the prompt has been rejected due to language."


def failed_annotation_verification_prompt(error):
    return f"Inform the user that the prompt failed annotation verification. \n{error}"


class Prompt:

    def __init__(self, u_id, prompt_id, completion_type, prompt="", **kwargs):
        # Data variables
        self._data = dict()
        self["u_id"] = str(u_id)
        self["prompt_id"] = str(prompt_id)
        self["prompt"] = prompt
        self["completion_type"] = completion_type
        self["overhead"] = kwargs.get("overhead", None)
        self["vaccinated_prompt"] = kwargs.get("vaccinated_prompt", None)
        self["model_parameters"] = kwargs.get("model_parameters", completion_default_params)
        if completion_type != "chat.completion":
            self["model_parameters"]["prompt"] = prompt
        self["output"] = kwargs.get("output", None)

        # Non-data variables
        if completion_type == "chat.completion":
            self.prompt = kwargs.get("model_parameters", {}).get("messages", [{}])[-1]
            self.prompt = self.prompt.get("content", "")
            self.starting_prompt = self.prompt
        else:
            self.prompt = prompt
            self.starting_prompt = self.prompt

        self.pre_layering = None
        self.post_layering = None
        self.staging_procedure = kwargs.get("staging_procedure", BasicStaging)
        self.rates = kwargs.get("rates", gpt_35_turbo)
        self._data.update(kwargs)

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __str__(self):
        return self.starting_prompt

    def dict(self):
        return self._data

    def calc_cost(self):
        return "{:.5f}".format(1/per * (
            self.rates["prompt"] * (self["layering_input_tokens"] + self["vaccinated_prompt_tokens"]) +
            + self.rates["completion"] * (self["layering_output_tokens"] + self["output_tokens"])
        ))

    def stage(self):
        cls = self.staging_procedure(self["completion_type"], self["model_parameters"])
        processed_prompt = self.starting_prompt

        gating_result = cls.gating(processed_prompt)
        self["gating"] = gating_result
        if gating_result.lower().startswith("blocked"):
            self["annotation_verification"] = "Cancelled"
            self["layering"] = "Cancelled"
            self["vaccination"] = "Cancelled"
            self["vaccinated_prompt"] = failed_gating_prompt()
        else:
            for s in ["[]", "{}", "<>"]:
                test = cls.annotation_verification(processed_prompt, s)
                if test.lower().startswith("error"):
                    break
            self["annotation_verification"] = test
            if test.lower().startswith("error:"):
                self["layering"] = "Cancelled"
                self["vaccination"] = "Cancelled"
                self["vaccinated_prompt"] = failed_annotation_verification_prompt(self["annotation_verification"])
            else:
                pre_processed_prompt, processed_prompt, result = cls.layering(processed_prompt)
                self.pre_layering = pre_processed_prompt
                self["layering"] = result
                self.post_layering = processed_prompt
                processed_prompt, result = cls.vaccination(processed_prompt)
                self["vaccination"] = result
                self["vaccinated_prompt"] = processed_prompt

        if self["completion_type"] == "chat.completion":
            cls.parameters["messages"][-1]["content"] = self["vaccinated_prompt"]
        else:
            cls.parameters["prompt"] = self["vaccinated_prompt"]

        self["output"] = cls.submit()

        self.generate_triage_report()

    def generate_triage_report(self):
        prompt_tokens = len(word_tokenize(self.prompt))
        vaccinated_prompt_tokens = len(word_tokenize(self["vaccinated_prompt"]))
        overhead = vaccinated_prompt_tokens - prompt_tokens

        layering_input_tokens = len(word_tokenize(self.pre_layering))
        layering_output_tokens = len(word_tokenize(self.post_layering))
        layering_overhead = layering_output_tokens - prompt_tokens

        layering_to_vaccinated_overhead = vaccinated_prompt_tokens - layering_output_tokens

        if self["completion_type"] == "chat.completion":
            output_tokens = len(word_tokenize(self["output"]["choices"][0]["message"]["content"]))
        else:
            output_tokens = len(word_tokenize(self["output"]["choices"][0]["text"]))

        new_data = {
            'u_id': self["u_id"],
            'prompt_id': self["prompt_id"],
            'time': datetime.datetime.now(),
            'completion_type': self["completion_type"],
            'prompt': self.starting_prompt,
            'risk_score': random.randint(1, 10),
            'prompt_tokens': prompt_tokens,
            'vaccinated_prompt_tokens': vaccinated_prompt_tokens,
            'overhead': overhead,
            'layering_input_tokens': layering_input_tokens,
            'layering_output': self.post_layering,
            'layering_output_tokens': layering_output_tokens,
            'layering_overhead': layering_overhead,
            'layering_to_vaccinated_overhead': layering_to_vaccinated_overhead,
            'gating': self['gating'],
            'annotation_verification': self['annotation_verification'],
            'layering': self['layering'],
            'vaccination': self['vaccination'],
            'vaccinated_prompt': self["vaccinated_prompt"],
            'output': self["output"],
            'output_tokens': output_tokens,
            "cost": None,
            'model_parameters': self["model_parameters"]
        }
        self._data = new_data
        self._data["cost"] = self.calc_cost()

    def save(self, filepath):
        with open(filepath, "w+") as f:
            json.dump(self._data, f)
