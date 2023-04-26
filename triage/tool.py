import ast

import tkinter as tk
from tkinter import simpledialog

from triage.staging import BasicStaging


class Prompt:

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


class PromptTrackerApp:
    def __init__(self, prompts, stages=None):
        self.prompts = prompts
        self.stages = stages

        self.window = tk.Tk()
        self.window.title("Prompt Triage Tracker")

        self.prompt_listbox = tk.Listbox(self.window, height=20, width=50)
        self.prompt_listbox.grid(row=1, column=0, rowspan=17)
        self.prompt_listbox.bind("<<ListboxSelect>>", self.on_prompt_select)

        self.add_prompt_button = tk.Button(self.window, text="Add Prompt", command=self.add_prompt)
        self.add_prompt_button.grid(row=0, column=0)

        self.scrollbar = tk.Scrollbar(self.window)
        self.scrollbar.grid(row=0, column=1, rowspan=10)

        self.prompt_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.prompt_listbox.yview)

        self.triage_report_label = tk.Label(self.window, width=15)
        self.triage_report_label.config(text="Triage report")
        self.triage_report_label.grid(row=1, column=2)

        self.prompt_text = tk.Entry(self.window, width=50, state="disabled")
        self.prompt_text.grid(row=0, column=3, rowspan=1)

        self.report_reasons_label = tk.Label(self.window, width=15)
        self.report_reasons_label.config(text="Report reasons")
        self.report_reasons_label.grid(row=4, column=2)

        self.stages_text = tk.Text(self.window, height=10, width=50, state="disabled")
        self.stages_text.grid(row=1, column=3, rowspan=3)

        self.triage_report_text = tk.Text(self.window, height=10, width=50, state="disabled")
        self.triage_report_text.grid(row=4, column=3, rowspan=3)

        self.update_button = tk.Button(self.window, text="Update", command=self.update)
        self.update_button.grid(row=9, column=3)

        self.update_prompt_list()
        self.prompt_listbox.selection_set(0)

    def run(self):
        self.window.mainloop()

    def add_prompt(self):
        prompt_text = simpledialog.askstring("Enter prompt", "Enter the prompt which you would like to add:", parent=self.window)
        if prompt_text:
            prompt = Prompt(prompt_text)
            prompt.stage(self.stages)
            self.prompts.append(prompt)
            self.update_prompt_list()
            self.prompt_listbox.selection_set(len(self.prompts)-1)
            self.set_prompt(prompt)
            self.set_prompt_info(prompt)

    def on_prompt_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            prompt = self.prompts[index]
            self.set_prompt(prompt)
            self.set_prompt_info(prompt)

    def set_prompt(self, prompt):
        self.prompt_text.configure(state="normal")
        self.prompt_text.delete(0, tk.END)
        self.prompt_text.insert(tk.END, prompt)
        self.prompt_text.configure(state="disabled")

    def set_prompt_info(self, prompt):
        self.stages_text.configure(state="normal")
        self.stages_text.delete("1.0", tk.END)
        self.stages_text.insert(tk.END, f"Risk score: {prompt.triage['risk_score']}\n")
        self.stages_text.insert(tk.END, "\n".join([f"{stage}: {value}" for stage, value in prompt.stages.items()]))
        self.stages_text.configure(state="disabled")
        self.triage_report_text.configure(state="normal")
        self.triage_report_text.delete("1.0", tk.END)
        self.triage_report_text.insert(tk.END, "\n".join(prompt.triage["report"]["reasons"]))
        self.triage_report_text.configure(state="disabled")

    def update_prompt_list(self):
        self.prompt_listbox.delete(0, tk.END)
        for prompt in self.prompts:
            self.prompt_listbox.insert(tk.END, prompt)

    def update(self):
        selection = self.prompt_listbox.curselection()
        if selection:
            index = selection[0]
            prompt = self.prompts[index]
            prompt.stage()
            self.set_prompt_info(prompt)


if __name__ == '__main__':
    prompt_1 = Prompt("What is the capital of France?")
    prompt_1.stage()
    prompt_2 = Prompt("[/a]What is the capital of Washington?[a]")
    prompt_2.stage()
    prompt_3 = Prompt("[a]Test[b]test[/a]test[/b]")
    prompt_3.stage()

    prompt_2.save("test.txt")
    prompt_2 = Prompt.load("test.txt")
    app = PromptTrackerApp([prompt_1, prompt_2, prompt_3])
    app.run()
