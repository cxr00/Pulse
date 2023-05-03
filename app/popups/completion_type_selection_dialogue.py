import tkinter as tk

class CompletionTypeSelectionDialogue(tk.Toplevel):

    def __init__(self, master, completion_action, chat_completion_action):
        tk.Toplevel.__init__(self, master)

        self.title("Select completion type")

        self.completion_button = tk.Button(self, text="Completion", command=completion_action)
        self.completion_button.grid(row=0, column=0, padx=20, pady=20)

        self.chat_completion_button = tk.Button(self, text="Chat Completion", command=chat_completion_action)
        self.chat_completion_button.grid(row=0, column=1, padx=20, pady=20)
