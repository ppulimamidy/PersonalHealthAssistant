/**
 * Medical Records screen — pathology, genomic, and imaging reports.
 * Extends beyond blood labs to support the full medical record spectrum.
 */

import { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
  Alert, Modal, Image,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import * as ImagePicker from 'expo-image-picker';
import { format } from 'date-fns';
import { api } from '@/services/api';

// ─── Types ────────────────────────────────────────────────────────────────────

type RecordType = 'pathology' | 'genomic' | 'imaging';

interface MedicalRecord {
  id: string;
  record_type: RecordType;
  title: string;
  report_date?: string;
  provider_name?: string;
  facility_name?: string;
  ai_summary?: string;
  extracted_data?: any;
  created_at: string;
}

const RECORD_TYPES: Array<{ key: RecordType; label: string; icon: string; color: string; desc: string }> = [
  { key: 'pathology', label: 'Pathology', icon: 'cut-outline', color: '#F87171', desc: 'Biopsy & tissue reports' },
  { key: 'genomic', label: 'Genomic', icon: 'code-working-outline', color: '#818CF8', desc: 'NGS, mutation panels' },
  { key: 'imaging', label: 'Imaging', icon: 'scan-outline', color: '#60A5FA', desc: 'CT, MRI, PET, X-ray' },
];

// ─── Record Cards ─────────────────────────────────────────────────────────────

function PathologyCardInner({ record }: Readonly<{ record: MedicalRecord }>) {
  const data = record.extracted_data ?? {};
  const stage = data.stage ?? {};
  return (
    <>
      <View className="flex-row items-center gap-2 mb-1">
        <Ionicons name="cut-outline" size={14} color="#F87171" />
        <Text className="text-[#E8EDF5] font-sansMedium text-sm flex-1">{record.title}</Text>
        {record.report_date && <Text className="text-[#3D4F66] text-[10px]">{record.report_date}</Text>}
      </View>
      {data.histological_subtype && <Text className="text-[#526380] text-xs">{data.histological_subtype}</Text>}
      {stage.overall && (
        <View className="flex-row gap-1 mt-1">
          <View className="bg-[#F8717120] rounded px-1.5 py-0.5"><Text className="text-[#F87171] text-[9px] font-sansMedium">{stage.overall}</Text></View>
          {stage.T && <View className="bg-white/5 rounded px-1.5 py-0.5"><Text className="text-[#526380] text-[9px]">T{stage.T}</Text></View>}
          {stage.N && <View className="bg-white/5 rounded px-1.5 py-0.5"><Text className="text-[#526380] text-[9px]">N{stage.N}</Text></View>}
          {stage.M && <View className="bg-white/5 rounded px-1.5 py-0.5"><Text className="text-[#526380] text-[9px]">M{stage.M}</Text></View>}
        </View>
      )}
      {record.ai_summary && <Text className="text-[#526380] text-xs mt-1 italic">{record.ai_summary}</Text>}
    </>
  );
}

function PathologyCard({ record }: Readonly<{ record: MedicalRecord }>) {
  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2">
      <PathologyCardInner record={record} />
    </View>
  );
}

