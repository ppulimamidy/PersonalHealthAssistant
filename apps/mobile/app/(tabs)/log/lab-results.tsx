/**
 * Lab Results screen — manual entry + photo/PDF OCR scan.
 *
 * POST   /api/v1/lab-results
 * POST   /api/v1/lab-results/scan-image  (multipart)
 * GET    /api/v1/lab-results
 * DELETE /api/v1/lab-results/{result_id}
 */

import { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, TextInput,
  ActivityIndicator, Alert, Modal, KeyboardAvoidingView, Platform, Image,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import * as ImagePicker from 'expo-image-picker';
import { format } from 'date-fns';
import { api } from '@/services/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Biomarker {
  name: string;
  value: string;
  unit: string;
  status?: 'normal' | 'low' | 'high' | 'critical';
}

interface LabResult {
  id: string;
  test_date: string;
  test_type: string;
  test_category?: string;
  lab_name?: string;
  ordering_provider?: string;
  biomarkers: Array<{
    name: string;
    value: number;
    unit: string;
    status?: string;
  }>;
  notes?: string;
  created_at: string;
}

// ─── Status helpers ───────────────────────────────────────────────────────────

const STATUS_COLOR: Record<string, string> = {
  normal:   '#6EE7B7',
  low:      '#60A5FA',
  high:     '#F5A623',
  critical: '#F87171',
};

const STATUS_LABEL: Record<string, string> = {
  normal:   'Normal',
  low:      'Low',
  high:     'High',
  critical: 'Critical',
};

// ─── Scan Lab Report Modal ────────────────────────────────────────────────────

