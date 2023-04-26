import ast
import os

from triage.staging import BasicStaging


class Prompt:

    @staticmethod
    def load_folder(directory_path, n=15):
        dirlist = os.listdir(directory_path)
        output = []
        for file in sorted(dirlist, key=lambda x: os.path.getmtime(os.path.join(directory_path, x)))[:n]:
            output.append(Prompt.load(os.path.join(directory_path, file)))
        return output

    @staticmethod
    def load(filepath):
        with open(filepath, "r") as f:
            d = ast.literal_eval(f.read())
        return Prompt(**d)

    def __init__(self, prompt, **kwargs):
        self.prompt = prompt
        self.stages = {
            'gating': kwargs.get("gating", None),
            'annotation_verification': kwargs.get("annotation_verification", None),
            'layering': kwargs.get("layering", None),
            'vaccination': kwargs.get("vaccination", None)
        }
        self.overhead = kwargs.get("overhead", None)
        self.triage = kwargs

    def __str__(self):
        return self.prompt

    def __repr__(self):
        return str(self.triage)

    def stage(self, cls=BasicStaging):
        cls = cls()
        processed_prompt = self.prompt

        processed_prompt = cls.gating(processed_prompt)
        self.stages["gating"] = processed_prompt

        for s in ["[]", "{}", "<>"]:
            test = cls.annotation_verification(processed_prompt, "[]")
            if test.lower().startswith("error"):
                break
        self.stages["annotation_verification"] = test
        if test.lower().startswith("error:"):
            self.stages["layering"] = "Cancelled"
            self.stages["vaccination"] = "Cancelled"
        else:
            processed_prompt = cls.layering(processed_prompt)
            self.stages["layering"] = processed_prompt
            processed_prompt = cls.vaccination(processed_prompt)
            self.stages["vaccination"] = processed_prompt

        self.generate_triage_report()

    def generate_triage_report(self):
        overhead = len(self.stages['vaccination'].split()) - len(self.prompt.split()) if self.stages["vaccination"] != "Cancelled" else -1
        report = {
            'prompt': self.prompt,
            'overhead': overhead,
            'gating': self.stages['gating'],
            'annotation_verification': self.stages['annotation_verification'],
            'layering': self.stages['layering'],
            'vaccination': self.stages['vaccination'],
            'risk_score': sum([1 for stage in self.stages.values() if not stage]) + int(overhead > 75),
            'report': {
                'risk_level': 'low',
                'reasons': [
                    'Prompt originated from trusted source',
                    'Short and simple prompt',
                    'No previous history of malicious behavior'
                ]
            }
        }
        self.triage = report

    def save(self, filepath):
        with open(filepath, "w+") as f:
            f.write(repr(self))
