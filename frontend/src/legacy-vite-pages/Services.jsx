import ServicesGrid from '../components/ServicesGrid.jsx';
import { SERVICES } from '../utils/constants.js';

export default function Services() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="text-3xl font-extrabold">Construction Services</h1>
      <p className="text-stone-600 mt-2 max-w-2xl">
        Residential, commercial, renovation and full project management — one accountable team from permits to handover.
      </p>
      <div className="mt-8"><ServicesGrid /></div>
      <div className="mt-10 grid md:grid-cols-2 gap-5">
        {SERVICES.map((s) => (
          <div key={s.slug} className="card p-6">
            <h3 className="font-bold">{s.title} — what's included</h3>
            <ul className="mt-2 text-sm text-stone-600 list-disc ml-5 space-y-1">
              <li>Free estimate & site survey</li>
              <li>Permits, safety & insurance handled</li>
              <li>Dedicated site manager + weekly photo reports</li>
              <li>1-year workmanship warranty</li>
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
