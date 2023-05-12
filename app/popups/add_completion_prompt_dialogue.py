import ast
from app.popups import CreateLogitBiasDialogue
import tkinter as tk
from tkinter import messagebox
from api.prompt import completion_models


class AddCompletionPromptDialogue(tk.Toplevel):
    """
    The AddCompletionPromptDialogue provides a validated interface for
    constructing prompts and their API call parameters
    """
    def __init__(self, master, action, prompt):
        tk.Toplevel.__init__(self, master=master)

        self.new_prompt = None
        self.action = action
        self.logit_bias_dialogue = None
        model_params = prompt.get("model_parameters", {})

        def numeric_validation(value):
            """
            Validates that characters entered are numeric
            Used for max_tokens and best_of
            """
            if value.isnumeric():
                return True
            elif value == "":
                return True
            return False

        text_height = 7
        text_width = 45

        self.add_prompt_label = tk.Label(self, text="Prompt:")
        self.add_prompt_label.grid(row=0, column=0)
        self.add_prompt_text = tk.Text(self, height=text_height, width=text_width)
        self.add_prompt_text.insert("1.0", prompt.get("prompt", ""))
        if prompt:
            to_insert = prompt["output"].get("choices", [{}])
            to_insert = to_insert[0].get("text", "")
            self.add_prompt_text.insert(tk.END, to_insert)
        self.add_prompt_text.grid(row=0, column=1, columnspan=4)

        self.model_selection_label = tk.Label(self, text="Model:")
        self.model_selection_label.grid(row=1, column=0)
        self.model_dropdown_var = tk.StringVar()
        self.model_selection_dropdown = tk.OptionMenu(self, self.model_dropdown_var, *completion_models)
        self.model_dropdown_var.set(model_params.get("model", "text-davinci-003"))
        self.model_selection_dropdown.grid(row=1, column=1, columnspan=4)

        self.suffix_label = tk.Label(self, text="Suffix:")
        self.suffix_label.grid(row=2, column=0)
        self.suffix_static_entry = tk.Entry(self)
        self.suffix_static_entry.insert(0, "[/]")
        self.suffix_static_entry.config(state="readonly")
        self.suffix_static_entry.grid(row=2, column=1, columnspan=4)

        self.max_tokens_label = tk.Label(self, text="Max tokens:")
        self.max_tokens_label.grid(row=3, column=0)
        self.max_tokens_validated_entry = tk.Entry(self, validate="key", validatecommand=(self.register(numeric_validation), "%P"))
        self.max_tokens_validated_entry.grid(row=3, column=1, columnspan=4)
        self.max_tokens_validated_entry.insert(0, model_params.get("max_tokens", "64"))

        self.temperature_label = tk.Label(self, text="Sampling temperature:")
        self.temperature_label.grid(row=4, column=0)
        self.temperature_entry = tk.Entry(self)
        self.temperature_entry.grid(row=4, column=1, columnspan=4)
        self.temperature_entry.insert(0, model_params.get("temperature", "1"))

        self.top_p_label = tk.Label(self, text="Nucleus sampling:")
        self.top_p_label.grid(row=5, column=0)
        self.top_p_entry = tk.Entry(self)
        self.top_p_entry.grid(row=5, column=1, columnspan=4)
        self.top_p_entry.insert(0, model_params.get("top_p", "1"))

        self.n_label = tk.Label(self, text="Number of completions (N):")
        self.n_label.grid(row=6, column=0)
        self.n_static_entry = tk.Entry(self)
        self.n_static_entry.insert(0, "1")
        self.n_static_entry.config(state="readonly")
        self.n_static_entry.grid(row=6, column=1, columnspan=4)

        self.presence_penalty_label = tk.Label(self, text="Presence penalty (-2.0 to 2.0):")
        self.presence_penalty_label.grid(row=7, column=0)
        self.presence_penalty_entry = tk.Entry(self)
        self.presence_penalty_entry.grid(row=7, column=1, columnspan=4)
        self.presence_penalty_entry.insert(0, model_params.get("presence_penalty", "0"))

        self.frequency_penalty_label = tk.Label(self, text="Frequency penalty (-2.0 to 2.0):")
        self.frequency_penalty_label.grid(row=8, column=0)
        self.frequency_penalty_entry = tk.Entry(self)
        self.frequency_penalty_entry.grid(row=8, column=1, columnspan=4)
        self.frequency_penalty_entry.insert(0, model_params.get("frequency_penalty", "0"))

        self.best_of_label = tk.Label(self, text="Best of N:\n(must be greater than N)")
        self.best_of_label.grid(row=9, column=0)
        self.best_of_validated_entry = tk.Entry(self, validate="key", validatecommand=(self.register(numeric_validation), "%P"))
        self.best_of_validated_entry.grid(row=9, column=1, columnspan=4)
        self.best_of_validated_entry.insert(0, model_params.get("best_of", "1"))

        self.logit_bias_label = tk.Label(self, text="Logit bias")
        self.logit_bias_label.grid(row=10, column=0)
        self.logit_bias_text = tk.Text(self, height=text_height, width=text_width)
        self.logit_bias_text.grid(row=10, column=1, columnspan=4)
        self.logit_bias_text.insert("1.0", model_params.get("logit_bias", "{}"))
        self.logit_bias_text.config(state="disabled")

        self.confirm_add_prompt_button = tk.Button(self, text="Add Prompt", command=self.confirm_add_prompt)
        self.confirm_add_prompt_button.grid(row=11, column=1)
        self.create_logit_bias_button = tk.Button(self, text="Create logit bias", command=self.create_logit_bias_dialogue)
        self.create_logit_bias_button.grid(row=11, column=2)
        self.clear_logit_bias_button = tk.Button(self, text="Clear logit bias", command=lambda: self.set_logit_bias("{}"))
        self.clear_logit_bias_button.grid(row=11, column=3)
        self.cancel_add_prompt_button = tk.Button(self, text="Cancel", command=self.destroy)
        self.cancel_add_prompt_button.grid(row=11, column=4)

        self.title("Add prompt")
        self.geometry("+100+100")
        self.config(padx=10, pady=10)
        self.iconbitmap("img/icon.ico")
        self.focus_set()

    def confirm_add_prompt(self):
        """
        Verifies that the entered values are valid,
        then creates a prompt and closes the Add Prompt window
        """
        is_valid = True

        # Validate all inputs then create prompt
        max_tokens = None
        best_of = None
        add_prompt_text = self.add_prompt_text.get("1.0", tk.END).strip()
        n = None
        temperature = None
        top_p = None
        presence_penalty = None
        frequency_penalty = None
        logit_bias = None

        try:
            max_tokens = int(self.max_tokens_validated_entry.get())
        except ValueError:
            is_valid = False
            messagebox.showerror("Empty token limit", "Token limit is empty", parent=self)

        try:
            best_of = int(self.best_of_validated_entry.get())
        except ValueError:
            is_valid = False
            messagebox.showerror("Empty best of", "Best of is empty", parent=self)

        try:
            temperature = float(self.temperature_entry.get())
            if 0 > temperature or 2.0 < temperature:
                is_valid = False
                messagebox.showerror("Invalid temperature", "Temperature must be between 0 and 2.0",
                                     parent=self)
        except ValueError:
            is_valid = False
            messagebox.showerror("Invalid temperature", "Temperature field is not a valid float",
                                 parent=self)

        try:
            top_p = float(self.top_p_entry.get())
            if 0 > top_p or 1.0 < top_p:
                is_valid = False
                messagebox.showerror("Invalid nucleus sampling parameter",
                                     "Nucleus sampling parameter must be between 0 and 1",
                                     parent=self)
        except ValueError:
            is_valid = False
            messagebox.showerror("Invalid temperature", "Temperature field is not a valid float",
                                 parent=self)

        try:
            presence_penalty = float(self.presence_penalty_entry.get())
            if -2.0 > presence_penalty or 2.0 < presence_penalty:
                is_valid = False
                messagebox.showerror("Invalid presence penalty",
                                     "Presence penalty parameter must be between -2.0 and 2.0",
                                     parent=self)
        except ValueError:
            is_valid = False
            messagebox.showerror("Invalid presence penalty", "Presence penalty field is not a valid float",
                                 parent=self)

        try:
            frequency_penalty = float(self.frequency_penalty_entry.get())
            if -2.0 > frequency_penalty or 2.0 < frequency_penalty:
                is_valid = False
                messagebox.showerror("Invalid frequency penalty",
                                     "Frequency penalty parameter must be between -2.0 and 2.0",
                                     parent=self)
        except ValueError:
            is_valid = False
            messagebox.showerror("Invalid frequency penalty", "Frequency penalty field is not a valid float",
                                 parent=self)

        try:
            logit_bias = ast.literal_eval(self.logit_bias_text.get("1.0", tk.END))
            if not isinstance(logit_bias, dict):
                is_valid = False
                messagebox.showerror("Invalid logit bias", "Logit bias must be dictionary",
                                     parent=self)
        except (SyntaxError, ValueError):
            is_valid = False
            messagebox.showerror("Invalid logit bias", "Logit bias is malformed", parent=self)

        try:
            n = int(self.n_static_entry.get())
        except ValueError:
            is_valid = False
            messagebox.showerror("Empty N", "Number of completions N is empty")

        if is_valid:
            if add_prompt_text == "":
                is_valid = False
                messagebox.showerror("Empty prompt", "Prompt field is empty")
            elif max_tokens > 4096:
                is_valid = False
                messagebox.showerror("Max token limit", f"{max_tokens} is above max token limit of 4096",
                                     parent=self)
            elif best_of < 1:
                is_valid = False
                messagebox.showerror("Invalid best of", "Best of parameter must be 1 or greater.",
                                     parent=self)

        if is_valid:
            d = dict()
            d["u_id"] = "999"  # Test u_id
            d["prompt"] = add_prompt_text
            d["completion_type"] = "completion"
            model_parameters = {
                "model": self.model_dropdown_var.get(),
                "suffix": self.suffix_static_entry.get(),
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "n": n,
                "stream": False,
                "logprobs": None,
                "echo": False,
                "stop": None,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "best_of": best_of,
                "logit_bias": logit_bias
            }
            d["model_parameters"] = model_parameters

            self.action(d)

    def get_logit_bias(self):
        return ast.literal_eval(self.logit_bias_text.get("1.0", tk.END))

    def set_logit_bias(self, new_logit_bias):
        self.logit_bias_text.config(state="normal")
        self.logit_bias_text.delete("1.0", tk.END)
        self.logit_bias_text.insert("1.0", str(new_logit_bias))
        self.logit_bias_text.config(state="disabled")
        if self.logit_bias_dialogue:
            self.logit_bias_dialogue.destroy()

    def create_logit_bias_dialogue(self):
        self.logit_bias_dialogue and self.logit_bias_dialogue.destroy()
        self.logit_bias_dialogue = CreateLogitBiasDialogue(self, self.set_logit_bias, self.get_logit_bias())
