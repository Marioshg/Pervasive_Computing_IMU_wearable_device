# Decision Tree Algorithm

##  Dataset Overview

- **Total recordings:** 1,740  
- **Gestures:** 49 unique gestures  
- **Users:** 3  

###  Recordings per User
- **User1:** 580 recordings (49 gestures)  
- **User2:** 580 recordings (49 gestures)  
- **User3:** 580 recordings (49 gestures)  

---

##  Data Processing

- Successfully mapped files to gesture labels  
- Constructed dataset with **2,100 samples**  

### 🏷️ Label Distribution (Balanced)
Each class contains **300 samples**:

- `look_left`, `look_right`, `look_up`, `look_down`  
- `tilt_left`, `tilt_right`  
- `none`  

---

##  Feature Extraction

- **Number of features per sample:** 600  

---

##  Train / Test Split

- **Training samples:** 1,260  
- **Test samples:** 840  

### Label Distribution
- **Train:** 180 samples per class  60%
- **Test:** 120 samples per class   40%

---

##  Model: Random Forest (Grid Search)

```python
grid = GridSearchCV(
    RandomForestClassifier(class_weight="balanced"),
    param_grid,
    cv=3
)
```


## Best Results

Acc: 88%
Memory Size: 3.1 MB
Cross-Validation Accuracy: 0.865
Best Hyperparameters
- max_depth = 30
- min_samples_split = 2
- F1 score per class: [0.97, 0.76, 0.83, 0.96, 0.69, 0.97, 0.94]
- Macro Avg F1: 0.87
- Weighted Avg F1: 0.87

## Comments: These are good results but the model is unacceptably big.
 So the most compromising solution is to use A smaller depth_value(5)
 sacrifysing accuracy, but to make up for it, increase the training set to 80%

2nd Run Results

- Acc: 0.65%
- Memory Size: 424 KB
- Cross-Validation Accuracy: 0.65

### Hyperparameters
- max_depth = 5
- min_samples_split = 2
- F1 average: 0.65
- F1 score per class: [0.76, 0.50, 0.48, 0.86, 0.25, 0.89, 0.82]
- Weighted Avg F1: 0.65

### Label Distribution
- **Train:** 240 samples per class  80%
- **Test:** 60 samples per class   20%

## Alternative Solution

Random Forest Takes a lot of space. Instead we use Decision Tree with the excact same parameters as the original RandomForest

- Acc: 74%
- Memory Size: 36 KB
- Cross-Validation Accuracy: 0.72

### Hyperparameters
- max_depth = 40
- min_samples_split = 2
- F1 average: 0.73
- F1 score per class: [0.89, 0.54, 0.62, 0.91, 0.42, 0.90, 0.85]
- Weighted Avg F1: 0.73

### Label Distribution
- **Train:** 180 samples per class  60%
- **Test:** 120 samples per class   40%

## Results:



## Final Outcome:

Even with Depth Reduction, the results are not promising for the Forest Tree. But A decision Tree is the perfect balance between performance and Memory size.  
