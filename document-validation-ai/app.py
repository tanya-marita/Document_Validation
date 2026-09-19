"""
app.py
------
The main entry point for the project. Run this from the command line
and point it at a document to validate.

Usage:
    python app.py path/to/document.docx
    python app.py path/to/document.pdf
    python app.py path/to/document.txt

What happens step by step (see README.md for the full explanation):
    1. extractor.py  -> pulls plain text out of the file
    2. validator.py  -> checks that text against config/ssr_rules.json
    3. ml_model.py   -> loads the trained model and scores the document
    4. report.py     -> combines both results into one final verdict
"""

import sys
import os

from src.extractor import extract_text
from src.validator import load_rules, validate_document
from src.ml_model import DocumentClassifier, MODEL_PATH
from src.report import build_report, print_report

RULES_PATH = os.path.join(os.path.dirname(__file__), "config", "ssr_rules.json")


def main():
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "--gui"):
        print("Launching Desktop Validation GUI...")
        from gui_app import main as launch_gui
        launch_gui()
        return

    if len(sys.argv) != 2:
        print("Usage:")
        print("  python app.py --gui                      (Launches Desktop UI)")
        print("  python app.py <path-to-document>          (Command-line validation)")
        sys.exit(1)

    file_path = sys.argv[1]

    print(f"Reading document: {file_path}")
    text = extract_text(file_path)

    print("Checking against SSR rules...")
    rules = load_rules(RULES_PATH)
    validation_result = validate_document(text, rules)

    print("Scoring with ML model...")
    if not os.path.exists(MODEL_PATH):
        print(
            "\nNo trained model found. Run 'python train_model.py' first.\n"
        )
        sys.exit(1)

    model = DocumentClassifier.load(MODEL_PATH)
    ml_confidence = model.predict_confidence(text)

    report = build_report(validation_result, ml_confidence)
    print()
    print_report(report)



if __name__ == "__main__":
    main()
