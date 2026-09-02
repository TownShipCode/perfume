import { createContext, useContext, useState, useCallback, useEffect } from 'react';

const CartContext = createContext(null);
const CART_KEY = 'zen_cart_v1';

function loadCart() {
  try {
    const raw = localStorage.getItem(CART_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function CartProvider({ children }) {
  const [items, setItems] = useState(loadCart);

  // Persist to localStorage so the cart survives page refresh.
  useEffect(() => {
    try {
      localStorage.setItem(CART_KEY, JSON.stringify(items));
    } catch {
      /* storage full or blocked — cart still works in-memory */
    }
  }, [items]);

  const addItem = useCallback((product) => {
    setItems(prev => {
      const existing = prev.find(i => i.id === product.id);
      if (existing) {
        return prev.map(i => i.id === product.id ? { ...i, qty: i.qty + 1 } : i);
      }
      return [...prev, { id: product.id, product_number: product.product_number, name: product.name, price: product.price, image_url: product.image_url, qty: 1 }];
    });
  }, []);

  const updateQty = useCallback((productId, qty) => {
    if (qty <= 0) {
      setItems(prev => prev.filter(i => i.id !== productId));
    } else {
      setItems(prev => prev.map(i => i.id === productId ? { ...i, qty } : i));
    }
  }, []);

  const removeItem = useCallback((productId) => {
    setItems(prev => prev.filter(i => i.id !== productId));
  }, []);

  const clearCart = useCallback(() => setItems([]), []);

  const total = items.reduce((sum, i) => sum + parseFloat(i.price || 0) * i.qty, 0);
  const count = items.reduce((sum, i) => sum + i.qty, 0);

  return (
    <CartContext.Provider value={{ items, addItem, updateQty, removeItem, clearCart, total, count }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be inside CartProvider');
  return ctx;
}
