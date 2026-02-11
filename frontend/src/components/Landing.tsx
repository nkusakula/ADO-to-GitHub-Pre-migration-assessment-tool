import { useNavigate } from 'react-router-dom';
import { GitBranch, FileCode, ArrowRightLeft, Search, Settings, BarChart3, CheckCircle2 } from 'lucide-react';

export default function Landing() {
  const navigate = useNavigate();

  const features = [
    {
      icon: Settings,
      title: 'Configure',
      description: 'Set up your Azure DevOps and GitHub credentials',
      action: () => navigate('/configure'),
      color: 'text-blue-400'
    },
    {
      icon: Search,
      title: 'Scan',
      description: 'Analyze your ADO organization for migration readiness',
      action: () => navigate('/scan'),
      color: 'text-purple-400'
    },
    {
      icon: BarChart3,
      title: 'Report',
      description: 'View detailed assessment results and complexity analysis',
      action: () => navigate('/report'),
      color: 'text-green-400'
    },
    {
      icon: ArrowRightLeft,
      title: 'Migrate',
      description: 'Execute repository migrations to GitHub',
      action: () => navigate('/migrate'),
      color: 'text-orange-400'
    },
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      {/* Hero Section */}
      <div className="text-center mb-16 max-w-4xl">
        <div className="flex items-center justify-center gap-4 mb-6">
          <GitBranch className="w-16 h-16 text-blue-500" />
          <ArrowRightLeft className="w-12 h-12 text-gray-500" />
          <FileCode className="w-16 h-16 text-green-500" />
        </div>
        
        <h1 className="text-5xl font-bold text-white mb-4">
          ADO Migration Readiness Analyzer
        </h1>
        
        <p className="text-xl text-gray-400 mb-8">
          Analyze your Azure DevOps organization and plan your migration to GitHub with confidence
        </p>

        <div className="flex items-center justify-center gap-4 mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors"
          >
            Go to Dashboard
          </button>
          <button
            onClick={() => navigate('/configure')}
            className="px-8 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-colors"
          >
            Get Started
          </button>
        </div>

        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
          <CheckCircle2 className="w-4 h-4 text-green-500" />
          <span>Built with Copilot CLI</span>
          <span className="mx-2">•</span>
          <CheckCircle2 className="w-4 h-4 text-green-500" />
          <span>FastAPI + React + TypeScript</span>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl w-full">
        {features.map((feature, index) => (
          <div
            key={index}
            onClick={feature.action}
            className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:bg-gray-750 hover:border-gray-600 cursor-pointer transition-all hover:shadow-lg"
          >
            <feature.icon className={`w-12 h-12 ${feature.color} mb-4`} />
            <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
            <p className="text-gray-400 text-sm">{feature.description}</p>
          </div>
        ))}
      </div>

      {/* Info Section */}
      <div className="mt-16 max-w-4xl">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-white mb-4">What You Can Do</h2>
          <ul className="space-y-3 text-gray-300">
            <li className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Discover all projects, repositories, pipelines, and work items in your ADO organization</span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Analyze compatibility and get complexity scores for each asset type</span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Generate comprehensive reports in multiple formats (HTML, JSON, console)</span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Migrate repositories directly to GitHub using the integrated migration tool</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
