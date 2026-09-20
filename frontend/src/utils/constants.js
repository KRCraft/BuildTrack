export const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) || 'http://localhost:8000/api/v1';

export const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/services', label: 'Services' },
  { to: '/projects', label: 'Projects' },
  { to: '/about', label: 'About' },
  { to: '/contact', label: 'Contact' },
  { to: '/dashboard', label: 'Dashboard' }
];

export const SERVICES = [
  {
    slug: 'residential',
    title: 'Residential Construction',
    description: 'Custom homes, multi-family units and extensions built to code, on time and on budget.',
    icon: '🏠'
  },
  {
    slug: 'commercial',
    title: 'Commercial Builds',
    description: 'Offices, retail and warehouses with safety-first delivery and minimal downtime.',
    icon: '🏢'
  },
  {
    slug: 'renovation',
    title: 'Renovation & Remodeling',
    description: 'Kitchens, bathrooms, full-house retrofits and energy-efficiency upgrades.',
    icon: '🔨'
  },
  {
    slug: 'project-management',
    title: 'Project Management',
    description: 'End-to-end planning, permits, subcontractor coordination and transparent reporting.',
    icon: '📋'
  }
];

export const SERVICE_TYPES = SERVICES.map((s) => s.slug);

export const FALLBACK_PROJECTS = [
  {
    id: 1,
    title: 'Maple Street Family Home',
    category: 'residential',
    location: 'Austin, TX',
    status: 'completed',
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&q=80',
    description: '3,200 sq ft custom home with energy-efficient framing.'
  },
  {
    id: 2,
    title: 'Downtown Office Fit-Out',
    category: 'commercial',
    location: 'Denver, CO',
    status: 'in-progress',
    image: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&q=80',
    description: '12,000 sq ft commercial interior build-out.'
  },
  {
    id: 3,
    title: 'Heritage Kitchen Renovation',
    category: 'renovation',
    location: 'Portland, OR',
    status: 'completed',
    image: 'https://images.unsplash.com/photo-1556909212-d5b604d0c90d?w=800&q=80',
    description: 'Full kitchen + structural retrofit in 1920s home.'
  }
];
