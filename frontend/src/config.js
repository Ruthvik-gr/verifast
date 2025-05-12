const environments = {
  development: {
    backendUrl: 'http://localhost:8000',
    wsProtocol: window.location.protocol === 'https:' ? 'wss:' : 'ws:',
    wsUrl: 'localhost:8000'
  },
  production: {
    backendUrl: import.meta.env.VITE_BACKEND_URL || 'https://your-backend-production-url.com',
    wsProtocol: 'wss:',
    wsUrl: import.meta.env.VITE_WS_URL || 'your-backend-production-url.com'
  }
};

const environment = import.meta.env.MODE === 'production' ? 'production' : 'development';

export default environments[environment];