function GenomicCardInner({ record }: Readonly<{ record: MedicalRecord }>) {
  const data = record.extracted_data ?? {};
  const mutations = data.mutations ?? [];
  return (
    <>
      <View className="flex-row items-center gap-2 mb-2">
        <Ionicons name="code-working-outline" size={14} color="#818CF8" />
        <Text className="text-[#E8EDF5] font-sansMedium text-sm flex-1">{record.title}</Text>
        {record.report_date && <Text className="text-[#3D4F66] text-[10px]">{record.report_date}</Text>}
      </View>
      {mutations.map((m: any, i: number) => (
        <View key={i} className="mb-2 pb-2 border-b border-surface-border last:border-b-0">
          <View className="flex-row items-center gap-1.5 mb-0.5">
            <Text className="text-[#E8EDF5] text-xs font-sansMedium">{m.gene} {m.exon ?? ''}</Text>
            {m.classification?.tier && (
              <View className="bg-[#818CF820] rounded px-1.5 py-0.5">
                <Text className="text-[#818CF8] text-[9px] font-sansMedium">{m.classification.tier}</Text>
              </View>
            )}
            {m.sensitivity && (
              <View className="rounded px-1.5 py-0.5" style={{ backgroundColor: m.sensitivity === 'Sensitive' ? '#6EE7B715' : '#F8717115' }}>
                <Text className="text-[9px] font-sansMedium" style={{ color: m.sensitivity === 'Sensitive' ? '#6EE7B7' : '#F87171' }}>
                  {m.sensitivity}
                </Text>
              </View>
            )}
          </View>
          {m.protein_change && <Text className="text-[#526380] text-[10px]">{m.protein_change}{m.vaf ? ` · VAF ${m.vaf}` : ''}</Text>}
          {m.sensitive_therapies?.length > 0 && (
            <View className="flex-row flex-wrap gap-1 mt-1">
              {m.sensitive_therapies.map((t: string, ti: number) => (
                <View key={ti} className="bg-[#00D4AA10] rounded px-1.5 py-0.5">
                  <Text className="text-[#00D4AA] text-[9px]">{t}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      ))}
      {record.ai_summary && <Text className="text-[#526380] text-xs italic">{record.ai_summary}</Text>}
    </>
  );
}

function GenomicCard({ record }: Readonly<{ record: MedicalRecord }>) {
  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2">
      <GenomicCardInner record={record} />
    </View>
  );
}

function ImagingCardInner({ record }: Readonly<{ record: MedicalRecord }>) {
  const data = record.extracted_data ?? {};
  const findings = data.findings ?? [];
  return (
    <>
      <View className="flex-row items-center gap-2 mb-1">
        <Ionicons name="scan-outline" size={14} color="#60A5FA" />
        <Text className="text-[#E8EDF5] font-sansMedium text-sm flex-1">{record.title}</Text>
        {record.report_date && <Text className="text-[#3D4F66] text-[10px]">{record.report_date}</Text>}
      </View>
      {data.modality && <Text className="text-[#60A5FA] text-[10px]">{data.modality} — {data.body_region}</Text>}
      {findings.slice(0, 3).map((f: any, i: number) => (
        <Text key={i} className="text-[#526380] text-xs mt-0.5">
          • {f.location}: {f.description}{f.measurement_cm ? ` (${f.measurement_cm}cm)` : ''}
        </Text>
      ))}
      {data.impression && <Text className="text-[#8B9BB4] text-xs mt-1 italic">{data.impression}</Text>}
    </>
  );
}

function ImagingCard({ record }: Readonly<{ record: MedicalRecord }>) {
  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2">
      <ImagingCardInner record={record} />
    </View>
  );
}

function InsightButton({ record, insights, loading, onPress }: {
  record: MedicalRecord;
  insights: Record<string, string>;
  loading: string | null;
  onPress: (id: string) => void;
}) {
  const isLoading = loading === record.id;
  const insight = insights[record.id];

  return (
    <View className="mt-2 pt-2 border-t border-surface-border">
      <TouchableOpacity
        onPress={() => onPress(record.id)}
        disabled={isLoading}
        className="flex-row items-center gap-1.5"
        activeOpacity={0.7}
      >
        {isLoading ? (
          <ActivityIndicator size="small" color="#00D4AA" />
        ) : (
          <Ionicons name="sparkles" size={14} color="#00D4AA" />
        )}
        <Text className="text-xs font-sansMedium" style={{ color: '#00D4AA' }}>
          {insight ? 'Hide AI Insight' : 'AI Clinical Insight'}
        </Text>
      </TouchableOpacity>
      {insight && (
        <View className="mt-2 p-3 rounded-lg" style={{ backgroundColor: '#00D4AA10', borderWidth: 1, borderColor: '#00D4AA20' }}>
          <Text className="text-xs text-[#C8D5E8] leading-5">{insight}</Text>
        </View>
      )}
    </View>
  );
}

function RecordCard({ record, insights, insightLoading, onInsight }: Readonly<{
  record: MedicalRecord;
  insights: Record<string, string>;
  insightLoading: string | null;
  onInsight: (id: string) => void;
}>) {
  const inner = record.record_type === 'pathology' ? <PathologyCard record={record} />
    : record.record_type === 'genomic' ? <GenomicCard record={record} />
    : record.record_type === 'imaging' ? <ImagingCard record={record} />
    : null;

  if (!inner) return null;

  // Wrap each card to append the insight button inside
  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2">
      {/* Re-render the card content without its own wrapper */}
      {record.record_type === 'pathology' && <PathologyCardInner record={record} />}
      {record.record_type === 'genomic' && <GenomicCardInner record={record} />}
      {record.record_type === 'imaging' && <ImagingCardInner record={record} />}
      <InsightButton record={record} insights={insights} loading={insightLoading} onPress={onInsight} />
    </View>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function MedicalRecordsScreen() {
  const queryClient = useQueryClient();
  const [activeType, setActiveType] = useState<RecordType | 'all'>('all');
  const [scanning, setScanning] = useState(false);
  const [scanType, setScanType] = useState<RecordType | null>(null);
  const [insightLoading, setInsightLoading] = useState<string | null>(null);
  const [insights, setInsights] = useState<Record<string, string>>({});

  const handleInsight = useCallback(async (recordId: string) => {
    if (insights[recordId]) {
      setInsights((prev) => { const next = { ...prev }; delete next[recordId]; return next; });
      return;
    }
    setInsightLoading(recordId);
    try {
      const { data } = await api.post(`/api/v1/medical-records/${recordId}/insight`);
      setInsights((prev) => ({ ...prev, [recordId]: data?.insight ?? 'No insight available.' }));
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } catch {
      setInsights((prev) => ({ ...prev, [recordId]: 'Failed to generate insight.' }));
    } finally {
      setInsightLoading(null);
    }
  }, [insights]);

  const { data: records, isLoading } = useQuery<MedicalRecord[]>({
    queryKey: ['medical-records', activeType],
    queryFn: async () => {
      const params = activeType !== 'all' ? `?record_type=${activeType}` : '';
      const { data } = await api.get(`/api/v1/medical-records${params}`);
      // Parse extracted_data for each record
      const list = data?.records ?? [];
      return list.map((r: any) => ({
        ...r,
        extracted_data: typeof r.extracted_data === 'string' ? JSON.parse(r.extracted_data) : r.extracted_data,
        tags: typeof r.tags === 'string' ? JSON.parse(r.tags) : r.tags,
      }));
    },
  });

  async function handleScan(type: RecordType) {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.8,
    });
    if (result.canceled || !result.assets?.[0]) return;

    setScanning(true);
    setScanType(type);
    try {
      const asset = result.assets[0];
      const formData = new FormData();
      formData.append('image', {
        uri: asset.uri,
        type: asset.mimeType ?? 'image/jpeg',
        name: asset.fileName ?? 'record.jpg',
      } as any);
      formData.append('record_type', type);

      const { data: scanResult } = await api.post('/api/v1/medical-records/scan', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      });

      if (scanResult?.extracted_data && Object.keys(scanResult.extracted_data).length > 0) {
        // Save the record
        await api.post('/api/v1/medical-records', {
          record_type: type,
          extracted_data: scanResult.extracted_data,
          report_date: scanResult.extracted_data.report_date ?? null,
          provider_name: scanResult.extracted_data.pathologist ?? scanResult.extracted_data.radiologist ?? null,
          facility_name: scanResult.extracted_data.lab ?? null,
        });
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        queryClient.invalidateQueries({ queryKey: ['medical-records'] });
      } else {
        Alert.alert('Extraction Failed', 'Could not extract data from this document. Try a clearer image.');
      }
    } catch {
      Alert.alert('Error', 'Failed to process the document.');
    } finally {
      setScanning(false);
      setScanType(null);
    }
  }

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
      {/* Header */}
      <View className="px-6 pt-14 pb-4 border-b border-surface-border">
        <View className="flex-row items-center justify-between mb-3">
          <Text className="text-xl font-display text-[#E8EDF5]">Medical Records</Text>
        </View>
        <Text className="text-[#526380] text-xs mb-3">Pathology, genomic profiles, and imaging reports</Text>

        {/* Type selector */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View className="flex-row gap-1.5">
            <TouchableOpacity
              onPress={() => setActiveType('all')}
              className="px-3 py-1.5 rounded-lg"
              style={{
                backgroundColor: activeType === 'all' ? '#00D4AA18' : 'transparent',
                borderWidth: 1,
                borderColor: activeType === 'all' ? '#00D4AA' : '#1E2A3B',
              }}
            >
              <Text className="text-xs font-sansMedium" style={{ color: activeType === 'all' ? '#00D4AA' : '#526380' }}>All</Text>
            </TouchableOpacity>
            {RECORD_TYPES.map((t) => (
              <TouchableOpacity
                key={t.key}
                onPress={() => setActiveType(t.key)}
                className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
                style={{
                  backgroundColor: activeType === t.key ? `${t.color}18` : 'transparent',
                  borderWidth: 1,
                  borderColor: activeType === t.key ? t.color : '#1E2A3B',
                }}
              >
                <Ionicons name={t.icon as never} size={12} color={activeType === t.key ? t.color : '#526380'} />
                <Text className="text-xs font-sansMedium" style={{ color: activeType === t.key ? t.color : '#526380' }}>{t.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>

      <View className="px-6 pt-4">
        {/* Upload buttons */}
        <View className="flex-row gap-2 mb-4">
          {RECORD_TYPES.map((t) => (
            <TouchableOpacity
              key={t.key}
              onPress={() => handleScan(t.key)}
              disabled={scanning}
              className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-3 items-center"
              activeOpacity={0.7}
            >
              {scanning && scanType === t.key ? (
                <ActivityIndicator color={t.color} size="small" />
              ) : (
                <Ionicons name={t.icon as never} size={18} color={t.color} />
              )}
              <Text className="text-[#8B9BB4] text-[9px] mt-1 font-sansMedium">{t.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Scanning indicator */}
        {scanning && (
          <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-4 items-center">
            <ActivityIndicator color="#818CF8" />
            <Text className="text-[#526380] text-xs mt-2">Analyzing {scanType} report...</Text>
          </View>
        )}

        {/* Records list */}
        {isLoading ? (
          <ActivityIndicator color="#00D4AA" className="mt-8" />
        ) : !records || records.length === 0 ? (
          <View className="items-center py-12">
            <Ionicons name="document-outline" size={44} color="#526380" />
            <Text className="text-[#E8EDF5] font-sansMedium mt-3">No records yet</Text>
            <Text className="text-[#526380] text-sm mt-1 text-center px-4">
              Upload a pathology report, genomic panel, or imaging result to get started.
            </Text>
          </View>
        ) : (
          records.map((r) => (
            <RecordCard
              key={r.id}
              record={r}
              insights={insights}
              insightLoading={insightLoading}
              onInsight={handleInsight}
            />
          ))
        )}
      </View>
    </ScrollView>
  );
}
