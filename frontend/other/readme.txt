# Veritas Sentinel - Frontend Setup Guide

## 🎨 Overview

This is a modern, production-ready frontend for the Veritas Sentinel fraud detection system. The UI features:

- **Advanced Dashboard Analytics** with real-time charts
- **Geographic Risk Mapping** using Leaflet.js
- **AI-Powered Intelligence Analysis**
- **Responsive Design** that works on all devices
- **Modern Gradient UI** with smooth animations
- **Zero Sample Data** - all data comes from your backend API

## 📁 File Structure

```
frontend/
├── login.html                  # Login page
├── admin_dashboard.html        # Admin dashboard
├── user_dashboard.html         # User dashboard
├── css/
│   ├── login.css              # Login styles
│   ├── admin_dashboard.css    # Admin dashboard styles
│   └── user_dashboard.css     # User dashboard styles
└── js/
    ├── login.js               # Login logic
    ├── admin_dashboard.js     # Admin dashboard logic (includes alerts & intel)
    ├── admin_dashboard_alerts.js  # Alert management functions
    └── user_dashboard.js      # User dashboard logic
```

## 🚀 Quick Start

### 1. Setup Directory Structure

Create the following structure in your project root:

```bash
mkdir -p frontend/css frontend/js
```

### 2. Place Files

- Place all `.html` files in the `frontend/` directory
- Place all `.css` files in the `frontend/css/` directory
- Place all `.js` files in the `frontend/js/` directory

### 3. Configure API Endpoint

In **all JavaScript files**, update the API_BASE constant to match your backend URL:

```javascript
const API_BASE = 'http://localhost:8000';  // Change this if your backend runs on a different port
```

Files to update:
- `js/login.js`
- `js/admin_dashboard.js`
- `js/admin_dashboard_alerts.js` (if separated)
- `js/user_dashboard.js`

### 4. Serve the Frontend

You can use any static file server. Here are a few options:

**Option A: Python HTTP Server**
```bash
cd frontend
python -m http.server 5173
```

**Option B: Node.js http-server**
```bash
npm install -g http-server
cd frontend
http-server -p 5173
```

**Option C: VS Code Live Server**
Install the "Live Server" extension and right-click on `login.html` → "Open with Live Server"

### 5. Access the Application

Open your browser and navigate to:
```
http://localhost:5173/login.html
```

## 👥 User Roles & Features

### Admin Dashboard Features

1. **Overview Page**
   - Total users count
   - Open alerts count
   - Daily transaction metrics
   - Average risk score
   - Global risk trend chart (30 days)
   - Risk level distribution pie chart

2. **Users Page**
   - List all users with search
   - View user details
   - Quick access to user intelligence

3. **Analytics Page**
   - Interactive geographic risk hotspots map
   - Daily transaction volume chart
   - Fraud probability trends
   - Configurable time ranges (7/30/90 days)

4. **Alerts Page**
   - View all security alerts
   - Filter by status (open/closed/confirmed/false positive)
   - Resolve alerts with notes
   - Real-time alert count badge

5. **Intelligence Page**
   - Deep-dive user analysis
   - AI-powered behavior summary
   - Speculation score with indicators
   - Investigation case files
   - 30-day risk trend visualization
   - Recent transactions & alerts

### User Dashboard Features

1. **Dashboard**
   - Animated trust score badge
   - Personal transaction statistics
   - 30-day risk trend chart
   - Security status overview

2. **New Transaction**
   - Create new transactions
   - Real-time risk analysis
   - Detailed risk scoring breakdown
   - Visual feedback on transaction safety

## 🔐 Authentication Flow

1. **Login** → User enters email and password
2. **Backend Validation** → OAuth2 password flow
3. **Token Storage** → JWT token saved in localStorage
4. **Role-Based Redirect**:
   - Admin → `admin_dashboard.html`
   - User → `user_dashboard.html`
5. **Auto-Logout** → On 401 errors or manual logout

## 🎨 Design Features

### Color Scheme
- Primary: `#6366f1` (Indigo)
- Success: `#10b981` (Green)
- Danger: `#ef4444` (Red)
- Warning: `#f59e0b` (Amber)

### Animations
- Page transitions: Fade in with slide up
- Card hover effects: Lift with shadow
- Button interactions: Press effect with glow
- Chart animations: Smooth data transitions
- Loader: Spinning ring with backdrop blur

### Responsive Breakpoints
- Desktop: > 1024px
- Tablet: 768px - 1024px
- Mobile: < 768px

