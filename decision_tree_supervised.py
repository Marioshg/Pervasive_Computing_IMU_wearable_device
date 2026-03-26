# imu_decision_tree.py

import os
import pandas as pd
import numpy as np
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
import pickle
import sys

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
from format_data import get_data
from sklearn.feature_selection import SelectKBest, f_classif

# --- CONFIG ---
DATA_FOLDER = "data"
TEST_SIZE = 0.4
SAMPLE_SEED = 42

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
                if true_label in ["tilt_left","tilt_right","shake","music_beat","look_around","look_direction","nod"]:
                    return "none"
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

# Load aggregated DataFrame using format_data.py
df_all = get_data(DATA_FOLDER)

# Separate features and labels
X = df_all.drop("label", axis=1)
y = df_all["label"].values

print(f"Total samples (after filtering unknowns): {len(df_all)}")
print("Label distribution:", df_all["label"].value_counts())

# --- TRAIN / TEST SPLIT ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, stratify=y, random_state=SAMPLE_SEED
)
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

#----COMMENT THIS IF YOU DONT WANT TO USE THIS FILES FEATURES---

#d = DataOrganiser("data")
#all_files = []
#for gesture, files in d.recordingDictByGesture.items():
#    for file in files: all_files.append((file, gesture))
     #ASSIGN DIFFERENT RECORDINGS FOR TRAINING AND TESTING, INSTEAD OF SEQUENCIAL#
#train_files, test_files = train_test_split(all_files, test_size=0.4,random_state=42)
#X_train, y_train = process_files(train_files)
#X_test, y_test = process_files(test_files)

#-----#

# -- OBTAIN THE FEATURES FOR TRAINING AND TESTING SET---

#-- MAKE THE TRAINIG SET HAVE AN EQUAL NUMBER OF SAMPLES BETWEEN ALL LABELS
# FIND THE LABEL WITH THE LEAST AMOUT OF SAMPLES AND MAKE EACH OTHER LABEL HAVE THE SAME AMOUNT--
df = X_train.copy()
df["label"] = y_train
# Find smallest class
min_count = df["label"].value_counts().min()
# Balance dataset
df_balanced = df.groupby("label", group_keys=False).apply(
    lambda x: x.sample(min_count, random_state=42)
)
# Shuffle after balancing (IMPORTANT)
df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)
# Split back
X_train = df_balanced.drop("label", axis=1)
y_train = df_balanced["label"].values

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

