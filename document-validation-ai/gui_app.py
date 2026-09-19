"""
gui_app.py
----------
Desktop GUI application for Document Validation AI.
Allows users to select a document file (.docx, .pdf, .txt), select the expected
document format type, and validate the document against rules and ML model.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from src.extractor import extract_text
from src.validator import load_rules, validate_document
from src.ml_model import DocumentClassifier, MODEL_PATH
from src.report import build_report

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")

DOCUMENT_TYPES = {
    "Safety Standard Report (SSR)": os.path.join(CONFIG_DIR, "ssr_rules.json"),
    "Technical Specification Report": os.path.join(CONFIG_DIR, "tech_spec_rules.json"),
    "Audit & Compliance Report": os.path.join(CONFIG_DIR, "audit_report_rules.json"),
}


class DocumentValidationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Document Validation AI - Desktop Assistant")
        self.geometry("980x720")
        self.minsize(900, 650)

        # Set theme and color palette
        self._configure_theme()
        self._create_widgets()

        # Pre-load or ensure ML model exists
        self.model = None
        self._init_model()

    def _configure_theme(self):
        self.bg_color = "#1E1E2E"
        self.card_bg = "#2B2B3D"
        self.fg_color = "#CDD6F4"
        self.accent_color = "#89B4FA"
        self.success_color = "#A6E3A1"
        self.warning_color = "#F9E2AF"
        self.danger_color = "#F38BA8"
        self.subtext_color = "#BAC2DE"

        self.configure(bg=self.bg_color)

        style = ttk.Style(self)
        style.theme_use("clam")

        # Customize TTK widget styles
        style.configure("TFrame", background=self.bg_color)
        style.configure("Card.TFrame", background=self.card_bg, relief="flat")
        style.configure(
            "TLabel",
            background=self.card_bg,
            foreground=self.fg_color,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Header.TLabel",
            background=self.bg_color,
            foreground=self.fg_color,
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "SubHeader.TLabel",
            background=self.bg_color,
            foreground=self.accent_color,
            font=("Segoe UI", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background=self.card_bg,
            foreground=self.accent_color,
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Badge.TLabel",
            font=("Segoe UI", 14, "bold"),
            anchor="center",
            padding=10,
        )

        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            background=self.accent_color,
            foreground="#11111B",
            borderwidth=0,
            padding=8,
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#B4BEFE"), ("pressed", "#74C7EC")],
        )

        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 9),
            background="#45475A",
            foreground=self.fg_color,
            borderwidth=0,
            padding=6,
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#585B70"), ("pressed", "#313244")],
        )

        style.configure(
            "TCombobox",
            fieldbackground="#313244",
            background="#45475A",
            foreground=self.fg_color,
            arrowcolor=self.fg_color,
            font=("Segoe UI", 10),
        )

    def _init_model(self):
        """Loads existing trained ML model or trains synthetic model if missing."""
        try:
            if os.path.exists(MODEL_PATH):
                self.model = DocumentClassifier.load(MODEL_PATH)
            else:
                from src.ml_model import generate_synthetic_dataset
                texts, labels = generate_synthetic_dataset(200)
                self.model = DocumentClassifier()
                self.model.train(texts, labels)
                self.model.save(MODEL_PATH)
        except Exception as e:
            print(f"Warning initializing model: {e}")

    def _create_widgets(self):
        # Header Container
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_label = ttk.Label(
            header_frame,
            text="Document Format & Compliance Inspector",
            style="Header.TLabel",
        )
        title_label.pack(anchor="w")

        subtitle_label = ttk.Label(
            header_frame,
            text="Verify document structure against standard specifications & AI confidence analysis",
            style="SubHeader.TLabel",
        )
        subtitle_label.pack(anchor="w")

        # Top Control Card (File Selection & Document Type Selection)
        control_card = ttk.Frame(self, style="Card.TFrame", padding=15)
        control_card.pack(fill="x", padx=20, pady=10)

        # File Selection Line
        file_label = ttk.Label(control_card, text="Document File:")
        file_label.grid(row=0, column=0, sticky="w", pady=5, padx=5)

        self.file_entry = ttk.Entry(control_card, font=("Segoe UI", 10))
        self.file_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        browse_btn = ttk.Button(
            control_card,
            text="Browse...",
            style="Secondary.TButton",
            command=self._browse_file,
        )
        browse_btn.grid(row=0, column=2, padx=5, pady=5)

        # Format Type Dropdown Line
        type_label = ttk.Label(control_card, text="Expected Document Format:")
        type_label.grid(row=1, column=0, sticky="w", pady=5, padx=5)

        self.type_combo = ttk.Combobox(
            control_card,
            values=list(DOCUMENT_TYPES.keys()),
            state="readonly",
        )
        self.type_combo.current(0)
        self.type_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        validate_btn = ttk.Button(
            control_card,
            text="🔍 Validate Document",
            style="Primary.TButton",
            command=self._validate_document,
        )
        validate_btn.grid(row=1, column=2, padx=5, pady=5)

        control_card.columnconfigure(1, weight=1)

        # Status & Results Container (Paned Window)
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        # Left Column: Validation Summary & Section Checklist
        left_frame = ttk.Frame(main_paned, style="Card.TFrame", padding=15)
        main_paned.add(left_frame, weight=1)

        # Verdict Badge
        self.verdict_label = tk.Label(
            left_frame,
            text="SELECT A FILE & CLICK VALIDATE",
            bg="#313244",
            fg=self.subtext_color,
            font=("Segoe UI", 12, "bold"),
            pady=10,
        )
        self.verdict_label.pack(fill="x", pady=(0, 10))

        # Metrics Bar Frame
        metrics_frame = ttk.Frame(left_frame, style="Card.TFrame")
        metrics_frame.pack(fill="x", pady=5)

        self.word_count_lbl = ttk.Label(
            metrics_frame, text="Word Count: -"
        )
        self.word_count_lbl.pack(side="left", padx=10)

        self.order_lbl = ttk.Label(
            metrics_frame, text="Section Order: -"
        )
        self.order_lbl.pack(side="left", padx=10)

        self.ml_score_lbl = ttk.Label(
            metrics_frame, text="ML Confidence: -"
        )
        self.ml_score_lbl.pack(side="left", padx=10)

        # Section Breakdown List
        section_hdr = ttk.Label(
            left_frame, text="Required Sections & Mandatory Fields", style="CardTitle.TLabel"
        )
        section_hdr.pack(anchor="w", pady=(10, 5))

        # Treeview Widget for Section Breakdown
        tree_scroll = ttk.Scrollbar(left_frame)
        tree_scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            left_frame,
            columns=("status", "details"),
            show="tree headings",
            selectmode="none",
            yscrollcommand=tree_scroll.set,
            height=10,
        )
        tree_scroll.config(command=self.tree.yview)

        self.tree.heading("#0", text="Item")
        self.tree.heading("status", text="Status")
        self.tree.heading("details", text="Details / Keyword")

        self.tree.column("#0", width=180)
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("details", width=220)

        self.tree.tag_configure("found", foreground=self.success_color)
        self.tree.tag_configure("missing", foreground=self.danger_color)
        self.tree.pack(fill="both", expand=True, pady=5)

        # Right Column: Document Content Preview & Actionable Reasons
        right_frame = ttk.Frame(main_paned, style="Card.TFrame", padding=15)
        main_paned.add(right_frame, weight=1)

        reasons_hdr = ttk.Label(
            right_frame, text="Validation Remarks & Issues", style="CardTitle.TLabel"
        )
        reasons_hdr.pack(anchor="w", pady=(0, 5))

        self.reasons_text = ScrolledText(
            right_frame,
            height=6,
            bg="#181825",
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=("Consolas", 9),
            relief="flat",
        )
        self.reasons_text.pack(fill="x", pady=(0, 10))

        preview_hdr = ttk.Label(
            right_frame, text="Extracted Document Text Preview", style="CardTitle.TLabel"
        )
        preview_hdr.pack(anchor="w", pady=(5, 5))

        self.preview_text = ScrolledText(
            right_frame,
            height=15,
            bg="#181825",
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=("Segoe UI", 9),
            relief="flat",
        )
        self.preview_text.pack(fill="both", expand=True)

    def _browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Document File",
            filetypes=[
                ("All Supported Documents", "*.txt *.docx *.pdf"),
                ("Text Files (*.txt)", "*.txt"),
                ("Word Documents (*.docx)", "*.docx"),
                ("PDF Files (*.pdf)", "*.pdf"),
            ],
        )
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)

    def _validate_document(self):
        file_path = self.file_entry.get().strip()
        selected_format = self.type_combo.get()

        if not file_path:
            messagebox.showwarning("File Required", "Please select or enter a document file path.")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("File Not Found", f"The file '{file_path}' does not exist.")
            return

        rules_path = DOCUMENT_TYPES.get(selected_format)
        if not rules_path or not os.path.exists(rules_path):
            messagebox.showerror("Rule File Missing", f"Could not find configuration rules for '{selected_format}'.")
            return

        try:
            # 1. Extract text from file
            text = extract_text(file_path)

            # 2. Display text preview
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert(tk.END, text)

            # 3. Perform rule-based validation
            rules = load_rules(rules_path)
            val_result = validate_document(text, rules)

            # 4. Perform ML scoring
            ml_confidence = 0.5
            if self.model and self.model.is_trained:
                try:
                    ml_confidence = self.model.predict_confidence(text)
                except Exception as e:
                    print(f"ML scoring error: {e}")

            # 5. Build final report
            report = build_report(val_result, ml_confidence)

            # 6. Update GUI components with report results
            self._update_gui_results(val_result, report, ml_confidence)

        except Exception as e:
            messagebox.showerror("Error Validating Document", str(e))

    def _update_gui_results(self, val_result: dict, report: dict, ml_confidence: float):
        verdict = report["decision"]

        if verdict == "ACCEPTED":
            self.verdict_label.config(
                text="✔ DOCUMENT FORMAT ACCEPTED",
                bg=self.success_color,
                fg="#11111B",
            )
        elif verdict == "NEEDS MANUAL REVIEW":
            self.verdict_label.config(
                text="⚠ NEEDS MANUAL REVIEW",
                bg=self.warning_color,
                fg="#11111B",
            )
        else:
            self.verdict_label.config(
                text="✖ DOCUMENT FORMAT REJECTED",
                bg=self.danger_color,
                fg="#11111B",
            )

        # Update Metrics
        self.word_count_lbl.config(
            text=f"Word Count: {val_result['word_count']} ({'OK' if val_result['min_word_count_ok'] else 'Too Low'})"
        )
        self.order_lbl.config(
            text=f"Section Order: {'Correct' if val_result['order_ok'] else 'Incorrect'}"
        )
        self.ml_score_lbl.config(text=f"ML Confidence: {int(ml_confidence * 100)}%")

        # Clear and populate Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert Sections
        sec_node = self.tree.insert("", "end", text="Required Sections", open=True)
        for sec in val_result["sections"]:
            status_text = "✔ FOUND" if sec["found"] else "✖ MISSING"
            tag = "found" if sec["found"] else "missing"
            pos_info = f"Position: char {sec['position']}" if sec["found"] else "Section missing"
            self.tree.insert(
                sec_node,
                "end",
                text=sec["name"],
                values=(status_text, pos_info),
                tags=(tag,),
            )

        # Insert Mandatory Fields
        field_node = self.tree.insert("", "end", text="Mandatory Fields", open=True)
        for name, info in val_result["mandatory_fields"].items():
            status_text = "✔ FOUND" if info["found"] else "✖ MISSING"
            tag = "found" if info["found"] else "missing"
            desc = info["description"]
            self.tree.insert(
                field_node,
                "end",
                text=name.capitalize(),
                values=(status_text, desc),
                tags=(tag,),
            )

        # Update Remarks text box
        self.reasons_text.delete("1.0", tk.END)
        if report["reasons"]:
            self.reasons_text.insert(tk.END, "Issues Identified:\n")
            for r in report["reasons"]:
                self.reasons_text.insert(tk.END, f" • {r}\n")
        else:
            self.reasons_text.insert(
                tk.END, "No issues found. Document complies with format specifications."
            )


def main():
    app = DocumentValidationApp()
    app.mainloop()


if __name__ == "__main__":
    main()
