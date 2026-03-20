/**
 * Biomarker Trend Chart — sparkline with reference range band
 * and medication/supplement start markers.
 */

import { View, Text } from 'react-native';
import Svg, { Path, Circle, Rect, Line, Text as SvgText } from 'react-native-svg';

interface DataPoint {
  date: string;
  value: number;
  status: string;
}

interface Marker {
  date: string;
  label: string;
  type: 'med_start' | 'supp_start';
}

interface Props {
  dataPoints: DataPoint[];
  referenceRange?: { normal_min?: number; normal_max?: number };
  medicationMarkers?: Marker[];
  supplementMarkers?: Marker[];
  unit?: string;
  width?: number;
  height?: number;
}

const STATUS_COLORS: Record<string, string> = {
  normal: '#6EE7B7',
  borderline: '#F5A623',
  abnormal: '#F87171',
  critical: '#F87171',
  unknown: '#526380',
};

export default function BiomarkerTrendChart({
  dataPoints,
  referenceRange,
  medicationMarkers = [],
  supplementMarkers = [],
  unit = '',
  width = 280,
  height = 100,
}: Readonly<Props>) {
  if (dataPoints.length < 2) {
    return (
      <View className="items-center py-3">
        <Text className="text-[#3D4F66] text-xs">Need 2+ results for trend</Text>
      </View>
    );
  }

  const pad = 12;
  const chartW = width - pad * 2;
  const chartH = height - pad * 2;

  const values = dataPoints.map((d) => d.value);
  const allValues = [...values];
  if (referenceRange?.normal_min != null) allValues.push(referenceRange.normal_min);
  if (referenceRange?.normal_max != null) allValues.push(referenceRange.normal_max);

  const min = Math.min(...allValues) * 0.9;
  const max = Math.max(...allValues) * 1.1;
  const range = max - min || 1;

  const toX = (i: number) => pad + (i / (dataPoints.length - 1)) * chartW;
  const toY = (v: number) => pad + (1 - (v - min) / range) * chartH;

  // Reference range band
  const refMinY = referenceRange?.normal_max != null ? toY(referenceRange.normal_max) : null;
  const refMaxY = referenceRange?.normal_min != null ? toY(referenceRange.normal_min) : null;

  // Line path
  const pts = dataPoints.map((d, i) => ({ x: toX(i), y: toY(d.value), ...d }));
  const pathD = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');

  // Map marker dates to x positions
  const dateToX = (markerDate: string): number | null => {
    if (!markerDate) return null;
    const md = markerDate.slice(0, 10);
    // Find closest data point index
    let bestIdx = 0;
    let bestDist = Infinity;
    for (let i = 0; i < dataPoints.length; i++) {
      const dist = Math.abs(new Date(dataPoints[i].date).getTime() - new Date(md).getTime());
      if (dist < bestDist) {
        bestDist = dist;
        bestIdx = i;
      }
    }
    return toX(bestIdx);
  };

  const lastPt = pts[pts.length - 1];
  const lastColor = STATUS_COLORS[lastPt.status] ?? '#526380';

  return (
    <View>
      <Svg width={width} height={height}>
        {/* Reference range band */}
        {refMinY != null && refMaxY != null && (
          <Rect
            x={pad}
            y={refMinY}
            width={chartW}
            height={refMaxY - refMinY}
            fill="#6EE7B7"
            opacity={0.08}
            rx={4}
          />
        )}

        {/* Medication markers */}
        {medicationMarkers.map((m, i) => {
          const x = dateToX(m.date);
          if (x == null) return null;
          return (
            <Line
              key={`med-${i}`}
              x1={x} y1={pad} x2={x} y2={height - pad}
              stroke="#2DD4BF" strokeWidth={1} strokeDasharray="4,3" opacity={0.5}
            />
          );
        })}

        {/* Supplement markers */}
        {supplementMarkers.map((m, i) => {
          const x = dateToX(m.date);
          if (x == null) return null;
          return (
            <Line
              key={`supp-${i}`}
              x1={x} y1={pad} x2={x} y2={height - pad}
              stroke="#818CF8" strokeWidth={1} strokeDasharray="2,4" opacity={0.5}
            />
          );
        })}

        {/* Line */}
        <Path d={pathD} stroke="#8B9BB4" strokeWidth={2} fill="none" strokeLinecap="round" strokeLinejoin="round" />

        {/* Data points */}
        {pts.map((p, i) => (
          <Circle
            key={i}
            cx={p.x} cy={p.y} r={3.5}
            fill={STATUS_COLORS[p.status] ?? '#526380'}
          />
        ))}

        {/* Current value label */}
        <SvgText
          x={lastPt.x}
          y={lastPt.y - 8}
          fontSize={10}
          fill={lastColor}
          textAnchor="middle"
          fontWeight="600"
        >
          {lastPt.value}
        </SvgText>
      </Svg>

      {/* Marker legend */}
      {(medicationMarkers.length > 0 || supplementMarkers.length > 0) && (
        <View className="flex-row flex-wrap gap-2 mt-1 px-1">
          {medicationMarkers.map((m, i) => (
            <View key={`ml-${i}`} className="flex-row items-center gap-1">
              <View className="w-2 h-0.5 bg-[#2DD4BF]" />
              <Text className="text-[#3D4F66] text-[8px]">{m.label}</Text>
            </View>
          ))}
          {supplementMarkers.map((m, i) => (
            <View key={`sl-${i}`} className="flex-row items-center gap-1">
              <View className="w-2 h-0.5 bg-[#818CF8]" />
              <Text className="text-[#3D4F66] text-[8px]">{m.label}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}
