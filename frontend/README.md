# DataBento Price Monitor - Frontend

React + TypeScript + Vite frontend for real-time price monitoring.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool and dev server
- **EventSource API** - Native SSE support

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
frontend/
├── public/           # Static assets
├── src/
│   ├── components/   # React components
│   │   ├── PriceMonitor.tsx
│   │   └── PriceMonitor.css
│   ├── App.tsx       # Main app component
│   ├── App.css       # App styles
│   ├── main.tsx      # Entry point
│   └── index.css     # Global styles
├── index.html        # HTML template
├── package.json      # Dependencies
├── tsconfig.json     # TypeScript config
└── vite.config.ts    # Vite config
```

## Features

- Real-time price streaming via SSE
- Multiple symbol monitoring
- Auto-reconnect on connection loss
- Responsive grid layout
- Live bid/ask spreads
- Connection status indicator

## Configuration

The frontend connects to the backend at `http://localhost:8000` by default.

To change the backend URL, modify the URL in `src/components/PriceMonitor.tsx:77`:

```typescript
const url = `http://your-backend-url/stream/prices?symbols=${encodeURIComponent(symbols)}`;
```

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Browser Support

Requires browsers with EventSource API support:
- Chrome/Edge 6+
- Firefox 6+
- Safari 5+
- Opera 11+
