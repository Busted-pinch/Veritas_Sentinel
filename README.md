<h1 align="center">Veritas Sentinel</h1>
<p align="center">
<img src="https://raw.githubusercontent.com/Busted-pinch/Veritas_Sentinel/main/frontend/images/Banner.png" width="650" height="325">
</p>
# 🚨 Veritas Sentinel  
### AI-Powered Fraud Detection & Real-Time Risk Intelligence System  
MIT Licensed • Full-Stack • ML-Driven • FinTech

Veritas Sentinel is an end-to-end **fraud detection and risk scoring platform** designed for fintech applications.  
It combines a **FastAPI backend**, **React frontend**, and a modular **Machine Learning Engine** to process transactions, detect anomalies, and score fraud likelihood in real-time.

This project is built for **portfolio demonstration**, **learning advanced AI workflows**, and **showcasing full-stack ML product engineering**.

---

## ⚡ Key Features

- 🔍 **AI-Driven Fraud Detection** using anomaly detection + predictive models  
- 📊 **Real-Time Risk Scoring Engine**  
- 🧠 **Modular ML Engine** with training, inference, and evaluation  
- 🌐 **FastAPI Backend** with clean REST endpoints  
- 🎨 **React Frontend Dashboard** for alerts, analytics, and transaction monitoring  
- 🧪 **Synthetic Demo Dataset + Seeder Script**  
- 🔐 **Secure API Structure** with reusable services  
- 📦 **Complete Project Architecture (Backend + Frontend + ML)**  
- 🛠️ **Easy local setup** with virtual environments or Docker (optional)  
- 📈 **Extendable for credit risk, anomaly detection pipelines, agentic systems, etc.**

---

## 📁 Project Structure

```
Veritas_Sentinel/
│
├── backend/
│   ├── app/
│   ├── core/
│   ├── routes/
│   ├── services/
│   └── tests/ (recommended)
│
├── frontend/
│   ├── src/
│   └── public/
│
├── ml_engine/
│   ├── models/
│   ├── training/
│   ├── inference/
│   └── evaluation/
│
├── seed_demo_data.py
├── requirements.txt
└── README.md
```

---

## 🏗️ System Architecture (High-Level)

```
                ┌─────────────────────┐
                │   React Frontend    │
                │  (Dashboard + UI)   │
                └──────────┬──────────┘
                           │ REST API
                ┌──────────▼──────────┐
                │     FastAPI API      │
                │ (Auth, Services, ML) │
                └──────────┬──────────┘
                        API Calls
                ┌──────────▼──────────┐
                │    ML Engine        │
                │ (Model + Scoring)   │
                └──────────┬──────────┘
                           │
                  Demo / Synthetic Data
```

---

## 🧠 Machine Learning Engine Overview

The **ML Engine** provides:

- Feature engineering  
- Outlier detection  
- Fraud probability estimation  
- Risk scoring pipeline  
- Model persistence  
- Evaluation & metrics  

It is structured so you can **replace the model** with XGBoost, LightGBM, deep learning, or anomaly detection modules.

---

## 🚀 Quick Start Guide

### **1. Clone the Repository**
```bash
git clone https://github.com/Busted-pinch/Veritas_Sentinel.git
cd Veritas_Sentinel
```

---

## 🖥️ Backend Setup (FastAPI)

### **2. Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows
```

### **3. Install requirements**
```bash
pip install -r requirements.txt
```

### **4. Run the backend**
```bash
uvicorn backend.app.main:app --reload
```

### **5. Open API Docs**
```
http://localhost:8000/docs
```

---

## 🌐 Frontend Setup (React)

```bash
cd frontend
npm install
npm start
```

Frontend runs on:
```
http://localhost:3000/
```

---

## 🧪 Load Demo Data

The project includes a synthetic fraud-like dataset generator.

Run:
```bash
python seed_demo_data.py
```

---

## 🧵 Sample API Requests

### **Score a transaction**

```bash
POST /api/v1/score
```

Example JSON:
```json
{
  "transaction_id": "TXN123",
  "amount": 4200,
  "location": "IN-MH",
  "channel": "UPI",
  "timestamp": "2025-01-10T13:22:14",
  "customer_age": 24
}
```

Example Response:
```json
{
  "risk_score": 0.87,
  "label": "High Fraud Probability",
  "explanation": "Amount unusually high compared to user history."
}
```

---

## 📊 Model Card (Summary)

| Property | Details |
|---------|---------|
| Model Type | Supervised classifier + anomaly detector |
| Input | Transaction metadata |
| Outputs | Fraud probability, risk score |
| Dataset | Synthetic (no real PII) |
| Metrics | Precision, Recall, F1, ROC-AUC |
| Limitations | Not suitable for real-world deployment without validation |

---

## 🔐 Security Notes

- No real user or PII data included  
- `.env.example` recommended  
- Avoid production deployment without auth, HTTPS, and rate limiting  

---

## 🛠️ Recommended Improvements (Future Work)

- Add Docker + `docker-compose.yml`  
- Add CI (GitHub Actions)  
- Add unit tests  
- Add model retraining pipeline  
- Add SHAP explainability  

---

## 📸 Screenshots (Placeholder)

```
/screenshots/dashboard.png
/screenshots/alerts.png
/screenshots/transactions.png
```

---

## 🤝 Contributing

Pull requests are welcome!  
Follow clean code, PEP8, and descriptive commit messages.

---

## 📜 License

MIT License — free to modify, use, and distribute.

---

## ⭐ Support the Project

If you found this useful, please give the repo a **star** ⭐
