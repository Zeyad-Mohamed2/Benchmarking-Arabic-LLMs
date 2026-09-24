import React, { useState } from 'react';
import { BenchmarkResults } from '../../types';

interface ModelRadarChartProps {
  results: BenchmarkResults;
}

const PALETTE = [
  { stroke: '#32C4B7', fill: 'rgba(50, 196, 183, 0.25)', dot: '#32C4B7' },
  { stroke: '#818cf8', fill: 'rgba(129, 140, 248, 0.25)', dot: '#818cf8' },
  { stroke: '#f472b6', fill: 'rgba(244, 114, 182, 0.25)', dot: '#f472b6' },
  { stroke: '#fbbf24', fill: 'rgba(251, 191, 36, 0.25)', dot: '#fbbf24' },
  { stroke: '#34d399', fill: 'rgba(52, 211, 153, 0.25)', dot: '#34d399' },
  { stroke: '#a78bfa', fill: 'rgba(167, 139, 250, 0.25)', dot: '#a78bfa' },
];

export const ModelRadarChart: React.FC<ModelRadarChartProps> = ({ results }) => {
  const modelEntries = Object.entries(results.model_results || {});
  const [hiddenModels, setHiddenModels] = useState<Set<string>>(new Set());

  if (modelEntries.length === 0) {
    return <div className="text-gray-400 text-sm">No model data available for radar visualization.</div>;
  }

  // Collect all available numeric metric keys across all models
  const metricKeysSet = new Set<string>();
  modelEntries.forEach(([_, item]) => {
    Object.entries(item.scores || {}).forEach(([k, v]) => {
      if (typeof v === 'number' && !isNaN(v)) {
        metricKeysSet.add(k);
      }
    });
  });

  const metrics = Array.from(metricKeysSet).slice(0, 8); // Display up to 8 axes for clean radar
  if (metrics.length < 3) {
    // If fewer than 3 metrics, a radar polygon cannot form nicely
    return (
      <div className="bg-[#1f2937]/30 p-6 rounded-lg border border-gray-700/50 text-gray-400 text-sm text-center">
        Radar chart requires at least 3 distinct evaluation metrics (found: {metrics.length}).
      </div>
    );
  }

  const toggleModel = (model: string) => {
    setHiddenModels(prev => {
      const next = new Set(prev);
      if (next.has(model)) next.delete(model);
      else next.add(model);
      return next;
    });
  };

  const size = 460;
  const center = size / 2;
  const radius = size * 0.36;
  const numMetrics = metrics.length;
  const angleStep = (Math.PI * 2) / numMetrics;

  const getCoordinates = (index: number, value: number) => {
    const angle = index * angleStep - Math.PI / 2;
    const clampedVal = Math.max(0, Math.min(1, value));
    const r = clampedVal * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  const rings = [0.25, 0.5, 0.75, 1.0];

  return (
    <div className="bg-[#1f2937]/30 border border-gray-700/50 rounded-xl p-6">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-4">
        <div>
          <h4 className="text-lg font-bold text-white flex items-center">
            🕸️ Multi-Metric Performance Radar
          </h4>
          <p className="text-xs text-gray-400 mt-1">
            Comparative normalized radar profile across all evaluation dimensions. Click model pills to toggle visibility.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-2">
          {modelEntries.map(([model], idx) => {
            const color = PALETTE[idx % PALETTE.length];
            const isHidden = hiddenModels.has(model);
            return (
              <button
                key={model}
                onClick={() => toggleModel(model)}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-all flex items-center gap-1.5 ${
                  isHidden
                    ? 'border-gray-700 bg-gray-800/40 text-gray-500 opacity-60'
                    : 'border-gray-600 bg-gray-900/80 text-gray-200'
                }`}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: isHidden ? '#6b7280' : color.stroke }}
                />
                <span className="truncate max-w-[140px]">{model.replace(':free', '')}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex justify-center items-center overflow-x-auto py-2">
        <svg width={size} height={size} className="overflow-visible">
          {/* Concentric Grid Rings */}
          {rings.map((ring) => {
            const r = ring * radius;
            const ringPoints = Array.from({ length: numMetrics }, (_, i) => {
              const angle = i * angleStep - Math.PI / 2;
              return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
            }).join(' ');

            return (
              <g key={ring}>
                <polygon
                  points={ringPoints}
                  fill="none"
                  stroke="#374151"
                  strokeWidth="1"
                  strokeDasharray={ring < 1.0 ? '3,3' : undefined}
                />
                <text
                  x={center + 6}
                  y={center - r + 12}
                  fill="#6b7280"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  {ring.toFixed(2)}
                </text>
              </g>
            );
          })}

          {/* Spokes & Axis Labels */}
          {metrics.map((metric, i) => {
            const end = getCoordinates(i, 1.0);
            const labelDist = radius + 22;
            const angle = i * angleStep - Math.PI / 2;
            const labelX = center + labelDist * Math.cos(angle);
            const labelY = center + labelDist * Math.sin(angle);

            let textAnchor: 'middle' | 'start' | 'end' = 'middle';
            if (Math.cos(angle) > 0.3) textAnchor = 'start';
            else if (Math.cos(angle) < -0.3) textAnchor = 'end';

            return (
              <g key={metric}>
                <line
                  x1={center}
                  y1={center}
                  x2={end.x}
                  y2={end.y}
                  stroke="#374151"
                  strokeWidth="1"
                />
                <text
                  x={labelX}
                  y={labelY + 4}
                  fill="#9ca3af"
                  fontSize="11"
                  fontWeight="600"
                  textAnchor={textAnchor}
                  className="select-none"
                >
                  {metric}
                </text>
              </g>
            );
          })}

          {/* Model Polygons */}
          {modelEntries.map(([model, item], idx) => {
            if (hiddenModels.has(model)) return null;
            const color = PALETTE[idx % PALETTE.length];

            const coords = metrics.map((metric, i) => {
              const val = Number(item.scores?.[metric] ?? 0);
              return getCoordinates(i, val);
            });

            const pointsStr = coords.map(c => `${c.x},${c.y}`).join(' ');

            return (
              <g key={model} className="transition-all duration-300">
                <polygon
                  points={pointsStr}
                  fill={color.fill}
                  stroke={color.stroke}
                  strokeWidth="2.5"
                />
                {coords.map((c, ptIdx) => (
                  <circle
                    key={ptIdx}
                    cx={c.x}
                    cy={c.y}
                    r="4"
                    fill={color.dot}
                    stroke="#111827"
                    strokeWidth="1.5"
                  />
                ))}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};
