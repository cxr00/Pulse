import tkinter as tk
from tkinter import messagebox


class CreateLogitBiasDialogue(tk.Toplevel):
    """
    The CreateLogitBiasDialogue provides a validated interface
    for the creation of logit bias dictionaries for API calls
    """

    @staticmethod
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

    def __init__(self, master, action, previous_logit_bias):
        tk.Toplevel.__init__(self, master)
        self.action = action
        self.logit_bias = previous_logit_bias
        self.iconbitmap("icon.ico")
        self.title("Create logit bias")
        self.config(padx=10, pady=10)

        self.size = 0

        self.token_label = tk.Label(self, text="Token")
        self.token_label.grid(row=0, column=2)

        self.token_bias_value_label = tk.Label(self, text="Bias (between -100 and 100)")
        self.token_bias_value_label.grid(row=0, column=3)

        self.add_field_button = tk.Button(self, text="Add field", command=self.add_entry)
        self.remove_field_button = tk.Button(self, text="Remove field", command=self.remove_entry)
        self.create_button = tk.Button(self, text="Create logit bias", command=self.create_logit_bias)
        self.cancel_button = tk.Button(self, text="Cancel", command=self.destroy)

        self.token_number_labels = []
        self.token_entries = []
        self.token_bias_entries = []

        # Create initial entry loc
        self.reconstruct_from_previous_logit_bias()
        self.add_entry()

    def add_entry(self, key="", value=""):
        """
        Add a new entry with optional key and value
        """
        self.size += 1
        new_token_number_label = tk.Label(self, text=str(self.size))
        new_token_entry = tk.Entry(self, validate="key", validatecommand=(self.register(CreateLogitBiasDialogue.numeric_validation), "%P"))
        new_token_entry.insert(0, key)
        new_token_bias_entry = tk.Entry(self)
        new_token_bias_entry.insert(0, value)
        new_token_number_label.grid(row=self.size, column=1)
        new_token_entry.grid(row=self.size, column=2)
        new_token_bias_entry.grid(row=self.size, column=3)
        self.add_field_button.grid(row=self.size+1, column=0)
        self.remove_field_button.grid(row=self.size+1, column=1)
        self.create_button.grid(row=self.size+1, column=2)
        self.cancel_button.grid(row=self.size+1, column=3)

        self.token_number_labels.append(new_token_number_label)
        self.token_entries.append(new_token_entry)
        self.token_bias_entries.append(new_token_bias_entry)

    def remove_entry(self):
        """
        Remove the entry fields at the end
        """
        if self.size > 1:
            self.size -= 1
            self.token_number_labels.pop(-1).destroy()
            self.token_entries.pop(-1).destroy()
            self.token_bias_entries.pop(-1).destroy()

    def reconstruct_from_previous_logit_bias(self):
        for key, value in self.logit_bias.items():
            self.add_entry(key, value)

    def create_logit_bias(self):
        """
        Validates and returns a logit bias to the AddPromptDialogue
        """
        for i, entry in enumerate(self.token_entries):
            try:
                v = int(entry.get())
            except ValueError:
                messagebox.showerror("Invalid token value", f"Empty token value for entry {i+1}", parent=self)
                self.focus_set()
                break
        else:
            for i, entry in enumerate(self.token_bias_entries):
                try:
                    v = int(entry.get())
                    if v > 100 or v < -100:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Invalid bias value", f"Invalid bias value for entry {i+1}", parent=self)
                    self.focus_set()
                    break
            else:
                for key, value in zip(self.token_entries, self.token_bias_entries):
                    self.logit_bias[int(key.get())] = int(value.get())
                self.action(self.logit_bias)
