import ast
import json

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from tkinter import ttk, messagebox

from app import PromptViewer, AnalyticsTab, AddPromptDialogue
from triage.prompt import Prompt
from triage.staging import models


class PromptTrackerApp:
    def __init__(self, prompts):
        self.prompts = prompts
        self.current_prompts = prompts

        self.window = tk.Tk()
        self.window.config(padx=5, pady=5)
        self.window.title("Pulse by Complexor")
        self.window.iconbitmap("icon.ico")

        self.popup_window = None

        # Listbox containing recent prompts
        self.prompt_listbox = tk.Listbox(self.window, height=10, width=50)
        self.prompt_listbox.grid(row=1, column=0, columnspan=2)
        self.prompt_listbox.bind("<<ListboxSelect>>", self.on_prompt_select)
        self.prompt_listbox.bind("<Double-Button-1>", self.prompt_popup)
        self.scrollbar = tk.Scrollbar(self.window)
        self.scrollbar.grid(row=1, column=2)
        self.prompt_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.prompt_listbox.yview)

        # Add prompt button + window components
        self.add_prompt_button = tk.Button(self.window, text="Add Prompt", command=self.add_prompt)
        self.add_prompt_button.grid(row=0, column=0)

        self.add_prompt_window = None
        self.add_prompt_label = None
        self.add_prompt_text = None

        self.model_selection_label = None
        self.model_dropdown_var = None
        self.model_selection_dropdown = None

        self.suffix_label = None
        self.suffix_static_entry = None

        self.max_tokens_label = None
        self.max_tokens_validated_entry = None

        self.temperature_label = None
        self.temperature_entry = None

        self.top_p_label = None
        self.top_p_entry = None

        self.n_label = None
        self.n_static_entry = None

        self.presence_penalty_label = None
        self.presence_penalty_entry = None

        self.frequency_penalty_label = None
        self.frequency_penalty_entry = None

        self.best_of_label = None
        self.best_of_validated_entry = None

        self.logit_bias_label = None
        self.logit_bias_text = None

        self.confirm_add_prompt_button = None
        self.cancel_add_prompt_button = None

        # Delete prompt button
        self.delete_prompt_button = tk.Button(self.window, text="Delete Prompt", command=self.delete_prompt)
        self.delete_prompt_button.grid(row=0, column=1)

        # Select u_id dropdown menu
        self.u_id_list = ["all"] + sorted(list(set([prompt.u_id for prompt in self.prompts])))
        self.dropdown_var = tk.StringVar()
        self.u_id_dropdown_menu = tk.OptionMenu(self.window, self.dropdown_var, *self.u_id_list)
        self.u_id_dropdown_menu.grid(row=0, column=2)
        self.dropdown_var.set("all")
        self.dropdown_var.trace("w", self.filter)

        # Triage report section
        self.triage_report_frame = tk.Frame(self.window, borderwidth=2, relief="groove")
        self.triage_report_text_frame = tk.Frame(self.window, borderwidth=2, relief="groove", width=10)

        self.u_id_label = tk.Label(self.triage_report_frame, text="u_id:", anchor="w")
        self.u_id_label.grid(row=1, column=0)
        self.overhead_label = tk.Label(self.triage_report_frame, text="Overhead:", anchor="w")
        self.overhead_label.grid(row=2, column=0)
        self.risk_score_label = tk.Label(self.triage_report_frame, text="Risk score:", anchor="w")
        self.risk_score_label.grid(row=3, column=0)
        self.gating_label = tk.Label(self.triage_report_frame, text="Gating:", anchor="w")
        self.gating_label.grid(row=4, column=0)
        self.annotation_verification_label = tk.Label(self.triage_report_frame, text="Annotation Verification:", anchor="w")
        self.annotation_verification_label.grid(row=5, column=0)
        self.layering_label = tk.Label(self.triage_report_frame, text="Layering:", anchor="w")
        self.layering_label.grid(row=6, column=0)
        self.vaccination_label = tk.Label(self.triage_report_frame, text="Vaccination:", anchor="w")
        self.vaccination_label.grid(row=7, column=0)

        self.u_id_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.u_id_text.grid(row=1, column=0, pady=1)
        self.overhead_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.overhead_text.grid(row=2, column=0, pady=1)
        self.risk_score_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.risk_score_text.config(bg="#f0f0f0", highlightthickness=0, borderwidth=0)
        self.risk_score_text.grid(row=3, column=0, pady=1)
        self.gating_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.gating_text.grid(row=4, column=0, pady=1)
        self.annotation_verification_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.annotation_verification_text.grid(row=5, column=0, pady=1)
        self.layering_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.layering_text.grid(row=6, column=0, pady=1)
        self.vaccination_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.vaccination_text.grid(row=7, column=0, pady=1)

        self.triage_report_frame.grid(row=1, column=3, columnspan=5, sticky="n")
        self.triage_report_text_frame.grid(row=1, column=8, columnspan=5, sticky="n")

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

        self.window.protocol("WM_DELETE_WINDOW", lambda: toggle_running())
        while running:
            self.window.update()

    def add_prompt(self):
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
            self.add_prompt_window.destroy()

        self.add_prompt_window and self.add_prompt_window.destroy()

        self.add_prompt_window = AddPromptDialogue(self.window, action=invoke_add_prompt)

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
        self.popup_window and self.popup_window.destroy()
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.popup_window = PromptViewer(self.window, self.current_prompts[index])

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
        self.analytics_tab = AnalyticsTab(self.window, option_var, selection, current_prompts, current_overhead_counts, current_risk_score_counts)

    def set_prompt_info(self, prompt):
        """
        Uses the currently-selected prompt to set the triage overview component.
        """
        def get_bg(score):
            return "green" if score < 3 else "white" if score < 5 else "dark orange" if score < 8 else "red"

        def get_fg(score):
            return "white" if score < 3 else "black" if score < 5 else "white"

        def get_status_bg(status):
            return "green" if status in ("Pass", "Complete") else "red"

        def set_component(component, value, set_colors=True):
            component.config(state="normal")
            component.delete(0, tk.END)
            component.insert(0, value)
            component.config(state="disabled")
            if set_colors:
                component.config(disabledbackground=get_status_bg(value), disabledforeground="white")

        set_component(self.u_id_text, prompt.u_id, False)
        set_component(self.overhead_text, prompt["overhead"], False)

        score = prompt["risk_score"]
        self.risk_score_text.config(state="normal")
        self.risk_score_text.delete(0, tk.END)
        self.risk_score_text.insert(0, score)
        self.risk_score_text.config(state="disabled", disabledbackground=get_bg(score), disabledforeground=get_fg(score))

        set_component(self.gating_text, prompt["gating"])
        set_component(self.annotation_verification_text, prompt["annotation_verification"].split(":")[0][:9])
        set_component(self.layering_text, prompt["layering"])
        set_component(self.vaccination_text, prompt["vaccination"])

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


if __name__ == '__main__':
    app = PromptTrackerApp(Prompt.load_folder("local"))
    app.run()
