import { useState } from 'react';
import client from '../api/client.js';

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', message: '' });
  const [msg, setMsg] = useState('');
  const onChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  const onSubmit = async (e) => {
    e.preventDefault();
    try {
      await client.post('/contact/', form);
      setMsg('Thanks! We will reply within 1 business day.');
      setForm({ name: '', email: '', message: '' });
    } catch {
      setMsg('Backend offline — email hello@buildtrack.example instead.');
    }
  };
  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-3xl font-extrabold">Contact Us</h1>
      <form onSubmit={onSubmit} className="card p-6 mt-6 space-y-4">
        <div><label className="label">Name</label><input className="input" name="name" value={form.name} onChange={onChange} required /></div>
        <div><label className="label">Email</label><input className="input" name="email" type="email" value={form.email} onChange={onChange} required /></div>
        <div><label className="label">Message</label><textarea className="input" rows="4" name="message" value={form.message} onChange={onChange} required /></div>
        {msg && <p className="text-sm bg-stone-100 rounded p-2">{msg}</p>}
        <button className="btn-primary w-full">Send Message</button>
      </form>
    </div>
  );
}
