import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { NAV_LINKS } from '../utils/constants.js';

export default function Navbar() {
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-50 bg-stone-900 text-white">
      <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded bg-amber-500 text-stone-900">B</span>
          BuildTrack
        </Link>
        <nav className="hidden md:flex items-center gap-6">
          {NAV_LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                isActive ? 'text-amber-400' : 'text-stone-200 hover:text-white'
              }
            >
              {l.label}
            </NavLink>
          ))}
          <Link to="/get-quote" className="btn-primary !py-2">
            Get a Quote
          </Link>
        </nav>
        <button className="md:hidden border rounded px-3 py-1" onClick={() => setOpen((v) => !v)} aria-label="Menu">
          ☰
        </button>
      </div>
      {open && (
        <div className="md:hidden px-4 pb-4 flex flex-col gap-3 bg-stone-900">
          {NAV_LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} onClick={() => setOpen(false)} className="text-stone-200">
              {l.label}
            </NavLink>
          ))}
          <Link to="/get-quote" onClick={() => setOpen(false)} className="btn-primary">
            Get a Quote
          </Link>
        </div>
      )}
    </header>
  );
}
