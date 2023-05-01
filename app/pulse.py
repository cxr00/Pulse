import tkinter as tk
from tkinter import messagebox

from app import PromptViewer, AnalyticsTab, AddPromptDialogue, TriagePanel
from triage.prompt import Prompt


class Pulse(tk.Tk):
    """
    Pulse is an application developed by Complexor which integrates
    prompt security into testing, monitoring, and profiling prompts created
    by users of an application.
    """
    def __init__(self, master=None, prompts=None):
        tk.Tk.__init__(self, master)
        self.prompts = prompts or []
        self.current_prompts = prompts or []

        self.config(padx=5, pady=5)
        self.title("Pulse - PromptOps by Complexor")
        self.iconbitmap("icon.ico")

        # PromptViewer toplevel
        self.prompt_viewer_popup = None

        # Listbox containing recent prompts
        self.prompt_listbox = tk.Listbox(self, height=10, width=50)
        self.prompt_listbox.grid(row=1, column=0, columnspan=2)
        self.prompt_listbox.bind("<<ListboxSelect>>", self.on_prompt_select)
        self.prompt_listbox.bind("<Double-Button-1>", self.prompt_popup)
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.grid(row=1, column=2)
        self.prompt_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.prompt_listbox.yview)

        # Add prompt button + dialogue component
        self.add_prompt_button = tk.Button(self, text="Add Prompt", command=self.add_prompt)
        self.add_prompt_button.grid(row=0, column=0)
        self.add_prompt_dialogue = None

        # Delete prompt button
        self.delete_prompt_button = tk.Button(self, text="Delete Prompt", command=self.delete_prompt)
        self.delete_prompt_button.grid(row=0, column=1)

        # Select u_id dropdown menu
        self.u_id_list = ["all"] + sorted(list(set([prompt.u_id for prompt in self.prompts])))
        self.dropdown_var = tk.StringVar()
        self.u_id_dropdown_menu = tk.OptionMenu(self, self.dropdown_var, *self.u_id_list)
        self.u_id_dropdown_menu.grid(row=0, column=2)
        self.dropdown_var.set("all")
        self.dropdown_var.trace("w", self.filter)

        # Triage panel
        self.triage_panel = TriagePanel(self)

        # Analytics tabs
        self.analytics_tab = None
        self.overhead_counts = [prompt["overhead"] for prompt in self.prompts]
        self.risk_score_counts = [prompt["risk_score"] for prompt in self.prompts]

        self.refresh_stats()
        self.update_prompt_list()

    def run(self):
        """
        Properly closeable main loop
        """
        running = True

        def toggle_running():
            nonlocal running
            running = False

        self.protocol("WM_DELETE_WINDOW", lambda: toggle_running())
        while running:
            self.update()

    def add_prompt(self, prompt=None):
        """
        Creates and displays an AddPromptDialogue, which
        allows users to customise an API call for a new prompt.
        """
        def invoke_add_prompt(new_prompt):
            self.prompts.append(new_prompt)
            self.overhead_counts.append(new_prompt["overhead"])
            self.risk_score_counts.append(new_prompt["risk_score"])

            self.refresh_stats()
            self.update_prompt_list()
            self.prompt_listbox.selection_set(len(self.current_prompts) - 1)
            self.set_prompt_info(new_prompt)
            self.add_prompt_dialogue.destroy()

        if prompt is None:
            prompt = {}
        self.add_prompt_dialogue and self.add_prompt_dialogue.destroy()

        self.add_prompt_dialogue = AddPromptDialogue(self, action=invoke_add_prompt, prompt=prompt)

    def delete_prompt(self):
        """
        Delete a prompt from the app and from local storage
        """
        selection = self.prompt_listbox.curselection()
        if selection:
            index = selection[0]
            if messagebox.askokcancel("Confirm deletion", f"Are you sure you want to delete the prompt?\n{str(self.current_prompts[index])}"):
                actual_index = self.prompts.index(self.current_prompts[index])
                to_delete = self.prompts.pop(actual_index)
                self.overhead_counts.pop(actual_index)
                self.risk_score_counts.pop(actual_index)
                to_delete.delete()
                self.refresh_stats()
                self.update_prompt_list()

    def filter(self, *args):
        """
        Update the currently-displayed prompts by u_id
        """
        self.refresh_stats()
        self.update_prompt_list()

    def on_prompt_select(self, event):
        """
        Update the currently-displayed prompt staging summary
        """
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            prompt = self.current_prompts[index]
            self.set_prompt_info(prompt)

    def prompt_popup(self, event):
        """
        Create and display a PromptViewer
        """
        self.prompt_viewer_popup and self.prompt_viewer_popup.destroy()
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.prompt_viewer_popup = PromptViewer(self, self.current_prompts[index], self.add_prompt)

    def refresh_prompt(self):
        """
        Unused method for cloning an existing prompt
        """
        selection = self.prompt_listbox.curselection()
        if selection:
            index = selection[0]
            d = self.current_prompts[index].triage
            u_id = "999"
            if "u_id" in d:
                del d["u_id"]
            prompt = Prompt(u_id, **d)
            prompt.stage()
            self.set_prompt_info(prompt)
            self.prompts.append(prompt)
            self.overhead_counts.append(prompt["overhead"])
            self.risk_score_counts.append(prompt["risk_score"])
            self.refresh_stats()
            self.update_prompt_list()
            self.prompt_listbox.selection_set(len(self.current_prompts)-1)

    def refresh_stats(self):
        """
        Updates the analytics tab
        """
        option_var = self.dropdown_var.get()
        current_prompts = [prompt for prompt in self.prompts if prompt.u_id == option_var or option_var == "all"]
        current_overhead_counts = [count for i, count in enumerate(self.overhead_counts) if self.prompts[i].u_id == option_var or option_var == "all"]
        current_risk_score_counts = [count for i, count in enumerate(self.risk_score_counts) if self.prompts[i].u_id == option_var or option_var == "all"]
        if self.analytics_tab:
            selection = int(self.analytics_tab.index("current"))
        else:
            selection = 0
        self.analytics_tab = AnalyticsTab(self, option_var, selection, current_prompts, current_overhead_counts, current_risk_score_counts)

    def set_prompt_info(self, prompt):
        """
        Update the TriagePanel's information
        """
        self.triage_panel.set_prompt_info(prompt)

    def update_prompt_list(self):
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

        self.prompt_listbox.delete(0, tk.END)
        for i, prompt in enumerate(self.current_prompts):
            self.prompt_listbox.insert(tk.END, prompt)
            self.prompt_listbox.itemconfig(i, select_bg_and_fg(self.current_prompts[i]["risk_score"]))
