import tkinter as tk


def get_bg(score):
    return "green" if score < 3 else "white" if score < 5 else "dark orange" if score < 8 else "red"


def get_fg(score):
    return "white" if score < 3 else "black" if score < 5 else "white"


def get_status_bg(status):
    return "green" if status in ("Pass", "Complete") else "red"


class TriagePanel:
    """
    The TriagePanel contains two Frames which display a summary
    of triage data for a given prompt
    """
    def __init__(self, master):

        self.triage_report_frame = tk.Frame(master, borderwidth=2, relief="groove")
        self.triage_report_text_frame = tk.Frame(master, borderwidth=2, relief="groove", width=10)

        self.prompt_id_label = tk.Label(self.triage_report_frame, text="prompt_id:", anchor="w")
        self.prompt_id_label.grid(row=1, column=0)
        self.u_id_label = tk.Label(self.triage_report_frame, text="u_id:", anchor="w")
        self.u_id_label.grid(row=2, column=0)
        self.overhead_label = tk.Label(self.triage_report_frame, text="Overhead:", anchor="w")
        self.overhead_label.grid(row=3, column=0)
        self.risk_score_label = tk.Label(self.triage_report_frame, text="Risk score:", anchor="w")
        self.risk_score_label.grid(row=4, column=0)
        self.gating_label = tk.Label(self.triage_report_frame, text="Gating:", anchor="w")
        self.gating_label.grid(row=5, column=0)
        self.annotation_verification_label = tk.Label(self.triage_report_frame, text="Annotation Verification:", anchor="w")
        self.annotation_verification_label.grid(row=6, column=0)
        self.layering_label = tk.Label(self.triage_report_frame, text="Layering:", anchor="w")
        self.layering_label.grid(row=7, column=0)
        self.vaccination_label = tk.Label(self.triage_report_frame, text="Vaccination:", anchor="w")
        self.vaccination_label.grid(row=8, column=0)

        self.prompt_id_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.prompt_id_text.grid(row=1, column=0, pady=1)
        self.u_id_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.u_id_text.grid(row=2, column=0, pady=1)
        self.overhead_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.overhead_text.grid(row=3, column=0, pady=1)
        self.risk_score_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.risk_score_text.config(bg="#f0f0f0", highlightthickness=0, borderwidth=0)
        self.risk_score_text.grid(row=4, column=0, pady=1)
        self.gating_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.gating_text.grid(row=5, column=0, pady=1)
        self.annotation_verification_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.annotation_verification_text.grid(row=6, column=0, pady=1)
        self.layering_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.layering_text.grid(row=7, column=0, pady=1)
        self.vaccination_text = tk.Entry(self.triage_report_text_frame, state="disabled")
        self.vaccination_text.grid(row=8, column=0, pady=1)

        self.triage_report_frame.grid(row=1, column=3, columnspan=5, sticky="n")
        self.triage_report_text_frame.grid(row=1, column=8, columnspan=5, sticky="n")

    def set_prompt_info(self, prompt):
        """
        Sets the text values based on the given prompt
        """

        def set_component(component, value, set_colors=True):
            component.config(state="normal")
            component.delete(0, tk.END)
            component.insert(0, value)
            component.config(state="disabled")
            if set_colors:
                component.config(disabledbackground=get_status_bg(value), disabledforeground="white")

        set_component(self.prompt_id_text, prompt.prompt_id, False)
        set_component(self.u_id_text, prompt.u_id, False)
        set_component(self.overhead_text, prompt["overhead"], False)

        score = prompt["risk_score"]
        self.risk_score_text.config(state="normal")
        self.risk_score_text.delete(0, tk.END)
        self.risk_score_text.insert(0, score)
        self.risk_score_text.config(state="disabled", disabledbackground=get_bg(score),
                                    disabledforeground=get_fg(score))

        set_component(self.gating_text, prompt["gating"])
        set_component(self.annotation_verification_text, prompt["annotation_verification"].split(":")[0][:9])
        set_component(self.layering_text, prompt["layering"])
        set_component(self.vaccination_text, prompt["vaccination"])
