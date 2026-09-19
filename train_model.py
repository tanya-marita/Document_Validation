"""
train_model.py
---------------
Run this ONCE to train the ML model and save it to models/ssr_classifier.pkl.

Beginner note: this script currently trains on SYNTHETIC (fake, generated)
data so the whole project works immediately without you needing real
documents first. As you collect real examples of valid/invalid SSR
documents, replace the call to `generate_synthetic_dataset()` below with
your own list of (text, label) pairs — 1 = valid SSR, 0 = invalid.

Usage:
    python train_model.py
"""

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from src.ml_model import DocumentClassifier, generate_synthetic_dataset, MODEL_PATH


def main():
    print("Generating synthetic training data...")
    texts, labels = generate_synthetic_dataset(n_samples=300)

    # Split into a training set and a test set so we can check how well
    # the model does on documents it has NOT seen during training.
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
