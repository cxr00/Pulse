import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class AnalyticsTab(ttk.Notebook):
    """
    The AnalyticsTab is a tabbed interface containing filtered
    data based on the current prompt set
    """
    def __init__(self, master, option_var, selection, current_prompts, current_overhead_counts, current_risk_score_counts):
        ttk.Notebook.__init__(self, master=master)
        plt.close("all")

        # Refresh current prompts
        l_p = len(current_prompts)

        # Overview
        self.overview_frame = ttk.Frame(self)

        text = f"Gated: {l_p - sum([1 for prompt in current_prompts if not prompt['gating'].lower().startswith('blocked')])}/{l_p}\n\n"
        text += f"Annotations verified: {sum([1 for prompt in current_prompts if prompt['annotation_verification'] == 'Pass'])}/{l_p}\n\n"
        text += f"Total overhead: {sum([prompt['overhead'] for prompt in current_prompts])}\n\n"
        text += f"Total staged: {sum([1 for prompt in current_prompts if prompt['vaccination'] != 'Cancelled'])}"

        self.overview_text = tk.Text(self.overview_frame, height=10, width=35, borderwidth=0, highlightthickness=0)
        self.overview_text.insert("1.0", text)
        self.overview_text.config(state="disabled", bg="#f0f0f0")
        self.overview_text.place(x=0, y=20)

        # Overhead graph
        self.overhead_frame = ttk.Frame(self)
        self.overhead_graph, ax = plt.subplots()
        avg = sum(current_overhead_counts) / max(1, len(current_overhead_counts))
        bar_colors = [
            "green" if coc < avg / 2 else "blue" if coc < avg else "yellow" if coc < avg * 1.5 else "red" for coc in current_overhead_counts
        ]

        ax.bar([i for i in range(1, len(current_prompts)+1)], current_overhead_counts, color=bar_colors)
        ax.set_ylabel("Overhead")
        ax.set_xlabel("Prompt")
        ax.set_title(f"Overhead of last {len(current_prompts)} prompts from {'u_id ' + option_var if option_var != 'all' else 'all users'}")
        self.overhead_graph_figure = FigureCanvasTkAgg(self.overhead_graph, master=self.overhead_frame)
        self.overhead_graph_figure.get_tk_widget().pack(expand=True, fill="both")
        plt.axhline(y=avg, color="black")

        # Risk factor graph
        self.risk_score_frame = ttk.Frame(self)
        self.risk_score_graph, bx = plt.subplots()
        bar_colors = [
            "green" if crsc < 3 else "yellow" if crsc < 5 else "orange" if crsc < 8 else "red" for crsc in current_risk_score_counts
        ]

        bx.bar([i for i in range(1, len(current_prompts)+1)], current_risk_score_counts, color=bar_colors)
        bx.set_ylabel("Risk Score")
        bx.set_xlabel("Prompt")
        bx.set_title(f"Risk score of last {len(current_prompts)} prompts from {'u_id ' + option_var if option_var != 'all' else 'all users'}")
        self.risk_score_graph_figure = FigureCanvasTkAgg(self.risk_score_graph, master=self.risk_score_frame)
        self.risk_score_graph_figure.get_tk_widget().pack(expand=True, fill="both")
        plt.axhline(y=sum(current_risk_score_counts) / max(1, len(current_risk_score_counts)))

        # Add tabs and grid
        self.add(self.overview_frame, text="Overview")
        self.add(self.overhead_frame, text="Overhead")
        self.add(self.risk_score_frame, text="Risk Score")
        self.grid(row=3, column=0, padx=10, columnspan=10)
        self.select(selection)
