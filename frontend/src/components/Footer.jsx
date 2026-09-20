import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-stone-900 text-stone-300 mt-16">
      <div className="mx-auto max-w-7xl px-4 py-10 grid gap-8 md:grid-cols-4">
        <div>
          <p className="text-white font-bold text-lg">BuildTrack</p>
          <p className="text-sm mt-2">Licensed general contractor. Residential, commercial, renovation & project management.</p>
          <p className="text-sm mt-2">License #BT-2026-001</p>
        </div>
        <div>
          <p className="text-white font-semibold mb-2">Services</p>
          <ul className="text-sm space-y-1">
            <li>Residential Construction</li>
            <li>Commercial Builds</li>
            <li>Renovation & Remodeling</li>
            <li>Project Management</li>
          </ul>
        </div>
        <div>
          <p className="text-white font-semibold mb-2">Company</p>
          <ul className="text-sm space-y-1">
            <li><Link to="/about" className="hover:text-white">About</Link></li>
            <li><Link to="/projects" className="hover:text-white">Projects</Link></li>
            <li><Link to="/contact" className="hover:text-white">Contact</Link></li>
            <li><Link to="/dashboard" className="hover:text-white">Dashboard</Link></li>
          </ul>
        </div>
        <div>
          <p className="text-white font-semibold mb-2">Contact</p>
          <p className="text-sm">hello@buildtrack.example</p>
          <p className="text-sm">+1 (555) 010-2030</p>
          <p className="text-sm">Mon–Sat, 8am–6pm</p>
        </div>
      </div>
      <div className="border-t border-stone-800 py-4 text-center text-xs">
        © {new Date().getFullYear()} BuildTrack. All rights reserved.
      </div>
    </footer>
  );
}
