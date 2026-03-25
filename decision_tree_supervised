# imu_decision_tree.py

import os
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import confusion_matrix
from utility import DataOrganiser
from collections import Counter
from sklearn.utils import shuffle

# --- CONFIG ---
DATA_FOLDER = "data"
TEST_SIZE = 0.4

# --- 1. DEFINE YOUR TRUE LABELS ---
GESTURE_KEYWORDS = {
    "look_left": ["look_left", "left", "behind_left"],
    "look_right": ["look_right", "right", "behind_right"],
    "look_up": ["look_up", "up"],
    "look_down": ["look_down", "down"],
    "tilt_left": ["tilt_left"],
    "tilt_right": ["tilt_right"],
    "nod": ["nod"],
    "shake": ["shake"],
    "idle": ["idle"],
    "walk": ["walk"],
    "jump": ["jump"],
    "sit_down": ["sit", "sit_down"],
    "get_up": ["get_up", "stand", "stand_up"],
    "music_beat": ["music_beat", "beat"],
    "look_around": ["look_around", "around"],
    "look_direction": ["look_direction", "direction"]
}

def normalise_label(label):
    name = label.lower()

    for true_label, keywords in GESTURE_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                return true_label

    return None  # unknown

def zero_crossings(x):
    return ((x[:-1] * x[1:]) < 0).sum()


# --- 1. FEATURE EXTRACTION ---
def extract_features(df):
    features = {}
    
    # Convert to numeric safely
    df = df.apply(pd.to_numeric, errors="coerce").dropna()

    # Drop timestamp
    df = df.iloc[:, 1:]

   # --- BASIC STATS  ---
    features.update(df.mean().add_prefix("mean_").to_dict())
    features.update(df.std().add_prefix("std_").to_dict())
    features.update(df.min().add_prefix("min_").to_dict())
    features.update(df.max().add_prefix("max_").to_dict())

    # Range (max - min)
    features.update((df.max() - df.min()).add_prefix("range_").to_dict())

    # Median
    features.update(df.median().add_prefix("median_").to_dict())

    # Absolute mean (useful for motion intensity)
    features.update(df.abs().mean().add_prefix("absmean_").to_dict())

    # magnitude (all axes together like you did)
    features["accel_magnitude_mean"] = np.sqrt((df.iloc[:, :3]**2).sum(axis=1)).mean()

    # change over time
    features["accel_diff_mean"] = df.diff().abs().mean().mean()

    # energy
    features["accel_energy"] = (df.iloc[:, :3]**2).sum().sum()
    features["gyro_energy"]  = (df.iloc[:, 3:]**2).sum().sum()

    # zero crossings (keep if you defined it)
    features["gyro_zero_cross"] = df.iloc[:, 3:].apply(zero_crossings).sum()

    return features


# --- 2. LOAD DATA ---

d = DataOrganiser("data")

all_files = []

for gesture, files in d.recordingDictByGesture.items():
    for file in files:
        all_files.append((file, gesture))

#ASSIGN DIFFERENT RECORDINGS FOR TRAINING AND TESTING, INSTEAD OF SEQUENCIAL
train_files, test_files = train_test_split(all_files, test_size=0.4, random_state=42)

def process_files(file_list):
    X, y = [], []
    for file, gesture in file_list:

        try:
            df = pd.read_csv(file, header=None)

            # Skip bad files
            if df.shape[1] != 7:
                print(f"Skipping {file} (wrong format)")
                continue
            window_size = 50
            step = 25
            for i in range(0, len(df) - window_size, step):
                window = df.iloc[i:i+window_size]
                features = extract_features(window)

                X.append(features)
                y.append(normalise_label(gesture))

        except Exception as e:
            print(f"Skipping {file}: {e}")

    return pd.DataFrame(X), np.array(y)

# -- OBTAIN THE FEAUTURES FOR TRAINING AND TESTING SET---
X_train, y_train = process_files(train_files)
X_test, y_test = process_files(test_files)
feature_names = X_train.columns
print("Number of features:", len(X_train.columns))

# --- SCALE THE FEATURES ---
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

print(f"Loaded {len(X_train)} samples")
print("Label distribution:", Counter(y_train))

param_grid = {
    "max_depth": [3, 5, 10,20, 30, 40 , 50],
    "min_samples_split": [2, 5, 10,15,20]
}

grid = GridSearchCV(RandomForestClassifier(), param_grid, cv=3)
grid.fit(X_train, y_train)

print("Best params:", grid.best_params_)
print("Best CV accuracy:", grid.best_score_)

# --- 7. EVALUATION ---
best_model = grid.best_estimator_
y_pred = best_model.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

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

