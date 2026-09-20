import { useEffect, useState } from 'react';
import client from '../api/client.js';
import { FALLBACK_PROJECTS } from '../utils/constants.js';

export default function useProjects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    async function fetchProjects() {
      try {
        const res = await client.get('/projects/');
        if (!mounted) return;
        const data = Array.isArray(res.data) ? res.data : res.data.results || [];
        setProjects(data.length ? data : FALLBACK_PROJECTS);
      } catch (e) {
        if (mounted) {
          setError('Backend unreachable — showing sample projects.');
          setProjects(FALLBACK_PROJECTS);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchProjects();
    return () => {
      mounted = false;
    };
  }, []);

  return { projects, loading, error };
}
