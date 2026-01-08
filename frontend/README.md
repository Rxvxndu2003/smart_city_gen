# Smart City Planning System - Frontend

React + TypeScript frontend for the AI-powered urban planning system.

## Features

- **React 18** with TypeScript
- **Vite** for fast development and building
- **TailwindCSS** for styling
- **React Router** for navigation
- **Zustand** for state management
- **React Query** for data fetching
- **Babylon.js** for 3D visualization
- **Google Maps API** integration
- **Role-based access control** with route guards

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `VITE_API_BASE_URL`: Backend API URL
- `VITE_GOOGLE_MAPS_API_KEY`: Google Maps API key

### 3. Run Development Server

```bash
npm run dev
```

Application will be available at: `http://localhost:5173`

### 4. Build for Production

```bash
npm run build
# Output will be in the dist/ directory
```

## Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── common/        # Buttons, inputs, modals, etc.
│   │   ├── layout/        # Header, sidebar, footer
│   │   ├── maps/          # Google Maps components
│   │   ├── viewer3d/      # Babylon.js 3D viewer
│   │   ├── projects/      # Project-related components
│   │   └── approvals/     # Approval workflow components
│   ├── pages/             # Page components
│   │   ├── public/        # Landing, login, register
│   │   ├── dashboard/     # Main dashboard
│   │   ├── projects/      # Project pages
│   │   └── admin/         # Admin panel pages
│   ├── services/          # API client services
│   ├── store/             # Zustand state management
│   ├── hooks/             # Custom React hooks
│   ├── guards/            # Route protection guards
│   ├── types/             # TypeScript type definitions
│   ├── utils/             # Utility functions
│   └── styles/            # Global styles
├── public/                # Static assets
└── index.html            # HTML entry point
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Lint code with ESLint

## Key Features

### Authentication
- Login and registration pages
- JWT token management
- Automatic token refresh
- Route guards for protected pages

### Role-Based Access
- Admin panel for user management
- Role-specific navigation and features
- Permission-based UI rendering

### Dashboard
- User-specific dashboard
- Quick access to projects and features
- Role-based action cards

### Admin Panel
- User management (create, edit, delete)
- Role assignment
- System statistics
- Approval workflow monitoring

## Development Guidelines

### Code Style
- Use TypeScript for type safety
- Follow React functional component patterns
- Use Tailwind CSS utility classes
- Keep components small and focused

### State Management
- Use Zustand for global state
- Use React Query for server state
- Keep local state minimal

### API Integration
- All API calls go through service files
- Use axios interceptors for auth
- Handle errors consistently

## Deployment

### Build

```bash
npm run build
```

### Serve with nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## License

Proprietary - All rights reserved
