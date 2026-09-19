"""
ml_model.py
-----------
This is the "AI/ML" half of the project.

Beginner note on WHY we need this at all, when validator.py already
checks the rules perfectly:
    Rule-based checks are great at answering "is the word 'Scope'
    present?" but they can be tricked by a document that includes all
    the right KEYWORDS in a nonsensical order or copy-pasted nonsense
    under each heading. A machine learning model looks at the overall
    *pattern* of the writing (which words tend to appear near each
    other) and gives a confidence score that a human reviewer can use
    as a second opinion alongside the rule-based reasons.

How it works, in plain English:
    1. TF-IDF turns text into a list of numbers representing which
       words are important in that document.
    2. Logistic Regression is a simple, well-understood ML algorithm
       that learns to separate "valid-looking" documents from
       "invalid-looking" ones based on those numbers.
    3. We save the trained model to disk with joblib so we don't have
       to retrain it every time the program runs.
"""

import os
import random

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "ssr_classifier.pkl")


class DocumentClassifier:
    def __init__(self):
        # A "Pipeline" just chains steps together: text -> TF-IDF numbers -> classifier.
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=2000, ngram_range=(1, 2))),
            ("clf", LogisticRegression(max_iter=1000)),
        ])
        self.is_trained = False

    def train(self, texts: list, labels: list):
        """
        texts: list of document strings
        labels: list of 1 (valid SSR) or 0 (invalid) matching each text
        """
        self.pipeline.fit(texts, labels)
        self.is_trained = True

    def predict_confidence(self, text: str) -> float:
        """
        Returns a float between 0 and 1: the model's estimated
        probability that this document is a well-formed SSR document.
        """
        if not self.is_trained:
            raise RuntimeError("Model has not been trained or loaded yet.")
        proba = self.pipeline.predict_proba([text])[0]
        # predict_proba returns [P(class=0), P(class=1)]; we want P(class=1)
        return float(proba[1])

    def save(self, path: str = MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.pipeline, path)

    @classmethod
    def load(cls, path: str = MODEL_PATH) -> "DocumentClassifier":
        instance = cls()
        instance.pipeline = joblib.load(path)
        instance.is_trained = True
        return instance


# ---------------------------------------------------------------------------
# Synthetic training data generator
# ---------------------------------------------------------------------------
# Beginner note: real machine learning projects need REAL labeled examples.
# Since we don't have your real historical documents yet, this function
# generates realistic-looking fake SSR documents so the model has SOMETHING
# to learn from and the project runs end-to-end immediately.
#
# --> Once you have real documents, replace this function's output with
#     your real (text, label) pairs. The rest of the code doesn't change.
# ---------------------------------------------------------------------------

_SECTION_TEXT = {
    "Title": "Title: Annual Safety Standard Report",
    "Introduction": "Introduction: This report explains the purpose of the review conducted this quarter.",
    "Scope": "Scope: This document covers all operations within the eastern division.",
    "Methodology": "Methodology: Data was gathered using site visits and structured interviews.",
    "Findings": "Findings: Several minor issues were observed in the storage area.",
    "Recommendations": "Recommendations: We recommend upgrading the ventilation system by next quarter.",
    "Conclusion": "Conclusion: Overall compliance is satisfactory with minor improvements needed.",
    "Signature": "Signature: Approved by J. Perera on 12/05/2026.",
}

_SECTION_ORDER = [
    "Title", "Introduction", "Scope", "Methodology",
    "Findings", "Recommendations", "Conclusion", "Signature",
]


def generate_synthetic_dataset(n_samples: int = 300, seed: int = 42):
    """
    Returns (texts, labels) — a synthetic dataset of fake documents.

    Roughly half are "valid": all sections present, in order.
    Roughly half are "invalid": missing sections, shuffled order, or short.
    """
    random.seed(seed)
    texts, labels = [], []

    for i in range(n_samples):
        make_valid = i % 2 == 0

        if make_valid:
            body = "\n".join(_SECTION_TEXT[name] for name in _SECTION_ORDER)
            texts.append(body)
            labels.append(1)
        else:
            # Randomly drop 1-4 sections and/or shuffle order to simulate
            # a broken / incomplete / malformed document.
            sections = _SECTION_ORDER.copy()
            num_to_drop = random.randint(1, 4)
            for _ in range(num_to_drop):
                if len(sections) > 2:
                    sections.pop(random.randrange(len(sections)))
            if random.random() < 0.5:
                random.shuffle(sections)

            body = "\n".join(_SECTION_TEXT[name] for name in sections)
            texts.append(body)
            labels.append(0)

    return texts, labels
