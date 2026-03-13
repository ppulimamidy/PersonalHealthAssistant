/**
 * Shared mini line chart component built on react-native-svg.
 * Used across Trends, Predictions, and other data-heavy screens.
 */

import { Dimensions } from 'react-native';
import Svg, { Path, Circle, Line, Text as SvgText } from 'react-native-svg';

const SCREEN_WIDTH = Dimensions.get('window').width;

interface MiniLineChartProps {
  data: number[];
  color?: string;
  height?: number;
  /** Optional width override; defaults to screen width minus 64 (px6 * 2 padding + card border) */
  width?: number;
  showDots?: boolean;
  showLastValue?: boolean;
}

export function MiniLineChart({
  data,
  color = '#00D4AA',
  height = 64,
  width = SCREEN_WIDTH - 80,
  showDots = false,
  showLastValue = false,
}: MiniLineChartProps) {
  if (data.length < 2) return null;

  const pad = 6;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const pts = data.map((v, i) => ({
    x: pad + (i / (data.length - 1)) * (width - pad * 2),
    y: pad + (1 - (v - min) / range) * (height - pad * 2 - (showLastValue ? 14 : 0)),
    v,
  }));

  const d = pts
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(' ');

  const last = pts[pts.length - 1];
  const first = pts[0];
  const trend = last.v - first.v;

  return (
    <Svg width={width} height={height + (showLastValue ? 4 : 0)}>
      <Path
        d={d}
        stroke={color}
        strokeWidth={2}
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {showDots &&
        pts.map((p, i) => (
          <Circle key={i} cx={p.x} cy={p.y} r={2.5} fill={color} opacity={0.7} />
        ))}
      {/* Last point highlight */}
      <Circle cx={last.x} cy={last.y} r={3.5} fill={color} />
      {showLastValue && (
        <SvgText
          x={last.x}
          y={height - 2}
          fontSize={10}
          fill={color}
          textAnchor="middle"
          fontWeight="600"
        >
          {last.v % 1 === 0 ? last.v : last.v.toFixed(1)}
        </SvgText>
      )}
    </Svg>
  );
}
