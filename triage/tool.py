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
        self.overhead_graph_figure = None
        self.risk_score_frame = None
        self.risk_score_graph = None
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
        prompt_text = simpledialog.askstring("Enter prompt", "Enter the prompt which you would like to add:", parent=self.window)
        if prompt_text:
            prompt = Prompt(prompt_text)
            prompt.stage(self.stages)
            self.prompts.append(prompt)
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
        # Analytics tabs
        self.analytics_tab = ttk.Notebook(self.window)

        # Overhead graph
        self.overhead_frame = ttk.Frame(self.analytics_tab)
        self.overhead_graph, ax = plt.subplots()

        # TODO: get rid of random.randint
        counts = [prompt.triage["overhead"] + random.randint(1, 10) for prompt in self.prompts]

        ax.bar([i for i in range(1, len(self.prompts)+1)], counts)
        ax.set_ylabel("Overhead")
        ax.set_xlabel("Prompt")
        ax.set_title(f"Overhead of last {len(self.prompts)} prompts")
        self.overhead_graph_figure = FigureCanvasTkAgg(self.overhead_graph, master=self.overhead_frame)
        self.overhead_graph_figure.get_tk_widget().pack(expand=True, fill="both")
        plt.axhline(y=sum(counts) / max(1, len(counts)))

        # Risk factor graph
        self.risk_score_frame = ttk.Frame(self.analytics_tab)
        self.risk_score_graph, bx = plt.subplots()

        # TODO: get rid of random.randint
        counts = [prompt.triage["risk_score"] + random.randint(10, 25) for prompt in self.prompts]

        bx.bar([i for i in range(1, len(self.prompts)+1)], counts)
        bx.set_ylabel("Risk Score")
        bx.set_xlabel("Prompt")
        bx.set_title(f"Risk score of last {len(self.prompts)} prompts")
        self.risk_score_graph_figure = FigureCanvasTkAgg(self.risk_score_graph, master=self.risk_score_frame)
        self.risk_score_graph_figure.get_tk_widget().pack(expand=True, fill="both")
        plt.axhline(y=sum(counts) / max(1, len(counts)))

        # Add tabs and grid
        self.analytics_tab.add(self.overhead_frame, text="Overhead")
        self.analytics_tab.add(self.risk_score_frame, text="Risk Score")
        self.analytics_tab.grid(row=3, column=4, padx=10)

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
        for prompt in self.prompts:
            self.prompt_listbox.insert(tk.END, prompt)


if __name__ == '__main__':
    prompt_1 = Prompt("What is the capital of France?")
    prompt_1.stage()
    prompt_2 = Prompt("[/a]What is the capital of Washington?[a]")
    prompt_2.stage()
    prompt_3 = Prompt("[a]Test[b]test[/a]test[/b]")
    prompt_3.stage()

    prompt_2.save("test/test.txt")
    prompt_2 = Prompt.load("test/test.txt")
    app = PromptTrackerApp([prompt_1, prompt_2, prompt_3])
    app.run()
