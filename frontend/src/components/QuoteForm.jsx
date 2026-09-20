import { useState } from 'react';
import client from '../api/client.js';
import { SERVICE_TYPES } from '../utils/constants.js';

const initial = { name: '', email: '', phone: '', service_type: 'residential', budget: '', message: '' };

export default function QuoteForm({ presetService }) {
  const [form, setForm] = useState({ ...initial, service_type: presetService || 'residential' });
  const [status, setStatus] = useState({ loading: false, ok: '', err: '' });

  const onChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setStatus({ loading: true, ok: '', err: '' });
    try {
      await client.post('/quotes/', form);
      setStatus({ loading: false, ok: 'Quote request sent! We reply within 1 business day.', err: '' });
      setForm(initial);
    } catch {
      setStatus({ loading: false, ok: '', err: 'Could not reach backend. Call +1 (555) 010-2030.' });
    }
  };

  return (
    <form onSubmit={onSubmit} className="card p-6 space-y-4">
      <div className="grid md:grid-cols-2 gap-4">
        <div><label className="label">Name</label><input className="input" name="name" value={form.name} onChange={onChange} required /></div>
        <div><label className="label">Email</label><input className="input" type="email" name="email" value={form.email} onChange={onChange} required /></div>
        <div><label className="label">Phone</label><input className="input" name="phone" value={form.phone} onChange={onChange} /></div>
        <div>
          <label className="label">Service</label>
          <select className="input" name="service_type" value={form.service_type} onChange={onChange}>
            {SERVICE_TYPES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>
      <div><label className="label">Budget (USD)</label><input className="input" name="budget" value={form.budget} onChange={onChange} placeholder="e.g. 50000" /></div>
      <div><label className="label">Project details</label><textarea className="input" rows="4" name="message" value={form.message} onChange={onChange} required placeholder="Location, size, timeline…" /></div>
      {status.ok && <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">{status.ok}</p>}
      {status.err && <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">{status.err}</p>}
      <button disabled={status.loading} className="btn-primary w-full">
        {status.loading ? 'Sending…' : 'Request Quote'}
      </button>
    </form>
  );
}
