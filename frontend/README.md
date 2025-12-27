# GROSINT Profiler UI

A comprehensive intelligence dashboard for profiling subjects using social media and web data.

## Features

- **Profile Creation**: Submit URLs from Instagram, Facebook, Twitter, and blogs
- **Dashboard**: View all profiles with filtering and search
- **Detailed Analysis**:
  - Profile traits visualization
  - Activity timeline
  - Network graphs
  - Risk indicators
  - Raw data viewer
- **Real-time Updates**: Automatic polling for in-progress profiles

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running (see main project README)

### Installation

```bash
cd frontend
npm install
```

### Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Update the values:
- `VITE_API_BASE_URL`: Backend API URL (default: `/api/v1`)
- `VITE_API_KEY`: Your API key for authentication

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

The production build will be in the `dist` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/          # Page components
│   ├── services/       # API client
│   ├── types/          # TypeScript types
│   ├── utils/          # Utility functions
│   └── App.tsx         # Main app component
├── public/             # Static assets
└── package.json
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Routing
- **React Query** - Data fetching
- **Recharts** - Data visualization
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

## API Integration

The frontend communicates with the backend API at `/api/v1`. All requests require an `x-api-key` header.

### Endpoints Used

- `POST /api/v1/profiles` - Create new profile
- `GET /api/v1/profiles/{id}` - Get profile status
- `GET /api/v1/profiles/{id}/details` - Get profile details
- `GET /api/v1/profiles/{id}/raw-data` - Get raw scraped data
