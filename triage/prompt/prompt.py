import ast
import nltk
from nltk.tokenize import word_tokenize
import os
import random
from triage.staging import BasicStaging
nltk.download("punkt")


def failed_gating_prompt():
    return "Inform the user that the prompt has been rejected due to language."


def failed_annotation_verification_prompt(error):
    return f"Inform the user that the prompt failed annotation verification. \n{error}"


class Prompt:

    @staticmethod
    def load_folder(directory_path, n=15, staging=None):
        if not os.path.isdir(directory_path):
            raise ValueError("Directory path is invalid")

        dirlist = os.listdir(directory_path)
        output = []
        for file in sorted(dirlist, key=lambda x: os.path.getmtime(os.path.join(directory_path, x)))[:n]:
            if not file.endswith(".txt"):
                continue
            filepath = os.path.join(directory_path, file)
            try:
                prompt = Prompt.load(filepath, staging)
                output.append(prompt)
            except ValueError as exc:
                print(filepath + " error:", exc)
        return output

    @staticmethod
    def load(filepath, staging=None):
        if not os.path.isfile(filepath):
            raise ValueError("File path is invalid")

        try:
            with open(filepath, "r") as f:
                d = ast.literal_eval(f.read())
        except (SyntaxError, ValueError):
            raise ValueError("File does not contain valid prompt data")

        if not isinstance(d, dict) or "u_id" not in d or "prompt" not in d:
            raise ValueError("File does not contain valid prompt data")

        if staging is not None and isinstance(staging, type):
            d["staging_procedure"] = staging
        return Prompt(**d)

    def __init__(self, u_id, prompt, **kwargs):
        self.u_id = str(u_id)
        self.prompt = prompt
        self.stages = {
            'gating': kwargs.get("gating", None),
            'annotation_verification': kwargs.get("annotation_verification", None),
            'layering': kwargs.get("layering", None),
            'vaccination': kwargs.get("vaccination", None)
        }
        self.overhead = kwargs.get("overhead", None)
        self.staging_procedure = kwargs.get("staging_procedure", BasicStaging)
        self.final_prompt = kwargs.get("final_prompt", None)
        self.triage = dict()
        self.triage["u_id"] = u_id
        self.triage["prompt"] = prompt
        self.triage.update(kwargs)

    def __getitem__(self, item):
        return self.triage[item]

    def __str__(self):
        return self.prompt

    def __repr__(self):
        return str(self.triage)

    def stage(self):
        cls = self.staging_procedure()
        processed_prompt = self.prompt

        gating_result = cls.gating(processed_prompt)
        self.stages["gating"] = gating_result
        if gating_result.lower().startswith("blocked"):
            self.stages["annotation_verification"] = "Cancelled"
            self.stages["layering"] = "Cancelled"
            self.stages["vaccination"] = "Cancelled"
            self.final_prompt = failed_gating_prompt()

        else:
            for s in ["[]", "{}", "<>"]:
                test = cls.annotation_verification(processed_prompt, s)
                if test.lower().startswith("error"):
                    break
            self.stages["annotation_verification"] = test
            if test.lower().startswith("error:"):
                self.stages["layering"] = "Cancelled"
                self.stages["vaccination"] = "Cancelled"
                self.final_prompt = failed_annotation_verification_prompt(self.stages["annotation_verification"])
            else:
                processed_prompt, result = cls.layering(processed_prompt)
                self.stages["layering"] = result
                processed_prompt, result = cls.vaccination(processed_prompt)
                self.stages["vaccination"] = result
                self.final_prompt = processed_prompt

        self.generate_triage_report()

    def generate_triage_report(self):
        overhead = len(word_tokenize(self.final_prompt)) - len(word_tokenize(self.prompt))
        report = {
            'u_id': self.u_id,
            'prompt': self.prompt,
            'risk_score': sum([1 for stage in self.stages.values() if not stage]) + int(overhead > 75) + random.randint(1, 10),
            'overhead': overhead,
            'gating': self.stages['gating'],
            'annotation_verification': self.stages['annotation_verification'],
            'layering': self.stages['layering'],
            'vaccination': self.stages['vaccination'],
            'final_prompt': self.final_prompt
        }
        self.triage = report

    def save(self, filepath):
        with open(filepath, "w+") as f:
            f.write(repr(self))
