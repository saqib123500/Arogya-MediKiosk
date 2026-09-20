import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import numpy as np

def train_triage_model(csv_path, model_path, scaler_path):
    # 1. Load data (Semicolon separated, using latin-1 encoding for compatibility)
    df = pd.read_csv(csv_path, sep=';', encoding='latin-1')

    # 2. Feature Selection
    # We use vitals and basic patient info as features
    features = ['Age', 'Sex', 'Mental', 'Pain', 'NRS_pain', 'SBP', 'DBP', 'HR', 'RR', 'BT', 'Saturation']
    target = 'KTAS_expert'

    # Handle missing values
    df = df.dropna(subset=[target])
    for col in features:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(df[col].median())

    X = df[features]
    y = df[target]

    # 3. Scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 4. Training
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 5. Save Artifacts
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    accuracy = model.score(X_test, y_test)
    print(f"Model trained successfully. Accuracy: {accuracy:.2f}")

if __name__ == "__main__":
    train_triage_model(
        csv_path='/Users/mohammadsaqib/Library/Application Support/Claude-3p/local-agent-mode-sessions/bf199cb3/00000000/0ed52bd9/uploads/data.csv',
        model_path='triage_model.joblib',
        scaler_path='scaler.joblib'
    )
