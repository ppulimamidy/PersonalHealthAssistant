'use client';

import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, XCircle, HelpCircle, Beaker } from 'lucide-react';
import { api } from '@/services/api';

interface EfficacyEntry {
  id: string;
  pattern: string;
  category: string;
  interventions_tried: number;
  avg_effect_size: number;
  confidence: number;
  best_duration: number | null;
  adherence_avg: number;
  last_tested: string | null;
  status: string;
  notes: string | null;
}

interface EfficacySummary {
  entries: EfficacyEntry[];
  proven: EfficacyEntry[];
  disproven: EfficacyEntry[];
  inconclusive: EfficacyEntry[];
  untested: string[];
  ai_summary: string | null;
}

const PATTERN_LABELS: Record<string, string> = {
  overtraining: 'Recovery Nutrition',
  inflammation: 'Anti-Inflammatory Diet',
  poor_recovery: 'Recovery Optimization',
  sleep_disruption: 'Sleep Hygiene + Nutrition',
};

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? '#00D4AA' : pct >= 40 ? '#F5A623' : '#526380';
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 rounded-full bg-white/5 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-[10px] text-[#526380]">{pct}%</span>
    </div>
  );
}

function EntryCard({ entry }: { entry: EfficacyEntry }) {
  const label = PATTERN_LABELS[entry.pattern] || entry.pattern.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const StatusIcon = entry.status === 'proven' ? CheckCircle2 : entry.status === 'disproven' ? XCircle : HelpCircle;
  const statusColor = entry.status === 'proven' ? '#00D4AA' : entry.status === 'disproven' ? '#F87171' : '#F5A623';
  const effectColor = entry.avg_effect_size > 3 ? '#00D4AA' : entry.avg_effect_size < -1 ? '#F87171' : '#526380';

  return (
    <div
      className="rounded-xl p-4"
      style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <StatusIcon className="w-4 h-4 flex-shrink-0" style={{ color: statusColor }} />
          <span className="text-sm font-medium text-[#E8EDF5]">{label}</span>
        </div>
        <span
          className="text-[10px] font-medium uppercase px-2 py-0.5 rounded-full"
          style={{ backgroundColor: `${statusColor}15`, color: statusColor }}
        >
          {entry.status}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-xs">
        <div>
          <p className="text-[#526380] text-[10px] uppercase tracking-wider mb-0.5">Times Tried</p>
          <p className="text-[#E8EDF5] font-medium">{entry.interventions_tried}</p>
        </div>
        <div>
          <p className="text-[#526380] text-[10px] uppercase tracking-wider mb-0.5">Avg Effect</p>
          <p className="font-medium" style={{ color: effectColor }}>
            {entry.avg_effect_size > 0 ? '+' : ''}{entry.avg_effect_size.toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-[#526380] text-[10px] uppercase tracking-wider mb-0.5">Adherence</p>
          <p className="text-[#E8EDF5] font-medium">{Math.round(entry.adherence_avg)}%</p>
        </div>
      </div>

      <div className="mt-2">
        <p className="text-[#526380] text-[10px] uppercase tracking-wider mb-0.5">Confidence</p>
        <ConfidenceBar value={entry.confidence} />
      </div>

      {entry.best_duration && (
        <p className="text-[10px] text-[#3D4F66] mt-2">Best duration: {entry.best_duration} days</p>
      )}
    </div>
  );
}

export default function EfficacyPage() {
  const { data, isLoading } = useQuery<EfficacySummary>({
    queryKey: ['efficacy'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/efficacy');
      return resp;
    },
  });

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[#E8EDF5]">What Works for Me</h1>
        <p className="text-sm text-[#526380] mt-1">Your personal health response profile, built from your experiments.</p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : !data || data.entries.length === 0 ? (
        <div
          className="rounded-xl p-8 text-center"
          style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
        >
          <Beaker className="w-10 h-10 text-[#526380] mx-auto mb-3" />
          <p className="text-sm text-[#E8EDF5] font-medium">No experiments yet</p>
          <p className="text-xs text-[#526380] mt-1">Complete your first experiment from the Home screen to start building your personal profile.</p>
        </div>
      ) : (
        <>
          {/* AI Summary */}
          {data.ai_summary && (
            <div
              className="rounded-xl p-4"
              style={{ backgroundColor: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.12)' }}
            >
              <p className="text-xs text-[#8B97A8] leading-relaxed">{data.ai_summary}</p>
            </div>
          )}

          {/* Proven */}
          {data.proven.length > 0 && (
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-wider text-[#00D4AA] mb-3">
                Proven Effective ({data.proven.length})
              </h2>
              <div className="space-y-3">
                {data.proven.map((e) => <EntryCard key={e.id} entry={e} />)}
              </div>
            </div>
          )}

          {/* Inconclusive */}
          {data.inconclusive.length > 0 && (
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-wider text-[#F5A623] mb-3">
                Inconclusive ({data.inconclusive.length})
              </h2>
              <div className="space-y-3">
                {data.inconclusive.map((e) => <EntryCard key={e.id} entry={e} />)}
              </div>
            </div>
          )}

          {/* Disproven */}
          {data.disproven.length > 0 && (
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-wider text-[#F87171] mb-3">
                Not Effective for You ({data.disproven.length})
              </h2>
              <div className="space-y-3">
                {data.disproven.map((e) => <EntryCard key={e.id} entry={e} />)}
              </div>
            </div>
          )}

          {/* Untested */}
          {data.untested.length > 0 && (
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-wider text-[#526380] mb-3">
                Not Yet Tested ({data.untested.length})
              </h2>
              <div className="flex flex-wrap gap-2">
                {data.untested.map((p) => (
                  <span
                    key={p}
                    className="text-xs px-3 py-1.5 rounded-lg text-[#8B97A8]"
                    style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
                  >
                    {PATTERN_LABELS[p] || p.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
