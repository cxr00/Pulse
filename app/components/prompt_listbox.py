import tkinter as tk

class PromptListbox(tk.Listbox):
    def __init__(self, master, on_select, on_double_click, scrollbar):
        tk.Listbox.__init__(self, master, height=10, width=50)

        self.bind("<<ListboxSelect>>", on_select)
        self.bind("<Double-Button-1>", on_double_click)
        self.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.yview)

    def update_prompts(self, prompts):
        """
        Fills the prompt listbox based on currently-selected u_id
        """
        def select_bg_and_fg(risk_score):
            if risk_score < 3:
                return {"bg": "Green", "fg": "White"}
            elif risk_score < 5:
                return {}
            elif risk_score < 8:
                return {"bg": "Dark Orange", "fg": "White"}
            return {"bg": "Red", "fg": "White"}

        self.delete(0, tk.END)
        for i, prompt in enumerate(prompts):
            self.insert(tk.END, prompt["prompt"])
            self.itemconfig(i, select_bg_and_fg(prompts[i]["risk_score"]))