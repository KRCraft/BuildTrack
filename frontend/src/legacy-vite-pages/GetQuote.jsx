import { useSearchParams } from 'react-router-dom';
import QuoteForm from '../components/QuoteForm.jsx';

export default function GetQuote() {
  const [params] = useSearchParams();
  const preset = params.get('service') || 'residential';
  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-3xl font-extrabold">Get a Free Quote</h1>
      <p className="text-stone-600 mt-2">Tell us about your project. Posts to <code>POST /api/quotes/</code>.</p>
      <div className="mt-6"><QuoteForm presetService={preset} /></div>
    </div>
  );
}
