import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRightLeft, GitBranch, CheckCircle, XCircle, Loader2, AlertCircle, Search, Check } from 'lucide-react';

interface Repo { project: string; name: string; id: string; size: number; url: string; }
interface MigrationStatus { status: string; repos: Record<string, { status: string; progress: number; message: string }>; error?: string; }

export default function Migrate() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [selectedRepos, setSelectedRepos] = useState<Set<string>>(new Set());
  const [targetOrg, setTargetOrg] = useState('');
  const [visibility, setVisibility] = useState('private');
  const [loading, setLoading] = useState(true);
  const [migrating, setMigrating] = useState(false);
  const [migrationStatus, setMigrationStatus] = useState<MigrationStatus | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    fetch('/api/repos').then(res => res.ok ? res.json() : { repos: [] }).then(data => { setRepos(data.repos || []); setLoading(false); }).catch(() => setLoading(false));
    fetch('/api/config').then(res => res.json()).then(data => { if (data.github_org) setTargetOrg(data.github_org); });
    return () => { wsRef.current?.close(); };
  }, []);

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/progress`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'migration') {
        setMigrationStatus(data);
        if (data.status === 'completed' || data.status === 'failed') setMigrating(false);
      }
    };
    wsRef.current = ws;
  };

  const toggleRepo = (name: string) => {
    const newSelected = new Set(selectedRepos);
    if (newSelected.has(name)) newSelected.delete(name); else newSelected.add(name);
    setSelectedRepos(newSelected);
  };

  const startMigration = async () => {
    if (selectedRepos.size === 0 || !targetOrg) return;
    setMigrating(true);
    setMigrationStatus({ status: 'starting', repos: Object.fromEntries(Array.from(selectedRepos).map(name => [name, { status: 'pending', progress: 0, message: '' }])) });
    connectWebSocket();
    try {
      await fetch('/api/migrate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ repos: Array.from(selectedRepos), target_org: targetOrg, visibility }) });
    } catch { setMigrating(false); setMigrationStatus({ status: 'failed', repos: {}, error: 'Failed to start migration' }); }
  };

  const filteredRepos = repos.filter(r => r.name.toLowerCase().includes(searchQuery.toLowerCase()) || r.project.toLowerCase().includes(searchQuery.toLowerCase()));

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 text-gray-400 animate-spin" /></div>;

  if (repos.length === 0) return (
    <div className="text-center py-16">
      <AlertCircle className="w-16 h-16 text-gray-600 mx-auto mb-4" />
      <h2 className="text-2xl font-bold text-white mb-2">No Repositories Found</h2>
      <p className="text-gray-400 mb-6">Run a scan first to discover repositories.</p>
      <Link to="/scan" className="inline-flex items-center gap-2 bg-github-green hover:bg-green-600 text-white px-6 py-3 rounded-lg font-medium"><Search className="w-5 h-5" />Scan Organization</Link>
    </div>
  );

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold text-white flex items-center gap-3"><ArrowRightLeft className="w-7 h-7 text-github-green" />Migrate Repositories</h1></div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-github-dark rounded-xl border border-gray-800">
          <div className="p-4 border-b border-gray-800 flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input type="text" placeholder="Search..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-github-green" />
            </div>
            <button onClick={() => setSelectedRepos(new Set(filteredRepos.map(r => r.name)))} className="text-sm text-gray-400 hover:text-white">Select All</button>
            <button onClick={() => setSelectedRepos(new Set())} className="text-sm text-gray-400 hover:text-white">Clear</button>
          </div>
          <div className="max-h-[500px] overflow-y-auto">
            {filteredRepos.map((repo) => (
              <div key={repo.id} onClick={() => toggleRepo(repo.name)} className={`flex items-center gap-4 p-4 border-b border-gray-800 cursor-pointer transition-colors ${selectedRepos.has(repo.name) ? 'bg-github-green/10' : 'hover:bg-gray-800/50'}`}>
                <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${selectedRepos.has(repo.name) ? 'bg-github-green border-github-green' : 'border-gray-600'}`}>
                  {selectedRepos.has(repo.name) && <Check className="w-3 h-3 text-white" />}
                </div>
                <GitBranch className="w-5 h-5 text-gray-400" />
                <div className="flex-1"><p className="text-white font-medium">{repo.name}</p><p className="text-gray-500 text-sm">{repo.project}</p></div>
                <span className="text-gray-500 text-sm">{(repo.size / 1024 / 1024).toFixed(1)} MB</span>
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-4">
          <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
            <h3 className="text-lg font-semibold text-white mb-4">Migration Settings</h3>
            <div className="space-y-4">
              <div><label className="block text-sm font-medium text-gray-300 mb-2">Target GitHub Org</label><input type="text" placeholder="your-github-org" value={targetOrg} onChange={(e) => setTargetOrg(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-github-green" /></div>
              <div><label className="block text-sm font-medium text-gray-300 mb-2">Visibility</label><select value={visibility} onChange={(e) => setVisibility(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-github-green"><option value="private">Private</option><option value="internal">Internal</option><option value="public">Public</option></select></div>
            </div>
          </div>
          <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-4"><span className="text-gray-400">Selected</span><span className="text-white font-bold text-2xl">{selectedRepos.size}</span></div>
            <button onClick={startMigration} disabled={selectedRepos.size === 0 || !targetOrg || migrating} className="w-full bg-github-green hover:bg-green-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium flex items-center justify-center gap-2">
              {migrating ? <><Loader2 className="w-5 h-5 animate-spin" />Migrating...</> : <><ArrowRightLeft className="w-5 h-5" />Start Migration</>}
            </button>
          </div>
          {migrationStatus && (
            <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
              <h3 className="text-lg font-semibold text-white mb-4">Progress</h3>
              <div className="space-y-3">
                {Object.entries(migrationStatus.repos).map(([name, status]) => (
                  <div key={name} className="flex items-center gap-3">
                    {status.status === 'completed' && <CheckCircle className="w-5 h-5 text-green-400" />}
                    {status.status === 'failed' && <XCircle className="w-5 h-5 text-red-400" />}
                    {status.status === 'in_progress' && <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />}
                    {status.status === 'pending' && <div className="w-5 h-5 rounded-full border-2 border-gray-600" />}
                    <span className={`text-sm ${status.status === 'completed' ? 'text-green-400' : status.status === 'failed' ? 'text-red-400' : status.status === 'in_progress' ? 'text-blue-400' : 'text-gray-400'}`}>{name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
