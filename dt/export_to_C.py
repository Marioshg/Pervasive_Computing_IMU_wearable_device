from sklearn_porter import Porter
from sklearn.tree import export_text
import joblib

# Load model
model = joblib.load("../decision_tree_model.pkl")

tree_text = export_text)(clf, )

# Export to C
porter = Porter(model, language='c')
c_code = porter.export()

# Save C code
with open("model.c", "w") as f:
    f.write(c_code)

print("C code exported!")