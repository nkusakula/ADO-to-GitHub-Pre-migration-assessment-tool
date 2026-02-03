import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, CheckCircle, Loader2, FolderGit2, AlertCircle } from 'lucide-react';

interface ScanProgress {
  status: string;
  progress: number;
  current_project?: string;
  projects_scanned?: number;
  total_projects?: number;
  error?: string;
  in_progress?: boolean;
}

export default function Scan() {
  const navigate = useNavigate();
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [selectedProject, setSelectedProject] = useState('');
  const [projects, setProjects] = useState<{ name: string; description: string }[]>([]);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetch('/api/test-connection')
      .then(res => res.json())
      .then(data => {
        if (data.projects) setProjects(data.projects);
      });

    // Check if scan already in progress
    fetch('/api/scan/status')
      .then(res => res.json())
      .then(data => {
        if (data.in_progress) {
          setScanning(true);
          setProgress(data);
          startPolling();
        }
      });

    return () => { 
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const startPolling = () => {
    // Clear any existing polling
    if (pollingRef.current) clearInterval(pollingRef.current);
    
    pollingRef.current = setInterval(() => {
      fetch('/api/scan/status')
        .then(res => res.json())
        .then(data => {
          console.log('Poll result:', data);
          setProgress(data);
          
          if (data.status === 'completed') {
            if (pollingRef.current) clearInterval(pollingRef.current);
            setScanning(false);
            setTimeout(() => navigate('/'), 1000);
          } else if (data.status === 'failed' || (!data.in_progress && data.status !== 'starting')) {
            if (pollingRef.current) clearInterval(pollingRef.current);
            setScanning(false);
          }
        })
        .catch(err => {
          console.error('Poll error:', err);
        });
    }, 1000);
  };

  const startScan = async () => {
    setScanning(true);
    setProgress({ status: 'starting', progress: 0 });

    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project: selectedProject || null }),
      });
      
      if (response.ok) {
        // Start polling for progress
        startPolling();
      } else {
        const error = await response.json();
        setScanning(false);
        setProgress({ status: 'failed', progress: 0, error: error.detail || 'Failed to start scan' });
      }
    } catch (err) {
      setScanning(false);
      setProgress({ status: 'failed', progress: 0, error: 'Failed to start scan' });
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Search className="w-7 h-7 text-github-green" />
          Scan Organization
        </h1>
        <p className="text-gray-400 mt-2">Analyze your Azure DevOps organization for migration readiness.</p>
      </div>

      {!scanning ? (
        <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">Project Filter (optional)</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-github-green"
            >
              <option value="">All Projects</option>
              {projects.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
            </select>
          </div>
          <button
            onClick={startScan}
            className="w-full bg-github-green hover:bg-green-600 text-white px-6 py-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            <Search className="w-5 h-5" />
            Start Scan
          </button>
        </div>
      ) : (
        <div className="bg-github-dark rounded-xl p-8 border border-gray-800">
          {progress?.status === 'completed' ? (
            <div className="text-center">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h2 className="text-xl font-bold text-white mb-2">Scan Complete!</h2>
              <p className="text-gray-400">Redirecting to dashboard...</p>
            </div>
          ) : progress?.status === 'failed' ? (
            <div className="text-center">
              <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <h2 className="text-xl font-bold text-white mb-2">Scan Failed</h2>
              <p className="text-red-400">{progress.error}</p>
              <button onClick={() => { setScanning(false); setProgress(null); }} className="mt-4 bg-gray-800 hover:bg-gray-700 text-white px-6 py-2 rounded-lg">
                Try Again
              </button>
            </div>
          ) : (
            <div>
              <div className="flex items-center gap-4 mb-6">
                <Loader2 className="w-8 h-8 text-github-green animate-spin" />
                <div>
                  <h2 className="text-lg font-semibold text-white">Scanning...</h2>
                  {progress?.current_project && (
                    <p className="text-gray-400 text-sm flex items-center gap-2">
                      <FolderGit2 className="w-4 h-4" />
                      {progress.current_project}
                    </p>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Progress</span>
                  <span className="text-white font-medium">{progress?.projects_scanned ?? 0} / {progress?.total_projects ?? '?'} projects</span>
                </div>
                <div className="h-3 bg-gray-900 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-github-green to-green-400 transition-all duration-300 progress-stripe" style={{ width: `${progress?.progress ?? 0}%` }} />
                </div>
                <p className="text-center text-gray-500 text-sm">{progress?.progress ?? 0}%</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
