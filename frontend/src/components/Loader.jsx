export default function Loader({ text = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center py-16 gap-3 text-stone-600">
      <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-stone-300 border-t-amber-500" />
      <span>{text}</span>
    </div>
  );
}
