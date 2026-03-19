import { View, Text, ScrollView, ActivityIndicator } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
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

function statusIcon(status: string): { name: string; color: string } {
  if (status === 'proven') return { name: 'checkmark-circle', color: '#00D4AA' };
  if (status === 'disproven') return { name: 'close-circle', color: '#F87171' };
  return { name: 'help-circle', color: '#F5A623' };
}

function EntryCard({ entry }: { entry: EfficacyEntry }) {
  const label = PATTERN_LABELS[entry.pattern] || entry.pattern.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
  const icon = statusIcon(entry.status);
  const effectColor = entry.avg_effect_size > 3 ? '#00D4AA' : entry.avg_effect_size < -1 ? '#F87171' : '#526380';
  const confPct = Math.round(entry.confidence * 100);
  const confColor = confPct >= 70 ? '#00D4AA' : confPct >= 40 ? '#F5A623' : '#526380';

  return (
    <View
      className="rounded-xl p-4 mb-2"
      style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <View className="flex-row items-center justify-between mb-2">
        <View className="flex-row items-center gap-2">
          <Ionicons name={icon.name as never} size={16} color={icon.color} />
          <Text className="text-sm font-sansMedium text-[#E8EDF5]">{label}</Text>
        </View>
        <View className="rounded-full px-2 py-0.5" style={{ backgroundColor: `${icon.color}15` }}>
          <Text className="text-[9px] font-bold uppercase" style={{ color: icon.color }}>{entry.status}</Text>
        </View>
      </View>

      <View className="flex-row gap-4 mb-2">
        <View>
          <Text className="text-[9px] text-[#526380] uppercase tracking-wider">Tried</Text>
          <Text className="text-xs font-sansMedium text-[#E8EDF5]">{entry.interventions_tried}x</Text>
        </View>
        <View>
          <Text className="text-[9px] text-[#526380] uppercase tracking-wider">Avg Effect</Text>
          <Text className="text-xs font-sansMedium" style={{ color: effectColor }}>
            {entry.avg_effect_size > 0 ? '+' : ''}{entry.avg_effect_size.toFixed(1)}%
          </Text>
        </View>
        <View>
          <Text className="text-[9px] text-[#526380] uppercase tracking-wider">Adherence</Text>
          <Text className="text-xs font-sansMedium text-[#E8EDF5]">{Math.round(entry.adherence_avg)}%</Text>
        </View>
      </View>

      <View>
        <Text className="text-[9px] text-[#526380] uppercase tracking-wider mb-1">Confidence</Text>
        <View className="flex-row items-center gap-2">
          <View className="flex-1 h-1.5 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
            <View className="h-1.5 rounded-full" style={{ width: `${confPct}%`, backgroundColor: confColor }} />
          </View>
          <Text className="text-[10px] text-[#526380]">{confPct}%</Text>
        </View>
      </View>
    </View>
  );
}

export default function EfficacyScreen() {
  const { data, isLoading } = useQuery<EfficacySummary>({
    queryKey: ['efficacy'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/efficacy');
      return resp;
    },
  });

  return (
    <ScrollView
      className="flex-1 bg-obsidian-900"
      contentContainerStyle={{ padding: 16, paddingTop: 56, paddingBottom: 32 }}
    >
      <Text className="text-2xl font-display text-[#E8EDF5] mb-1">What Works for Me</Text>
      <Text className="text-sm text-[#526380] mb-6">Personal health response profile</Text>

      {isLoading ? (
        <ActivityIndicator color="#00D4AA" className="mt-10" />
      ) : !data || data.entries.length === 0 ? (
        <View
          className="rounded-2xl p-6 items-center"
          style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
        >
          <Ionicons name="flask-outline" size={36} color="#526380" />
          <Text className="text-[#E8EDF5] font-sansMedium text-base mt-3 mb-1">No experiments yet</Text>
          <Text className="text-[#526380] text-sm text-center leading-5">
            Complete your first experiment from the Home screen to start building your personal profile.
          </Text>
        </View>
      ) : (
        <>
          {data.ai_summary && (
            <View
              className="rounded-xl p-4 mb-4"
              style={{ backgroundColor: 'rgba(0,212,170,0.04)', borderWidth: 1, borderColor: 'rgba(0,212,170,0.12)' }}
            >
              <Text className="text-xs text-[#8B97A8] leading-5">{data.ai_summary}</Text>
            </View>
          )}

          {data.proven.length > 0 && (
            <View className="mb-4">
              <Text className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: '#00D4AA' }}>
                Proven Effective ({data.proven.length})
              </Text>
              {data.proven.map((e) => <EntryCard key={e.id} entry={e} />)}
            </View>
          )}

          {data.inconclusive.length > 0 && (
            <View className="mb-4">
              <Text className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: '#F5A623' }}>
                Inconclusive ({data.inconclusive.length})
              </Text>
              {data.inconclusive.map((e) => <EntryCard key={e.id} entry={e} />)}
            </View>
          )}

          {data.disproven.length > 0 && (
            <View className="mb-4">
              <Text className="text-xs font-bold uppercase tracking-wider mb-2" style={{ color: '#F87171' }}>
                Not Effective ({data.disproven.length})
              </Text>
              {data.disproven.map((e) => <EntryCard key={e.id} entry={e} />)}
            </View>
          )}

          {data.untested.length > 0 && (
            <View className="mb-4">
              <Text className="text-xs font-bold uppercase tracking-wider text-[#526380] mb-2">
                Not Yet Tested ({data.untested.length})
              </Text>
              <View className="flex-row flex-wrap gap-2">
                {data.untested.map((p) => (
                  <View
                    key={p}
                    className="rounded-lg px-3 py-1.5"
                    style={{ backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' }}
                  >
                    <Text className="text-xs text-[#8B97A8]">
                      {PATTERN_LABELS[p] || p.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
                    </Text>
                  </View>
                ))}
              </View>
            </View>
          )}
        </>
      )}
    </ScrollView>
  );
}
