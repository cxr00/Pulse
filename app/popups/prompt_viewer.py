import ast
import json
import tkinter as tk


class PromptViewer(tk.Toplevel):
    """
    A PromptViewer displays information about a prompt as it moves
    through each stage, as well as the dictionary containing the
    full triage report.
    """
    def __init__(self, master, prompt, clone_action):
        tk.Toplevel.__init__(self, master=master)
        width = 50
        self.iconbitmap("img/icon.ico")
        self.title(str(prompt))
        self.config(padx=10, pady=10)
        self.clone_action = clone_action
        self.prompt = prompt
        tk.Label(self, text=f"Prompt:\n{prompt['prompt_tokens']} tokens").grid(row=0, column=0)
        text = tk.Text(self, height=5, width=width)
        text.insert("1.0", prompt["prompt"])
        text.grid(row=0, column=1)
        text.config(state="disabled")
        if prompt["gating"].lower() == "blocked":
            tk.Label(self, text="Gating error:").grid(row=1, column=0)
            text = tk.Text(self, height=1, width=width)
            text.insert("1.0", "Gating step blocked prompt")
            text.grid(row=1, column=1)
            text.config(state="disabled")
        elif prompt["annotation_verification"].lower().startswith("error"):
            tk.Label(self, text="Annotation verification error:").grid(row=1, column=0)
            text = tk.Text(self, height=2, width=width)
            text.insert("1.0", prompt["annotation_verification"])
            text.grid(row=1, column=1)
            text.config(state="disabled")
        elif prompt["layering_output"]:
            tk.Label(self, text=f"Post-layering:\n+{prompt['layering_overhead']} tokens").grid(row=1, column=0)
            text = tk.Text(self, height=5, width=width)
            text.insert("1.0", prompt["layering_output"])
            text.grid(row=1, column=1)
            text.config(state="disabled")
            if prompt["vaccinated_prompt"]:
                tk.Label(self, text=f"Vaccinated:\n+{prompt['layering_to_vaccinated_overhead']} tokens").grid(row=2, column=0)
                text = tk.Text(self, height=5, width=width)
                text.insert("1.0", prompt["vaccinated_prompt"])
                text.grid(row=2, column=1)
                text.config(state="disabled")
                tk.Label(self, text=f"Output:").grid(row=3, column=0)
                text = tk.Text(self, height=5, width=width)
                if prompt["completion_type"] == "chat.completion":
                    text.insert("1.0", prompt["output"]["choices"][0]["message"]["content"])
                else:
                    text.insert("1.0", prompt["output"]["choices"][0]["text"])
                text.grid(row=3, column=1)
                text.config(state="disabled")
        tk.Label(self, text=f"Full triage report:").grid(row=4, column=0)
        self.triage_text = tk.Text(self, height=15, width=width)
        self.triage_text.insert("1.0", json.dumps(prompt.dict(), indent=2))
        self.triage_text.grid(row=4, column=1)
        self.triage_text.config(state="disabled")
        self.clone_button = tk.Button(self, text="Clone prompt", command=self.clone)
        self.clone_button.grid(row=5, column=1)

    def clone(self):
        clone_dict = {
            "prompt": self.prompt["prompt"],
            "output": self.prompt["output"],
            "completion_type": self.prompt["completion_type"],
            "model_parameters": self.prompt["model_parameters"]
        }
        self.clone_action(clone_dict)
        self.destroy()