import axios from 'axios';

// Configure API base URL based on environment
const getApiBaseUrl = () => {
  // If REACT_APP_API_URL is explicitly set, use it
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }

  // For production deployment, detect the backend URL
  if (process.env.NODE_ENV === 'production') {
    const currentHost = window.location.hostname;
    const currentProtocol = window.location.protocol;

    // If deployed on co.nnecti.ng, use the same domain for API
    if (currentHost === 'co.nnecti.ng') {
      return `${currentProtocol}//api.co.nnecti.ng`;
    }

    // For other production deployments, assume API is on same host with different port
    return `${currentProtocol}//${currentHost}:5000`;
  }

  // For development, use empty string (relies on proxy)
  return '';
};

const API_BASE_URL = getApiBaseUrl();

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default api;
