# RAG Summarizer Frontend

Professional React frontend for the RAG Customer Support Summarizer.

## Features

- Clean, professional UI (no emojis)
- Real-time summarization
- Multiple pipeline modes
- Performance metrics visualization
- Responsive design

## Setup

### Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Open http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Serve build folder
npx serve -s build
```

### Docker

```bash
# Build Docker image
docker build -t rag-summarizer-frontend .

# Run container
docker run -p 3000:80 rag-summarizer-frontend
```

## Environment Variables

Create `.env` file:

```
REACT_APP_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── App.jsx          # Main application
│   ├── index.js         # Entry point
│   ├── index.css        # Global styles
│   └── services/
│       └── api.js       # API client
├── package.json
├── tailwind.config.js
└── postcss.config.js
```

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

## API Integration

The frontend connects to the backend API at `http://localhost:8000` by default.

Configure via `REACT_APP_API_URL` environment variable.