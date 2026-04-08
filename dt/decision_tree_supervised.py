# imu_decision_tree.py

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import pickle
import sys

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import confusion_matrix
from collections import Counter
from dataPreprocessing.aggregate import get_aggregate

import pandas as pd

# --- CONFIG ---
DATA_FOLDER = os.path.abspath("./data")
TEST_SIZE = 0.4
SAMPLE_SEED = 42

# --- 2. LOAD DATA ---

# Load aggregated DataFrame using aggregate.py
df_all = get_aggregate(DATA_FOLDER, raw=False, window_size=100, overlap=25)

# run aggregate.py to generate aggregate file
#aggregate_file = 'aggregated_features_100_25.csv'

#df_all = pd.read_csv(os.path.join(DATA_FOLDER, aggregate_file))

# Separate features and labels
X = df_all.drop(columns=["label"])
y = df_all["label"].values

print(f"Total samples (after filtering unknowns): {len(df_all)}")
print("Label distribution:", df_all["label"].value_counts())

# --- TRAIN / TEST SPLIT ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, stratify=y, random_state=SAMPLE_SEED
)

#-- MAKE THE TRAINIG SET HAVE AN EQUAL NUMBER OF SAMPLES BETWEEN ALL LABELS
# FIND THE LABEL WITH THE LEAST AMOUT OF SAMPLES AND MAKE EACH OTHER LABEL HAVE THE SAME AMOUNT--
# df = X_train.copy()
# df["label"] = y_train
# # Find smallest class
# min_count = df["label"].value_counts().min()
# # Balance dataset
# df_balanced = df.groupby("label", group_keys=False).apply(
#     lambda x: x.sample(min_count, random_state=42)
# )
# # Shuffle after balancing (IMPORTANT)
# df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)
# # Split back
# X_train = df_balanced.drop(columns=["label"])
# y_train = df_balanced["label"].values

feature_names = X_train.columns
print("Number of features:", len(X_train.columns))

# --- SCALE THE FEATURES ---
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

print(f"Loaded {len(X_train)} samples")
print("Label distribution:", Counter(y_train))
print("Test:", Counter(y_test))

param_grid = {
    "max_depth": [3, 5,10, 20, 30, 40, 50],
    "min_samples_split": [6, 10, 12, 16, 20]
}
grid = GridSearchCV(
    DecisionTreeClassifier(class_weight="balanced"),
    param_grid,
    cv=3
)
#grid = GridSearchCV(RandomForestClassifier(class_weight="balanced"), param_grid, cv=3)
grid.fit(X_train, y_train)

print("Best params:", grid.best_params_)
print("Best CV accuracy:", grid.best_score_)

# --- 7. EVALUATION ---
best_model = grid.best_estimator_
y_pred = best_model.predict(X_test)

print("Predicted labels:", Counter(y_pred))
print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))


# --Calculate Model size --
with open("model.pkl", "wb") as f:
    pickle.dump(best_model, f)

print("Model size (bytes):", os.path.getsize("model.pkl"))

# --PLOT FEAUTURE IMPORTANCE--

importances = best_model.feature_importances_

feat_imp = pd.Series(importances, index=feature_names)
feat_imp = feat_imp.sort_values(ascending=False)

print(feat_imp.head(20))
plt.figure(figsize=(10,6))
feat_imp.head(20).plot(kind="barh")
plt.title("Top 20 Feature Importances")
plt.gca().invert_yaxis()
plt.show()

# --- PRINT CONFUSION MATRIX ---
cm = confusion_matrix(y_test, y_pred)
labels = sorted(set(y_test))

plt.figure(figsize=(12,10))
sns.heatmap(cm, 
            xticklabels=labels, 
            yticklabels=labels, 
            annot=False, 
            cmap="Blues")

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")

plt.xticks(rotation=45)
plt.yticks(rotation=0)

plt.tight_layout()
plt.savefig("confusion_matrix.png")
plt.show()
