'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { medicationsService } from '@/services/medications';
import { Check, X, Pill } from 'lucide-react';
import type { TodayMedication } from '@/types';
import toast from 'react-hot-toast';

function SlotButton({
  slot,
  med,
  onLog,
}: {
  slot: number;
  med: TodayMedication;
  onLog: (medicationId: string, slot: number, wasTaken: boolean) => void;
}) {
  const log = med.logs.find((l) => {
    if (!l.scheduled_time) return false;
    const hour = new Date(l.scheduled_time).getUTCHours();
    const slotHour = slot === 1 ? 8 : slot === 2 ? 14 : 20;
    return hour === slotHour;
  });

  const taken = log?.was_taken;
  const missed = log && !log.was_taken;

  return (
    <div className="flex gap-1">
      <button
        onClick={() => onLog(med.medication_id, slot, true)}
        className="w-7 h-7 rounded-lg flex items-center justify-center transition-all"
        style={{
          backgroundColor: taken ? '#00D4AA' : 'rgba(0,212,170,0.08)',
          border: `1px solid ${taken ? '#00D4AA' : 'rgba(0,212,170,0.2)'}`,
        }}
        title="Mark taken"
      >
        <Check className={`w-3.5 h-3.5 ${taken ? 'text-white' : 'text-[#00D4AA]/50'}`} />
      </button>
      <button
        onClick={() => onLog(med.medication_id, slot, false)}
        className="w-7 h-7 rounded-lg flex items-center justify-center transition-all"
        style={{
          backgroundColor: missed ? 'rgba(248,113,113,0.15)' : 'rgba(255,255,255,0.03)',
          border: `1px solid ${missed ? 'rgba(248,113,113,0.4)' : 'rgba(255,255,255,0.06)'}`,
        }}
        title="Mark missed"
      >
        <X className={`w-3.5 h-3.5 ${missed ? 'text-red-400' : 'text-[#526380]/50'}`} />
      </button>
    </div>
  );
}

export function DailyAdherenceStrip() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['adherence-today'],
    queryFn: medicationsService.getTodayAdherence,
    staleTime: 30_000,
  });

  const { mutate: log } = useMutation({
    mutationFn: ({ medicationId, slot, wasTaken }: { medicationId: string; slot: number; wasTaken: boolean }) =>
      medicationsService.logAdherence({
        medication_id: medicationId,
        was_taken: wasTaken,
        scheduled_slot: slot,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adherence-today'] });
      queryClient.invalidateQueries({ queryKey: ['adherence-stats'] });
    },
    onError: () => toast.error('Failed to log dose'),
  });

  const handleLog = (medicationId: string, slot: number, wasTaken: boolean) => {
    log({ medicationId, slot, wasTaken });
  };

  if (isLoading) {
    return (
      <div
        className="rounded-xl p-4"
        style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
      >
        <div className="animate-pulse h-12 bg-white/5 rounded" />
      </div>
    );
  }

  const medications = data?.medications ?? [];

  if (medications.length === 0) {
    return (
      <div
        className="rounded-xl p-4 flex items-center gap-3"
        style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
      >
        <Pill className="w-4 h-4 text-[#526380]" />
        <p className="text-xs text-[#526380]">No medications scheduled today</p>
      </div>
    );
  }

  return (
    <div
      className="rounded-xl p-4"
      style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-[#E8EDF5] flex items-center gap-2">
          <Pill className="w-4 h-4 text-[#00D4AA]" />
          Today&apos;s Medications
        </h3>
        <span className="text-xs text-[#526380]">
          {medications.filter((m) => m.logs.some((l) => l.was_taken)).length}/{medications.length} taken
        </span>
      </div>

      <div className="space-y-2.5">
        {medications.map((med) => (
          <div key={med.medication_id} className="flex items-center gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-[#C8D5E8] truncate">{med.medication_name}</p>
              <p className="text-[10px] text-[#3D4F66]">{med.dosage}</p>
            </div>
            <div className="flex gap-1.5">
              {Array.from({ length: med.doses_today }, (_, i) => (
                <SlotButton
                  key={i + 1}
                  slot={i + 1}
                  med={med}
                  onLog={handleLog}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
