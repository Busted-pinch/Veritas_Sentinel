import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
from pipeline.data_cleaning import DataCleaner

cleaner = DataCleaner()

# Load only NON-FRAUD transactions
df = pd.read_csv("data/paysim_small.csv")
df = df[df["is_fraud"] == 0]

df_clean = cleaner.clean(df.drop('is_fraud', axis=1))
df_scaled = cleaner.scale(df_clean)

iso = IsolationForest(contamination=0.01)
iso.fit(df_scaled)

joblib.dump(iso, "models/anomaly_iforest.pkl")