## 📊 Charts & Visualizations

### Chart.js Implementation

All charts use Chart.js v4.4.0 with:
- Smooth line curves (tension: 0.4)
- Fill areas with transparency
- Responsive sizing
- Interactive tooltips
- Legend positioning

### Leaflet Maps

Geographic hotspots use Leaflet.js with:
- OpenStreetMap tiles
- Circle markers sized by transaction count
- Color-coded by risk level
- Interactive popups with metrics

## 🔧 API Integration

### Endpoints Used

**Authentication:**
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user

**Admin:**
- `GET /api/admin/users` - List users
- `GET /api/admin/alerts` - List alerts
- `PATCH /api/admin/alerts/{alert_id}` - Resolve alert
- `GET /api/admin/risk-trend-global` - Global risk trends
- `GET /api/admin/geo-hotspots` - Geographic hotspots

**Agent/Intelligence:**
- `POST /api/agent/intel` - User intelligence
- `GET /api/agent/risk-trend/{user_id}` - User risk trend

**User:**
- `POST /api/transaction/new` - Create transaction

### Error Handling

The frontend handles:
- 401 Unauthorized → Auto-logout
- Network errors → User-friendly notifications
- Empty data → Graceful fallback messages
- Invalid responses → Console logging + alerts

## 🐛 Troubleshooting

### CORS Issues

If you see CORS errors, ensure your backend has proper CORS configuration:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Charts Not Rendering

1. Check browser console for errors
2. Verify Chart.js is loaded: Check for `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>`
3. Ensure data is being fetched from API

### Map Not Loading

1. Verify Leaflet CSS is loaded
2. Check for JavaScript errors in console
3. Ensure geo data from API includes valid lat/lon

### Login Not Working

1. Check API_BASE URL in `js/login.js`
2. Verify backend is running
3. Check browser console for errors
4. Verify credentials are correct

## 🚀 Production Deployment

### Before Deployment:

1. **Update API URLs** in all JS files to production backend URL
2. **Minify Assets**:
   ```bash
   # Minify CSS
   npx csso css/login.css -o css/login.min.css
   
   # Minify JS
   npx terser js/login.js -o js/login.min.js
   ```
3. **Update HTML** to reference minified files
4. **Add Analytics** (optional)
5. **Configure CDN** for static assets

### Deployment Options:

- **Netlify**: Drag & drop the `frontend` folder
- **Vercel**: Connect GitHub repo
- **AWS S3 + CloudFront**: For scalable hosting
- **Traditional Hosting**: Upload via FTP

## 📝 Customization

### Changing Colors

Edit CSS variables in each `.css` file:

```css
:root {
    --primary: #6366f1;    /* Change to your brand color */
    --success: #10b981;
    --danger: #ef4444;
    /* ... other colors */
}
```

### Adding New Pages

1. Create HTML file in `frontend/`
2. Create corresponding CSS in `css/`
3. Create corresponding JS in `js/`
4. Add navigation link in sidebar
5. Update page content system

### Modifying Charts

Charts are configured in the respective JS files. Look for functions like:
- `renderRiskTrendChart()`
- `renderRiskDistributionChart()`
- `renderGeoMap()`

## 📚 Dependencies

### CDN Resources:
- **Chart.js 4.4.0**: Charts and graphs
- **Leaflet 1.9.4**: Interactive maps

### Fonts:
- **Inter**: System fallback for clean typography

## 🎯 Best Practices

1. **Always test with real backend** - No sample data in code
2. **Check console** for errors during development
3. **Use browser DevTools** to debug API calls
4. **Test on multiple screen sizes** for responsiveness
5. **Clear localStorage** if experiencing auth issues

## 📞 Support

For issues or questions:
1. Check browser console for errors
2. Verify backend is running and accessible
3. Review API endpoint configuration
4. Check CORS settings

## 🎉 Features Highlights

✅ **No Sample Data** - All data from API  
✅ **Real-time Updates** - Refresh button on all pages  
✅ **Responsive Design** - Works on all devices  
✅ **Modern UI** - Gradients, animations, shadows  
✅ **Error Handling** - Graceful degradation  
✅ **Role-Based Access** - Admin vs User views  
✅ **Interactive Charts** - Hover, zoom, legend  
✅ **Geographic Mapping** - Risk hotspot visualization  
✅ **AI Integration** - LLM-powered insights  

---

**Built with ❤️ for Veritas Sentinel**