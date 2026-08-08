import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';

export default function Landing() {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);
  const [subError, setSubError] = useState('');
  const [openFaq, setOpenFaq] = useState(null);

  const faqs = [
    { q: 'Are these real designer perfumes?', a: 'They are premium interpretations inspired by iconic designer scents — not fakes. Our fragrances are oil-based, alcohol-free, long-lasting and skin-friendly.' },
    { q: 'How do I order?', a: 'Two ways: browse this store and check out, or order on WhatsApp — just send a product name like "5 Rose Oud" and we\'ll confirm it for you.' },
    { q: 'How long does delivery take?', a: '3-5 working days nationwide via The Courier Guy. R65 flat rate, and FREE delivery on orders over R2,000.' },
    { q: 'Can I become an agent or reseller?', a: 'Yes — zero startup cost. Buy at wholesale, sell at your own price (~2×), and earn commission by building your team. No starter pack required.' },
    { q: 'Are they safe on my skin?', a: 'We use high-quality, IFRA-compliant fragrance oils that are skin-friendly and alcohol-free.' },
    { q: 'What if I don\'t like the scent?', a: 'Check our returns and exchange policy — we want you happy with your fragrance.' },
  ];

  async function handleSubscribe(e) {
    e.preventDefault();
    setSubError('');
    try {
      await api('/api/newsletter', { method: 'POST', body: JSON.stringify({ email }) });
      setSubscribed(true);
    } catch (err) {
      setSubError(err.message);
    }
  }

  return (
    <div>
      <section className="text-center py-24 px-4 bg-gradient-to-b from-purple-50 to-white">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">Zen Fragrances</h1>
        <p className="text-xl text-gray-600 max-w-xl mx-auto mb-4">
          Inspired by your favourite designer scents — not a dupe. Wholesale perfumes for resellers. Buy at wholesale, sell at your price.
        </p>
        <div className="flex flex-wrap gap-2 justify-center mb-8">
          {['Inspired by, not a dupe', 'Oil-based · Alcohol-free', 'Long-lasting', 'Skin-friendly'].map(v => (
            <span key={v} className="bg-purple-100 text-purple-700 text-xs font-semibold px-3 py-1.5 rounded-full">{v}</span>
          ))}
        </div>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link to="/catalogue" className="bg-purple-700 text-white px-8 py-3 rounded-xl font-medium text-lg hover:bg-purple-800 transition-colors">
            Browse Catalogue
          </Link>
          <Link to="/quick-order" className="bg-green-600 text-white px-8 py-3 rounded-xl font-medium text-lg hover:bg-green-700 transition-colors">
            ⚡ Quick Order
          </Link>
          <Link to="/register/agent" className="border-2 border-purple-700 text-purple-700 px-8 py-3 rounded-xl font-medium text-lg hover:bg-purple-50 transition-colors">
            Become an Agent
          </Link>
        </div>
      </section>

      <section className="max-w-5xl mx-auto py-16 px-4 grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
        {[
          { title: '99+ Fragrances', desc: 'Woody, floral, oriental, fresh — a scent for every customer.' },
          { title: 'Nationwide Delivery', desc: 'R65 flat rate. Free shipping on orders over R2000.' },
          { title: 'Agent Program', desc: 'Buy wholesale, sell at 2×. Earn 5% from your team.' },
          { title: 'WhatsApp Ordering', desc: 'Order in seconds via WhatsApp. No website needed.' },
        ].map(f => (
          <div key={f.title} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
            <p className="text-sm text-gray-500">{f.desc}</p>
          </div>
        ))}
      </section>

      <section className="max-w-5xl mx-auto pb-16 px-4 grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/quick-order" className="bg-white rounded-xl p-6 shadow-sm border border-purple-100 hover:border-purple-300 hover:shadow-md transition-all text-center group">
          <span className="text-3xl">⚡</span>
          <h3 className="font-semibold mt-2 group-hover:text-purple-700">Quick Order</h3>
          <p className="text-sm text-gray-500 mt-1">Add quantities and send your order in one tap</p>
        </Link>
        <Link to="/blog" className="bg-white rounded-xl p-6 shadow-sm border border-purple-100 hover:border-purple-300 hover:shadow-md transition-all text-center group">
          <span className="text-3xl">📝</span>
          <h3 className="font-semibold mt-2 group-hover:text-purple-700">Fragrance Blog</h3>
          <p className="text-sm text-gray-500 mt-1">Guides, tips, and industry insights for resellers</p>
        </Link>
        <Link to="/agents" className="bg-white rounded-xl p-6 shadow-sm border border-purple-100 hover:border-purple-300 hover:shadow-md transition-all text-center group">
          <span className="text-3xl">🔍</span>
          <h3 className="font-semibold mt-2 group-hover:text-purple-700">Find an Agent</h3>
          <p className="text-sm text-gray-500 mt-1">Find a Zen Fragrances agent in your area</p>
        </Link>
      </section>

      <section className="bg-white py-16 px-4">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">Frequently asked questions</h2>
          <div className="space-y-3">
            {faqs.map((faq, i) => (
              <div key={i} className="bg-gray-50 rounded-xl border border-gray-100 overflow-hidden">
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-gray-100 transition-colors">
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

      <section className="bg-purple-50 py-16 px-4">
        <div className="max-w-lg mx-auto text-center">
          <h2 className="text-2xl font-bold mb-2">Get launch updates</h2>
          <p className="text-gray-500 text-sm mb-6">New fragrances, deals and restock alerts straight to your inbox. No spam.</p>
          {subscribed ? (
            <p className="text-green-600 font-medium">✅ Thanks! You're on the list.</p>
          ) : (
            <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-2">
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@email.com"
                className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-300"
              />
              <button type="submit" className="bg-purple-700 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-purple-800 transition-colors">
                Sign Up
              </button>
            </form>
          )}
          {subError && <p className="text-red-600 text-sm mt-3">{subError}</p>}
        </div>
      </section>

      <section className="bg-purple-700 text-white py-16 text-center">
        <h2 className="text-3xl font-bold mb-4">Ready to start selling?</h2>
        <p className="text-purple-200 mb-6">Join as an agent, buy at wholesale, and sell at your own price.</p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link to="/register/agent" className="bg-white text-purple-700 px-8 py-3 rounded-xl font-medium text-lg hover:bg-purple-50 transition-colors">
            Become an Agent
          </Link>
          <Link to="/catalogue" className="border-2 border-white text-white px-8 py-3 rounded-xl font-medium text-lg hover:bg-purple-600 transition-colors">
            Browse Catalogue
          </Link>
        </div>
      </section>
    </div>
  );
}
