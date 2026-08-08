import { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';
import { assembleChartjs } from 'flint-chart';

/**
 * FlintChart — renders a chart from a compact Flint spec via the Chart.js backend.
 * Data and semantic types come from the caller (e.g. /api/analytics/daily).
 * Ref: https://microsoft.github.io/flint-chart/ (MIT, Microsoft Research)
 */
export default function FlintChart({ values, semanticTypes, chartType, xField, yField, title, height = 280 }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!values || !values.length) return;

    const input = {
      data: { values },
      semantic_types: semanticTypes,
      chart_spec: {
        chartType,
        encodings: { x: { field: xField }, y: { field: yField } },
        baseSize: { width: 520, height },
      },
    };

    let config;
    try {
      config = assembleChartjs(input);
    } catch (e) {
      console.error('Flint assemble failed:', e.message);
      return;
    }
    if (!config.type) {
      config.type = chartType.toLowerCase().includes('bar') ? 'bar' : 'line';
    }

    if (chartRef.current) chartRef.current.destroy();
    chartRef.current = new Chart(canvasRef.current, config);

    return () => { if (chartRef.current) chartRef.current.destroy(); };
  }, [values, semanticTypes, chartType, xField, yField, height]);

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      {title && <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>}
      <canvas ref={canvasRef} />
    </div>
  );
}
