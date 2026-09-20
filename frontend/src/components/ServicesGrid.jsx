import { Link } from 'react-router-dom';
import { SERVICES } from '../utils/constants.js';

export default function ServicesGrid({ compact = false }) {
  const list = compact ? SERVICES.slice(0, 4) : SERVICES;
  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
      {list.map((s) => (
        <div key={s.slug} className="card p-6 flex flex-col">
          <div className="text-3xl">{s.icon}</div>
          <h3 className="mt-3 font-bold text-lg">{s.title}</h3>
          <p className="mt-2 text-sm text-stone-600 flex-1">{s.description}</p>
          <Link to={`/get-quote?service=${s.slug}`} className="mt-4 text-sm font-semibold text-amber-600 hover:underline">
            Request this service →
          </Link>
        </div>
      ))}
    </div>
  );
}
