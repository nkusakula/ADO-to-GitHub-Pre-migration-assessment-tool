import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  GitBranch, FileCode, Workflow, ListChecks, Settings,
  ArrowRight, RefreshCw, AlertTriangle, CheckCircle
} from 'lucide-react';

interface ScanResults {
  summary: {
    total_projects: number;
    total_repositories: number;
    total_pipelines: number;
    total_work_items: number;
    complexity: {
      overall: number;
      rating: string;
      repositories: { rating: string; score: number };
      pipelines: { rating: string; score: number };
      work_items: { rating: string; score: number };
    };
    blockers: string[];
  };
}

function StatCard({ 
  icon: Icon, 
  label, 
  value, 
  rating, 
  color 
}: { 
  icon: React.ElementType; 
  label: string; 
  value: string | number; 
  rating?: string;
  color: string;
}) {
  const ratingColors: Record<string, string> = {
    Low: 'text-green-400 bg-green-900/30',
    Medium: 'text-yellow-400 bg-yellow-900/30',
    High: 'text-red-400 bg-red-900/30',
  };

  return (
    <div className="bg-github-dark rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm mb-1">{label}</p>
          <p className="text-3xl font-bold text-white">{value.toLocaleString()}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      {rating && (
        <div className="mt-4">
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${ratingColors[rating]}`}>
            {rating} Complexity
          </span>
        </div>
      )}
    </div>
  );
}

function ComplexityMeter({ score, rating }: { score: number; rating: string }) {
  return (
    <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
      <h3 className="text-lg font-semibold text-white mb-4">Overall Migration Complexity</h3>
      <div className="flex items-center gap-6">
        <div className="relative w-32 h-32">
          <svg className="w-full h-full transform -rotate-90">
            <circle cx="64" cy="64" r="56" fill="none" stroke="#21262d" strokeWidth="12" />
            <circle
              cx="64" cy="64" r="56" fill="none"
              stroke={rating === 'Low' ? '#238636' : rating === 'Medium' ? '#f0883e' : '#f85149'}
              strokeWidth="12"
              strokeDasharray={`${score * 3.52} 352`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <span className="text-3xl font-bold text-white">{score}</span>
              <span className="text-gray-400">/100</span>
            </div>
          </div>
        </div>
        <div>
          <p className={`text-2xl font-bold ${
            rating === 'Low' ? 'text-green-400' : 
            rating === 'Medium' ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {rating}
          </p>
          <p className="text-gray-400 text-sm mt-1">
            {rating === 'Low' && 'Migration should be straightforward'}
            {rating === 'Medium' && 'Some challenges expected'}
            {rating === 'High' && 'Complex migration, plan carefully'}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [results, setResults] = useState<ScanResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [configured, setConfigured] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch('/api/config').then(r => r.json()),
      fetch('/api/scan/results').then(r => r.ok ? r.json() : null).catch(() => null),
    ]).then(([config, scan]) => {
      setConfigured(config.configured);
      setResults(scan);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-gray-400 animate-spin" />
      </div>
    );
  }

  if (!configured) {
    return (
      <div className="text-center py-16">
        <Settings className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Welcome!</h2>
        <p className="text-gray-400 mb-6">Configure your Azure DevOps connection to get started.</p>
        <Link
          to="/configure"
          className="inline-flex items-center gap-2 bg-ado-blue hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          <Settings className="w-5 h-5" />
          Configure Connection
        </Link>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="text-center py-16">
        <GitBranch className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Ready to Scan</h2>
        <p className="text-gray-400 mb-6">Scan your Azure DevOps organization to see migration assessment.</p>
        <Link
          to="/scan"
          className="inline-flex items-center gap-2 bg-github-green hover:bg-green-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          <RefreshCw className="w-5 h-5" />
          Start Scan
        </Link>
      </div>
    );
  }

  const { summary } = results;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Migration Dashboard</h1>
        <div className="flex gap-3">
          <Link
            to="/scan"
            className="inline-flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Rescan
          </Link>
          <Link
            to="/migrate"
            className="inline-flex items-center gap-2 bg-github-green hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
          >
            Start Migration
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={GitBranch}
          label="Repositories"
          value={summary.total_repositories}
          rating={summary.complexity.repositories.rating}
          color="bg-blue-900/30 text-blue-400"
        />
        <StatCard
          icon={Workflow}
          label="Pipelines"
          value={summary.total_pipelines}
          rating={summary.complexity.pipelines.rating}
          color="bg-purple-900/30 text-purple-400"
        />
        <StatCard
          icon={ListChecks}
          label="Work Items"
          value={summary.total_work_items}
          rating={summary.complexity.work_items.rating}
          color="bg-orange-900/30 text-orange-400"
        />
        <StatCard
          icon={FileCode}
          label="Projects"
          value={summary.total_projects}
          color="bg-cyan-900/30 text-cyan-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ComplexityMeter 
          score={summary.complexity.overall} 
          rating={summary.complexity.rating}
        />
        
        <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            Migration Blockers
          </h3>
          {summary.blockers.length === 0 ? (
            <div className="flex items-center gap-2 text-green-400">
              <CheckCircle className="w-5 h-5" />
              <span>No major blockers identified!</span>
            </div>
          ) : (
            <ul className="space-y-2">
              {summary.blockers.map((blocker, i) => (
                <li key={i} className="flex items-start gap-2 text-gray-300">
                  <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{blocker}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
