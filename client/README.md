# AI-Driven GitHub Alternative Frontend

A modern, AI-powered interface for GitHub that transforms how you interact with your repositories. Built with Next.js 15 and React 19, this application provides intelligent insights, semantic search, and automated summaries to enhance your development workflow.

## ✨ Features

### 🤖 AI-Powered Insights
- **Semantic Search**: Find code, commits, PRs, and issues by meaning, not just keywords
- **Automated Summaries**: AI-generated weekly progress reports without manual writeups
- **Intelligent Q&A**: Ask questions about your codebase and get immediate, context-aware answers
- **Smart Analytics**: Advanced repository metrics and team collaboration insights

### 🎯 Enhanced GitHub Experience
- **Unified Dashboard**: Centralized view of all your repositories and team activity
- **Real-time Updates**: Live synchronization with GitHub data
- **Team Collaboration**: Enhanced visibility into team progress and blockers
- **Repository Management**: Streamlined settings and configuration management

### 🎨 Modern Interface
- **Responsive Design**: Works seamlessly across desktop, tablet, and mobile devices
- **Dark/Light Mode**: Automatic theme switching based on user preference
- **Accessibility**: Full keyboard navigation and screen reader support
- **Fast Performance**: Optimized loading with Suspense and lazy loading

## 🚀 Tech Stack

- **Framework**: [Next.js 15](https://nextjs.org/) with App Router
- **Runtime**: [React 19](https://react.dev/) with latest features
- **Language**: [TypeScript](https://www.typescriptlang.org/) for type safety
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) for utility-first styling
- **UI Components**: [Radix UI](https://www.radix-ui.com/) primitives with custom design system
- **Icons**: [Lucide React](https://lucide.dev/) for consistent iconography
- **Forms**: [React Hook Form](https://react-hook-form.com/) validation
- **Charts**: [Recharts](https://recharts.org/) for data visualization
- **Package Manager**: [pnpm](https://pnpm.io/) for efficient dependency management

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: Version 24.0.0 or higher
- **pnpm**: Version 10.0.0 or higher
- **GitHub Personal Access Token**: Required for GitHub API access

### GitHub Personal Access Token Setup

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `read:user` (Read access to user profile data)
   - `read:org` (Read access to organization data)
4. Copy the generated token (you'll need this for the application)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:AET-DevOps25/team-promptheus.git
   cd client
   ```

2. **Install dependencies**
   ```bash
   pnpm install
   ```

3. **Start the development server**
   ```bash
   pnpm dev
   ```

4. **Open your browser**
   Navigate to [http://localhost:8081](http://localhost:8081)

## 🎯 Usage

### Getting Started

1. **Authentication**: Enter your GitHub Personal Access Token on the home page
2. **Dashboard**: View your repositories, team metrics, and recent activity
3. **Search**: Use the semantic search to find anything across your repositories
4. **Q&A**: Ask questions about your codebase and get AI-powered answers
5. **Weekly Summaries**: Review automated progress reports and team insights

### Navigation

- **Home (`/`)**: Landing page and authentication
- **Dashboard (`/dashboard`)**: Main application interface
- **Q&A (`/qa`)**: Repository question and answer interface
- **Settings (`/settings`)**: Repository configuration and preferences
- **Weekly Summary (`/weekly-summary`)**: Detailed progress reports

### Keyboard Shortcuts

- `⌘/Ctrl + K`: Open semantic search modal
- `⌘/Ctrl + /`: Show help and shortcuts
- `Esc`: Close modals and overlays

## 🔧 Development

### Available Scripts

```bash
# Start development server
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Run linting
pnpm lint

# Type checking
pnpm type-check
```

### Project Structure

```
client/
├── app/                    # Next.js App Router pages
│   ├── (dashboard)/       # Dashboard layout group
│   │   ├── dashboard/     # Main dashboard pages
│   │   ├── qa/           # Q&A functionality
│   │   ├── settings/     # Repository settings
│   │   └── weekly-summary/ # Progress reports
│   ├── api/              # API routes
│   └── globals.css       # Global styles
├── components/           # Reusable React components
│   ├── ui/              # Base UI components (Radix + custom)
│   └── *.tsx            # Feature-specific components
├── hooks/               # Custom React hooks
├── lib/                 # Utility functions and configurations
├── public/              # Static assets
└── styles/              # Additional stylesheets
```

### Component Development

We use a design system based on Radix UI primitives. All components are:

- **Accessible**: Following ARIA guidelines and keyboard navigation
- **Composable**: Built with compound component patterns
- **Consistent**: Using shared design tokens and variants
- **Typed**: Full TypeScript support with proper prop types

## 🚀 Deployment

### Docker

```bash
# Build the image
docker build -t client .

# Run the container
docker run -p 8081:8081 client
```

### Manual Deployment

```bash
# Build the application
pnpm build

# Start the production server
pnpm start
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and ensure tests pass
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Code Style

- **ESLint**: Configured with Next.js recommended rules
- **Prettier**: Code formatting (run with `pnpm format`)
- **TypeScript**: Strict mode enabled
- **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/)

## 🔒 Security

- **Authentication**: GitHub Personal Access Tokens are validated client-side
- **API Security**: All GitHub API calls are made directly from the client
- **No Server Storage**: Tokens are not stored on any backend servers
- **HTTPS Only**: All production deployments enforce HTTPS

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

<sub> Built with ❤️ by the Team Promptheus <sub>
