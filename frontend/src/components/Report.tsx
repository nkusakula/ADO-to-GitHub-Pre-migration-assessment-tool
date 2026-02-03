import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BarChart3, Download, Search, FileText, AlertCircle, CheckCircle, AlertTriangle, ChevronDown, ChevronRight } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

interface ScanResults {
  organization_url: string;
  projects: Array<{ name: string; repositories: { count: number; tfvc_used: boolean }; pipelines: { yaml_count: number; release_definitions: number }; work_items: { total: number; by_type: Record<string, number> }; }>;
  summary: { total_projects: number; total_repositories: number; total_pipelines: number; total_work_items: number; complexity: { overall: number; rating: string; repositories: { rating: string; score: number; effort: string }; pipelines: { rating: string; score: number; effort: string }; work_items: { rating: string; score: number; effort: string }; }; blockers: string[]; };
}

const COLORS = ['#238636', '#f0883e', '#8b949e', '#58a6ff', '#a371f7'];

export default function Report() {
  const [results, setResults] = useState<ScanResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch('/api/scan/results').then(res => res.ok ? res.json() : null).then(data => { setResults(data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const toggleProject = (name: string) => {
    const newExpanded = new Set(expandedProjects);
    if (newExpanded.has(name)) newExpanded.delete(name); else newExpanded.add(name);
    setExpandedProjects(newExpanded);
  };

  const downloadReport = () => {
    if (!results) return;
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'ado-migration-report.json'; a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-2 border-github-green border-t-transparent" /></div>;

  if (!results) return (
    <div className="text-center py-16">
      <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
      <h2 className="text-2xl font-bold text-white mb-2">No Report Available</h2>
      <p className="text-gray-400 mb-6">Run a scan first to generate a report.</p>
      <Link to="/scan" className="inline-flex items-center gap-2 bg-github-green hover:bg-green-600 text-white px-6 py-3 rounded-lg font-medium"><Search className="w-5 h-5" />Scan Organization</Link>
    </div>
  );

  const { summary, projects } = results;
  const complexityData = [{ name: 'Repos', score: summary.complexity.repositories.score, fill: '#58a6ff' }, { name: 'Pipelines', score: summary.complexity.pipelines.score, fill: '#a371f7' }, { name: 'Work Items', score: summary.complexity.work_items.score, fill: '#f0883e' }];
  const assetDistribution = [{ name: 'Repositories', value: summary.total_repositories }, { name: 'Pipelines', value: summary.total_pipelines }, { name: 'Work Items', value: Math.min(summary.total_work_items / 100, 100) }];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-white flex items-center gap-3"><BarChart3 className="w-7 h-7 text-github-green" />Migration Report</h1><p className="text-gray-400 mt-1">{results.organization_url}</p></div>
        <button onClick={downloadReport} className="inline-flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm"><Download className="w-4 h-4" />Export JSON</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {(['repositories', 'pipelines', 'work_items'] as const).map((key) => {
          const data = summary.complexity[key]; const labels = { repositories: 'Repositories', pipelines: 'Pipelines', work_items: 'Work Items' }; const counts = { repositories: summary.total_repositories, pipelines: summary.total_pipelines, work_items: summary.total_work_items };
          return (
            <div key={key} className="bg-github-dark rounded-xl p-6 border border-gray-800">
              <div className="flex items-center justify-between mb-4"><h3 className="text-lg font-semibold text-white">{labels[key]}</h3><span className={`text-xs font-medium px-2 py-1 rounded-full ${data.rating === 'Low' ? 'text-green-400 bg-green-900/30' : data.rating === 'Medium' ? 'text-yellow-400 bg-yellow-900/30' : 'text-red-400 bg-red-900/30'}`}>{data.rating}</span></div>
              <p className="text-3xl font-bold text-white mb-2">{counts[key].toLocaleString()}</p>
              <div className="h-2 bg-gray-900 rounded-full overflow-hidden mb-2"><div className={`h-full rounded-full ${data.rating === 'Low' ? 'bg-green-500' : data.rating === 'Medium' ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${data.score}%` }} /></div>
              <p className="text-sm text-gray-400">Est. effort: <span className="text-white">{data.effort}</span></p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
          <h3 className="text-lg font-semibold text-white mb-4">Complexity by Category</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={complexityData} layout="vertical"><XAxis type="number" domain={[0, 100]} stroke="#6e7681" /><YAxis type="category" dataKey="name" stroke="#6e7681" width={80} /><Tooltip contentStyle={{ backgroundColor: '#21262d', border: '1px solid #30363d' }} /><Bar dataKey="score" radius={[0, 4, 4, 0]} /></BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
          <h3 className="text-lg font-semibold text-white mb-4">Asset Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart><Pie data={assetDistribution} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={5} dataKey="value">{assetDistribution.map((_, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}</Pie><Tooltip contentStyle={{ backgroundColor: '#21262d', border: '1px solid #30363d' }} /><Legend /></PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-github-dark rounded-xl p-6 border border-gray-800">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">{summary.blockers.length > 0 ? <AlertTriangle className="w-5 h-5 text-yellow-400" /> : <CheckCircle className="w-5 h-5 text-green-400" />}Migration Blockers</h3>
        {summary.blockers.length === 0 ? <p className="text-green-400">No major blockers identified!</p> : <ul className="space-y-2">{summary.blockers.map((blocker, i) => <li key={i} className="flex items-start gap-2 text-gray-300"><AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" /><span>{blocker}</span></li>)}</ul>}
      </div>

      <div className="bg-github-dark rounded-xl border border-gray-800">
        <div className="p-6 border-b border-gray-800"><h3 className="text-lg font-semibold text-white">Project Details</h3></div>
        <div>
          {projects.map((project) => (
            <div key={project.name} className="border-b border-gray-800 last:border-b-0">
              <button onClick={() => toggleProject(project.name)} className="w-full flex items-center justify-between p-4 hover:bg-gray-800/50">
                <div className="flex items-center gap-3">{expandedProjects.has(project.name) ? <ChevronDown className="w-5 h-5 text-gray-400" /> : <ChevronRight className="w-5 h-5 text-gray-400" />}<span className="text-white font-medium">{project.name}</span></div>
                <div className="flex items-center gap-6 text-sm text-gray-400"><span>{project.repositories.count} repos</span><span>{project.pipelines.yaml_count + project.pipelines.release_definitions} pipelines</span><span>{project.work_items.total.toLocaleString()} items</span></div>
              </button>
              {expandedProjects.has(project.name) && (
                <div className="px-12 pb-4 space-y-2 text-sm">
                  {project.repositories.tfvc_used && <div className="flex items-center gap-2 text-yellow-400"><AlertTriangle className="w-4 h-4" /><span>Uses TFVC</span></div>}
                  {project.pipelines.release_definitions > 0 && <div className="flex items-center gap-2 text-yellow-400"><AlertTriangle className="w-4 h-4" /><span>{project.pipelines.release_definitions} Classic release pipelines</span></div>}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
