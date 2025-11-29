import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
from pipeline.data_cleaning import DataCleaner

cleaner = DataCleaner()

# 1. Load dataset
df = pd.read_csv("data/Fraud_dataset.csv")

# 2. Prepare X, y
y = df['is_fraud']
X = df.drop(['is_fraud'], axis=1)

# 3. Clean & scale
X = cleaner.clean(X)
X_scaled = cleaner.scale(X)

# 4. Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# 5. Model
model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    scale_pos_weight=10  # handles imbalance
)

print("Training supervised model...")
model.fit(X_train, y_train)

# 6. Evaluate
preds = model.predict(X_test)
print(classification_report(y_test, preds))

# 7. Save model
joblib.dump(model, "models/supervised_xgb.pkl")