function ScanLabModal({
  visible,
  onClose,
  onSaved,
}: {
  visible: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [phase, setPhase] = useState<'pick' | 'review'>('pick');
  const [error, setError] = useState<string | null>(null);

  // Editable scan results
  const [testType, setTestType] = useState('');
  const [testDate, setTestDate] = useState('');
  const [labName, setLabName] = useState('');
  const [provider, setProvider] = useState('');
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([]);
  const [notes, setNotes] = useState('');

  function reset() {
    setPhotoUri(null);
    setPhase('pick');
    setError(null);
    setTestType('');
    setTestDate('');
    setLabName('');
    setProvider('');
    setBiomarkers([]);
    setNotes('');
  }

  function handleClose() { reset(); onClose(); }

  async function pickFromGallery() {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Allow photo library access to scan lab reports.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.9,
      allowsEditing: false,
    });
    if (!result.canceled && result.assets[0]) setPhotoUri(result.assets[0].uri);
  }

  async function takePhoto() {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Allow camera access to scan lab reports.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.9 });
    if (!result.canceled && result.assets[0]) setPhotoUri(result.assets[0].uri);
  }

  async function scanReport() {
    if (!photoUri) return;
    setScanning(true);
    setError(null);
    try {
      const formData = new FormData();
      const filename = photoUri.split('/').pop() ?? 'lab.jpg';
      const ext = filename.split('.').pop()?.toLowerCase() ?? 'jpg';
      formData.append('image', { uri: photoUri, name: filename, type: ext === 'png' ? 'image/png' : 'image/jpeg' } as any);

      const { data } = await api.post('/api/v1/lab-results/scan-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setTestType(data?.test_type ?? '');
      setTestDate(data?.test_date ?? format(new Date(), 'yyyy-MM-dd'));
      setLabName(data?.lab_name ?? '');
      setProvider(data?.ordering_provider ?? '');
      setNotes(data?.notes ?? '');
      const parsed: Biomarker[] = (data?.biomarkers ?? []).map((b: any) => ({
        name: b.biomarker_name ?? b.name ?? '',
        value: String(b.value ?? ''),
        unit: b.unit ?? '',
        status: b.status ?? undefined,
      }));
      setBiomarkers(parsed.length > 0 ? parsed : [{ name: '', value: '', unit: '', status: undefined }]);
      setPhase('review');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to scan report. Try a clearer image.');
    } finally {
      setScanning(false);
    }
  }

  function updateBiomarker(idx: number, field: keyof Biomarker, value: string) {
    setBiomarkers((prev) => prev.map((b, i) => (i === idx ? { ...b, [field]: value } : b)));
  }
  function addBiomarker() { setBiomarkers((prev) => [...prev, { name: '', value: '', unit: '', status: undefined }]); }
  function removeBiomarker(idx: number) { setBiomarkers((prev) => prev.filter((_, i) => i !== idx)); }

  async function handleSave() {
    if (!testType.trim()) { setError('Test type is required.'); return; }
    const valid = biomarkers.filter((b) => b.name.trim() && b.value.trim() && b.unit.trim());
    if (valid.length === 0) { setError('At least one complete biomarker is required.'); return; }
    setSaving(true);
    setError(null);
    try {
      await api.post('/api/v1/lab-results/lab-results', {
        test_date: testDate || format(new Date(), 'yyyy-MM-dd'),
        test_type: testType.trim(),
        lab_name: labName.trim() || undefined,
        ordering_provider: provider.trim() || undefined,
        biomarkers: valid.map((b) => ({ name: b.name.trim(), value: parseFloat(b.value), unit: b.unit.trim() })),
        notes: notes.trim() || undefined,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      reset();
      onSaved();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={handleClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} className="flex-1 bg-obsidian-900">
        <View className="flex-row items-center justify-between px-6 pt-14 pb-4 border-b border-surface-border">
          <TouchableOpacity onPress={phase === 'review' ? () => setPhase('pick') : handleClose}>
            <Text className="text-[#526380] font-sansMedium">{phase === 'review' ? '← Back' : 'Cancel'}</Text>
          </TouchableOpacity>
          <Text className="text-[#E8EDF5] font-sansMedium text-base">
            {phase === 'pick' ? 'Scan Lab Report' : 'Review Results'}
          </Text>
          {phase === 'review' ? (
            <TouchableOpacity onPress={handleSave} disabled={saving}>
              {saving ? <ActivityIndicator size="small" color="#00D4AA" /> : (
                <Text className="text-primary-500 font-sansMedium">Save</Text>
              )}
            </TouchableOpacity>
          ) : <View style={{ width: 50 }} />}
        </View>

        <ScrollView className="flex-1 px-6 pt-5" keyboardShouldPersistTaps="handled">
          {phase === 'pick' ? (
            <>
              <Text className="text-[#526380] text-sm text-center mb-5 leading-5">
                Take a photo or upload an image of your lab report. Claude AI will extract all biomarkers automatically.
              </Text>

              {photoUri ? (
                <View className="mb-5">
                  <Image source={{ uri: photoUri }} className="w-full rounded-2xl" style={{ height: 240 }} resizeMode="contain" />
                  <TouchableOpacity
                    onPress={() => setPhotoUri(null)}
                    className="absolute top-2 right-2 bg-obsidian-900/80 rounded-full p-1.5"
                  >
                    <Ionicons name="close" size={16} color="#E8EDF5" />
                  </TouchableOpacity>
                </View>
              ) : (
                <View className="flex-row gap-3 mb-5">
                  <TouchableOpacity
                    onPress={takePhoto}
                    className="flex-1 bg-surface-raised border border-surface-border rounded-2xl py-8 items-center gap-2"
                  >
                    <Ionicons name="camera" size={28} color="#00D4AA" />
                    <Text className="text-[#E8EDF5] text-sm font-sansMedium">Take Photo</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={pickFromGallery}
                    className="flex-1 bg-surface-raised border border-surface-border rounded-2xl py-8 items-center gap-2"
                  >
                    <Ionicons name="images" size={28} color="#818CF8" />
                    <Text className="text-[#E8EDF5] text-sm font-sansMedium">From Gallery</Text>
                  </TouchableOpacity>
                </View>
              )}

              {error && <Text className="text-health-critical text-sm mb-4 text-center">{error}</Text>}

              {photoUri && (
                <TouchableOpacity
                  onPress={scanReport}
                  disabled={scanning}
                  className="bg-primary-500 rounded-2xl py-4 items-center flex-row justify-center gap-2"
                  activeOpacity={0.8}
                >
                  {scanning ? (
                    <>
                      <ActivityIndicator size="small" color="#080B10" />
                      <Text className="text-obsidian-900 font-sansMedium">Extracting results…</Text>
                    </>
                  ) : (
                    <>
                      <Ionicons name="scan" size={18} color="#080B10" />
                      <Text className="text-obsidian-900 font-sansMedium text-base">Extract with Claude AI</Text>
                    </>
                  )}
                </TouchableOpacity>
              )}
            </>
          ) : (
            <>
              <View className="bg-primary-500/10 border border-primary-500/30 rounded-xl px-4 py-3 mb-5 flex-row gap-2 items-center">
                <Ionicons name="checkmark-circle" size={16} color="#00D4AA" />
                <Text className="text-primary-500 text-xs flex-1">Review and correct the extracted data before saving.</Text>
              </View>

              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Test Type *</Text>
              <TextInput
                className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-4"
                value={testType}
                onChangeText={setTestType}
                placeholder="e.g. Lipid Panel, CBC"
                placeholderTextColor="#526380"
              />

              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Test Date</Text>
              <TextInput
                className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-4"
                value={testDate}
                onChangeText={setTestDate}
                placeholder="YYYY-MM-DD"
                placeholderTextColor="#526380"
                keyboardType="numbers-and-punctuation"
              />

              <View className="flex-row gap-3 mb-4">
                <View className="flex-1">
                  <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Lab Name</Text>
                  <TextInput
                    className="bg-surface-raised border border-surface-border rounded-xl px-3 py-3 text-[#E8EDF5]"
                    value={labName}
                    onChangeText={setLabName}
                    placeholder="Quest, LabCorp…"
                    placeholderTextColor="#526380"
                  />
                </View>
                <View className="flex-1">
                  <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Provider</Text>
                  <TextInput
                    className="bg-surface-raised border border-surface-border rounded-xl px-3 py-3 text-[#E8EDF5]"
                    value={provider}
                    onChangeText={setProvider}
                    placeholder="Dr. Smith…"
                    placeholderTextColor="#526380"
                  />
                </View>
              </View>

              <View className="flex-row items-center justify-between mb-2">
                <Text className="text-[#526380] text-xs uppercase tracking-wider">Biomarkers ({biomarkers.length})</Text>
                <TouchableOpacity onPress={addBiomarker} className="flex-row items-center gap-1">
                  <Ionicons name="add-circle-outline" size={16} color="#00D4AA" />
                  <Text className="text-primary-500 text-xs font-sansMedium">Add</Text>
                </TouchableOpacity>
              </View>

              {biomarkers.map((b, idx) => (
                <View key={idx} className="bg-surface border border-surface-border rounded-xl p-3 mb-2">
                  <View className="flex-row items-center justify-between mb-2">
                    <Text className="text-[#526380] text-xs">#{idx + 1}</Text>
                    {biomarkers.length > 1 && (
                      <TouchableOpacity onPress={() => removeBiomarker(idx)}>
                        <Ionicons name="close-circle" size={18} color="#F87171" />
                      </TouchableOpacity>
                    )}
                  </View>
                  <TextInput
                    className="bg-surface-raised border border-surface-border rounded-xl px-3 py-2.5 text-[#E8EDF5] text-sm mb-2"
                    value={b.name}
                    onChangeText={(v) => updateBiomarker(idx, 'name', v)}
                    placeholder="e.g. Total Cholesterol"
                    placeholderTextColor="#526380"
                  />
                  <View className="flex-row gap-2">
                    <TextInput
                      className="bg-surface-raised border border-surface-border rounded-xl px-3 py-2.5 text-[#E8EDF5] text-sm flex-1"
                      value={b.value}
                      onChangeText={(v) => updateBiomarker(idx, 'value', v)}
                      placeholder="Value"
                      placeholderTextColor="#526380"
                      keyboardType="decimal-pad"
                    />
                    <TextInput
                      className="bg-surface-raised border border-surface-border rounded-xl px-3 py-2.5 text-[#E8EDF5] text-sm"
                      value={b.unit}
                      onChangeText={(v) => updateBiomarker(idx, 'unit', v)}
                      placeholder="Unit"
                      placeholderTextColor="#526380"
                      style={{ width: 80 }}
                    />
                  </View>
                </View>
              ))}

              {error && <Text className="text-health-critical text-sm mt-2 mb-2">{error}</Text>}
            </>
          )}
          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Add Lab Result Modal ─────────────────────────────────────────────────────

function AddLabResultModal({
  visible,
  onClose,
  onSaved,
}: {
  visible: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [testDate, setTestDate] = useState(() => format(new Date(), 'yyyy-MM-dd'));
  const [testType, setTestType] = useState('');
  const [labName, setLabName] = useState('');
  const [provider, setProvider] = useState('');
  const [notes, setNotes] = useState('');
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([{ name: '', value: '', unit: '', status: undefined }]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setTestDate(format(new Date(), 'yyyy-MM-dd'));
    setTestType('');
    setLabName('');
    setProvider('');
    setNotes('');
    setBiomarkers([{ name: '', value: '', unit: '', status: undefined }]);
    setError(null);
  }

  function handleClose() {
    reset();
    onClose();
  }

  function addBiomarker() {
    setBiomarkers((prev) => [...prev, { name: '', value: '', unit: '', status: undefined }]);
  }

  function removeBiomarker(idx: number) {
    setBiomarkers((prev) => prev.filter((_, i) => i !== idx));
  }

  function updateBiomarker(idx: number, field: keyof Biomarker, value: string) {
    setBiomarkers((prev) => prev.map((b, i) => (i === idx ? { ...b, [field]: value } : b)));
  }

  async function handleSave() {
    if (!testType.trim()) {
      setError('Test type is required (e.g. "Lipid Panel", "CBC").');
      return;
    }
    if (!testDate) {
      setError('Test date is required.');
      return;
    }
    const validBiomarkers = biomarkers.filter((b) => b.name.trim() && b.value.trim() && b.unit.trim());
    if (validBiomarkers.length === 0) {
      setError('Add at least one biomarker with name, value, and unit.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await api.post('/api/v1/lab-results/lab-results', {
        test_date: testDate,
        test_type: testType.trim(),
        lab_name: labName.trim() || undefined,
        ordering_provider: provider.trim() || undefined,
        biomarkers: validBiomarkers.map((b) => ({
          name: b.name.trim(),
          value: parseFloat(b.value),
          unit: b.unit.trim(),
        })),
        notes: notes.trim() || undefined,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      reset();
      onSaved();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save lab result';
      setError(msg);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={handleClose}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        className="flex-1 bg-obsidian-900"
      >
        {/* Header */}
        <View className="flex-row items-center justify-between px-6 pt-14 pb-4 border-b border-surface-border">
          <TouchableOpacity onPress={handleClose}>
            <Text className="text-[#526380] font-sansMedium">Cancel</Text>
          </TouchableOpacity>
          <Text className="text-[#E8EDF5] font-sansMedium text-base">Add Lab Result</Text>
          <TouchableOpacity onPress={handleSave} disabled={saving}>
            {saving ? (
              <ActivityIndicator size="small" color="#00D4AA" />
            ) : (
              <Text className="text-primary-500 font-sansMedium">Save</Text>
            )}
          </TouchableOpacity>
        </View>

        <ScrollView className="flex-1 px-6 pt-5" keyboardShouldPersistTaps="handled">
          {/* Test info */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Test Type *</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-4"
            value={testType}
            onChangeText={setTestType}
            placeholder="e.g. Lipid Panel, CBC, Metabolic Panel"
            placeholderTextColor="#526380"
          />

          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Test Date *</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-4"
            value={testDate}
            onChangeText={setTestDate}
            placeholder="YYYY-MM-DD"
            placeholderTextColor="#526380"
            keyboardType="numbers-and-punctuation"
          />

          <View className="flex-row gap-3 mb-4">
            <View className="flex-1">
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Lab Name</Text>
              <TextInput
                className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5]"
                value={labName}
                onChangeText={setLabName}
                placeholder="e.g. Quest Diagnostics"
                placeholderTextColor="#526380"
              />
            </View>
          </View>

          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Ordering Provider</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-5"
            value={provider}
            onChangeText={setProvider}
            placeholder="e.g. Dr. Smith"
            placeholderTextColor="#526380"
          />

          {/* Biomarkers */}
          <View className="flex-row items-center justify-between mb-2">
            <Text className="text-[#526380] text-xs uppercase tracking-wider">Biomarkers *</Text>
            <TouchableOpacity onPress={addBiomarker} className="flex-row items-center gap-1">
              <Ionicons name="add-circle-outline" size={16} color="#00D4AA" />
              <Text className="text-primary-500 text-xs font-sansMedium">Add marker</Text>
            </TouchableOpacity>
          </View>

          {biomarkers.map((b, idx) => (
            <View key={idx} className="bg-surface border border-surface-border rounded-xl p-3 mb-2">
              <View className="flex-row items-center justify-between mb-2">
                <Text className="text-[#526380] text-xs">Biomarker {idx + 1}</Text>
                {biomarkers.length > 1 && (
                  <TouchableOpacity onPress={() => removeBiomarker(idx)}>
                    <Ionicons name="close-circle" size={18} color="#F87171" />
                  </TouchableOpacity>
                )}
              </View>
              <TextInput
                className="bg-surface-raised border border-surface-border rounded-xl px-3 py-2.5 text-[#E8EDF5] text-sm mb-2"
                value={b.name}
                onChangeText={(v) => updateBiomarker(idx, 'name', v)}
                placeholder="e.g. Total Cholesterol"
                placeholderTextColor="#526380"
              />
              <View className="flex-row gap-2">
                <TextInput
                  className="bg-surface-raised border border-surface-border rounded-xl px-3 py-2.5 text-[#E8EDF5] text-sm flex-1"
                  value={b.value}
                  onChangeText={(v) => updateBiomarker(idx, 'value', v)}
                  placeholder="Value"
                  placeholderTextColor="#526380"
                  keyboardType="decimal-pad"
                />
                <TextInput
                  className="bg-surface-raised border border-surface-border rounded-xl px-3 py-2.5 text-[#E8EDF5] text-sm"
                  value={b.unit}
                  onChangeText={(v) => updateBiomarker(idx, 'unit', v)}
                  placeholder="Unit"
                  placeholderTextColor="#526380"
                  style={{ width: 90 }}
                />
              </View>
            </View>
          ))}

          {/* Notes */}
          <Text className="text-[#526380] text-xs uppercase tracking-wider mt-4 mb-2">Notes</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-5"
            value={notes}
            onChangeText={setNotes}
            placeholder="Additional notes…"
            placeholderTextColor="#526380"
            multiline
            numberOfLines={3}
          />

          {error && (
            <Text className="text-health-critical text-sm mb-4">{error}</Text>
          )}
          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Lab Result Card ──────────────────────────────────────────────────────────

function LabResultCard({ result, onDelete }: { result: LabResult; onDelete: (id: string) => void }) {
  const [expanded, setExpanded] = useState(false);

  const abnormalCount = result.biomarkers.filter(
    (b) => b.status && b.status !== 'normal',
  ).length;

  function confirmDelete() {
    Alert.alert('Delete Lab Result', 'Remove this lab result?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => onDelete(result.id) },
    ]);
  }

  return (
    <TouchableOpacity
      onPress={() => setExpanded((e) => !e)}
      className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2"
      activeOpacity={0.8}
    >
      <View className="flex-row items-start justify-between">
        <View className="flex-row items-center gap-3 flex-1">
          <View className="w-10 h-10 rounded-xl bg-primary-500/10 items-center justify-center">
            <Ionicons name="flask-outline" size={18} color="#00D4AA" />
          </View>
          <View className="flex-1">
            <Text className="text-[#E8EDF5] font-sansMedium text-sm">{result.test_type}</Text>
            <Text className="text-[#526380] text-xs mt-0.5">
              {format(new Date(result.test_date), 'MMM d, yyyy')}
              {result.lab_name ? ` · ${result.lab_name}` : ''}
            </Text>
          </View>
        </View>
        <View className="flex-row items-center gap-2">
          {abnormalCount > 0 && (
            <View className="bg-amber-500/20 rounded-full px-2 py-0.5">
              <Text className="text-amber-500 text-xs font-sansMedium">{abnormalCount} abnormal</Text>
            </View>
          )}
          <TouchableOpacity onPress={confirmDelete} className="p-1">
            <Ionicons name="trash-outline" size={16} color="#526380" />
          </TouchableOpacity>
          <Ionicons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={16}
            color="#526380"
          />
        </View>
      </View>

      {expanded && result.biomarkers.length > 0 && (
        <View className="mt-3 pt-3 border-t border-surface-border gap-1.5">
          {result.biomarkers.map((b, i) => {
            const statusColor = STATUS_COLOR[b.status ?? 'normal'] ?? '#6EE7B7';
            return (
              <View key={i} className="flex-row items-center justify-between">
                <Text className="text-[#E8EDF5] text-xs flex-1">{b.name}</Text>
                <View className="flex-row items-center gap-2">
                  <Text className="text-[#E8EDF5] text-xs font-sansMedium">
                    {b.value} {b.unit}
                  </Text>
                  {b.status && (
                    <View className="px-1.5 py-0.5 rounded" style={{ backgroundColor: `${statusColor}20` }}>
                      <Text className="text-xs" style={{ color: statusColor }}>
                        {STATUS_LABEL[b.status] ?? b.status}
                      </Text>
                    </View>
                  )}
                </View>
              </View>
            );
          })}
          {result.notes && (
            <Text className="text-[#526380] text-xs mt-1 leading-4">{result.notes}</Text>
          )}
        </View>
      )}
    </TouchableOpacity>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function LabResultsScreen() {
  const queryClient = useQueryClient();
  const [showManual, setShowManual] = useState(false);
  const [showScan, setShowScan] = useState(false);

  const { data: results, isLoading } = useQuery<LabResult[]>({
    queryKey: ['lab-results'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/lab-results/lab-results');
      return (data?.lab_results ?? data?.results ?? data ?? []) as LabResult[];
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/lab-results/lab-results/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['lab-results'] }),
    onError: () => Alert.alert('Error', 'Could not delete lab result'),
  });

  const handleSaved = useCallback(() => {
    setShowManual(false);
    setShowScan(false);
    queryClient.invalidateQueries({ queryKey: ['lab-results'] });
  }, [queryClient]);

  return (
    <>
      <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
        {/* Header */}
        <View className="px-6 pt-14 pb-4 border-b border-surface-border">
          <Text className="text-xl font-display text-[#E8EDF5] mb-3">Lab Results</Text>
          <View className="flex-row gap-3">
            <TouchableOpacity
              onPress={() => setShowScan(true)}
              className="flex-1 bg-primary-500 rounded-xl py-2.5 flex-row items-center justify-center gap-1.5"
              activeOpacity={0.8}
            >
              <Ionicons name="scan" size={16} color="#080B10" />
              <Text className="text-obsidian-900 font-sansMedium text-sm">Scan Report</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => setShowManual(true)}
              className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-2.5 flex-row items-center justify-center gap-1.5"
              activeOpacity={0.8}
            >
              <Ionicons name="create-outline" size={16} color="#E8EDF5" />
              <Text className="text-[#E8EDF5] font-sansMedium text-sm">Manual Entry</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View className="px-6 pt-5">

          {isLoading ? (
            <ActivityIndicator color="#00D4AA" className="mt-8" />
          ) : !results || results.length === 0 ? (
            <View className="items-center py-12">
              <Ionicons name="flask-outline" size={40} color="#526380" />
              <Text className="text-[#526380] text-base mt-3">No lab results yet</Text>
              <Text className="text-[#526380] text-sm mt-1 text-center">
                Tap "Add" to enter your first lab result
              </Text>
            </View>
          ) : (
            results.map((result) => (
              <LabResultCard
                key={result.id}
                result={result}
                onDelete={(id) => deleteMutation.mutate(id)}
              />
            ))
          )}
        </View>
      </ScrollView>

      <ScanLabModal visible={showScan} onClose={() => setShowScan(false)} onSaved={handleSaved} />
      <AddLabResultModal visible={showManual} onClose={() => setShowManual(false)} onSaved={handleSaved} />
    </>
  );
}
