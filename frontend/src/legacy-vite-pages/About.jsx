export default function About() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="text-3xl font-extrabold">About BuildTrack</h1>
      <p className="mt-3 text-stone-600">
        Family-run general contractor since 2008. 240+ homes, offices and retrofits delivered
        with in-house carpenters, licensed electricians/plumbers and a dedicated project manager on every job.
      </p>
      <div className="mt-8 grid md:grid-cols-3 gap-5">
        <div className="card p-6"><h3 className="font-bold">Safety first</h3><p className="text-sm text-stone-600 mt-1">OSHA-trained crews, daily checklists, fully insured.</p></div>
        <div className="card p-6"><h3 className="font-bold">Transparent pricing</h3><p className="text-sm text-stone-600 mt-1">Line-item estimates, no hidden change orders.</p></div>
        <div className="card p-6"><h3 className="font-bold">On-time handover</h3><p className="text-sm text-stone-600 mt-1">Weekly photo reports + milestone schedule you can track.</p></div>
      </div>
    </div>
  );
}
