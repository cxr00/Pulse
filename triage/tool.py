import random

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from tkinter import simpledialog, ttk

from triage.prompt import Prompt
from triage.staging import BasicStaging


class PromptTrackerApp:
    def __init__(self, prompts, stages=BasicStaging):
        self.prompts = prompts
        self.current_prompts = prompts
        self.stages = stages

        self.window = tk.Tk()
        self.window.title("Prompt Triage Tracker")

        # Listbox containing recent prompts
        self.prompt_listbox = tk.Listbox(self.window, height=20, width=50)
        self.prompt_listbox.grid(row=2, column=0, rowspan=17)
        self.prompt_listbox.bind("<<ListboxSelect>>", self.on_prompt_select)
        self.scrollbar = tk.Scrollbar(self.window)
        self.scrollbar.grid(row=0, column=1, rowspan=10)
        self.prompt_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.prompt_listbox.yview)

        # Add prompt button
        self.add_prompt_button = tk.Button(self.window, text="Add Prompt", command=self.add_prompt)
        self.add_prompt_button.grid(row=0, column=0)

        # Delete prompt button
        self.delete_prompt_button = tk.Button(self.window, text="Delete Prompt", command=self.delete_prompt)
        self.delete_prompt_button.grid(row=1, column=0)

        # Select u_id dropdown menu
        self.u_id_list = ["all"] + sorted(list(set([prompt.u_id for prompt in self.prompts]))) + ["999"]
        self.dropdown_var = tk.StringVar()
        self.u_id_dropdown_menu = tk.OptionMenu(self.window, self.dropdown_var, *self.u_id_list)
        self.u_id_dropdown_menu.grid(row=2, column=0)
        self.dropdown_var.set("all")
        self.dropdown_var.trace("w", self.filter)

        # Refresh button
        self.refresh_button = tk.Button(self.window, text="Refresh", command=self.refresh_prompt)
        self.refresh_button.grid(row=9, column=3)

        # Triage report section
        self.triage_report_label = tk.Label(self.window, width=15)
        self.triage_report_label.config(text="Triage report")
        self.triage_report_label.grid(row=0, column=3)

        self.prompt_text = tk.Entry(self.window, width=50, state="disabled")
        self.prompt_text.grid(row=1, column=3, rowspan=1)

        self.triage_report_text = tk.Text(self.window, height=20, width=50, state="disabled")
        self.triage_report_text.grid(row=2, column=3, rowspan=3)

        # Analytics tabs
        self.analytics_tab = None
        self.overhead_frame = None
        self.overhead_graph = None
        self.overhead_counts = [prompt["overhead"] for prompt in self.prompts]
        self.current_overhead_counts = self.overhead_counts
        self.overhead_graph_figure = None
        self.risk_score_frame = None
        self.risk_score_graph = None
        self.risk_score_counts = [prompt["risk_score"] for prompt in self.prompts]
        self.current_risk_score_counts = self.risk_score_counts
        self.risk_score_graph_figure = None
        self.refresh_stats()

        self.update_prompt_list()
        self.prompt_listbox.selection_set(0)

    def run(self):
        running = True

        def toggle_running():
            nonlocal running
            running = False

        self.window.protocol("WM_DELETE_WINDOW", lambda: toggle_running())
        while running:
            self.window.update()

    def add_prompt(self):
        u_id = "999"  # Test u_id
        prompt_text = simpledialog.askstring("Enter prompt", "Enter the prompt which you would like to add:", parent=self.window)
        if prompt_text:
            prompt = Prompt(u_id, prompt_text)
            prompt.stage(self.stages)
            self.prompts.append(prompt)
            if self.dropdown_var.get() == u_id:
                self.current_prompts.append(prompt)

            self.overhead_counts.append(prompt["overhead"])
            self.risk_score_counts.append(prompt["risk_score"])

            self.update_prompt_list()
            self.prompt_listbox.selection_set(len(self.prompts)-1)
            self.set_prompt(prompt)
            self.set_prompt_info(prompt)
            self.refresh_stats()

    def delete_prompt(self):
        selection = self.prompt_listbox.curselection()
        if selection:
            index = selection[0]
            self.prompts.pop(index)
            self.overhead_counts.pop(index)
            self.risk_score_counts.pop(index)
            self.update_prompt_list()
            self.refresh_stats()

    def filter(self, *args):
        v = self.dropdown_var.get()
        if v == "all":
            self.current_prompts = self.prompts
        else:
            self.current_prompts = [prompt for prompt in self.prompts if prompt.u_id == v]
        self.update_prompt_list()
        self.refresh_stats()

    def on_prompt_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            prompt = self.prompts[index]
            self.set_prompt(prompt)
            self.set_prompt_info(prompt)

    def refresh_prompt(self):
        selection = self.prompt_listbox.curselection()
        if selection:
            index = selection[0]
            prompt = self.prompts[index]
            prompt.stage()
            self.set_prompt_info(prompt)

    def refresh_stats(self):
        option_var = self.dropdown_var.get()

        # Save previously-selected tab
        selection = self.analytics_tab.index("current") if self.analytics_tab else 0

        # Analytics tabs
        self.analytics_tab = ttk.Notebook(self.window)

        # Overhead graph
        self.overhead_frame = ttk.Frame(self.analytics_tab)
        self.overhead_graph, ax = plt.subplots()
        self.current_overhead_counts = [count for i, count in enumerate(self.overhead_counts) if self.prompts[i].u_id == option_var or option_var == "all"]

        ax.bar([i for i in range(1, len(self.current_prompts)+1)], self.current_overhead_counts)
        ax.set_ylabel("Overhead")
        ax.set_xlabel("Prompt")
        ax.set_title(f"Overhead of last {len(self.current_prompts)} prompts from {'u_id ' + option_var if option_var != 'all' else 'all users'}")
        self.overhead_graph_figure = FigureCanvasTkAgg(self.overhead_graph, master=self.overhead_frame)
        self.overhead_graph_figure.get_tk_widget().pack(expand=True, fill="both")
        plt.axhline(y=sum(self.current_overhead_counts) / max(1, len(self.current_overhead_counts)))

        # Risk factor graph
        self.risk_score_frame = ttk.Frame(self.analytics_tab)
        self.risk_score_graph, bx = plt.subplots()
        self.current_risk_score_counts = [count for i, count in enumerate(self.risk_score_counts) if self.prompts[i].u_id == option_var or option_var == "all"]

        bx.bar([i for i in range(1, len(self.current_prompts)+1)], self.current_risk_score_counts)
        bx.set_ylabel("Risk Score")
        bx.set_xlabel("Prompt")
        bx.set_title(f"Risk score of last {len(self.current_prompts)} prompts from {'u_id ' + option_var if option_var != 'all' else 'all users'}")
        self.risk_score_graph_figure = FigureCanvasTkAgg(self.risk_score_graph, master=self.risk_score_frame)
        self.risk_score_graph_figure.get_tk_widget().pack(expand=True, fill="both")
        plt.axhline(y=sum(self.current_risk_score_counts) / max(1, len(self.current_risk_score_counts)))

        # Add tabs and grid
        self.analytics_tab.add(self.overhead_frame, text="Overhead")
        self.analytics_tab.add(self.risk_score_frame, text="Risk Score")
        self.analytics_tab.grid(row=3, column=4, padx=10)
        self.analytics_tab.select(selection)

    def set_prompt(self, prompt):
        self.prompt_text.configure(state="normal")
        self.prompt_text.delete(0, tk.END)
        self.prompt_text.insert(tk.END, prompt)
        self.prompt_text.configure(state="disabled")

    def set_prompt_info(self, prompt):
        self.triage_report_text.configure(state="normal")
        self.triage_report_text.delete("1.0", tk.END)
        self.triage_report_text.insert(tk.END, "\n\n".join([f"{key}: {value}" for key, value in prompt.triage.items()]))
        self.triage_report_text.configure(state="disabled")

    def update_prompt_list(self):
        self.prompt_listbox.delete(0, tk.END)
        for prompt in self.current_prompts:
            self.prompt_listbox.insert(tk.END, prompt)


if __name__ == '__main__':
    prompt_1 = Prompt(0, "What is the capital of France?")
    prompt_1.stage()
    prompt_2 = Prompt(0, "[/a]What is the capital of Washington?[a]")
    prompt_2.stage()
    prompt_3 = Prompt(1, "[a]Test[b]test[/a]test[/b]")
    prompt_3.stage()

    prompt_2.save("test/test.txt")
    prompt_2 = Prompt.load("test/test.txt")
    app = PromptTrackerApp([prompt_1, prompt_2, prompt_3])
    app.run()
