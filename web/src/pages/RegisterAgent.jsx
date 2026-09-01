import { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { registerAgent } from '../api';

const WHOLESALE_AVG = 85;
const RETAIL_MULTIPLIER = 2;

export default function RegisterAgent() {
  const [form, setForm] = useState({ name: '', surname: '', phone: '', team_code: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [bottles, setBottles] = useState(50);
  const [openFaq, setOpenFaq] = useState(null);
  const formRef = useRef(null);

  function set(k) { return e => setForm(f => ({ ...f, [k]: e.target.value })); }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      const data = await registerAgent(form);
      setResult(data);
    } catch (err) {
      setError(err.message);
    }
  }

  const profit = bottles * WHOLESALE_AVG;
  const revenue = bottles * WHOLESALE_AVG * RETAIL_MULTIPLIER;
  const teamCommission = Math.round(bottles * 0.6 * WHOLESALE_AVG * 0.05);
  const totalEarnings = profit + teamCommission;

  const faqs = [
    { q: 'Do I need a website or store?', a: 'No. All you need is WhatsApp on your phone. You order from us via WhatsApp, and sell to your customers however you like — in person, on social media, or via WhatsApp.' },
    { q: 'What if a fragrance doesn\'t sell?', a: 'There\'s no minimum order and no starter pack. Start with a few bottles. If one scent doesn\'t move, try another. You only order what you can sell.' },
    { q: 'How do customers pay me?', a: 'However you prefer — cash, EFT, or you can use your own Yoco card machine. You set your own retail price. We only charge you the wholesale price.' },
    { q: 'How do I get my stock?', a: 'We courier nationwide via The Courier Guy. R65 flat rate, free delivery on orders over R2,000. Delivery within 3-5 working days.' },
    { q: 'Can I build a team?', a: 'Yes. Share your agent code. When agents register under you, you earn 5% commission on every wholesale order they place — for life. There\'s no limit to your team size.' },
  ];

  if (result) return (
    <div className="max-w-lg mx-auto px-4 py-16 text-center">
      <div className="bg-green-50 border border-green-200 rounded-2xl p-8">
        <p className="text-4xl mb-4 font-serif font-bold text-purple-700">✓</p>
        <p className="text-green-700 text-2xl font-bold mb-2">Welcome, Agent!</p>
        <p className="text-gray-600 mb-4">Your agent code is:</p>
        <p className="text-3xl font-mono font-bold text-purple-700 tracking-wider bg-purple-50 inline-block px-6 py-2 rounded-lg">{result.agent_code}</p>
        <p className="text-red-600 font-bold mt-4">Save your recovery PIN now — it will not be shown again.</p>
        <div className="mt-6 space-y-3">
          <p className="text-sm text-gray-500">You can now order via WhatsApp or sign in to your dashboard.</p>
          <div className="flex gap-3 justify-center flex-wrap">
            <Link to="/login" className="bg-purple-700 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-purple-800 transition-colors">Sign In to Dashboard</Link>
            <a href="https://wa.me/27605283020" target="_blank" rel="noopener noreferrer"
              className="bg-green-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-green-700 transition-colors">
              Order via WhatsApp
            </a>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div>
      {/* ── HERO ── */}
      <section className="bg-gradient-to-b from-purple-700 to-purple-900 text-white py-16 px-4 text-center">
        <span className="inline-block bg-purple-500/40 text-purple-100 text-xs font-semibold px-3 py-1 rounded-full mb-4">
          NO STARTER PACK REQUIRED
        </span>
        <h1 className="text-3xl md:text-4xl font-bold mb-3">
          Turn your phone into a perfume business
        </h1>
        <p className="text-purple-200 max-w-lg mx-auto mb-6 text-lg">
          Buy wholesale. Sell at <strong>2× your price</strong>. Earn <strong>5% commission</strong> from agents you recruit.
          All from WhatsApp. No website needed.
        </p>
        <div className="flex gap-3 justify-center flex-wrap">
          <button onClick={() => formRef.current?.scrollIntoView({ behavior: 'smooth' })}
            className="bg-white text-purple-700 px-8 py-3 rounded-xl font-bold text-lg hover:bg-purple-50 transition-colors">
            Start Selling Today
          </button>
          <a href="https://wa.me/27605283020" target="_blank" rel="noopener noreferrer"
            className="border-2 border-purple-300 text-white px-8 py-3 rounded-xl font-medium text-lg hover:bg-purple-600 transition-colors">
            Ask on WhatsApp
          </a>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="max-w-4xl mx-auto py-16 px-4">
        <h2 className="text-2xl font-bold text-center mb-10">How it works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { step: '1', icon: '1', title: 'Register', desc: 'Fill in your details below. Get your agent code instantly. No approval. No waiting.' },
            { step: '2', icon: '2', title: 'Order via WhatsApp', desc: 'Type "5 Rose Oud" on WhatsApp. Confirm. We deliver to your door in 3-5 days. R65 flat rate.' },
            { step: '3', icon: '3', title: 'Sell at Your Price', desc: 'Sell to your customers at ~2× wholesale. Keep 100% of your markup. Build a team, earn 5% from their orders.' },
          ].map(item => (
            <div key={item.step} className="text-center">
              <div className="w-16 h-16 bg-purple-100 text-purple-700 rounded-2xl flex items-center justify-center text-2xl font-serif font-bold mx-auto mb-4">{item.icon}</div>
              <div className="text-xs font-bold text-purple-400 mb-1">STEP {item.step}</div>
              <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
              <p className="text-sm text-gray-500">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── WHY ZEN vs OTHERS ── */}
      <section className="bg-gray-50 py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">Why agents choose Zen Fragrances</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm bg-white rounded-xl shadow-sm overflow-hidden">
              <thead>
                <tr className="bg-purple-50 text-left">
                  <th className="px-6 py-3 font-semibold"></th>
                  <th className="px-6 py-3 font-semibold text-purple-700">Zen Fragrances</th>
                  <th className="px-6 py-3 text-gray-500">Fine Fragrance Collection</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {[
                  ['Starter cost', 'R0 — start with 1 bottle', 'R960 starter pack'],
                  ['Ordering', 'WhatsApp — instant', 'Website only'],
                  ['Agent margin', '100% markup (2× wholesale)', '100% markup'],
                  ['Team commissions', '5% on agent orders', 'None'],
                  ['Stock check', 'WhatsApp: "stock 1"', 'Login + browse website'],
                  ['Delivery', 'R65 nationwide', 'R65 nationwide'],
                  ['Agent dashboard', 'Track orders, earnings, team', 'Account management'],
                  ['Fragrances', '99+ (expanding)', '42'],
                ].map(([label, zen, ffc], i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                    <td className="px-6 py-3 font-medium text-gray-700">{label}</td>
                    <td className="px-6 py-3 text-purple-700 font-medium">{zen}</td>
                    <td className="px-6 py-3 text-gray-500">{ffc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── EARNINGS CALCULATOR ── */}
      <section className="max-w-4xl mx-auto py-16 px-4">
        <h2 className="text-2xl font-bold text-center mb-2">What you could earn</h2>
        <p className="text-center text-gray-500 mb-8">Slide to see your potential monthly income</p>

        <div className="bg-gradient-to-br from-purple-50 to-white rounded-2xl border border-purple-100 p-6 md:p-8 max-w-lg mx-auto">
          <div className="mb-6">
            <div className="flex justify-between items-baseline mb-2">
              <label className="text-sm font-medium text-gray-600">Bottles sold per month</label>
              <span className="text-2xl font-bold text-purple-700">{bottles}</span>
            </div>
            <input type="range" min="5" max="200" step="5" value={bottles}
              onChange={e => setBottles(Number(e.target.value))}
              className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer accent-purple-700" />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>5</span><span>50</span><span>100</span><span>150</span><span>200</span>
            </div>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-purple-100">
              <span className="text-gray-600">Wholesale cost</span>
              <span className="font-medium">R{profit.toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-purple-100">
              <span className="text-gray-600">Your retail revenue</span>
              <span className="font-medium text-green-700">R{revenue.toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-purple-100">
              <span className="text-gray-600">Your profit (100% markup)</span>
              <span className="font-bold text-green-700">R{profit.toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-purple-100">
              <span className="text-gray-600">Team commission (3 agents)</span>
              <span className="font-medium text-purple-700">+ R{teamCommission.toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-3">
              <span className="text-gray-800 font-semibold">Total monthly earnings</span>
              <span className="text-xl font-bold text-purple-700">R{totalEarnings.toLocaleString()}</span>
            </div>
          </div>

          <p className="text-xs text-gray-400 mt-4 text-center">
            Based on R{WHOLESALE_AVG} avg wholesale × {RETAIL_MULTIPLIER}× markup. Team: 3 agents selling 60% of your volume at 5% commission.
          </p>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="bg-gray-50 py-16 px-4">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">Frequently asked questions</h2>
          <div className="space-y-3">
            {faqs.map((faq, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-gray-50 transition-colors">
                  <span className="font-medium text-gray-800 pr-4">{faq.q}</span>
                  <span className={`text-purple-500 transition-transform flex-shrink-0 ${openFaq === i ? 'rotate-45' : ''}`}>＋</span>
                </button>
                {openFaq === i && (
                  <div className="px-6 pb-4 text-sm text-gray-600 leading-relaxed">{faq.a}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── REGISTRATION FORM ── */}
      <section ref={formRef} className="max-w-lg mx-auto py-16 px-4">
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 md:p-8">
          <h2 className="text-xl font-bold text-center mb-1">Register as an Agent</h2>
          <p className="text-center text-sm text-gray-500 mb-6">
            Already have a team member&apos;s code? Enter it below. Don&apos;t have one?{' '}
            <a href="https://wa.me/27605283020" target="_blank" rel="noopener noreferrer" className="text-purple-700 underline">Contact us on WhatsApp</a> and we&apos;ll assign you one.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            {error && <p className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">{error}</p>}
            <div className="grid grid-cols-2 gap-3">
              <input placeholder="First Name" value={form.name} onChange={set('name')}
                className="border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-300 focus:border-purple-400" required />
              <input placeholder="Surname" value={form.surname} onChange={set('surname')}
                className="border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-300 focus:border-purple-400" required />
            </div>
            <input type="tel" placeholder="Phone number (e.g. 0821234567)" value={form.phone} onChange={set('phone')}
              className="border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-300 focus:border-purple-400" required />
            <input placeholder="Team Code (from your team member)" value={form.team_code} onChange={set('team_code')}
              className="border border-gray-300 rounded-lg px-4 py-2.5 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-purple-300 focus:border-purple-400"
              required />
            <input type="email" placeholder="Email (optional — for dashboard login)" value={form.email} onChange={set('email')}
              className="border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-300 focus:border-purple-400" />
            <input type="password" placeholder="Password (optional — for dashboard login)" value={form.password} onChange={set('password')}
              className="border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-300 focus:border-purple-400" />
            <button type="submit"
              className="bg-purple-700 text-white py-3 rounded-lg font-semibold text-lg hover:bg-purple-800 transition-colors mt-2">
              Start Your Perfume Business
            </button>
          </form>
          <p className="text-center text-sm text-gray-500 mt-4">
            Already registered? <Link to="/login" className="text-purple-700 font-medium">Sign In</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
