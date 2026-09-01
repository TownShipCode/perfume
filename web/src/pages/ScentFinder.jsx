import { useState } from 'react';
import { Link } from 'react-router-dom';

// Simple scent quiz — maps answers to our 16 seeded scents.
// Client-side only (no API needed). Guides discovery like Acqua di Parma's finder.

const STEPS = [
  {
    key: 'gender',
    q: 'Who is it for?',
    options: [
      { value: 'men', label: '👨 For Men' },
      { value: 'women', label: '👩 For Women' },
      { value: 'unisex', label: '👥 Either / Gift' },
    ],
  },
  {
    key: 'occasion',
    q: 'Where will they wear it?',
    options: [
      { value: 'daily', label: '🏃 Every day' },
      { value: 'night', label: '🌙 Nights out' },
      { value: 'work', label: '💼 Work / meetings' },
    ],
  },
  {
    key: 'mood',
    q: 'What vibe?',
    options: [
      { value: 'fresh', label: '💧 Fresh & clean' },
      { value: 'warm', label: '🔥 Warm & bold' },
      { value: 'soft', label: '🌸 Soft & elegant' },
    ],
  },
];

// Order: [gender][occasion][mood] -> product id hint (by product_number)
const MATCHES = {
  men: { daily: { fresh: 'L\'EAU D\'ISSEY', warm: 'INVICTUS', soft: 'LEGEND' }, night: { fresh: 'ONE MILLION', warm: 'SCANDAL', soft: 'DESIRE' }, work: { fresh: '212 VIP', warm: 'LEGEND', soft: 'INVICTUS' } },
  women: { daily: { fresh: 'GUCCI RUSH', warm: 'BLACK OPIUM', soft: 'NARCISO RODRIGUEZ' }, night: { fresh: 'GOOD GIRL', warm: 'BLACK OPIUM', soft: 'SCANDAL' }, work: { fresh: 'CHANNEL NO 5', warm: 'ARMANI SI', soft: 'LADY MILLION' } },
  unisex: { daily: { fresh: 'L\'EAU D\'ISSEY', warm: 'ONE MILLION', soft: 'GUCCI RUSH' }, night: { fresh: 'GOOD GIRL', warm: 'SCANDAL', soft: 'BLACK OPIUM' }, work: { fresh: 'CHANNEL NO 5', warm: 'ARMANI SI', soft: 'LEGEND' } },
};

export default function ScentFinder() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);

  function pick(value) {
    const next = { ...answers, [STEPS[step].key]: value };
    setAnswers(next);
    if (step < STEPS.length - 1) {
      setStep(step + 1);
    } else {
      setResult(next);
    }
  }

  const reset = () => { setStep(0); setAnswers({}); setResult(null); };

  const guess = result && MATCHES[result.gender]?.[result.occasion]?.[result.mood];

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <Link to="/catalogue" className="text-purple-700 text-sm hover:underline">&larr; Back to Catalogue</Link>
      <h1 className="text-3xl font-bold mt-4 mb-2 text-center">Find Your Scent</h1>
      <p className="text-gray-500 text-center mb-8">Answer three quick questions and we'll point you to a good starting scent.</p>

      {result ? (
        <div className="text-center">
          <p className="text-5xl mb-4">✨</p>
          <p className="text-gray-500 mb-1">Based on your answers, start with</p>
          <p className="text-2xl font-bold text-purple-700 mb-1">{guess || 'our bestseller'}</p>
          <p className="text-sm text-gray-500 mb-6">Then explore the catalogue and swap it for whatever smells right.</p>
          <div className="flex gap-3 justify-center">
            <Link to="/catalogue" className="bg-purple-700 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-purple-800">Browse Catalogue</Link>
            <button onClick={reset} className="border border-purple-700 text-purple-700 px-6 py-2.5 rounded-lg font-medium hover:bg-purple-50">Start Over</button>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <p className="text-sm text-gray-400 mb-2">Question {step + 1} of {STEPS.length}</p>
          <h2 className="text-xl font-bold mb-6">{STEPS[step].q}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {STEPS[step].options.map(o => (
              <button key={o.value} onClick={() => pick(o.value)}
                className="border-2 border-gray-200 rounded-xl p-4 hover:border-purple-500 hover:bg-purple-50 transition-colors text-center">
                <span className="text-2xl block mb-2">{o.label.split(' ')[0]}</span>
                <span className="text-sm font-medium text-gray-700">{o.label.slice(2)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
