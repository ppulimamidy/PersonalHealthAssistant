/**
 * Clinical Research Screen — treatments, drugs, trials, guidelines.
 * Multi-source search with AI synthesis personalized to user's conditions.
 */

import { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, TextInput,
  ActivityIndicator, Share,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';
import ClinicalTrialCard from '@/components/ClinicalTrialCard';

// ─── Types ────────────────────────────────────────────────────────────────────

interface DrugProfile {
  name: string;
  drug_class: string;
  mechanism: string;
  approved_indications: string[];
  efficacy_summary: string;
  side_effects: { common: string[]; serious: string[] };
  interactions_with_user_meds: string[];
  cost_range: string;
  guideline_position: string;
}

interface TreatmentOption {
  name: string;
  type: string;
  evidence_level: string;
  efficacy: string;
  guideline_position: string;
  side_effects: string;
  compatibility: string;
  notes: string;
}

interface TreatmentReport {
  condition: string;
  guidelines_referenced: string[];
  treatment_options: TreatmentOption[];
  drug_comparisons: any[];
  doctor_questions: string[];
  disclaimer: string;
}

interface SearchResult {
  articles: any[];
  drugs_mentioned: DrugProfile[];
  ai_synthesis: string;
  treatment_report?: TreatmentReport;
}

// ─── Components ───────────────────────────────────────────────────────────────

function DrugProfileCard({ drug }: Readonly<{ drug: DrugProfile }>) {
  const [expanded, setExpanded] = useState(false);
  const hasInteractions = drug.interactions_with_user_meds?.length > 0;

  return (
    <TouchableOpacity
      onPress={() => setExpanded((e) => !e)}
      className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2"
      activeOpacity={0.8}
    >
      <View className="flex-row items-center justify-between mb-1">
        <Text className="text-[#E8EDF5] font-sansMedium text-sm flex-1">{drug.name}</Text>
        {hasInteractions ? (
          <View className="bg-[#F8717115] rounded px-1.5 py-0.5">
            <Text className="text-[#F87171] text-[9px]">Interaction</Text>
          </View>
        ) : (
          <View className="bg-[#6EE7B715] rounded px-1.5 py-0.5">
            <Text className="text-[#6EE7B7] text-[9px]">Compatible</Text>
          </View>
        )}
      </View>
      <Text className="text-[#526380] text-xs">{drug.drug_class}</Text>
      {drug.guideline_position && (
        <Text className="text-[#818CF8] text-[10px] mt-0.5">{drug.guideline_position}</Text>
      )}

      {expanded && (
        <View className="mt-3 pt-3 border-t border-surface-border">
          <Text className="text-[#8B9BB4] text-xs leading-5 mb-2">{drug.mechanism}</Text>
          <Text className="text-[#E8EDF5] text-xs font-sansMedium mb-1">Efficacy</Text>
          <Text className="text-[#526380] text-xs leading-4 mb-2">{drug.efficacy_summary}</Text>
          {drug.side_effects?.common?.length > 0 && (
            <View className="mb-2">
              <Text className="text-[#F5A623] text-[10px] font-sansMedium">Common side effects</Text>
              <Text className="text-[#526380] text-xs">{drug.side_effects.common.join(', ')}</Text>
            </View>
          )}
          {hasInteractions && (
            <View className="bg-[#F8717110] rounded-lg p-2 mb-2">
              <Text className="text-[#F87171] text-[10px] font-sansMedium mb-0.5">Interactions with your meds</Text>
              {drug.interactions_with_user_meds.map((int, i) => (
                <Text key={i} className="text-[#F87171] text-xs">• {int}</Text>
              ))}
            </View>
          )}
          {drug.cost_range && (
            <Text className="text-[#3D4F66] text-[10px]">Cost: {drug.cost_range}</Text>
          )}
        </View>
      )}
    </TouchableOpacity>
  );
}

function TreatmentOptionCard({ option, rank }: Readonly<{ option: TreatmentOption; rank: number }>) {
  const [expanded, setExpanded] = useState(false);
  const evidenceColor = option.evidence_level === 'strong' ? '#6EE7B7' : option.evidence_level === 'moderate' ? '#F5A623' : '#526380';

  return (
    <TouchableOpacity
      onPress={() => setExpanded((e) => !e)}
      className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2"
      activeOpacity={0.8}
    >
      <View className="flex-row items-start gap-2">
        <View className="w-6 h-6 rounded-full bg-white/5 items-center justify-center">
          <Text className="text-[#526380] text-xs font-sansMedium">{rank}</Text>
        </View>
        <View className="flex-1">
          <View className="flex-row items-center gap-2 mb-0.5">
            <Text className="text-[#E8EDF5] font-sansMedium text-sm">{option.name}</Text>
            <View className="rounded px-1.5 py-0.5" style={{ backgroundColor: `${evidenceColor}15` }}>
              <Text className="text-[9px] font-sansMedium" style={{ color: evidenceColor }}>{option.evidence_level}</Text>
            </View>
          </View>
          {option.guideline_position && (
            <Text className="text-[#818CF8] text-[10px]">{option.guideline_position}</Text>
          )}
          <Text className="text-[#526380] text-xs mt-1" numberOfLines={expanded ? undefined : 2}>{option.efficacy}</Text>
        </View>
      </View>

      {expanded && (
        <View className="mt-2 ml-8">
          {option.side_effects && (
            <Text className="text-[#F5A623] text-[10px] mb-1">Side effects: {option.side_effects}</Text>
          )}
          {option.compatibility && (
            <Text className="text-[#6EE7B7] text-[10px] mb-1">Compatibility: {option.compatibility}</Text>
          )}
          {option.notes && (
            <Text className="text-[#3D4F66] text-[10px] italic">{option.notes}</Text>
          )}
        </View>
      )}
    </TouchableOpacity>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function ClinicalResearchScreen() {
  const params = useLocalSearchParams<{ initialQuery?: string }>();
  const [query, setQuery] = useState(params.initialQuery ?? '');
  const [searching, setSearching] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [trials, setTrials] = useState<any[]>([]);
  const [trialsLoading, setTrialsLoading] = useState(false);

  useEffect(() => {
    if (params.initialQuery) {
      handleSearch(params.initialQuery);
    }
  }, []);

  async function handleSearch(q?: string) {
    const searchQuery = (q ?? query).trim();
    if (!searchQuery || searchQuery.length < 3) return;
    setSearching(true);
    setError(null);
    setResult(null);
    try {
      // Phase 1: Fast synthesis (renders immediately)
      const { data: synthData } = await api.post(
        '/api/v1/research/clinical-search',
        { query: searchQuery, search_type: 'all' },
        { timeout: 60_000 },
      );
      setResult(synthData);
      setSearching(false); // Show synthesis immediately

      // Phase 2: Detailed treatment options + drug profiles (loads in background)
      try {
        const [detailsResp, trialsResp] = await Promise.allSettled([
          api.post('/api/v1/research/clinical-search/details', { query: searchQuery }, { timeout: 90_000 }),
          api.get('/api/v1/research/trials', { params: { condition: searchQuery, max_results: 5 }, timeout: 15_000 }),
        ]);
        if (detailsResp.status === 'fulfilled') {
          setResult((prev) => prev ? {
            ...prev,
            treatment_report: detailsResp.value.data?.treatment_report ?? prev.treatment_report,
            drugs_mentioned: detailsResp.value.data?.drugs_mentioned ?? prev.drugs_mentioned,
          } : prev);
        }
        if (trialsResp.status === 'fulfilled') setTrials(trialsResp.value.data?.trials ?? []);
      } catch { /* details are bonus, synthesis already shown */ }
    } catch (e: any) {
      setError(e?.message ?? 'Search failed. Please try again.');
      setSearching(false);
    }
  }

  async function handleShare() {
    if (!result) return;
    const lines: string[] = [`Clinical Research: ${query}\n`];
    if (result.ai_synthesis) lines.push(result.ai_synthesis + '\n');
    if (result.treatment_report?.treatment_options) {
      lines.push('Treatment Options:');
      result.treatment_report.treatment_options.forEach((t, i) => {
        lines.push(`${i + 1}. ${t.name} — ${t.efficacy}`);
      });
    }
    if (result.treatment_report?.doctor_questions) {
      lines.push('\nQuestions for Your Doctor:');
      result.treatment_report.doctor_questions.forEach((q) => lines.push(`○ ${q}`));
    }
    lines.push('\n---\nGenerated by Vitalix. Not medical advice.');
    await Share.share({ message: lines.join('\n'), title: 'Clinical Research Report' });
  }

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className="text-xl font-display text-[#E8EDF5]">Clinical Research</Text>
          <Text className="text-[#526380] text-xs mt-0.5">Treatments, drugs, trials & guidelines</Text>
        </View>
        {result && (
          <TouchableOpacity onPress={handleShare}>
            <Ionicons name="share-outline" size={20} color="#00D4AA" />
          </TouchableOpacity>
        )}
      </View>

      {/* Search bar */}
      <View className="px-6 py-4">
        <View className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl px-4 py-3 gap-2">
          <Ionicons name="search" size={16} color="#526380" />
          <TextInput
            className="flex-1 text-[#E8EDF5] text-sm"
            placeholder="Search treatments, drugs, trials..."
            placeholderTextColor="#526380"
            value={query}
            onChangeText={setQuery}
            onSubmitEditing={() => handleSearch()}
            returnKeyType="search"
          />
          <TouchableOpacity
            onPress={() => handleSearch()}
            disabled={searching || query.trim().length < 3}
            className="bg-[#818CF8] rounded-lg px-3 py-1.5"
            activeOpacity={0.7}
          >
            <Text className="text-white text-xs font-sansMedium">
              {searching ? 'Searching...' : 'Search'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <View className="px-6">
        {/* Loading */}
        {searching && (
          <View className="items-center py-12">
            <ActivityIndicator color="#818CF8" size="large" />
            <Text className="text-[#526380] text-sm mt-3">Searching medical literature, drugs & guidelines...</Text>
            <Text className="text-[#3D4F66] text-xs mt-1">Personalizing to your health profile</Text>
          </View>
        )}

        {/* Error */}
        {error && (
          <View className="bg-[#F8717115] border border-[#F8717130] rounded-xl p-4 mb-4">
            <Text className="text-[#F87171] text-sm">{error}</Text>
          </View>
        )}

        {/* Results */}
        {result && !searching && (
          <>
            {/* AI Synthesis */}
            {result.ai_synthesis && (
              <View className="bg-[#818CF810] border border-[#818CF825] rounded-2xl p-4 mb-4">
                <View className="flex-row items-center gap-1.5 mb-2">
                  <Ionicons name="sparkles" size={14} color="#818CF8" />
                  <Text className="text-[#818CF8] text-xs font-sansMedium uppercase tracking-wider">AI Synthesis</Text>
                </View>
                <Text className="text-[#C8D6E5] text-sm leading-6">{result.ai_synthesis}</Text>
              </View>
            )}

            {/* Guidelines referenced */}
            {result.treatment_report?.guidelines_referenced?.length > 0 && (
              <View className="flex-row flex-wrap gap-1.5 mb-3">
                {result.treatment_report.guidelines_referenced.map((g, i) => (
                  <View key={i} className="bg-[#818CF812] rounded-full px-2.5 py-1">
                    <Text className="text-[#818CF8] text-[9px] font-sansMedium">{g}</Text>
                  </View>
                ))}
              </View>
            )}

            {/* Treatment options */}
            {result.treatment_report?.treatment_options?.length > 0 && (
              <View className="mb-4">
                <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Treatment Options</Text>
                {result.treatment_report.treatment_options.map((opt, i) => (
                  <TreatmentOptionCard key={i} option={opt} rank={i + 1} />
                ))}
              </View>
            )}

            {/* Drug profiles */}
            {result.drugs_mentioned?.length > 0 && (
              <View className="mb-4">
                <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Drug Profiles</Text>
                {result.drugs_mentioned.map((drug, i) => (
                  <DrugProfileCard key={i} drug={drug} />
                ))}
              </View>
            )}

            {/* Doctor questions */}
            {result.treatment_report?.doctor_questions?.length > 0 && (
              <View className="mb-4">
                <Text className="text-[#00D4AA] text-xs uppercase tracking-wider mb-2">Questions for Your Doctor</Text>
                <View className="bg-surface-raised border border-surface-border rounded-xl p-4 gap-2">
                  {result.treatment_report.doctor_questions.map((q, i) => (
                    <View key={i} className="flex-row items-start gap-2">
                      <Text className="text-[#00D4AA] text-xs">{i + 1}.</Text>
                      <Text className="text-[#8B9BB4] text-xs leading-5 flex-1">{q}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Research articles */}
            {result.articles?.length > 0 && (
              <View className="mb-4">
                <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">
                  Research Articles ({result.articles.length})
                </Text>
                {result.articles.slice(0, 5).map((a, i) => (
                  <View key={i} className="bg-surface-raised border border-surface-border rounded-xl p-3 mb-2">
                    <Text className="text-[#E8EDF5] text-xs font-sansMedium leading-5" numberOfLines={2}>{a.title}</Text>
                    <Text className="text-[#3D4F66] text-[10px] mt-1">
                      {a.journal} · {a.publication_date?.slice(0, 4)}
                      {a.evidence_level && ` · ${a.evidence_level}`}
                    </Text>
                  </View>
                ))}
              </View>
            )}

            {/* Clinical Trials */}
            {trials.length > 0 && (
              <View className="mb-4">
                <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">
                  Clinical Trials ({trials.length} recruiting)
                </Text>
                {trials.map((trial, i) => (
                  <ClinicalTrialCard key={trial.nct_id || i} trial={trial} />
                ))}
              </View>
            )}

            {/* Disclaimer */}
            <View className="bg-white/3 rounded-xl p-3 mt-2">
              <Text className="text-[#3D4F66] text-[10px] leading-4 text-center">
                {result.treatment_report?.disclaimer ?? 'This is not medical advice. Discuss all findings with your healthcare provider before making any treatment changes.'}
              </Text>
            </View>
          </>
        )}

        {/* Empty state */}
        {!result && !searching && !error && (
          <View className="items-center py-16">
            <Ionicons name="flask-outline" size={48} color="#818CF8" />
            <Text className="text-[#E8EDF5] font-sansMedium text-base mt-3">Clinical Research</Text>
            <Text className="text-[#526380] text-sm mt-1 text-center leading-5 px-4">
              Search for treatments, drugs, clinical trials, or ask about guidelines for any condition
            </Text>
            <View className="flex-row flex-wrap gap-2 mt-4 justify-center px-4">
              {['PCOS treatments', 'Metformin alternatives', 'Latest cancer immunotherapy', 'Statin comparison'].map((s) => (
                <TouchableOpacity
                  key={s}
                  onPress={() => { setQuery(s); handleSearch(s); }}
                  className="bg-[#818CF812] border border-[#818CF825] rounded-full px-3 py-1.5"
                  activeOpacity={0.7}
                >
                  <Text className="text-[#818CF8] text-xs">{s}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}
      </View>
    </ScrollView>
  );
}
