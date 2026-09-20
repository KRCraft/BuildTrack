import useProjects from '../hooks/useProjects.js';
import Loader from '../components/Loader.jsx';
import { useAuth } from '../context/AuthContext.jsx';

export default function Dashboard() {
  const { projects, loading } = useProjects();
  const { user, login, logout } = useAuth();

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="text-3xl font-extrabold">Client Dashboard</h1>
      <p className="text-stone-600 mt-2">Track your builds, milestones and documents (stub — connect to backend auth).</p>
      <div className="mt-4">
        {!user ? (
          <button className="btn-outline" onClick={() => login({ name: 'Demo Client', email: 'client@example.com' })}>
            Sign in as demo client
          </button>
        ) : (
          <div className="flex items-center gap-3">
            <span className="text-sm">Signed in as <b>{user.name}</b></span>
            <button className="btn-outline !py-1" onClick={logout}>Logout</button>
          </div>
        )}
      </div>
      {loading ? <Loader /> : (
        <div className="mt-6 card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-stone-100 text-left">
              <tr><th className="p-3">Project</th><th className="p-3">Category</th><th className="p-3">Location</th><th className="p-3">Status</th></tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.id} className="border-t">
                  <td className="p-3 font-semibold">{p.title}</td>
                  <td className="p-3">{p.category}</td>
                  <td className="p-3">{p.location}</td>
                  <td className="p-3">{p.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
