# 🚀 co.nnecti.ng Deployment Guide

## 🎯 Quick Fix for Current Issue

Your frontend is trying to connect to `localhost:5000` in production. Here's how to fix it:

### Step 1: Update Environment Variables

Create or update `frontend/.env.production` with your actual backend URL:

```bash
# Replace with your actual backend URL
REACT_APP_API_URL=https://your-backend-domain.com
# OR if backend is on same server with different port:
REACT_APP_API_URL=https://co.nnecti.ng:5000
# OR if using subdomain:
REACT_APP_API_URL=https://api.co.nnecti.ng
```

### Step 2: Rebuild Frontend

```bash
cd frontend
npm run build
```

### Step 3: Update Flask CORS Configuration

In your `app/__init__.py`, update the CORS origins to include your production domain:

```python
# Configure CORS
cors.init_app(app, 
              origins=[
                  "https://localhost:8443", 
                  "http://localhost:3000",
                  "https://co.nnecti.ng",        # Your production domain
                  "http://co.nnecti.ng",         # HTTP version
                  "https://api.co.nnecti.ng"     # If using subdomain
              ],
              supports_credentials=True,
              allow_headers=["Content-Type", "Authorization"],
              methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
```

### Step 4: Deploy Updated Files

1. Upload the new `frontend/build` directory to your web server
2. Restart your Flask backend with the updated CORS configuration

## 🏗️ Complete Deployment Architecture

### Recommended Setup

```
https://co.nnecti.ng          → Frontend (React build)
https://api.co.nnecti.ng      → Backend (Flask API)
```

### Alternative Setup (Same Domain)

```
https://co.nnecti.ng          → Frontend (React build)
https://co.nnecti.ng:5000     → Backend (Flask API)
```

## 🔧 Environment Configuration

### Frontend Environment Files

**`.env.production`** (for production builds):
```
REACT_APP_API_URL=https://api.co.nnecti.ng
GENERATE_SOURCEMAP=false
```

**`.env.local`** (for local development):
```
REACT_APP_API_URL=http://localhost:5000
```

### Backend Environment

Update your Flask `.env` file:
```
SECRET_KEY=your-production-secret-key
DATABASE_URL=your-production-database-url
FLASK_ENV=production
```

## 🚀 Deployment Commands

### Build for Production
```bash
# Option 1: Use environment file
cd frontend && npm run build

# Option 2: Set environment variable
cd frontend && REACT_APP_API_URL=https://api.co.nnecti.ng npm run build

# Option 3: Use build script
./scripts/build-production.sh
```

### Deploy Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python init_db.py

# Start production server
python app.py
```

## 🔍 Troubleshooting

### CORS Errors
- Ensure your Flask backend includes your production domain in CORS origins
- Check that the API URL in frontend matches your actual backend URL
- Verify your backend is accessible from the frontend domain

### API Connection Issues
- Check browser developer tools → Network tab for failed requests
- Verify the API URL is correct in the frontend build
- Test API endpoints directly with curl or Postman

### Environment Variables Not Working
- Ensure environment variables start with `REACT_APP_`
- Rebuild the frontend after changing environment variables
- Check that `.env.production` is in the `frontend/` directory

## 📋 Deployment Checklist

- [ ] Update `REACT_APP_API_URL` in `.env.production`
- [ ] Add production domain to Flask CORS configuration
- [ ] Rebuild frontend with production environment
- [ ] Upload frontend build to web server
- [ ] Deploy Flask backend with updated CORS
- [ ] Test login and API functionality
- [ ] Verify Socket.IO connections work
- [ ] Check all features work in production

## 🌐 Web Server Configuration

### Nginx Example
```nginx
# Frontend
server {
    listen 443 ssl;
    server_name co.nnecti.ng;
    
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }
}

# Backend API
server {
    listen 443 ssl;
    server_name api.co.nnecti.ng;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔐 Security Notes

- Use HTTPS in production
- Set secure session cookies in Flask
- Use environment variables for sensitive data
- Enable CORS only for trusted domains
- Use strong secret keys for production
