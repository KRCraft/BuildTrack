import { Link } from 'react-router-dom';

export default function ProjectCard({ project }) {
  return (
    <Link to={`/projects/${project.id}`} className="card hover:shadow-md transition block">
      <img
        src={project.image || 'https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=800&q=80'}
        alt={project.title}
        className="h-48 w-full object-cover"
        loading="lazy"
      />
      <div className="p-4">
        <div className="flex items-center justify-between text-xs">
          <span className="uppercase tracking-wide font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
            {project.category || 'general'}
          </span>
          <span className="text-stone-500">{project.status || 'completed'}</span>
        </div>
        <h3 className="mt-2 font-bold">{project.title}</h3>
        <p className="text-sm text-stone-600 line-clamp-2">{project.description}</p>
        <p className="mt-2 text-xs text-stone-500">{project.location}</p>
      </div>
    </Link>
  );
}
