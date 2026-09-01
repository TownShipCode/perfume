import { useEffect, useState } from 'react';
import { api } from './api';

const FALLBACK = { shipping_fee: '65.00', free_shipping_threshold: '2000.00' };

let cached = null;

export function useConfig() {
  const [config, setConfig] = useState(cached || FALLBACK);
  useEffect(() => {
    if (cached) return;
    api('/api/config')
      .then(d => { cached = d; setConfig(d); })
      .catch(() => { /* keep fallback */ });
  }, []);
  return config;
}

export function shippingFee(config) {
  return parseFloat(config.shipping_fee || '65');
}

export function freeThreshold(config) {
  return parseFloat(config.free_shipping_threshold || '2000');
}
