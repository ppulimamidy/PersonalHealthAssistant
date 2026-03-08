'use client';

import { useQuery } from '@tanstack/react-query';
import { medicationsService } from '@/services/medications';
import type { MedAdherenceHistory } from '@/types';

function dayLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00');
  const today = new Date();
  today.setHours(12, 0, 0, 0);
  const diff = Math.round((today.getTime() - d.getTime()) / 86400000);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Yest';
  return d.toLocaleDateString('en-US', { weekday: 'short' });
}

function Cell({ scheduled, taken }: { scheduled: number; taken: number }) {
  if (scheduled === 0) {
    return (
      <div className="w-7 h-7 flex items-center justify-center text-[#3D4F66] text-xs">·</div>
    );
  }
  const allTaken = taken >= scheduled;
  const noneTaken = taken === 0;
  return (
    <div
      className="w-7 h-7 rounded-md flex items-center justify-center text-[11px] font-bold"
      title={`${taken}/${scheduled} taken`}
      style={{
        backgroundColor: allTaken
          ? 'rgba(0,212,170,0.18)'
          : noneTaken
          ? 'rgba(248,113,113,0.15)'
          : 'rgba(251,191,36,0.15)',
        color: allTaken ? '#00D4AA' : noneTaken ? '#F87171' : '#FBD24C',
        border: `1px solid ${allTaken ? 'rgba(0,212,170,0.3)' : noneTaken ? 'rgba(248,113,113,0.3)' : 'rgba(251,191,36,0.3)'}`,
      }}
    >
      {allTaken ? '✓' : noneTaken ? '✗' : `${taken}/${scheduled}`}
    </div>
  );
}

export function AdherenceCalendar() {
  const { data, isLoading } = useQuery({
    queryKey: ['adherence-history', 7],
    queryFn: () => medicationsService.getAdherenceHistory(7),
    staleTime: 60_000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-20">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (!data || data.medications.length === 0) {
    return null;
  }

  const { dates, medications } = data;

  return (
    <div
      className="rounded-xl p-5"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <h3 className="text-sm font-semibold text-[#8B97A8] mb-4">7-Day Adherence</h3>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[360px]">
          <thead>
            <tr>
              <th className="text-left text-[11px] text-[#3D4F66] font-normal pb-2 pr-3 w-32">
                Medication
              </th>
              {dates.map((d) => (
                <th key={d} className="text-center text-[11px] text-[#3D4F66] font-normal pb-2 px-0.5 w-8">
                  {dayLabel(d)}
                </th>
              ))}
              <th className="text-right text-[11px] text-[#3D4F66] font-normal pb-2 pl-3 w-16">
                Rate
              </th>
            </tr>
          </thead>
          <tbody>
            {medications.map((med: MedAdherenceHistory) => {
              const totalScheduled = dates.reduce(
                (s, d) => s + (med.days[d]?.scheduled ?? 0),
                0
              );
              const totalTaken = dates.reduce(
                (s, d) => s + (med.days[d]?.taken ?? 0),
                0
              );
              const rate = totalScheduled > 0 ? Math.round((totalTaken / totalScheduled) * 100) : null;

              return (
                <tr key={med.medication_id ?? med.medication_name} className="border-t border-white/5">
                  <td className="pr-3 py-2">
                    <span className="text-xs text-[#C8D5E8] truncate block max-w-[112px]" title={med.medication_name}>
                      {med.medication_name}
                    </span>
                  </td>
                  {dates.map((d) => (
                    <td key={d} className="px-0.5 py-2">
                      <Cell
                        scheduled={med.days[d]?.scheduled ?? 0}
                        taken={med.days[d]?.taken ?? 0}
                      />
                    </td>
                  ))}
                  <td className="pl-3 py-2 text-right">
                    <span
                      className="text-xs font-semibold"
                      style={{
                        color:
                          rate == null
                            ? '#526380'
                            : rate >= 80
                            ? '#00D4AA'
                            : rate >= 50
                            ? '#FBD24C'
                            : '#F87171',
                      }}
                    >
                      {rate != null ? `${rate}%` : '—'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-4 mt-4 text-[10px] text-[#3D4F66]">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: 'rgba(0,212,170,0.25)', border: '1px solid rgba(0,212,170,0.4)' }} />
          Taken
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: 'rgba(248,113,113,0.2)', border: '1px solid rgba(248,113,113,0.35)' }} />
          Missed
        </span>
        <span className="flex items-center gap-1">
          <span className="text-[#3D4F66]">·</span>
          Not scheduled
        </span>
      </div>
    </div>
  );
}
