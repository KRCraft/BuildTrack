import { Link } from 'react-router-dom';
import Hero from '../components/Hero.jsx';
import ServicesGrid from '../components/ServicesGrid.jsx';
import ProjectCard from '../components/ProjectCard.jsx';
import useProjects from '../hooks/useProjects.js';
import Loader from '../components/Loader.jsx';

export default function Home() {
  const { projects, loading } = useProjects();
  return (
    <div>
      <Hero />
      <section className="mx-auto max-w-7xl px-4 py-12">
        <div className="flex items-end justify-between mb-6">
          <h2 className="text-2xl font-extrabold">Our Services</h2>
          <Link to="/services" className="text-sm font-semibold text-amber-700 hover:underline">All services →</Link>
        </div>
        <ServicesGrid compact />
      </section>
      <section className="mx-auto max-w-7xl px-4 py-4">
        <div className="flex items-end justify-between mb-6">
          <h2 className="text-2xl font-extrabold">Featured Projects</h2>
          <Link to="/projects" className="text-sm font-semibold text-amber-700 hover:underline">All projects →</Link>
        </div>
        {loading ? <Loader /> : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {projects.slice(0, 3).map((p) => <ProjectCard key={p.id} project={p} />)}
          </div>
        )}
      </section>
      <section className="mx-auto max-w-7xl px-4 py-12">
        <div className="card p-8 bg-stone-900 !text-white flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-2xl font-bold">Have plans or just an idea?</h3>
            <p className="text-stone-300 mt-1">Free site visit + detailed estimate within 48 hours.</p>
          </div>
          <Link to="/get-quote" className="btn-primary whitespace-nowrap">Get a Free Quote</Link>
        </div>
      </section>
    </div>
  );
}
