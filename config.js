// Configuration for the frontend application
// This allows the app to work in different environments (local, Render, etc.)

const config = {
  // Detect if we're running on Render
  isRender: window.location.hostname.includes('onrender.com'),
  
  // API base URL - will be set based on environment
  get apiUrl() {
    if (this.isRender) {
      // On Render, we need to point to the backend service
      // Replace 'invoice-extractor-api' with your actual Render service name
      return 'https://invoice-extractor-api.onrender.com';
    } else {
      // Local development
      return 'http://localhost:5000';
    }
  }
};

// Export for use in other files
window.APP_CONFIG = config;