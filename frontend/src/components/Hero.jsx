import { Link } from 'react-router-dom';

export default function Hero({ title, subtitle }) {
  return (
    <section className="bg-stone-900 text-white">
      <div className="mx-auto max-w-7xl px-4 py-16 md:py-24 grid md:grid-cols-2 gap-10 items-center">
        <div>
          <p className="inline-block text-xs font-bold tracking-widest uppercase bg-amber-500 text-stone-900 px-3 py-1 rounded-full mb-4">
            Licensed • Insured • Since 2008
          </p>
          <h1 className="text-4xl md:text-5xl font-extrabold leading-tight">
            {title || 'We build homes & workplaces that last.'}
          </h1>
          <p className="mt-4 text-stone-300 text-lg">
            {subtitle || 'From custom homes to commercial fit-outs and full renovations — transparent pricing, safety-first crews, on-time delivery.'}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/get-quote" className="btn-primary">Get a Free Quote</Link>
            <Link to="/projects" className="btn-outline !text-white !border-stone-600">View Projects</Link>
          </div>
          <div className="mt-8 flex gap-8 text-sm">
            <div><p className="text-2xl font-bold text-amber-400">240+</p><p className="text-stone-400">Projects done</p></div>
            <div><p className="text-2xl font-bold text-amber-400">18 yrs</p><p className="text-stone-400">Experience</p></div>
            <div><p className="text-2xl font-bold text-amber-400">4.9★</p><p className="text-stone-400">Client rating</p></div>
          </div>
        </div>
        <div className="rounded-2xl overflow-hidden shadow-2xl">
          <img
            src="https://images.unsplash.com/photo-1541888946425-d81bb19240f5?w=1000&q=80"
            alt="Construction site"
            className="w-full h-80 md:h-96 object-cover"
            loading="lazy"
          />
        </div>
      </div>
    </section>
  );
}
