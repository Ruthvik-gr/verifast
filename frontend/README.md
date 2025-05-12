# News RAG Chatbot - Frontend

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![React](https://img.shields.io/badge/react-18.0.0-blue.svg)
![Vite](https://img.shields.io/badge/vite-4.0.0-blue.svg)

The frontend component of the News RAG Chatbot application, built with React and Vite, providing a modern and responsive user interface for interacting with the news-based chatbot.

## Features

- **💬 Real-time Chat Interface**: Smooth messaging experience with token-by-token streaming
- **🔄 WebSocket Integration**: Real-time communication with the backend
- **📱 Responsive Design**: Works on desktop and mobile devices
- **🌙 Dark Mode Support**: Comfortable viewing experience in any lighting condition
- **⚡ Vite-powered**: Fast development and optimized production builds

## Architecture

The frontend is built with modern web technologies:

1. **React**: Component-based UI library
2. **Vite**: Next-generation frontend tooling
3. **WebSockets**: Real-time communication with the backend
4. **CSS Modules**: Scoped styling for components
5. **Environment Configuration**: Support for development and production environments

## Prerequisites

- **Node.js 16+**
- **npm** or **yarn**

## Installation

1. Install dependencies:

```bash
npm install
# or
yarn install
```

2. Create environment files for development and production:

For development (`.env.development`):
```
VITE_BACKEND_URL=http://localhost:8000
VITE_WS_URL=localhost:8000
```

For production (`.env.production`):
```
VITE_BACKEND_URL=https://your-backend-production-url.com
VITE_WS_URL=your-backend-production-url.com
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `VITE_BACKEND_URL` | URL of the backend API | http://localhost:8000 |
| `VITE_WS_URL` | WebSocket URL for real-time communication | localhost:8000 |

## Usage

### Development Mode

Start the development server:

```bash
npm run dev
# or
yarn dev
```

The development server will be available at http://localhost:5173.

### Production Build

Create a production build:

```bash
npm run build
# or
yarn build
```

Preview the production build:

```bash
npm run preview
# or
yarn preview
```

## Docker Deployment

You can build and run the frontend using Docker:

```bash
docker build -t news-rag-frontend .
docker run -p 80:80 news-rag-frontend
```

The Docker image uses Nginx to serve the static files and proxy API requests to the backend.

## Project Structure

```
frontend/
├── public/           # Static assets
├── src/
│   ├── components/   # React components
│   ├── styles/       # CSS styles
│   ├── App.jsx       # Main application component
│   ├── config.js     # Environment configuration
│   └── main.jsx      # Entry point
├── .env.development  # Development environment variables
├── .env.production   # Production environment variables
├── Dockerfile        # Docker configuration
├── nginx.conf        # Nginx configuration for Docker
└── package.json      # Dependencies and scripts
```

## Customization

You can customize the frontend by:

1. Modifying the components in the `src/components` directory
2. Updating the styles in the `src/styles` directory
3. Changing the environment variables in the `.env` files

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
