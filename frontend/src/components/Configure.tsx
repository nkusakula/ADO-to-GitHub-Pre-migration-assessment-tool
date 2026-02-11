import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Settings, Eye, EyeOff, CheckCircle, XCircle, Loader2, ArrowRight } from 'lucide-react';

export default function Configure() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    organization_url: '',
    pat: '',
    github_token: '',
    github_org: '',
  });
  const [showPat, setShowPat] = useState(false);
  const [showGithubToken, setShowGithubToken] = useState(false);
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [currentConfig, setCurrentConfig] = useState<{ configured: boolean; organization_url?: string } | null>(null);

  useEffect(() => {
    fetch('/api/config')
      .then(res => res.json())
      .then(data => {
        setCurrentConfig(data);
        if (data.organization_url) {
          setFormData(prev => ({ ...prev, organization_url: data.organization_url }));
        }
      });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTestResult(null);

    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      
      if (res.ok) {
        const testRes = await fetch('/api/test-connection');
        const testData = await testRes.json();
        setTestResult(testData);
        
        if (testData.success) {
          setTimeout(() => navigate('/scan'), 1500);
        }
      }
    } catch {
      setTestResult({ success: false, message: 'Failed to save configuration' });
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setLoading(true);
    setTestResult(null);
    
    try {
      const res = await fetch('/api/test-connection');
      const data = await res.json();
      setTestResult(data);
    } catch {
      setTestResult({ success: false, message: 'Connection test failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Settings className="w-7 h-7 text-ado-blue" />
          Configuration
        </h1>
        <p className="text-gray-400 mt-2">
          Connect to your Azure DevOps organization and GitHub to enable migration.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <div className="w-6 h-6 bg-ado-blue rounded flex items-center justify-center text-xs font-bold">A</div>
            Azure DevOps
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Organization URL</label>
              <input
                type="url"
                placeholder="https://dev.azure.com/your-org"
                value={formData.organization_url}
                onChange={(e) => setFormData(prev => ({ ...prev, organization_url: e.target.value }))}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-ado-blue"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Personal Access Token (PAT)</label>
              <div className="relative">
                <input
                  type={showPat ? 'text' : 'password'}
                  placeholder="Enter your PAT with read permissions"
                  value={formData.pat}
                  onChange={(e) => setFormData(prev => ({ ...prev, pat: e.target.value }))}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 pr-12 text-white placeholder-gray-500 focus:outline-none focus:border-ado-blue"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPat(!showPat)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                >
                  {showPat ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.605-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.295 24 12c0-6.63-5.37-12-12-12" />
            </svg>
            GitHub (for migration)
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Target Organization</label>
              <input
                type="text"
                placeholder="your-github-org"
                value={formData.github_org}
                onChange={(e) => setFormData(prev => ({ ...prev, github_org: e.target.value }))}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-github-green"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Personal Access Token (optional)</label>
              <div className="relative">
                <input
                  type={showGithubToken ? 'text' : 'password'}
                  placeholder="ghp_..."
                  value={formData.github_token}
                  onChange={(e) => setFormData(prev => ({ ...prev, github_token: e.target.value }))}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 pr-12 text-white placeholder-gray-500 focus:outline-none focus:border-github-green"
                />
                <button
                  type="button"
                  onClick={() => setShowGithubToken(!showGithubToken)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                >
                  {showGithubToken ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
          </div>
        </div>

        {testResult && (
          <div className={`rounded-lg p-4 flex items-center gap-3 ${
            testResult.success ? 'bg-green-900/30 border border-green-800' : 'bg-red-900/30 border border-red-800'
          }`}>
            {testResult.success ? <CheckCircle className="w-5 h-5 text-green-400" /> : <XCircle className="w-5 h-5 text-red-400" />}
            <span className={testResult.success ? 'text-green-400' : 'text-red-400'}>{testResult.message}</span>
          </div>
        )}

        <div className="flex gap-4">
          {currentConfig?.configured && (
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={loading}
              className="flex-1 bg-gray-800 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Test Connection'}
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-ado-blue hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <>Save & Continue <ArrowRight className="w-5 h-5" /></>}
          </button>
        </div>
      </form>
    </div>
  );
}
