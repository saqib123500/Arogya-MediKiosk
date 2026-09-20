# ML Triage System Design Document

## 1. Overview
The Triage System aims to automatically categorize patients based on their symptoms to help staff prioritize care and route patients to the correct specialist.

## 2. Technology Stack
- **ML Frameworks**: Scikit-learn (for baseline models like Random Forest/SVM), TensorFlow (for deeper analysis if needed).
- **API**: FastAPI (High-performance asynchronous API for model serving).
- **Database**: MySQL (Production storage for training data and triage logs).
- **Infrastructure**: AWS/Azure (Hosting for the FastAPI service and model artifacts).

## 3. Triage Logic
### Input Features
- **General Symptoms**: Binary indicators for fever, cough, dizziness, etc.
- **Fever Metrics**: Temperature value and duration.
- **Pain Profile**: Location of pain and severity (1-10).
- **Patient Demographics**: Age (to identify high-risk groups).

### Target Labels (Triage Categories)
- **Level 1 (Critical)**: Immediate attention required (e.g., chest pain, severe breathing difficulty).
- **Level 2 (Urgent)**: Needs attention within a few hours (e.g., high fever, moderate pain).
- **Level 3 (Standard)**: Routine appointment (e.g., mild cough, general check-up).
- **Level 4 (Low)**: Non-urgent/Administrative.

## 4. Architecture
`Patient Form (Django)` $\rightarrow$ `Symptom Submission` $\rightarrow$ `Triage API (FastAPI)` $\rightarrow$ `ML Model` $\rightarrow$ `Priority Score` $\rightarrow$ `Staff Dashboard (Django)`

## 5. Implementation Roadmap
1. **Data Synthesis**: Generate a synthetic dataset based on medical triage guidelines.
2. **Model Training**: Train a classifier to predict the triage level.
3. **API Development**: Build FastAPI endpoints to accept symptom JSON and return a priority label.
4. **Django Integration**: Update `save_symptoms` to call the API and store the result in a new `TriageRecord` model.
5. **UI Update**: Add color-coded priority badges to the Staff Dashboard.
