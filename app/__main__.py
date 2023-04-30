import ast
import json

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from tkinter import ttk, messagebox

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
        self.u_id_list = ["all"] + sorted(list(set([prompt.u_id for prompt in self.prompts]))) + ["999"]
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

        self.overview_frame = None
        self.overview_text = None

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

    def run(self):
        running = True

        def toggle_running():
            nonlocal running
            running = False

        self.window.protocol("WM_DELETE_WINDOW", lambda: toggle_running())
        while running:
            self.window.update()

    def add_prompt(self):

        def numeric_validation(value):
            if value.isnumeric():
                return True
            elif value == "":
                return True
            return False

        def confirm_add_prompt():
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
                messagebox.showerror("Empty token limit", "Token limit is empty", parent=self.add_prompt_window)

            try:
                best_of = int(self.best_of_validated_entry.get())
            except ValueError:
                is_valid = False
                messagebox.showerror("Empty best of", "Best of is empty", parent=self.add_prompt_window)

            try:
                temperature = float(self.temperature_entry.get())
                if 0 > temperature or 2.0 < temperature:
                    is_valid = False
                    messagebox.showerror("Invalid temperature", "Temperature must be between 0 and 2.0", parent=self.add_prompt_window)
            except ValueError:
                is_valid = False
                messagebox.showerror("Invalid temperature", "Temperature field is not a valid float", parent=self.add_prompt_window)

            try:
                top_p = float(self.top_p_entry.get())
                if 0 > top_p or 1.0 < top_p:
                    is_valid = False
                    messagebox.showerror("Invalid nucleus sampling parameter", "Nucleus sampling parameter must be between 0 and 1", parent=self.add_prompt_window)
            except ValueError:
                is_valid = False
                messagebox.showerror("Invalid temperature", "Temperature field is not a valid float", parent=self.add_prompt_window)

            try:
                presence_penalty = float(self.presence_penalty_entry.get())
                if -2.0 > presence_penalty or 2.0 < presence_penalty:
                    is_valid = False
                    messagebox.showerror("Invalid presence penalty", "Presence penalty parameter must be between -2.0 and 2.0", parent=self.add_prompt_window)
            except ValueError:
                is_valid = False
                messagebox.showerror("Invalid presence penalty", "Presence penalty field is not a valid float", parent=self.add_prompt_window)

            try:
                frequency_penalty = float(self.frequency_penalty_entry.get())
                if -2.0 > frequency_penalty or 2.0 < frequency_penalty:
                    is_valid = False
                    messagebox.showerror("Invalid frequency penalty", "Frequency penalty parameter must be between -2.0 and 2.0", parent=self.add_prompt_window)
            except ValueError:
                is_valid = False
                messagebox.showerror("Invalid frequency penalty", "Frequency penalty field is not a valid float", parent=self.add_prompt_window)

            try:
                logit_bias = ast.literal_eval(self.logit_bias_text.get("1.0", tk.END))
                if not isinstance(logit_bias, dict):
                    is_valid = False
                    messagebox.showerror("Invalid logit bias", "Logit bias must be dictionary", parent=self.add_prompt_window)
            except (SyntaxError, ValueError):
                is_valid = False
                messagebox.showerror("Invalid logit bias", "Logit bias is malformed", parent=self.add_prompt_window)

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
                    messagebox.showerror("Max token limit", f"{max_tokens} is above max token limit of 4096", parent=self.add_prompt_window)
                elif best_of < 1:
                    is_valid = False
                    messagebox.showerror("Invalid best of", "Best of parameter must be 1 or greater.", parent=self.add_prompt_window)

            if is_valid:
                d = dict()
                d["u_id"] = "999"  # Test u_id
                d["prompt"] = add_prompt_text
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

                new_prompt = Prompt(**d)
                new_prompt.stage()
                self.prompts.append(new_prompt)
                if self.dropdown_var.get() == u_id:
                    self.current_prompts.append(new_prompt)

                self.overhead_counts.append(new_prompt["overhead"])
                self.risk_score_counts.append(new_prompt["risk_score"])

                self.refresh_stats()
                self.update_prompt_list()
                self.prompt_listbox.selection_set(len(self.current_prompts) - 1)
                self.set_prompt_info(new_prompt)
                self.add_prompt_window.destroy()
            else:
                self.add_prompt_window.focus_set()

        u_id = "999"  # Test u_id

        text_height = 7
        text_width = 45

        self.add_prompt_window and self.add_prompt_window.destroy()
        self.add_prompt_window = tk.Toplevel(self.window)
        self.add_prompt_window.iconbitmap("icon.ico")

        self.add_prompt_label = tk.Label(self.add_prompt_window, text="Prompt:")
        self.add_prompt_label.grid(row=0, column=0)
        self.add_prompt_text = tk.Text(self.add_prompt_window, height=text_height, width=text_width)
        self.add_prompt_text.grid(row=0, column=1, columnspan=2)

        self.model_selection_label = tk.Label(self.add_prompt_window, text="Model:")
        self.model_selection_label.grid(row=1, column=0)
        self.model_dropdown_var = tk.StringVar()
        self.model_selection_dropdown = tk.OptionMenu(self.add_prompt_window, self.model_dropdown_var, *models)
        self.model_dropdown_var.set("gpt-3.5-turbo")
        self.model_selection_dropdown.grid(row=1, column=1, columnspan=2)

        self.suffix_label = tk.Label(self.add_prompt_window, text="Suffix:")
        self.suffix_label.grid(row=2, column=0)
        self.suffix_static_entry = tk.Entry(self.add_prompt_window)
        self.suffix_static_entry.insert(0, "[/]")
        self.suffix_static_entry.config(state="readonly")
        self.suffix_static_entry.grid(row=2, column=1, columnspan=2)

        self.max_tokens_label = tk.Label(self.add_prompt_window, text="Max tokens:")
        self.max_tokens_label.grid(row=3, column=0)
        self.max_tokens_validated_entry = tk.Entry(self.add_prompt_window, validate="key", validatecommand=(self.add_prompt_window.register(numeric_validation), "%P"))
        self.max_tokens_validated_entry.grid(row=3, column=1, columnspan=2)
        self.max_tokens_validated_entry.insert(0, "16")

        self.temperature_label = tk.Label(self.add_prompt_window, text="Sampling temperature:")
        self.temperature_label.grid(row=4, column=0)
        self.temperature_entry = tk.Entry(self.add_prompt_window)
        self.temperature_entry.grid(row=4, column=1, columnspan=2)
        self.temperature_entry.insert(0, "1")

        self.top_p_label = tk.Label(self.add_prompt_window, text="Nucleus sampling:")
        self.top_p_label.grid(row=5, column=0)
        self.top_p_entry = tk.Entry(self.add_prompt_window)
        self.top_p_entry.grid(row=5, column=1, columnspan=2)
        self.top_p_entry.insert(0, "1")

        self.n_label = tk.Label(self.add_prompt_window, text="Number of completions (N):")
        self.n_label.grid(row=6, column=0)
        self.n_static_entry = tk.Entry(self.add_prompt_window)
        self.n_static_entry.insert(0, "1")
        self.n_static_entry.config(state="readonly")
        self.n_static_entry.grid(row=6, column=1, columnspan=2)

        self.presence_penalty_label = tk.Label(self.add_prompt_window, text="Presence penalty (-2.0 to 2.0):")
        self.presence_penalty_label.grid(row=7, column=0)
        self.presence_penalty_entry = tk.Entry(self.add_prompt_window)
        self.presence_penalty_entry.grid(row=7, column=1, columnspan=2)
        self.presence_penalty_entry.insert(0, "0")

        self.frequency_penalty_label = tk.Label(self.add_prompt_window, text="Frequency penalty (-2.0 to 2.0):")
        self.frequency_penalty_label.grid(row=8, column=0)
        self.frequency_penalty_entry = tk.Entry(self.add_prompt_window)
        self.frequency_penalty_entry.grid(row=8, column=1, columnspan=2)
        self.frequency_penalty_entry.insert(0, "0")

        self.best_of_label = tk.Label(self.add_prompt_window, text="Best of N:\n(must be greater than N)")
        self.best_of_label.grid(row=9, column=0)
        self.best_of_validated_entry = tk.Entry(self.add_prompt_window, validate="key", validatecommand=(self.add_prompt_window.register(numeric_validation), "%P"))
        self.best_of_validated_entry.grid(row=9, column=1, columnspan=2)
        self.best_of_validated_entry.insert(0, "1")

        self.logit_bias_label = tk.Label(self.add_prompt_window, text="Logit bias")
        self.logit_bias_label.grid(row=10, column=0)
        self.logit_bias_text = tk.Text(self.add_prompt_window, height=text_height, width=text_width)
        self.logit_bias_text.grid(row=10, column=1, columnspan=2)
        self.logit_bias_text.insert("1.0", "{}")

        self.confirm_add_prompt_button = tk.Button(self.add_prompt_window, text="Add Prompt", command=confirm_add_prompt)
        self.confirm_add_prompt_button.grid(row=11, column=1)
        self.cancel_add_prompt_button = tk.Button(self.add_prompt_window, text="Cancel", command=self.add_prompt_window.destroy)
        self.cancel_add_prompt_button.grid(row=11, column=2)

        self.add_prompt_window.iconbitmap("icon.ico")
        self.add_prompt_window.title("Add prompt")
        self.add_prompt_window.config(padx=10, pady=10)

    def delete_prompt(self):
        selection = self.prompt_listbox.curselection()
        if selection:
            index = selection[0]
            self.prompts.pop(index)
            self.overhead_counts.pop(index)
            self.risk_score_counts.pop(index)
            self.refresh_stats()
            self.update_prompt_list()

    def filter(self, *args):
        self.refresh_stats()
        self.update_prompt_list()

    def on_prompt_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            prompt = self.current_prompts[index]
            self.set_prompt_info(prompt)

    def prompt_popup(self, event):
        selection = event.widget.curselection()
        width = 50
        if selection:
            index = selection[0]
            prompt = self.current_prompts[index]
            self.popup_window and self.popup_window.destroy()
            self.popup_window = tk.Toplevel(self.window)
            self.popup_window.iconbitmap("icon.ico")
            self.popup_window.title(str(prompt))
            self.popup_window.config(padx=10, pady=10)
            tk.Label(self.popup_window, text=f"Prompt:\n{prompt['prompt_tokens']} tokens").grid(row=0, column=0)
            text = tk.Text(self.popup_window, height=5, width=width)
            text.insert("1.0", str(prompt))
            text.grid(row=0, column=1)
            text.config(state="disabled")
            if prompt["gating"].lower() == "blocked":
                tk.Label(self.popup_window, text="Gating error:").grid(row=1, column=0)
                text = tk.Text(self.popup_window, height=1, width=width)
                text.insert("1.0", "Gating step blocked prompt")
                text.grid(row=1, column=1)
                text.config(state="disabled")
            elif prompt["annotation_verification"].lower().startswith("error"):
                tk.Label(self.popup_window, text="Annotation verification error:").grid(row=1, column=0)
                text = tk.Text(self.popup_window, height=2, width=width)
                text.insert("1.0", prompt["annotation_verification"])
                text.grid(row=1, column=1)
                text.config(state="disabled")
            elif prompt.post_layering:
                tk.Label(self.popup_window, text=f"Post-layering:\n+{prompt['layering_overhead']} tokens").grid(row=1, column=0)
                text = tk.Text(self.popup_window, height=5, width=width)
                text.insert("1.0", prompt.post_layering)
                text.grid(row=1, column=1)
                text.config(state="disabled")
                if prompt.vaccinated:
                    tk.Label(self.popup_window, text=f"Vaccinated:\n+{prompt['layering_to_vaccinated_overhead']} tokens").grid(row=2, column=0)
                    text = tk.Text(self.popup_window, height=5, width=width)
                    text.insert("1.0", prompt.vaccinated)
                    text.grid(row=2, column=1)
                    text.config(state="disabled")
                    tk.Label(self.popup_window, text=f"Output:").grid(row=3, column=0)
                    text = tk.Text(self.popup_window, height=5, width=width)
                    text.insert("1.0", prompt["output"])
                    text.grid(row=3, column=1)
                    text.config(state="disabled")
            tk.Label(self.popup_window, text=f"Full triage report:").grid(row=4, column=0)
            text = tk.Text(self.popup_window, height=15, width=width)
            text.insert("1.0", json.dumps(prompt.triage, indent=2))
            text.grid(row=4, column=1)
            text.config(state="disabled")

    def refresh_prompt(self):
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
        option_var = self.dropdown_var.get()
        plt.close("all")

        # Save previously-selected tab
        selection = self.analytics_tab.index("current") if self.analytics_tab else 0

        # Analytics tabs
        self.analytics_tab = ttk.Notebook(self.window)

        # Refresh current prompts
        self.current_prompts = [prompt for prompt in self.prompts if prompt.u_id == option_var or option_var == "all"]
        l_p = len(self.current_prompts)

        # Overview
        self.overview_frame = ttk.Frame(self.analytics_tab)

        text = f"Gated: {l_p - sum([1 for prompt in self.current_prompts if not prompt['gating'].lower().startswith('blocked')])}/{l_p}\n\n"
        text += f"Annotations verified: {sum([1 for prompt in self.current_prompts if prompt['annotation_verification'] == 'Pass'])}/{l_p}\n\n"
        text += f"Total overhead: {sum([prompt['overhead'] for prompt in self.current_prompts])}\n\n"
        text += f"Total staged: {sum([1 for prompt in self.current_prompts if prompt['vaccination'] != 'Cancelled'])}"

        self.overview_text = tk.Text(self.overview_frame, height=10, width=35, borderwidth=0, highlightthickness=0)
        self.overview_text.insert("1.0", text)
        self.overview_text.config(state="disabled", bg="#f0f0f0")
        self.overview_text.place(x=0, y=20)

        # Overhead graph
        self.overhead_frame = ttk.Frame(self.analytics_tab)
        self.overhead_graph, ax = plt.subplots()
        self.current_overhead_counts = [count for i, count in enumerate(self.overhead_counts) if self.prompts[i].u_id == option_var or option_var == "all"]
        avg = sum(self.current_overhead_counts) / max(1, len(self.current_overhead_counts))
        bar_colors = [
            "green" if coc < avg / 2 else "blue" if coc < avg else "yellow" if coc < avg * 1.5 else "red" for coc in self.current_overhead_counts
        ]

        ax.bar([i for i in range(1, len(self.current_prompts)+1)], self.current_overhead_counts, color=bar_colors)
        ax.set_ylabel("Overhead")
        ax.set_xlabel("Prompt")
        ax.set_title(f"Overhead of last {len(self.current_prompts)} prompts from {'u_id ' + option_var if option_var != 'all' else 'all users'}")
        self.overhead_graph_figure = FigureCanvasTkAgg(self.overhead_graph, master=self.overhead_frame)
        self.overhead_graph_figure.get_tk_widget().pack(expand=True, fill="both")
        plt.axhline(y=avg, color="black")

        # Risk factor graph
        self.risk_score_frame = ttk.Frame(self.analytics_tab)
        self.risk_score_graph, bx = plt.subplots()
        self.current_risk_score_counts = [count for i, count in enumerate(self.risk_score_counts) if self.prompts[i].u_id == option_var or option_var == "all"]
        bar_colors = [
            "green" if crsc < 3 else "yellow" if crsc < 5 else "orange" if crsc < 8 else "red" for crsc in self.current_risk_score_counts
        ]

        bx.bar([i for i in range(1, len(self.current_prompts)+1)], self.current_risk_score_counts, color=bar_colors)
        bx.set_ylabel("Risk Score")
        bx.set_xlabel("Prompt")
        bx.set_title(f"Risk score of last {len(self.current_prompts)} prompts from {'u_id ' + option_var if option_var != 'all' else 'all users'}")
        self.risk_score_graph_figure = FigureCanvasTkAgg(self.risk_score_graph, master=self.risk_score_frame)
        self.risk_score_graph_figure.get_tk_widget().pack(expand=True, fill="both")
        plt.axhline(y=sum(self.current_risk_score_counts) / max(1, len(self.current_risk_score_counts)))

        # Add tabs and grid
        self.analytics_tab.add(self.overview_frame, text="Overview")
        self.analytics_tab.add(self.overhead_frame, text="Overhead")
        self.analytics_tab.add(self.risk_score_frame, text="Risk Score")
        self.analytics_tab.grid(row=3, column=0, padx=10, columnspan=10)
        self.analytics_tab.select(selection)

    def set_prompt_info(self, prompt):
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
