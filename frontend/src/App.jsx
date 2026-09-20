import { Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import Footer from './components/Footer.jsx';
import Home from './legacy-vite-pages/Home.jsx';
import Services from './legacy-vite-pages/Services.jsx';
import Projects from './legacy-vite-pages/Projects.jsx';
import ProjectDetail from './legacy-vite-pages/ProjectDetail.jsx';
import About from './legacy-vite-pages/About.jsx';
import Contact from './legacy-vite-pages/Contact.jsx';
import GetQuote from './legacy-vite-pages/GetQuote.jsx';
import Dashboard from './legacy-vite-pages/Dashboard.jsx';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-stone-50 text-stone-900 font-display">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/services" element={<Services />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/get-quote" element={<GetQuote />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
