import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client.js';
import Loader from '../components/Loader.jsx';
import { FALLBACK_PROJECTS } from '../utils/constants.js';

export default function ProjectDetail() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await client.get(`/projects/${id}/`);
        setProject(res.data);
      } catch {
        setProject(FALLBACK_PROJECTS.find((p) => String(p.id) === String(id)) || FALLBACK_PROJECTS[0]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) return <Loader text="Loading project…" />;
  if (!project) return <p className="p-10">Project not found.</p>;

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <Link to="/projects" className="text-sm text-amber-700 font-semibold">← Back to projects</Link>
      <h1 className="mt-2 text-3xl font-extrabold">{project.title}</h1>
      <p className="text-stone-600">{project.location} • {project.category} • {project.status}</p>
      <img
        src={project.image || 'https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=1000&q=80'}
        alt={project.title}
        className="mt-6 rounded-2xl w-full h-80 object-cover"
      />
      <p className="mt-6 text-stone-700">{project.description}</p>
      <div className="mt-8 flex gap-3">
        <Link to="/get-quote" className="btn-primary">Start a similar project</Link>
        <Link to="/contact" className="btn-outline">Talk to us</Link>
      </div>
    </div>
  );
}
