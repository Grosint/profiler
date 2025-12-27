import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Plus, Search } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-dark-950">
      {/* Header */}
      <header className="bg-dark-900 border-b border-dark-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-8">
              <Link to="/" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <Search className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-dark-100">GROSINT Profiler</span>
              </Link>
              <nav className="hidden md:flex space-x-1">
                <Link
                  to="/"
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive('/')
                      ? 'bg-dark-800 text-primary-400'
                      : 'text-dark-400 hover:text-dark-200 hover:bg-dark-800'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4 inline mr-2" />
                  Dashboard
                </Link>
                <Link
                  to="/create"
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive('/create')
                      ? 'bg-dark-800 text-primary-400'
                      : 'text-dark-400 hover:text-dark-200 hover:bg-dark-800'
                  }`}
                >
                  <Plus className="w-4 h-4 inline mr-2" />
                  New Profile
                </Link>
              </nav>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
