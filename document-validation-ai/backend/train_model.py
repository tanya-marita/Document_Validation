"""
train_model.py
--------------
Trains the Document Validation ML Classifier model.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from app.core.ml_model import DocumentClassifier, generate_synthetic_dataset, MODEL_PATH


def main():
    print("Generating synthetic training dataset...")
    texts, labels = generate_synthetic_dataset(n_samples=300)

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )

    print(f"Training on {len(X_train)} documents, testing on {len(X_test)}...")
    model = DocumentClassifier()
    model.train(X_train, y_train)

    predictions = [1 if model.predict_confidence(t) >= 0.5 else 0 for t in X_test]
    accuracy = accuracy_score(y_test, predictions)
    print(f"\nTest accuracy: {accuracy:.2%}\n")
    print(classification_report(y_test, predictions, target_names=["invalid", "valid"]))

    model.save(MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
