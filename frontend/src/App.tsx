import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import {
  Search, GitBranch, FileCode, Settings, Home,
  ArrowRightLeft, BarChart3, CheckCircle2, AlertCircle
} from 'lucide-react';
import Landing from './components/Landing';
import Dashboard from './components/Dashboard';
import Configure from './components/Configure';
import Scan from './components/Scan';
import Migrate from './components/Migrate';
import Report from './components/Report';

function Navigation() {
  const location = useLocation();
  
  // Don't show nav on landing page
  if (location.pathname === '/') return null;
  
  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/dashboard', icon: BarChart3, label: 'Dashboard' },
    { path: '/configure', icon: Settings, label: 'Configure' },
    { path: '/scan', icon: Search, label: 'Scan' },
    { path: '/migrate', icon: ArrowRightLeft, label: 'Migrate' },
    { path: '/report', icon: BarChart3, label: 'Report' },
  ];

  return (
    <nav className="bg-github-dark border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 text-white font-bold text-lg">
              <GitBranch className="w-6 h-6 text-ado-blue" />
              <span>ADO</span>
              <ArrowRightLeft className="w-4 h-4 text-gray-500" />
              <FileCode className="w-6 h-6 text-github-green" />
              <span>GitHub</span>
            </div>
          </div>
          
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}

function StatusBanner() {
  const location = useLocation();
  const [status, setStatus] = useState<{configured: boolean; connected: boolean} | null>(null);

  useEffect(() => {
    // Don't fetch on landing page
    if (location.pathname === '/') return;
    
    fetch('/api/config')
      .then(res => res.json())
      .then(data => {
        setStatus({ configured: data.configured, connected: false });
        if (data.configured) {
          fetch('/api/test-connection')
            .then(res => res.json())
            .then(conn => setStatus({ configured: true, connected: conn.success }));
        }
      })
      .catch(() => setStatus({ configured: false, connected: false }));
  }, [location.pathname]);

  // Don't show banner on landing page
  if (location.pathname === '/') return null;

  if (!status) return null;

  if (!status.configured) {
    return (
      <div className="bg-yellow-900/30 border-b border-yellow-800 px-4 py-2">
        <div className="max-w-7xl mx-auto flex items-center gap-2 text-yellow-400 text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>Not configured.</span>
          <Link to="/configure" className="underline hover:text-yellow-300">
            Configure now →
          </Link>
        </div>
      </div>
    );
  }

  if (status.configured && status.connected) {
    return (
      <div className="bg-green-900/30 border-b border-green-800 px-4 py-2">
        <div className="max-w-7xl mx-auto flex items-center gap-2 text-green-400 text-sm">
          <CheckCircle2 className="w-4 h-4" />
          <span>Connected to Azure DevOps</span>
        </div>
      </div>
    );
  }

  return null;
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-github-darker">
        <Navigation />
        <StatusBanner />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={
            <main className="max-w-7xl mx-auto px-4 py-8">
              <Dashboard />
            </main>
          } />
          <Route path="/configure" element={
            <main className="max-w-7xl mx-auto px-4 py-8">
              <Configure />
            </main>
          } />
          <Route path="/scan" element={
            <main className="max-w-7xl mx-auto px-4 py-8">
              <Scan />
            </main>
          } />
          <Route path="/migrate" element={
            <main className="max-w-7xl mx-auto px-4 py-8">
              <Migrate />
            </main>
          } />
          <Route path="/report" element={
            <main className="max-w-7xl mx-auto px-4 py-8">
              <Report />
            </main>
          } />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
