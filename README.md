# Document Validation AI (SSR Format Checker)

A beginner-friendly Python project that checks whether an uploaded document
(`.txt`, `.docx`, or `.pdf`) matches a required "SSR" format, tells you
**exactly which parts are missing**, and gives a final **ACCEPTED / REJECTED**
decision with reasons.

It combines two techniques on purpose:

| Layer | File | What it does | Why it's needed |
|---|---|---|---|
| Rule-based | `src/validator.py` | Checks for required sections, order, and fields (date, signature) using plain logic | Gives you **exact, explainable reasons** ("Scope section is missing") |
| Machine Learning | `src/ml_model.py` | A TF-IDF + Logistic Regression classifier scores the overall structure | Catches documents that technically contain the right *keywords* but don't read like a real SSR document |

The final report (`src/report.py`) combines both and only accepts a
document if **both** checks agree.

> **Important — this uses a made-up definition of "SSR."** I don't know your
> organization's exact SSR spec, so I defined a reasonable one (Title,
> Introduction, Scope, Methodology, Findings, Recommendations, Conclusion,
> Signature) in `config/ssr_rules.json`. **Open that file and edit the
> section names/keywords to match your real format** — you never need to
> touch the Python code to do this.

---

## 1. Project structure

```
document-validation-ai/
├── app.py                     # Main program you run from the command line
├── train_model.py             # Trains the ML model (run once)
├── requirements.txt           # List of Python packages needed
├── .gitignore
├── config/
│   └── ssr_rules.json         # EDIT THIS to define your real SSR format
├── src/
│   ├── extractor.py           # Reads text out of .txt/.docx/.pdf files
│   ├── validator.py           # Rule-based checking logic
│   ├── ml_model.py            # The AI/ML classifier
│   └── report.py              # Combines both checks into one final report
├── models/
│   └── ssr_classifier.pkl     # Created automatically after training
├── data/
│   └── sample_documents/      # Two example files to test with
└── tests/
    └── test_validator.py      # Automated tests
```

---

## 2. Prerequisites

- Python 3.10 or newer installed on your computer
  (check with `python3 --version` in a terminal)
- Git installed (check with `git --version`)
- A free GitHub account, if you want to push this to a remote repo

---

## 3. Set up the project locally

```bash
# 1. Unzip the project, then move into it
cd document-validation-ai

# 2. Create a virtual environment (an isolated space for this project's packages)
python3 -m venv venv

# 3. Activate it
#    On Mac/Linux:
source venv/bin/activate
#    On Windows (Command Prompt):
venv\Scripts\activate.bat

# 4. Install the required packages
pip install -r requirements.txt
```

**Beginner note:** a virtual environment keeps this project's Python
packages separate from every other Python project on your machine, so
installing something here never breaks another project.

---

## 4. Set up the Git repository

```bash
# Initialize a new git repo inside the project folder
git init

# Stage all files
git add .

# Make your first commit
git commit -m "Initial commit: document validation AI project"

# (Optional) Connect it to a GitHub repo you've created online
git remote add origin https://github.com/YOUR-USERNAME/document-validation-ai.git
git branch -M main
git push -u origin main
```

**Beginner note:**
- `git init` turns the folder into a repository git can track.
- `git add .` stages every file (tells git "include these in the next commit").
- `git commit` saves a snapshot with a message describing what changed.
- `git remote add origin ...` links your local folder to an empty repo you
  created on GitHub.com first (create it there before running this line).
- `git push` uploads your commits to GitHub.

From now on, whenever you change code:

```bash
git add .
git commit -m "Describe what you changed"
git push
```

---

## 5. Train the ML model (run once)

```bash
python train_model.py
```

This generates synthetic (fake, computer-generated) example documents,
trains the classifier on them, prints an accuracy score, and saves the
trained model to `models/ssr_classifier.pkl`.

**Beginner note:** real ML projects train on real historical data. Since
you don't have a labeled dataset of real valid/invalid SSR documents yet,
this script fakes one so the whole pipeline works immediately. Once you
have, say, 50-100 real example documents you've manually labeled as
"valid" or "invalid," open `src/ml_model.py`, find
`generate_synthetic_dataset()`, and replace its output with your real
`(text, label)` pairs — nothing else in the project needs to change.

---

## 6. Validate a document

Two sample files are already included for you to try:

```bash
# This one should be ACCEPTED
python app.py data/sample_documents/valid_sample.txt

# This one should be REJECTED
python app.py data/sample_documents/invalid_sample.txt
```

You can also point it at your own `.docx` or `.pdf` file:

```bash
python app.py "/path/to/your/document.docx"
```

Example output:

```
============================================================
 FINAL DECISION: REJECTED
============================================================
Rule-based check passed : False
ML confidence score     : 22%
Word count               : 24
Section order correct   : True

Section-by-section results:
  - Title           FOUND
  - Introduction    MISSING
  - Scope           MISSING
  - Methodology     MISSING
  - Findings        FOUND
  - Recommendations MISSING
  - Conclusion      MISSING
  - Signature       MISSING

Missing items:
  - Section missing: Introduction
  - Section missing: Scope
  ...

Reasons for this decision:
  * Missing required section: Introduction
  * Missing required section: Scope
  * Missing mandatory field: date — A date must appear somewhere...
  * Missing mandatory field: signature — There must be a signature...
  * Document is too short (24 words, minimum is 80).
  * ML model confidence too low (22%); the document's overall structure
    doesn't strongly resemble a valid SSR document.
============================================================
```

---

## 7. Run the automated tests

```bash
pytest tests/
```

This runs the checks in `tests/test_validator.py` and tells you
immediately if a future code change accidentally breaks something.

---

## 8. Customizing this for YOUR real SSR format

1. Open `config/ssr_rules.json`.
2. Rename the sections, add/remove them, and edit their `keywords` list
   to match the actual headings your real SSR documents use.
3. Adjust `min_word_count` if your real documents are typically shorter
   or longer.
4. Re-run `python app.py <file>` — no code changes needed.

If you later want to plug this into a bigger system (e.g. a web app where
users upload documents through a browser), the three functions you need
are:

```python
from src.extractor import extract_text
from src.validator import load_rules, validate_document
from src.ml_model import DocumentClassifier
from src.report import build_report
```

Call them in that order (extract → validate → score → build_report) and
you'll get back a plain Python dictionary you can turn into JSON for any
web framework (Flask, FastAPI, Django, etc.).

---

## 9. How each ML/AI concept works (glossary for beginners)

- **TF-IDF (Term Frequency–Inverse Document Frequency):** a way of
  converting text into numbers by measuring how important each word is
  to a specific document compared to all documents. Common words like
  "the" get a low score; distinctive words get a higher one.
- **Logistic Regression:** a simple, fast machine learning algorithm
  that learns a boundary between two categories (here: "valid" vs
  "invalid") based on those numbers.
- **Training:** the process of showing the model many labeled examples
  so it can learn the pattern.
- **Confidence score / probability:** a number between 0 and 1 (or 0%
  to 100%) representing how sure the model is about its prediction.
- **Pipeline:** chaining multiple processing steps (TF-IDF, then the
  classifier) into one object so you can call `.fit()` and `.predict()`
  once instead of managing each step by hand.
