<h1 align="center">Veritas Sentinel</h1>
<p align="center">
<img src="https://raw.githubusercontent.com/Busted-pinch/Veritas_Sentinel/main/frontend/images/Banner.png" width="650" height="325">
</p>

# **Veritas Sentinel**  
### **AI-Driven Fraud Detection & Risk Intelligence Platform**

Veritas Sentinel is a full-stack FinTech solution that provides real-time fraud detection, behavioral risk scoring, financial threat analytics, and user-level risk monitoring.  
Built for enterprise-grade security, Veritas Sentinel combines:

- A scalable **FastAPI backend**
- An AI-powered **ML scoring engine**
- A modern **HTML/CSS/JS frontend**
- Real-time **Fraud Analytics & Geo-Risk Visualization**
- Secure **JWT-based authentication**  
- Admin & User dashboards for role-based operations

---

## **Table of Contents**
1. [Overview](#overview)  
2. [Features](#features)  
3. [System Architecture](#system-architecture)  
4. [Technology Stack](#technology-stack)  
5. [Core Modules](#core-modules)  
6. [Machine Learning Engine](#machine-learning-engine)  
7. [Geo-Risk Mapping](#geo-risk-mapping)  
8. [Frontend Modules](#frontend-modules)  
9. [Installation](#installation)  
10. [Environment Variables](#environment-variables)  
11. [API Endpoints](#api-endpoints)  
12. [Screenshots (Optional)](#screenshots-optional)  
13. [Future Enhancements](#future-enhancements)  
14. [License](#license)

---

# **Overview**

Veritas Sentinel is designed to detect financial fraud patterns and anomalous transaction behavior by applying Machine Learning, geolocation intelligence, and behavioral analytics.  

The system provides:

- **User Dashboard** for personal transaction monitoring  
- **Admin Dashboard** for organization-wide fraud visibility  
- **Automated alerting** for suspicious activities  
- **Geo-risk heatmaps** showing high-risk regions  
- **Transaction scoring engine** powered by an AI model  

The platform can be integrated with banking systems, payment processors, or digital finance apps.

---

# **Features**

### **User-Facing Features**
✔ Real-time transaction scoring  
✔ Personal risk trend visualization  
✔ Dynamic trust score calculation  
✔ Alert history and event logs  
✔ Create transactions with geo-location & device attributes  

### **Admin-Facing Features**
✔ Organization-wide user management  
✔ Admin-level fraud alerts dashboard  
✔ Geo-risk hotspot visualizations  
✔ High-risk activity breakdown  
✔ Advanced analytics (volume, fraud probability)  
✔ Intelligence module for searching user risk footprint  

### **Security Features**
✔ JWT Authentication  
✔ Role-based access control (Admin/User)  
✔ Server-side validation  
✔ Sanitized inputs and secure database operations  

### **ML Engine**
✔ ML scoring pipeline  
✔ Fraud probability estimation  
✔ Anomaly scoring  
✔ Multi-factor risk classification  

---

# **System Architecture**

```
                    ┌───────────────────────┐
                    │     Frontend UI       │
                    │  (HTML, CSS, JS)      │
                    └──────────┬────────────┘
                               │
                REST API Calls │
                               ▼
               ┌────────────────────────────────┐
               │            Backend API         │
               │            (FastAPI)           │
               ├────────────────────────────────┤
               │  Authentication Module         │
               │  Transaction Engine            │
               │  Alerts & Risk Analysis        │
               │  Geo-Risk Aggregation          │
               │  User Management               │
               └───────────┬─────────┬──────────┘
                           │         │
                           ▼         ▼
              ┌────────────────┐   ┌────────────────┐
              │ ML Engine      │   │ Database       │
              │ (Risk Model)   │   │ MongoDB        │
              └────────────────┘   └────────────────┘
```

---

# **Technology Stack**

### **Frontend**
- HTML5, CSS3  
- Vanilla JavaScript  
- Leaflet.js (Maps)  
- Chart.js (Charts)  

### **Backend**
- **FastAPI**  
- Python 3.10+  
- JWT Authentication  
- Pydantic Models  
- Uvicorn  

### **Database**
- **MongoDB** (Users, Transactions, Alerts)

### **Machine Learning**
- Scikit-Learn / Custom Models  
- Feature Engineering Pipeline  
- Risk Classification & Scoring  

---

# **Core Modules**

## **1. Authentication**
- JWT-based sign-in/sign-up  
- Role-based route protection  
- Secure token validation  
- Password hashing with `passlib`

## **2. User Management**
Admin features include:
- Create user  
- View user list  
- Assign roles  
- Status tracking  
- Risk summary lookup

## **3. Transactions Module**
Handles:
- Transaction creation  
- ML-based scoring  
- Fraud probability  
- Anomaly score  
- Trust score computation  
- History and logs  

## **4. Alerts Engine**
Automatically generates alerts based on:
- High-risk scores  
- Suspicious location patterns  
- Device inconsistency  
- Velocity checks  

Each alert includes:
- Risk level  
- Fraud probability  
- Classification  
- Actions (Resolve, Mark Legit)

## **5. Analytics & Reporting**
Provides insights such as:
- Global risk trends  
- Volume charts  
- High-risk activity distribution  
- Real-time summary metrics  

---

# **Machine Learning Engine**

The ML engine computes:

### **1. Final Risk Score**
Multi-factor fusion of:
- Transaction attributes  
- Behavioral patterns  
- Geolocation data  
- Prior anomalies  
- ML prediction  

### **2. Fraud Probability**
Generated using supervised classification model (Logistic Regression / RandomForest / etc.)

### **3. Anomaly Score**
Computed using:
- Isolation Forest  
- Statistical deviation  
- Outlier detection  

### **4. Trust Score**
Weighted combination of multiple signals:
- Avg risk trend  
- User consistency  
- Historical alerts  
- Transaction behavior  

---

# **Geo-Risk Mapping**

Geo analytics module computes risk heatmaps using:

- Lat/Lon clusters  
- Regional high-risk transactions  
- Velocity risk  
- Aggregated ML scores  

Output includes:
- Dynamic radius scaling  
- Color-coded risk classes  
- Real-time hotspot visualization  
- Interactive map with Leaflet.js  

---

# **Frontend Modules**

## **User Dashboard**
Includes:
- Trust score ring  
- Recent transactions  
- Alert history  
- Risk trend chart  
- Quick metrics  
- New transaction form  

## **Admin Dashboard**
Includes:
- Total users  
- Alerts summary  
- High-risk event timeline  
- Analytics charts  
- Geo-hotspots  
- User intelligence search  
- Create new users  

---

# **Installation**

### **Clone Repository**
```bash
git clone https://github.com/Busted-pinch/Veritas_Sentinel.git
cd Veritas_Sentinel
```

### **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate
# Or for Windows:
venv\Scripts\activate
```

### **Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Start Backend**
```bash
uvicorn backend.app.main:app --reload
```

### **Start Frontend**
Use VSCode Live Server or any static server.

---

# **Environment Variables**

Create a `.env` file:

```
JWT_SECRET_KEY=your_secret_key
MONGO_URI=mongodb://localhost:27017
DB_NAME=veritas_db
```

---

# **API Endpoints**

### **Auth**
- POST `/auth/register`  
- POST `/auth/login`

### **User**
- GET `/api/transactions/me/summary`  
- GET `/api/transactions/me/history`  
- GET `/api/transactions/me/alerts`

### **Admin**
- GET `/api/admin/users`  
- GET `/api/admin/alerts`  
- GET `/api/admin/geo-hotspots`  
- POST `/api/admin/create-user`

### **Transaction**
- POST `/api/transaction/new`

---

# **Future Enhancements**
- LLM-powered fraud explanation  
- Device fingerprinting  
- Real-time WebSocket event streams  
- Vector DB for anomaly search  
- Advanced deep learning models  

---

# **License**
MIT License  
