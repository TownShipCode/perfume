// Creative placeholder emoji per scent — used until real product photos exist.
// Keeps the brand feel: soft purple/amber tile with a scent-inspired glyph.

const EMOJI_BY_NAME = {
  '212 VIP': '🥂',
  'DESIRE': '🔥',
  'INVICTUS': '🏆',
  "L'EAU D'ISSEY": '🌊',
  'LEGEND': '🦁',
  'ONE MILLION': '💵',
  'ONLY THE BRAVE': '🦅',
  'SCANDAL': '🖤',
  'ARMANI SI': '🌹',
  'BLACK OPIUM': '🌙',
  'CHANNEL NO 5': '⭐',
  'GOOD GIRL': '👠',
  'GUCCI RUSH': '⚡',
  'LADY MILLION': '💎',
  'NARCISO RODRIGUEZ': '🌸',
};

export function productEmoji(product) {
  if (!product) return '🧴';
  const name = (product.name || '').toUpperCase().trim();
  if (name === 'SCANDAL' && product.gender === 'women') return '🍒';
  return EMOJI_BY_NAME[name] || (product.gender === 'women' ? '🌷' : product.gender === 'men' ? '🫧' : '🧴');
}
