import { useState } from 'react';
import ProjectCard from '../components/ProjectCard.jsx';
import Loader from '../components/Loader.jsx';
import useProjects from '../hooks/useProjects.js';

export default function Projects() {
  const { projects, loading, error } = useProjects();
  const [filter, setFilter] = useState('all');
  const filtered = filter === 'all' ? projects : projects.filter((p) => p.category === filter);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="text-3xl font-extrabold">Our Projects</h1>
      <p className="text-stone-600 mt-2">Filter by category. Data loads from <code>/api/projects/</code> with offline fallback.</p>
      <div className="mt-4 flex gap-2 flex-wrap">
        {['all', 'residential', 'commercial', 'renovation', 'project-management'].map((c) => (
          <button
            key={c}
            onClick={() => setFilter(c)}
            className={`px-4 py-1.5 rounded-full text-sm font-semibold border ${filter === c ? 'bg-stone-900 text-white' : 'bg-white'}`}
          >
            {c}
          </button>
        ))}
      </div>
      {error && <p className="mt-4 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">{error}</p>}
      {loading ? <Loader text="Loading projects…" /> : (
        <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => <ProjectCard key={p.id} project={p} />)}
        </div>
      )}
    </div>
  );
}
