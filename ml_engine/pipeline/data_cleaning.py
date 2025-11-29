import pandas as pd
from sklearn.preprocessing import StandardScaler

class DataCleaner:
    def __init__(self):
        self.scaler = StandardScaler()

    def clean(self, df):
        # Drop columns you don’t need
        df = df.dropna()

        # Convert timestamp if available
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour

        # Fix category values
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype('category').cat.codes

        return df

    def scale(self, df):
        scaled = self.scaler.fit_transform(df)
        return scaled
