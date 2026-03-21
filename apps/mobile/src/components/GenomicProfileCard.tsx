/**
 * Genomic Profile Card — summary of user's molecular profile
 * with mutation badges and "Search clinical trials" CTA.
 */

import { View, Text, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { api } from '@/services/api';

interface Mutation {
  gene: string;
  exon?: string;
  protein_change?: string;
  classification?: { tier?: string; level?: string };
  sensitivity?: string;
  sensitive_therapies?: string[];
}

export default function GenomicProfileCard() {
  const { data } = useQuery({
    queryKey: ['medical-records', 'genomic'],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get('/api/v1/medical-records?record_type=genomic');
        const records = resp?.records ?? [];
        // Extract all mutations from all genomic records
        const mutations: Mutation[] = [];
        for (const rec of records) {
          let ed = rec.extracted_data;
          if (typeof ed === 'string') {
            try { ed = JSON.parse(ed); } catch { ed = {}; }
          }
          for (const m of ed?.mutations ?? []) {
            mutations.push(m);
          }
        }
        return mutations;
      } catch { return []; }
    },
    staleTime: 10 * 60_000,
  });

  if (!data || data.length === 0) return null;

  return (
    <View className="bg-surface-raised border border-[#818CF830] rounded-2xl p-4 mb-3">
      <View className="flex-row items-center gap-2 mb-3">
        <Ionicons name="code-working-outline" size={14} color="#818CF8" />
        <Text className="text-[#818CF8] text-xs uppercase tracking-wider font-sansMedium">Your Molecular Profile</Text>
      </View>

      {/* Mutation badges */}
      <View className="flex-row flex-wrap gap-2 mb-3">
        {data.map((m, i) => {
          const color = m.sensitivity === 'Sensitive' ? '#6EE7B7' : m.sensitivity === 'Resistant' ? '#F87171' : '#526380';
          return (
            <View key={i} className="bg-white/5 rounded-lg px-2.5 py-1.5">
              <View className="flex-row items-center gap-1">
                <Text className="text-[#E8EDF5] text-xs font-sansMedium">{m.gene}</Text>
                {m.classification?.tier && (
                  <View className="bg-[#818CF820] rounded px-1 py-0.5">
                    <Text className="text-[#818CF8] text-[8px]">{m.classification.tier}</Text>
                  </View>
                )}
                <View className="rounded px-1 py-0.5" style={{ backgroundColor: `${color}15` }}>
                  <Text className="text-[8px]" style={{ color }}>{m.sensitivity ?? 'Unknown'}</Text>
                </View>
              </View>
              {m.protein_change && (
                <Text className="text-[#526380] text-[9px] mt-0.5">{m.protein_change}</Text>
              )}
              {m.sensitive_therapies && m.sensitive_therapies.length > 0 && (
                <Text className="text-[#00D4AA] text-[9px] mt-0.5" numberOfLines={1}>
                  → {m.sensitive_therapies.slice(0, 3).join(', ')}
                </Text>
              )}
            </View>
          );
        })}
      </View>

      {/* CTAs */}
      <View className="flex-row gap-2">
        <TouchableOpacity
          onPress={() => {
            const genes = data.map((m) => m.gene).filter(Boolean);
            const query = `${genes.join(' ')} mutation targeted therapy`;
            router.push({
              pathname: '/(tabs)/chat/research',
              params: { initialQuery: query },
            } as never);
          }}
          className="flex-1 flex-row items-center justify-center gap-1 py-2 rounded-lg"
          style={{ backgroundColor: '#818CF815', borderWidth: 1, borderColor: '#818CF830' }}
          activeOpacity={0.7}
        >
          <Ionicons name="flask-outline" size={12} color="#818CF8" />
          <Text className="text-[#818CF8] text-xs font-sansMedium">Research treatments</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => {
            const genes = data.map((m) => m.gene).filter(Boolean);
            router.push({
              pathname: '/(tabs)/chat/research',
              params: { initialQuery: `clinical trials ${genes.join(' ')} mutation` },
            } as never);
          }}
          className="flex-1 flex-row items-center justify-center gap-1 py-2 rounded-lg"
          style={{ backgroundColor: '#00D4AA12', borderWidth: 1, borderColor: '#00D4AA25' }}
          activeOpacity={0.7}
        >
          <Ionicons name="search-outline" size={12} color="#00D4AA" />
          <Text className="text-[#00D4AA] text-xs font-sansMedium">Find trials</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
