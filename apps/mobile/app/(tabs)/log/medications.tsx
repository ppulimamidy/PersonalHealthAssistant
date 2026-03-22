import { useState, useEffect } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, RefreshControl, ActivityIndicator,
  Modal, ScrollView, TextInput, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import * as Haptics from 'expo-haptics';
import * as ImagePicker from 'expo-image-picker';
import { api } from '@/services/api';
import type { Medication } from '@/types';
import TreatmentOverviewCard from '@/components/TreatmentOverviewCard';
import InteractionAlertCard from '@/components/InteractionAlertCard';
import MedScheduleCard from '@/components/MedScheduleCard';

// ─── Lab Evidence Badge ──────────────────────────────────────────────────────

function LabEvidenceBadge({ medicationId }: Readonly<{ medicationId: string }>) {
  const { data } = useQuery({
    queryKey: ['med-evidence', medicationId],
    queryFn: async () => {
      try {
        const { data: resp } = await api.get(`/api/v1/lab-intelligence/med-evidence/${medicationId}`);
        return resp;
      } catch { return null; }
    },
    staleTime: 10 * 60_000,
  });

  if (!data?.evidence?.length) return null;

  // Find the most significant evidence
  const best = data.evidence.reduce((a: any, b: any) => {
    if (b.verdict === 'improving') return b;
    if (a.verdict === 'improving') return a;
    return Math.abs(b.delta_pct ?? 0) > Math.abs(a.delta_pct ?? 0) ? b : a;
  }, data.evidence[0]);

  if (!best || best.verdict === 'insufficient_data') {
    return (
      <View className="flex-row items-center gap-1 bg-white/5 rounded-md px-2 py-0.5 mt-1.5">
        <Ionicons name="hourglass-outline" size={10} color="#526380" />
        <Text className="text-[#526380] text-[10px]">Monitoring — awaiting lab data</Text>
      </View>
    );
  }

  const isGood = best.verdict === 'improving';
  const isStale = best.verdict === 'no_change';
  const color = isGood ? '#6EE7B7' : isStale ? '#F5A623' : '#F87171';
  const icon = isGood ? 'trending-down' : isStale ? 'remove-outline' : 'trending-up';
  const deltaTxt = best.delta_pct != null ? `${best.delta_pct > 0 ? '+' : ''}${best.delta_pct}%` : '';

  return (
    <TouchableOpacity
      onPress={() => router.push('/(tabs)/log/lab-results')}
      className="flex-row items-center gap-1 rounded-md px-2 py-0.5 mt-1.5"
      style={{ backgroundColor: `${color}12` }}
      activeOpacity={0.7}
    >
      <Ionicons name={icon as never} size={10} color={color} />
      <Text className="text-[10px] font-sansMedium" style={{ color }}>
        {best.biomarker} {deltaTxt}
      </Text>
      <Text className="text-[#3D4F66] text-[9px]">since starting</Text>
    </TouchableOpacity>
  );
}

interface Supplement {
  id: string;
  supplement_name: string;
  brand?: string;
  dosage: string;
  frequency: string;
  form: string;
  purpose?: string;
  is_active: boolean;
}

const ROUTES = ['oral', 'topical', 'injection', 'inhaled'] as const;
const FREQUENCIES = [
  'Once daily', 'Twice daily', 'Three times daily',
  'Every 8 hours', 'Every 12 hours', 'Once weekly', 'As needed',
];

// ─── Edit Modal ──────────────────────────────────────────────────────────────

interface EditModalProps {
  med: Medication | null;
  onClose: () => void;
  onSaved: () => void;
}

