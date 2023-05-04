import requests
import tkinter as tk
from tkinter import messagebox

from app import PromptViewer, AnalyticsTab, CompletionTypeSelectionDialogue, AddChatCompletionPromptDialogue, AddCompletionPromptDialogue, TriagePanel
from prompt import Prompt
from web import pulse_api_url, pulse_user_api_url


class Pulse(tk.Tk):
    """
    Pulse is an application developed by Complexor which integrates
    prompt security into testing, monitoring, and profiling prompts created
    by users of an application.
    """
    def __init__(self, master=None, prompts=None):
        tk.Tk.__init__(self, master)
        self.prompts = prompts or []

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
        self.scrollbar.grid(row=1, column=2, sticky="nsw")
        self.prompt_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.prompt_listbox.yview)

        # Add prompt button + dialogue component
        self.add_prompt_button = tk.Button(self, text="Add Prompt", command=self.add_prompt)
        self.add_prompt_button.grid(row=0, column=0)
        self.completion_type_selection_dialogue = None
        self.add_completion_prompt_dialogue = None
        self.add_chat_completion_prompt_dialogue = None

        # Delete prompt button
        self.delete_prompt_button = tk.Button(self, text="Delete Prompt", command=self.delete_prompt)
        self.delete_prompt_button.grid(row=0, column=1)

        # Select u_id dropdown menu
        self.u_id_list = ["all"] + sorted(list(set([prompt.u_id for prompt in self.prompts])))
        self.dropdown_var = tk.StringVar()
        self.u_id_dropdown_menu = None
        self.dropdown_var.set("all")
        self.dropdown_var.trace("w", self.update_displayed_prompts)

        # Triage panel
        self.triage_panel = TriagePanel(self)

        # Analytics tabs
        self.analytics_tab = None

        # Initialise
        self.update_displayed_prompts()

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
        Creates and displays an AddCompletionPromptDialogue, which
        allows users to customise an API call for a new prompt.
        """
        def invoke_add_prompt(new_prompt_data):
            self.add_completion_prompt_dialogue and self.add_completion_prompt_dialogue.destroy()
            self.add_chat_completion_prompt_dialogue and self.add_chat_completion_prompt_dialogue.destroy()
            new_prompt_data = requests.post(pulse_api_url, json=new_prompt_data)
            new_prompt = Prompt(**new_prompt_data.json())
            self.update_displayed_prompts()
            self.prompt_listbox.selection_set(len(self.prompts) - 1)
            self.set_prompt_info(new_prompt)

        def create_completion_prompt_dialogue():
            self.completion_type_selection_dialogue and self.completion_type_selection_dialogue.destroy()
            self.add_completion_prompt_dialogue = AddCompletionPromptDialogue(self, action=invoke_add_prompt, prompt=prompt)

        def create_chat_completion_prompt_dialogue():
            self.completion_type_selection_dialogue and self.completion_type_selection_dialogue.destroy()
            self.add_chat_completion_prompt_dialogue = AddChatCompletionPromptDialogue(self, action=invoke_add_prompt, prompt=prompt)

        if prompt is None:
            prompt = {}
            self.completion_type_selection_dialogue and self.completion_type_selection_dialogue.destroy()
            self.add_completion_prompt_dialogue and self.add_completion_prompt_dialogue.destroy()
            self.add_chat_completion_prompt_dialogue and self.add_chat_completion_prompt_dialogue.destroy()

            self.completion_type_selection_dialogue = CompletionTypeSelectionDialogue(self, create_completion_prompt_dialogue, create_chat_completion_prompt_dialogue)
        else:
            if prompt["completion_type"] == "chat.completion":
                create_chat_completion_prompt_dialogue()
            else:
                create_completion_prompt_dialogue()


    def delete_prompt(self):
        """
        Delete a prompt from the app and from local storage
        """
        selection = self.prompt_listbox.curselection()
        if selection:
            index = selection[0]
            if messagebox.askokcancel("Confirm deletion", f"Are you sure you want to delete the prompt?\n{str(self.prompts[index])}"):
                to_delete = self.prompts[index].prompt_id
                requests.delete("/".join([pulse_api_url, to_delete]))
                self.update_displayed_prompts()

    def update_displayed_prompts(self, *args):
        """
        Update the currently-displayed prompts by u_id
        """
        self.refresh_stats()
        self.update_prompt_listbox()
        selection = self.prompt_listbox.curselection()
        if selection:
            index = selection[0]
            self.set_prompt_info(self.prompts[index])
        else:
            self.clear_prompt_info()

    def on_prompt_select(self, event):
        """
        Update the currently-displayed prompt staging summary
        """
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            prompt = self.prompts[index]
            self.set_prompt_info(prompt)

    def prompt_popup(self, event):
        """
        Create and display a PromptViewer
        """
        self.prompt_viewer_popup and self.prompt_viewer_popup.destroy()
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.prompt_viewer_popup = PromptViewer(self, self.prompts[index], self.add_prompt)

    def refresh_stats(self):
        """
        Updates the analytics tab
        """
        option_var = self.dropdown_var.get()
        self.prompts = [Prompt(**data) for data in requests.get(pulse_user_api_url + option_var).json()]
        self.u_id_list = ["all"] + list(set([prompt.u_id for prompt in self.prompts]))
        self.u_id_dropdown_menu = tk.OptionMenu(self, self.dropdown_var, *self.u_id_list)
        self.u_id_dropdown_menu.grid(row=0, column=2)

        if self.analytics_tab:
            selection = int(self.analytics_tab.index("current"))
        else:
            selection = 0
        self.analytics_tab = AnalyticsTab(self, option_var, selection, self.prompts)

    def clear_prompt_info(self):
        self.triage_panel.clear_prompt_info()

    def set_prompt_info(self, prompt):
        """
        Update the TriagePanel's information
        """
        self.triage_panel.set_prompt_info(prompt)

    def update_prompt_listbox(self):
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
        for i, prompt in enumerate(self.prompts):
            self.prompt_listbox.insert(tk.END, prompt)
            self.prompt_listbox.itemconfig(i, select_bg_and_fg(self.prompts[i]["risk_score"]))
