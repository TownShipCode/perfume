// Reviews wall — seeded placeholder reviews until real customer reviews exist (month 1).
const REVIEWS = [
  { name: 'Thabo M.', role: 'Agent — Soweto', text: 'Ordered on WhatsApp, got my stock in 3 days. The Sauvage sells itself at R70.', stars: 5 },
  { name: 'Nomsa K.', role: 'Agent — Tembisa', text: 'No starter pack is the whole point. I started with 10 bottles and grew my own team.', stars: 5 },
  { name: 'Sipho D.', role: 'Customer', text: 'Good Girl smells amazing and lasts the whole day. Better than what I used to pay 3x for.', stars: 5 },
  { name: 'Lerato P.', role: 'Agent — Mamelodi', text: 'The 5% commission from my team members adds up. Best side hustle I have.', stars: 5 },
];

function Stars({ n }) {
  return <span className="text-purple-500 text-sm">{'★'.repeat(n)}</span>;
}

export default function Reviews() {
  return (
    <section className="bg-white py-16 px-4">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-center mb-2">What our agents &amp; customers say</h2>
        <p className="text-gray-500 text-center text-sm mb-8">Because reviews say more than a thousand words.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {REVIEWS.map((r, i) => (
            <div key={i} className="bg-gray-50 rounded-xl border border-gray-100 p-5">
              <Stars n={r.stars} />
              <p className="text-sm text-gray-700 mt-2 leading-relaxed">"{r.text}"</p>
              <p className="text-xs text-gray-500 mt-3">
                <span className="font-semibold text-gray-700">{r.name}</span> · {r.role}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