function EditMedicationModal({ med, onClose, onSaved }: EditModalProps) {
  const [name, setName] = useState(med?.medication_name ?? '');
  const [dosage, setDosage] = useState(med?.dosage ?? '');
  const [frequency, setFrequency] = useState(() => {
    const f = med?.frequency ?? '';
    return FREQUENCIES.includes(f) ? f : f ? 'custom' : '';
  });
  const [customFrequency, setCustomFrequency] = useState(() => {
    const f = med?.frequency ?? '';
    return FREQUENCIES.includes(f) ? '' : f;
  });
  const [route, setRoute] = useState<typeof ROUTES[number]>(
    (med?.route as typeof ROUTES[number]) ?? 'oral'
  );
  const [indication, setIndication] = useState(med?.indication ?? '');
  const [prescribingDoctor, setPrescribingDoctor] = useState(med?.prescribing_doctor ?? '');
  const [notes, setNotes] = useState(med?.notes ?? '');
  const [isActive, setIsActive] = useState(med?.is_active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const effectiveFrequency = frequency === 'custom' ? customFrequency : frequency;

  async function handleSave() {
    if (!name.trim()) { setError('Medication name is required'); return; }
    if (!dosage.trim()) { setError('Dosage is required'); return; }
    if (!effectiveFrequency.trim()) { setError('Frequency is required'); return; }

    setError('');
    setLoading(true);
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await api.put(`/api/v1/medications/medications/${med!.id}`, {
        medication_name: name.trim(),
        dosage: dosage.trim(),
        frequency: effectiveFrequency.trim(),
        route,
        indication: indication.trim() || undefined,
        prescribing_doctor: prescribingDoctor.trim() || undefined,
        notes: notes.trim() || undefined,
        is_active: isActive,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      onSaved();
    } catch {
      setError('Failed to update medication. Please try again.');
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal visible={!!med} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        className="flex-1 bg-obsidian-900"
      >
        {/* Header */}
        <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
          <TouchableOpacity onPress={onClose} className="mr-4 p-1">
            <Ionicons name="close" size={24} color="#E8EDF5" />
          </TouchableOpacity>
          <Text className="text-xl font-display text-[#E8EDF5] flex-1">Edit Medication</Text>
          <TouchableOpacity
            onPress={handleSave}
            disabled={loading}
            className="bg-primary-500 px-4 py-2 rounded-xl"
          >
            {loading
              ? <ActivityIndicator size="small" color="#080B10" />
              : <Text className="text-obsidian-900 font-sansMedium text-sm">Save</Text>
            }
          </TouchableOpacity>
        </View>

        <ScrollView
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{ padding: 24, paddingBottom: 48 }}
        >
          {error ? (
            <View className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 mb-5">
              <Text className="text-red-400 text-sm">{error}</Text>
            </View>
          ) : null}

          {/* Medication Name */}
          <View className="mb-5">
            <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
              Medication Name *
            </Text>
            <TextInput
              className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
              placeholder="e.g. Metformin, Lisinopril"
              placeholderTextColor="#526380"
              value={name}
              onChangeText={setName}
              autoCapitalize="words"
            />
          </View>

          {/* Dosage */}
          <View className="mb-5">
            <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
              Dosage *
            </Text>
            <TextInput
              className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
              placeholder="e.g. 500mg, 10mg/5ml"
              placeholderTextColor="#526380"
              value={dosage}
              onChangeText={setDosage}
            />
          </View>

          {/* Frequency */}
          <View className="mb-5">
            <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
              Frequency *
            </Text>
            <View className="flex-row flex-wrap gap-2 mb-2">
              {FREQUENCIES.map((f) => (
                <TouchableOpacity
                  key={f}
                  onPress={() => setFrequency(f)}
                  className={`px-3 py-2 rounded-lg border ${
                    frequency === f
                      ? 'bg-primary-500/20 border-primary-500/60'
                      : 'bg-surface-raised border-surface-border'
                  }`}
                >
                  <Text className={`text-sm ${frequency === f ? 'text-primary-500' : 'text-[#E8EDF5]'}`}>
                    {f}
                  </Text>
                </TouchableOpacity>
              ))}
              <TouchableOpacity
                onPress={() => setFrequency('custom')}
                className={`px-3 py-2 rounded-lg border ${
                  frequency === 'custom'
                    ? 'bg-primary-500/20 border-primary-500/60'
                    : 'bg-surface-raised border-surface-border'
                }`}
              >
                <Text className={`text-sm ${frequency === 'custom' ? 'text-primary-500' : 'text-[#E8EDF5]'}`}>
                  Custom…
                </Text>
              </TouchableOpacity>
            </View>
            {frequency === 'custom' && (
              <TextInput
                className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
                placeholder="Describe frequency..."
                placeholderTextColor="#526380"
                value={customFrequency}
                onChangeText={setCustomFrequency}
              />
            )}
          </View>

          {/* Route */}
          <View className="mb-5">
            <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
              Route of Administration
            </Text>
            <View className="flex-row gap-2">
              {ROUTES.map((r) => (
                <TouchableOpacity
                  key={r}
                  onPress={() => setRoute(r)}
                  className={`flex-1 py-2.5 rounded-xl border items-center ${
                    route === r
                      ? 'bg-primary-500/20 border-primary-500/60'
                      : 'bg-surface-raised border-surface-border'
                  }`}
                >
                  <Text className={`text-xs capitalize ${route === r ? 'text-primary-500' : 'text-[#E8EDF5]'}`}>
                    {r}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Indication */}
          <View className="mb-5">
            <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
              What is it for? (optional)
            </Text>
            <TextInput
              className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
              placeholder="e.g. Type 2 diabetes, blood pressure"
              placeholderTextColor="#526380"
              value={indication}
              onChangeText={setIndication}
              autoCapitalize="sentences"
            />
          </View>

          {/* Prescribing Doctor */}
          <View className="mb-5">
            <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
              Prescribing Doctor (optional)
            </Text>
            <TextInput
              className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
              placeholder="e.g. Dr. Sarah Smith"
              placeholderTextColor="#526380"
              value={prescribingDoctor}
              onChangeText={setPrescribingDoctor}
              autoCapitalize="words"
            />
          </View>

          {/* Notes */}
          <View className="mb-5">
            <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
              Notes (optional)
            </Text>
            <TextInput
              className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
              placeholder="Any additional notes..."
              placeholderTextColor="#526380"
              value={notes}
              onChangeText={setNotes}
              multiline
              numberOfLines={3}
              textAlignVertical="top"
              style={{ minHeight: 80 }}
            />
          </View>

          {/* Active toggle */}
          <TouchableOpacity
            onPress={() => setIsActive((v) => !v)}
            className={`flex-row items-center justify-between px-4 py-3 rounded-xl border ${
              isActive
                ? 'bg-primary-500/10 border-primary-500/30'
                : 'bg-surface-raised border-surface-border'
            }`}
          >
            <Text className="text-[#E8EDF5] font-sansMedium">Active medication</Text>
            <View className={`w-12 h-6 rounded-full items-center justify-center ${isActive ? 'bg-primary-500' : 'bg-surface-border'}`}>
              <View className={`w-5 h-5 rounded-full bg-white absolute ${isActive ? 'right-0.5' : 'left-0.5'}`} />
            </View>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Scan Prescription Modal ─────────────────────────────────────────────────

interface ScanResult {
  medication_name?: string;
  generic_name?: string;
  dosage?: string;
  frequency?: string;
  route?: string;
  indication?: string;
  prescribing_doctor?: string;
  is_supplement?: boolean;
  brand?: string;
  form?: string;
  purpose?: string;
  confidence?: number;
  image_type?: string;
}

function ScanPrescriptionModal({ visible, onClose, onSaved }: { visible: boolean; onClose: () => void; onSaved: () => void }) {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Editable fields from scan
  const [name, setName] = useState('');
  const [genericName, setGenericName] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('');
  const [routeVal, setRouteVal] = useState('oral');
  const [indication, setIndication] = useState('');
  const [isSupplement, setIsSupplement] = useState(false);
  const [brand, setBrand] = useState('');
  const [form, setForm] = useState('');
  const [purpose, setPurpose] = useState('');

  function resetState() {
    setResult(null);
    setError('');
    setName('');
    setGenericName('');
    setDosage('');
    setFrequency('');
    setRouteVal('oral');
    setIndication('');
    setIsSupplement(false);
    setBrand('');
    setForm('');
    setPurpose('');
  }

  function applyResult(r: ScanResult) {
    setResult(r);
    setName(r.medication_name ?? r.brand ?? '');
    setGenericName(r.generic_name ?? '');
    setDosage(r.dosage ?? '');
    setFrequency(r.frequency ?? '');
    setRouteVal(r.route ?? 'oral');
    setIndication(r.indication ?? '');
    setIsSupplement(r.is_supplement ?? false);
    setBrand(r.brand ?? '');
    setForm(r.form ?? '');
    setPurpose(r.purpose ?? '');
  }

  async function pickAndScan(useCamera: boolean) {
    setError('');
    setScanning(true);
    try {
      const opts: ImagePicker.ImagePickerOptions = {
        mediaTypes: ['images'],
        quality: 0.8,
        base64: false,
      };
      const picked = useCamera
        ? await ImagePicker.launchCameraAsync(opts)
        : await ImagePicker.launchImageLibraryAsync(opts);

      if (picked.canceled || !picked.assets?.[0]) {
        setScanning(false);
        return;
      }

      const asset = picked.assets[0];
      const formData = new FormData();
      formData.append('file', {
        uri: asset.uri,
        type: asset.mimeType ?? 'image/jpeg',
        name: asset.fileName ?? 'scan.jpg',
      } as any);

      const { data } = await api.post('/api/v1/medications/scan-prescription', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60_000,
      });

      applyResult(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Scan failed. Try again or enter manually.');
    } finally {
      setScanning(false);
    }
  }

  async function handleSave() {
    if (!name.trim()) { setError('Name is required'); return; }
    setSaving(true);
    setError('');
    try {
      if (isSupplement) {
        await api.post('/api/v1/supplements', {
          supplement_name: name.trim(),
          brand: brand.trim() || undefined,
          dosage: dosage.trim() || undefined,
          frequency: frequency.trim() || undefined,
          form: form.trim() || 'capsule',
          purpose: purpose.trim() || indication.trim() || undefined,
          is_active: true,
        });
      } else {
        await api.post('/api/v1/medications', {
          medication_name: name.trim(),
          generic_name: genericName.trim() || undefined,
          dosage: dosage.trim() || undefined,
          frequency: frequency.trim() || undefined,
          route: routeVal || 'oral',
          indication: indication.trim() || undefined,
          is_active: true,
        });
      }
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      resetState();
      onSaved();
    } catch {
      setError('Failed to save. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => { resetState(); onClose(); }}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        className="flex-1 bg-obsidian-900"
      >
        {/* Header */}
        <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
          <TouchableOpacity onPress={() => { resetState(); onClose(); }} className="mr-4 p-1">
            <Ionicons name="close" size={24} color="#E8EDF5" />
          </TouchableOpacity>
          <Text className="text-xl font-display text-[#E8EDF5] flex-1">Scan Medication</Text>
          {result && (
            <TouchableOpacity onPress={handleSave} disabled={saving} className="bg-primary-500 px-4 py-2 rounded-xl">
              {saving
                ? <ActivityIndicator size="small" color="#080B10" />
                : <Text className="text-obsidian-900 font-sansMedium text-sm">Save</Text>
              }
            </TouchableOpacity>
          )}
        </View>

        <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: 24, paddingBottom: 48 }}>
          {error ? (
            <View className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 mb-5">
              <Text className="text-red-400 text-sm">{error}</Text>
            </View>
          ) : null}

          {!result && !scanning && (
            <View>
              <Text className="text-[#8B9BB4] text-sm text-center mb-6 leading-5">
                Take a photo of a prescription label, medication bottle, supplement bottle, or pill strip.
                AI will extract the details automatically.
              </Text>
              <TouchableOpacity
                onPress={() => pickAndScan(true)}
                className="bg-primary-500/20 border border-primary-500/50 rounded-2xl py-5 items-center mb-3"
              >
                <Ionicons name="camera" size={32} color="#00D4AA" />
                <Text className="text-primary-500 font-sansMedium mt-2">Take Photo</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => pickAndScan(false)}
                className="bg-surface-raised border border-surface-border rounded-2xl py-5 items-center"
              >
                <Ionicons name="images" size={32} color="#8B9BB4" />
                <Text className="text-[#8B9BB4] font-sansMedium mt-2">Choose from Gallery</Text>
              </TouchableOpacity>
            </View>
          )}

          {scanning && (
            <View className="items-center py-16">
              <ActivityIndicator size="large" color="#00D4AA" />
              <Text className="text-[#8B9BB4] mt-4">Analyzing image with AI...</Text>
            </View>
          )}

          {result && !scanning && (
            <View>
              {/* Confidence + type badge */}
              <View className="flex-row items-center gap-2 mb-4">
                {result.confidence != null && (
                  <View className={`rounded-full px-2.5 py-1 ${
                    result.confidence > 0.8 ? 'bg-green-500/10' : result.confidence > 0.5 ? 'bg-amber-500/10' : 'bg-red-500/10'
                  }`}>
                    <Text className={`text-[10px] font-sansMedium ${
                      result.confidence > 0.8 ? 'text-green-400' : result.confidence > 0.5 ? 'text-amber-400' : 'text-red-400'
                    }`}>
                      {Math.round(result.confidence * 100)}% confidence
                    </Text>
                  </View>
                )}
                <View className={`rounded-full px-2.5 py-1 ${isSupplement ? 'bg-green-500/10' : 'bg-blue-500/10'}`}>
                  <Text className={`text-[10px] font-sansMedium ${isSupplement ? 'text-green-400' : 'text-blue-400'}`}>
                    {isSupplement ? 'Supplement' : 'Medication'}
                  </Text>
                </View>
              </View>

              {/* Toggle medication/supplement */}
              <TouchableOpacity
                onPress={() => setIsSupplement((v) => !v)}
                className="flex-row items-center gap-2 mb-5 bg-surface-raised border border-surface-border rounded-xl px-4 py-3"
              >
                <Ionicons name={isSupplement ? 'leaf-outline' : 'medkit-outline'} size={16} color="#00D4AA" />
                <Text className="text-[#E8EDF5] text-sm flex-1">
                  {isSupplement ? 'Save as Supplement' : 'Save as Medication'}
                </Text>
                <Ionicons name="swap-horizontal" size={14} color="#526380" />
              </TouchableOpacity>

              {/* Name */}
              <View className="mb-4">
                <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
                  {isSupplement ? 'Supplement Name' : 'Medication Name'} *
                </Text>
                <TextInput
                  className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
                  value={name}
                  onChangeText={setName}
                  placeholderTextColor="#526380"
                />
              </View>

              {!isSupplement && genericName ? (
                <View className="mb-4">
                  <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">Generic Name</Text>
                  <TextInput
                    className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
                    value={genericName}
                    onChangeText={setGenericName}
                    placeholderTextColor="#526380"
                  />
                </View>
              ) : null}

              {/* Dosage */}
              <View className="mb-4">
                <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">Dosage</Text>
                <TextInput
                  className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
                  value={dosage}
                  onChangeText={setDosage}
                  placeholderTextColor="#526380"
                />
              </View>

              {/* Frequency */}
              <View className="mb-4">
                <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">Frequency</Text>
                <TextInput
                  className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
                  value={frequency}
                  onChangeText={setFrequency}
                  placeholderTextColor="#526380"
                />
              </View>

              {/* Indication / Purpose */}
              <View className="mb-4">
                <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-2">
                  {isSupplement ? 'Purpose' : 'Indication'}
                </Text>
                <TextInput
                  className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
                  value={isSupplement ? purpose : indication}
                  onChangeText={isSupplement ? setPurpose : setIndication}
                  placeholderTextColor="#526380"
                />
              </View>

              {/* Rescan button */}
              <TouchableOpacity
                onPress={() => resetState()}
                className="border border-surface-border rounded-xl py-3 items-center mt-2"
              >
                <Text className="text-[#526380] text-sm">
                  <Ionicons name="refresh" size={14} color="#526380" /> Scan Again
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Adherence Row ────────────────────────────────────────────────────────────

interface AdherenceRowProps {
  med: Medication;
  logged: boolean;
  onLog: (id: string, taken: boolean) => void;
  onEdit: (med: Medication) => void;
  onDelete: (med: Medication) => void;
}

function AdherenceRow({ med, logged, onLog, onEdit, onDelete }: AdherenceRowProps) {
  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-3">
      {/* Top row: name + actions */}
      <View className="flex-row items-start justify-between mb-3">
        <View className="flex-1 mr-3">
          <Text className="text-[#E8EDF5] font-sansMedium">{med.medication_name}</Text>
          {med.dosage ? <Text className="text-[#526380] text-sm mt-0.5">{med.dosage}</Text> : null}
          {med.frequency ? <Text className="text-[#526380] text-xs mt-0.5">{med.frequency}</Text> : null}
          {med.indication ? (
            <Text className="text-[#526380] text-xs mt-1 italic">{med.indication}</Text>
          ) : null}
          <LabEvidenceBadge medicationId={med.id} />
        </View>
        <View className="flex-row gap-1">
          <TouchableOpacity
            onPress={() => onEdit(med)}
            className="bg-surface border border-surface-border rounded-lg p-2"
          >
            <Ionicons name="pencil-outline" size={14} color="#526380" />
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => onDelete(med)}
            className="bg-surface border border-surface-border rounded-lg p-2"
          >
            <Ionicons name="trash-outline" size={14} color="#EF4444" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Bottom row: Taken / Skip */}
      <View className="flex-row gap-2">
        {logged ? (
          <View className="flex-1 bg-primary-500/10 border border-primary-500/30 rounded-lg py-2 flex-row items-center justify-center gap-1">
            <Ionicons name="checkmark-circle" size={16} color="#00D4AA" />
            <Text className="text-primary-500 text-sm font-sansMedium">Taken</Text>
          </View>
        ) : (
          <TouchableOpacity
            onPress={() => onLog(med.id, true)}
            className="flex-1 bg-primary-500/20 border border-primary-500/50 rounded-lg py-2 items-center"
          >
            <Text className="text-primary-500 text-sm font-sansMedium">Taken</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          onPress={() => onLog(med.id, false)}
          disabled={logged}
          className={`flex-1 bg-surface border border-surface-border rounded-lg py-2 items-center ${logged ? 'opacity-40' : ''}`}
        >
          <Text className="text-[#526380] text-sm">Skip</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────

export default function MedicationsScreen() {
  const queryClient = useQueryClient();
  const [editingMed, setEditingMed] = useState<Medication | null>(null);
  const [loggedMeds, setLoggedMeds] = useState<Set<string>>(new Set());
  const [saveError, setSaveError] = useState('');
  const [showScan, setShowScan] = useState(false);

  const { data: medications, isLoading, refetch } = useQuery({
    queryKey: ['medications'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/medications');
      return (resp?.medications ?? resp ?? []) as Medication[];
    },
  });

  const { data: supplements, isLoading: supLoading } = useQuery({
    queryKey: ['supplements'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/supplements');
      return (Array.isArray(resp) ? resp : (resp?.supplements ?? [])) as Supplement[];
    },
  });

  const deleteSupMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/supplements/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['supplements'] }),
  });

  const { data: streaks } = useQuery({
    queryKey: ['adherence', 'streaks'],
    queryFn: async () => {
      const { data: resp } = await api.get('/api/v1/adherence/streaks');
      return resp;
    },
  });

  // Intelligence queries
  const { data: treatmentOverview } = useQuery({
    queryKey: ['treatment-overview'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/med-intelligence/treatment-overview');
        return data;
      } catch { return null; }
    },
    staleTime: 2 * 60_000,
  });

  const { data: interactions } = useQuery({
    queryKey: ['med-interactions'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/med-intelligence/interactions');
        return data;
      } catch { return null; }
    },
    staleTime: 5 * 60_000,
  });

  const { data: scheduleData } = useQuery({
    queryKey: ['med-schedule'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/med-intelligence/schedule');
        return data;
      } catch { return null; }
    },
    staleTime: 10 * 60_000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/medications/medications/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['medications'] }),
  });

  async function handleLog(medicationId: string, wasTaken: boolean) {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      await api.post('/api/v1/adherence/log', {
        medication_id: medicationId,
        was_taken: wasTaken,
        taken_at: new Date().toISOString(),
      });
      if (wasTaken) {
        setLoggedMeds((prev) => new Set(prev).add(medicationId));
      }
      setSaveError('');
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['adherence'] });
      queryClient.invalidateQueries({ queryKey: ['adherence-today'] });
      queryClient.invalidateQueries({ queryKey: ['adherence', 'today'] });
      queryClient.invalidateQueries({ queryKey: ['batch', 'home'] });
    } catch {
      setSaveError('Failed to log medication. Please try again.');
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }
  }

  function handleDelete(med: Medication) {
    Alert.alert(
      'Delete Medication',
      `Remove "${med.medication_name}" from your medications?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            deleteMutation.mutate(med.id);
          },
        },
      ]
    );
  }

  const medsList = Array.isArray(medications) ? medications : [];
  const active = medsList.filter((m) => m.is_active);
  const inactive = medsList.filter((m) => !m.is_active);

  // AI medication recommendations (shown when no meds logged)
  const { data: recsData, isLoading: recsLoading } = useQuery({
    queryKey: ['med-recommendations'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/med-intelligence/recommendations');
        return data as {
          recommendations: Array<{
            name: string;
            category: string;
            rationale: string;
            evidence_level: string;
            priority: string;
            discuss_with_doctor: boolean;
            relevant_data?: string;
            estimated_cost?: string;
            efficacy?: string;
          }>;
          summary: string;
          disclaimer: string;
          data_sources: { conditions: number; lab_results: number; medical_records: number; symptoms: number };
        };
      } catch { return null; }
    },
    staleTime: 10 * 60_000,
    enabled: medsList.length === 0,
  });

  return (
    <View className="flex-1 bg-obsidian-900">
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4">
        <View className="flex-1">
          <Text className="text-2xl font-display text-[#E8EDF5]">Medications</Text>
          {streaks?.current_streak > 0 && (
            <View className="flex-row items-center mt-2 bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-2 self-start">
              <Ionicons name="flame" size={16} color="#F5A623" />
              <Text className="text-amber-500 text-sm ml-2 font-sansMedium">
                {streaks.current_streak} day streak
              </Text>
            </View>
          )}
        </View>
        <View className="flex-row gap-2">
          <TouchableOpacity
            onPress={() => setShowScan(true)}
            className="bg-surface-raised border border-primary-500/40 rounded-xl px-3 py-2 flex-row items-center gap-1"
          >
            <Ionicons name="scan" size={16} color="#00D4AA" />
            <Text className="text-primary-500 font-sansMedium text-sm">Scan</Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => router.push('/(tabs)/log/new-medication')}
            className="bg-primary-500 rounded-xl px-4 py-2 flex-row items-center gap-1"
          >
            <Ionicons name="add" size={18} color="#080B10" />
            <Text className="text-obsidian-900 font-sansMedium text-sm">Add</Text>
          </TouchableOpacity>
        </View>
      </View>

      {isLoading ? (
        <ActivityIndicator color="#00D4AA" className="mt-10" />
      ) : (
        <ScrollView
          contentContainerStyle={{ padding: 16, paddingTop: 4, paddingBottom: 40 }}
          refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#00D4AA" />}
        >
          {/* Treatment Intelligence */}
          {treatmentOverview && (
            <TreatmentOverviewCard
              adherence={treatmentOverview.adherence ?? { rate_pct: 0, taken_today: 0, total_today: 0 }}
              labValidation={treatmentOverview.lab_validation ?? { improving: 0, monitoring: 0 }}
              supplementGaps={treatmentOverview.supplement_gaps ?? 0}
              interactionAlerts={treatmentOverview.interaction_alerts ?? 0}
              aiSummary={treatmentOverview.ai_summary ?? ''}
            />
          )}

          {interactions && (
            <InteractionAlertCard
              drugNutrient={interactions.drug_nutrient ?? []}
              drugFood={interactions.drug_food ?? []}
              drugDrug={interactions.drug_drug ?? []}
              onAddSupplement={(nutrient) => router.push('/(tabs)/log/new-medication')}
            />
          )}

          {scheduleData?.schedule?.length > 0 && (
            <MedScheduleCard
              schedule={scheduleData.schedule}
              supplementInteractions={scheduleData.supplement_interactions ?? []}
            />
          )}

          {saveError ? (
            <View className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 mb-3">
              <Text className="text-red-400 text-sm">{saveError}</Text>
            </View>
          ) : null}

          {medsList.length === 0 && (
            <>
              {recsLoading ? (
                <View className="items-center py-12">
                  <ActivityIndicator color="#00D4AA" />
                  <Text className="text-[#526380] text-sm mt-3">Analyzing your health profile...</Text>
                </View>
              ) : recsData?.recommendations && recsData.recommendations.length > 0 ? (
                <View>
                  {/* AI Summary */}
                  {recsData.summary && (
                    <View className="bg-[#00D4AA08] border border-[#00D4AA18] rounded-2xl p-4 mb-3">
                      <View className="flex-row items-center gap-1.5 mb-2">
                        <Ionicons name="sparkles" size={14} color="#00D4AA" />
                        <Text className="text-[#00D4AA] text-[10px] font-sansMedium uppercase tracking-wider">AI Recommendations</Text>
                      </View>
                      <Text className="text-[#8B9BB4] text-xs leading-5">{recsData.summary}</Text>
                      {recsData.data_sources && (
                        <Text className="text-[#3D4F66] text-[10px] mt-2">
                          Based on {recsData.data_sources.conditions} condition{recsData.data_sources.conditions !== 1 ? 's' : ''}, {recsData.data_sources.lab_results} lab result{recsData.data_sources.lab_results !== 1 ? 's' : ''}, {recsData.data_sources.medical_records} record{recsData.data_sources.medical_records !== 1 ? 's' : ''}
                        </Text>
                      )}
                    </View>
                  )}

                  {/* Recommendation Cards */}
                  {recsData.recommendations.map((rec, i) => {
                    const priorityColor = rec.priority === 'high' ? '#F87171' : rec.priority === 'medium' ? '#FBBF24' : '#60A5FA';
                    const priorityLabel = rec.priority === 'high' ? 'High Priority' : rec.priority === 'medium' ? 'Medium' : 'Low';
                    const catIcon = rec.category === 'prescription' ? 'medkit-outline' : rec.category === 'supplement' ? 'flask-outline' : 'medical-outline';
                    const evidenceColor = rec.evidence_level === 'strong' ? '#6EE7B7' : rec.evidence_level === 'moderate' ? '#FBBF24' : '#60A5FA';

                    return (
                      <View key={i} className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2">
                        <View className="flex-row items-start gap-3">
                          <View className="w-9 h-9 rounded-lg items-center justify-center" style={{ backgroundColor: `${priorityColor}15` }}>
                            <Ionicons name={catIcon as any} size={18} color={priorityColor} />
                          </View>
                          <View className="flex-1">
                            <View className="flex-row items-center gap-1.5 flex-wrap mb-0.5">
                              <Text className="text-[#E8EDF5] font-sansMedium text-sm">{rec.name}</Text>
                              <View className="rounded-full px-1.5 py-0.5" style={{ backgroundColor: `${priorityColor}15` }}>
                                <Text className="text-[9px] font-sansMedium" style={{ color: priorityColor }}>{priorityLabel}</Text>
                              </View>
                              <View className="rounded-full px-1.5 py-0.5" style={{ backgroundColor: `${evidenceColor}15` }}>
                                <Text className="text-[9px] font-sansMedium" style={{ color: evidenceColor }}>{rec.evidence_level}</Text>
                              </View>
                            </View>
                            {rec.discuss_with_doctor && (
                              <View className="flex-row items-center gap-1 mb-1">
                                <View className="rounded-full px-1.5 py-0.5 bg-purple-500/10">
                                  <Text className="text-purple-400 text-[9px] font-sansMedium">Rx — discuss with doctor</Text>
                                </View>
                              </View>
                            )}
                            <Text className="text-[#526380] text-xs leading-5">{rec.rationale}</Text>
                            {(rec.efficacy || rec.estimated_cost) && (
                              <View className="flex-row flex-wrap gap-x-3 gap-y-1 mt-1.5">
                                {rec.efficacy && (
                                  <View className="flex-row items-center gap-1">
                                    <Ionicons name="trending-up" size={10} color="#6EE7B7" />
                                    <Text className="text-[#6EE7B7] text-[10px]">{rec.efficacy}</Text>
                                  </View>
                                )}
                                {rec.estimated_cost && (
                                  <Text className="text-[#526380] text-[10px]">Cost: {rec.estimated_cost}</Text>
                                )}
                              </View>
                            )}
                            {rec.relevant_data && (
                              <View className="flex-row items-center gap-1 mt-1">
                                <Ionicons name="arrow-forward" size={9} color="#526380" />
                                <Text className="text-[#526380] text-[10px]">{rec.relevant_data}</Text>
                              </View>
                            )}
                          </View>
                        </View>
                      </View>
                    );
                  })}

                  {/* Disclaimer */}
                  <View className="flex-row items-start gap-2 p-3 rounded-xl bg-[#FBBF2408] border border-[#FBBF2415] mb-3">
                    <Ionicons name="shield-checkmark-outline" size={14} color="#FBBF24" style={{ marginTop: 1 }} />
                    <Text className="text-[#526380] text-[10px] leading-4 flex-1">{recsData.disclaimer}</Text>
                  </View>

                  {/* Add medication button */}
                  <TouchableOpacity
                    onPress={() => router.push('/(tabs)/log/new-medication')}
                    className="border border-dashed border-[#3D4F66] rounded-xl py-3 items-center"
                    activeOpacity={0.7}
                  >
                    <Text className="text-[#526380] text-sm">
                      <Ionicons name="add" size={14} color="#526380" /> Add a medication you're already taking
                    </Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <View className="items-center py-12">
                  <Ionicons name="medical-outline" size={48} color="#526380" />
                  <Text className="text-[#526380] mt-4 text-center">No medications added yet</Text>
                  <TouchableOpacity
                    onPress={() => router.push('/(tabs)/log/new-medication')}
                    className="mt-4 bg-primary-500/20 border border-primary-500/40 rounded-xl px-5 py-3"
                  >
                    <Text className="text-primary-500 font-sansMedium">Add your first medication</Text>
                  </TouchableOpacity>
                </View>
              )}
            </>
          )}

          {active.length > 0 && (
            <>
              <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-3 mt-1">
                Active ({active.length})
              </Text>
              {active.map((med) => (
                <AdherenceRow
                  key={med.id}
                  med={med}
                  logged={loggedMeds.has(med.id)}
                  onLog={handleLog}
                  onEdit={setEditingMed}
                  onDelete={handleDelete}
                />
              ))}
            </>
          )}

          {inactive.length > 0 && (
            <>
              <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider mb-3 mt-4">
                Inactive ({inactive.length})
              </Text>
              {inactive.map((med) => (
                <AdherenceRow
                  key={med.id}
                  med={med}
                  logged={loggedMeds.has(med.id)}
                  onLog={handleLog}
                  onEdit={setEditingMed}
                  onDelete={handleDelete}
                />
              ))}
            </>
          )}

          {/* ── Supplements ──────────────────────────────────────── */}
          <View className="mt-6 pt-4 border-t border-surface-border">
            <View className="flex-row items-center justify-between mb-3">
              <Text className="text-[#526380] text-xs font-sansMedium uppercase tracking-wider">
                Supplements {supplements?.length ? `(${supplements.length})` : ''}
              </Text>
            </View>
            {supLoading && <ActivityIndicator color="#00D4AA" size="small" />}
            {!supLoading && (!supplements || supplements.length === 0) && (
              <Text className="text-[#3A4A5C] text-sm mb-2">No supplements added yet.</Text>
            )}
            {supplements?.map((sup) => (
              <View
                key={sup.id}
                className="bg-surface-raised border border-surface-border rounded-xl p-3 mb-2 flex-row items-center"
              >
                <View className="w-9 h-9 rounded-lg items-center justify-center mr-3" style={{ backgroundColor: '#6EE7B718' }}>
                  <Ionicons name="leaf-outline" size={18} color="#6EE7B7" />
                </View>
                <View className="flex-1">
                  <Text className="text-[#E8EDF5] text-sm font-sansMedium">{sup.supplement_name}</Text>
                  <Text className="text-[#526380] text-xs mt-0.5">
                    {sup.dosage}{sup.frequency ? ` · ${sup.frequency}` : ''}{sup.brand ? ` · ${sup.brand}` : ''}
                  </Text>
                  {sup.purpose ? (
                    <Text className="text-[#3A4A5C] text-[10px] mt-0.5">{sup.purpose}</Text>
                  ) : null}
                </View>
                <TouchableOpacity
                  onPress={() => {
                    Alert.alert('Delete Supplement', `Remove "${sup.supplement_name}"?`, [
                      { text: 'Cancel', style: 'cancel' },
                      { text: 'Delete', style: 'destructive', onPress: () => deleteSupMutation.mutate(sup.id) },
                    ]);
                  }}
                  className="p-2"
                >
                  <Ionicons name="trash-outline" size={16} color="#526380" />
                </TouchableOpacity>
              </View>
            ))}
          </View>
        </ScrollView>
      )}

      <EditMedicationModal
        med={editingMed}
        onClose={() => setEditingMed(null)}
        onSaved={() => {
          setEditingMed(null);
          queryClient.invalidateQueries({ queryKey: ['medications'] });
        }}
      />

      <ScanPrescriptionModal
        visible={showScan}
        onClose={() => setShowScan(false)}
        onSaved={() => {
          setShowScan(false);
          queryClient.invalidateQueries({ queryKey: ['medications'] });
          queryClient.invalidateQueries({ queryKey: ['supplements'] });
        }}
      />
    </View>
  );
}
