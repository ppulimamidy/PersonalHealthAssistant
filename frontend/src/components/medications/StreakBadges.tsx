'use client';

import { useQuery } from '@tanstack/react-query';
import { Flame, Trophy, AlertCircle } from 'lucide-react';
import { medicationsService } from '@/services/medications';

export function StreakBadges() {
  const { data, isLoading } = useQuery({
    queryKey: ['adherence-streaks'],
    queryFn: () => medicationsService.getAdherenceStreaks(90),
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="h-16 rounded-xl animate-pulse" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }} />
    );
  }

  if (!data || data.medications.length === 0) return null;

  const ocs = data.overall_current_streak;
  const ols = data.overall_longest_streak;

  // Find meds with at least 2 days of data and a pattern
  const patterned = data.medications.filter((m) => m.missed_days_of_week.length > 0);

  return (
    <div className="space-y-3">
      {/* Overall streak banner */}
      <div
        className="flex items-center justify-between p-4 rounded-xl"
        style={{
          backgroundColor: ocs >= 7 ? 'rgba(0,212,170,0.07)' : 'rgba(255,255,255,0.03)',
          border: `1px solid ${ocs >= 7 ? 'rgba(0,212,170,0.2)' : 'rgba(255,255,255,0.06)'}`,
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: ocs >= 7 ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.05)' }}
          >
            <Flame
              className="w-5 h-5"
              style={{ color: ocs >= 7 ? '#00D4AA' : '#526380' }}
            />
          </div>
          <div>
            <p className="text-sm font-semibold" style={{ color: '#E8EDF5' }}>
              {ocs === 0
                ? 'Start your streak'
                : ocs === 1
                ? '1 day streak'
                : `${ocs}-day streak`}
            </p>
            <p className="text-xs mt-0.5" style={{ color: '#526380' }}>
              All medications taken each day
            </p>
          </div>
        </div>
        {ols > 0 && (
          <div className="flex items-center gap-1.5 text-right">
            <Trophy className="w-3.5 h-3.5" style={{ color: '#FBB124' }} />
            <div>
              <p className="text-xs font-medium" style={{ color: '#FBB124' }}>
                Best: {ols}d
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Per-medication streaks */}
      {data.medications.length > 1 && (
        <div
          className="p-4 rounded-xl space-y-3"
          style={{
            backgroundColor: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.05)',
          }}
        >
          <p className="text-xs font-medium" style={{ color: '#526380' }}>
            PER MEDICATION
          </p>
          {data.medications.map((med) => {
            const pct =
              med.total_days_logged > 0
                ? Math.round((med.total_days_taken / med.total_days_logged) * 100)
                : null;
            return (
              <div key={med.medication_id} className="flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate" style={{ color: '#C8D5E8' }}>
                    {med.medication_name}
                  </p>
                  {med.missed_days_of_week.length > 0 && (
                    <p className="text-xs mt-0.5" style={{ color: '#F87171' }}>
                      Often missed: {med.missed_days_of_week.join(', ')}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  {pct !== null && (
                    <span
                      className="text-xs font-medium px-2 py-0.5 rounded-full"
                      style={{
                        backgroundColor:
                          pct >= 80
                            ? 'rgba(0,212,170,0.1)'
                            : pct >= 60
                            ? 'rgba(251,177,36,0.1)'
                            : 'rgba(248,113,113,0.1)',
                        color:
                          pct >= 80 ? '#00D4AA' : pct >= 60 ? '#FBB124' : '#F87171',
                      }}
                    >
                      {pct}%
                    </span>
                  )}
                  <div className="flex items-center gap-1">
                    <Flame
                      className="w-3.5 h-3.5"
                      style={{ color: med.current_streak >= 3 ? '#00D4AA' : '#3D4F66' }}
                    />
                    <span className="text-sm font-semibold" style={{ color: '#E8EDF5' }}>
                      {med.current_streak}d
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Missed dose pattern warning */}
      {patterned.length > 0 && (
        <div
          className="flex items-start gap-2.5 p-3 rounded-xl"
          style={{
            backgroundColor: 'rgba(248,113,113,0.06)',
            border: '1px solid rgba(248,113,113,0.15)',
          }}
        >
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#F87171' }} />
          <div>
            <p className="text-xs font-medium" style={{ color: '#F87171' }}>
              Missed-dose pattern detected
            </p>
            <p className="text-xs mt-0.5" style={{ color: '#8B97A8' }}>
              {patterned.map((m) => `${m.medication_name} (${m.missed_days_of_week.join(', ')})`).join(' · ')}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
