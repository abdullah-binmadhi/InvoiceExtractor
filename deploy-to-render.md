# Deploying InvoiceExtractor to Render

This guide will help you deploy the InvoiceExtractor application to Render.

## Prerequisites
1. A GitHub account
2. A Render account (free tier available)

## Deployment Steps

### 1. Fork the Repository
1. Go to your GitHub account
2. Fork this repository to your account

### 2. Create Render Account
1. Visit https://render.com/
2. Sign up for a free account
3. Verify your email address

### 3. Connect GitHub to Render
1. In Render dashboard, click "Connect Account" under GitHub
2. Authorize Render to access your GitHub repositories

### 4. Deploy Using Blueprint (Recommended)
1. In Render dashboard, click "New +" > "Blueprint"
2. Select your forked repository
3. Choose the `render.yaml` file
4. Click "Apply"
5. Wait for both services to deploy

### 5. Configure Environment Variables
1. Go to the `invoice-extractor-api` service
2. Click "Environment" > "Add Environment Variable"
3. Add the following variable:
   - Key: `SECRET_KEY`
   - Value: Generate a random secret key (you can use an online password generator)

### 6. Update Frontend Configuration
1. After deployment, note the URL of your backend API service
2. Update `frontend/config.js` with the correct backend URL:
   ```javascript
   get apiUrl() {
     if (this.isRender) {
       // Replace with your actual backend service URL
       return 'https://your-backend-service-name.onrender.com';
     } else {
       // Local development
       return 'http://localhost:5000';
     }
   }
   ```

### 7. Redeploy Frontend
1. After updating the config, commit and push the changes
2. Render will automatically redeploy the frontend

## Accessing Your Application
- Frontend URL: Provided by Render for the frontend service
- Backend API: Provided by Render for the backend service

## Troubleshooting
1. If the application fails to start, check the logs in Render dashboard
2. Make sure all environment variables are set correctly
3. Ensure the build script has execute permissions
4. Check that the frontend is pointing to the correct backend URL

## Limitations
- Render's free tier may have performance limitations
- Cold starts may occur after periods of inactivity
- File processing time may be limited