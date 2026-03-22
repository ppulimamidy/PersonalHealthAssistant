/**
 * Nutrition Log screen — manual entry + photo scanning.
 *
 * POST /api/v1/nutrition/recognize-meal-image  (multipart)
 * POST /api/v1/nutrition/log-meal
 * GET  /api/v1/nutrition/meals?days=7
 * DELETE /api/v1/nutrition/meals/{meal_id}
 */

import { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, TextInput,
  ActivityIndicator, Alert, Modal, KeyboardAvoidingView,
  Platform, Image,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import * as ImagePicker from 'expo-image-picker';
import { format, isToday, isYesterday } from 'date-fns';
import { api } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';
import DailyProgressCard from '@/components/DailyProgressCard';
import NutritionInsightCard from '@/components/NutritionInsightCard';
import ProactiveSuggestionCard from '@/components/ProactiveSuggestionCard';
import InlineNutritionChat from '@/components/InlineNutritionChat';
import SwapSheet from '@/components/SwapSheet';
import { router } from 'expo-router';

// ─── Types ────────────────────────────────────────────────────────────────────

type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

type PortionUnit =
  | 'g' | 'oz' | 'cups' | 'tbsp' | 'tsp' | 'ml'
  | 'piece' | 'pieces' | 'slice' | 'slices'
  | 'scoop' | 'scoops' | 'nugget' | 'nuggets'
  | 'wing' | 'strip' | 'patty' | 'fillet'
  | 'bowl' | 'handful' | 'serving' | 'bar'
  | 'can' | 'bottle' | 'stick' | 'packet';

const PORTION_UNITS: { value: PortionUnit; label: string }[] = [
  { value: 'g', label: 'g' },
  { value: 'oz', label: 'oz' },
  { value: 'piece', label: 'piece' },
  { value: 'pieces', label: 'pieces' },
  { value: 'slice', label: 'slice' },
  { value: 'slices', label: 'slices' },
  { value: 'cups', label: 'cup' },
  { value: 'bowl', label: 'bowl' },
  { value: 'scoop', label: 'scoop' },
  { value: 'scoops', label: 'scoops' },
  { value: 'tbsp', label: 'tbsp' },
  { value: 'tsp', label: 'tsp' },
  { value: 'handful', label: 'handful' },
  { value: 'serving', label: 'serving' },
  { value: 'nugget', label: 'nugget' },
  { value: 'nuggets', label: 'nuggets' },
  { value: 'wing', label: 'wing' },
  { value: 'strip', label: 'strip' },
  { value: 'patty', label: 'patty' },
  { value: 'fillet', label: 'fillet' },
  { value: 'bar', label: 'bar' },
  { value: 'can', label: 'can' },
  { value: 'bottle', label: 'bottle' },
  { value: 'ml', label: 'ml' },
];

// Approximate gram equivalents per unit (generic defaults)
const UNIT_TO_GRAMS: Record<string, number> = {
  g: 1, oz: 28, cups: 240, tbsp: 15, tsp: 5, ml: 1,
  piece: 120, pieces: 120, slice: 30, slices: 30,
  scoop: 65, scoops: 65, bowl: 300, handful: 30,
  serving: 100, nugget: 18, nuggets: 18, wing: 30,
  strip: 25, patty: 115, fillet: 170, bar: 50,
  can: 355, bottle: 500, stick: 15, packet: 30,
};

interface FoodItem {
  name: string;
  portion_g: number;
  quantity?: number;
  unit?: PortionUnit;
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
}

interface RecognizedFood {
  name: string;
  confidence?: number;
  portion_g?: number;
  quantity?: number;
  unit?: string;
  calories?: number;
  category?: string;
}

interface MealLog {
  id: string;
  meal_type: MealType;
  meal_name?: string;
  food_items: FoodItem[];
  user_notes?: string;
  logged_at?: string;
  timestamp?: string;
  total_calories?: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const MEAL_TYPE_CONFIG: Record<MealType, { icon: string; color: string; label: string }> = {
  breakfast: { icon: '🌅', color: '#F5A623', label: 'Breakfast' },
  lunch:     { icon: '☀️', color: '#6EE7B7', label: 'Lunch' },
  dinner:    { icon: '🌙', color: '#818CF8', label: 'Dinner' },
  snack:     { icon: '🍎', color: '#F87171', label: 'Snack' },
};

function inferMealType(): MealType {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 11) return 'breakfast';
  if (hour >= 11 && hour < 15) return 'lunch';
  if (hour >= 17 && hour < 21) return 'dinner';
  return 'snack';
}

function formatMealDate(dateStr?: string): string {
  if (!dateStr) return 'Unknown';
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return 'Unknown';
  if (isToday(d)) return 'Today';
  if (isYesterday(d)) return 'Yesterday';
  return format(d, 'MMM d');
}

// ─── Photo Scan Modal ─────────────────────────────────────────────────────────

function PhotoScanModal({
  visible,
  onClose,
  onSaved,
}: {
  visible: boolean;
  onClose: () => void;
  onSaved: (mealType?: string, foodItems?: any[]) => void;
}) {
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [mealType, setMealType] = useState<MealType>(inferMealType());
  const [recognizedFoods, setRecognizedFoods] = useState<FoodItem[]>([]);
  const [mealName, setMealName] = useState('');
  const [scanning, setScanning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [phase, setPhase] = useState<'pick' | 'review'>('pick');
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setPhotoUri(null);
    setMealType(inferMealType());
    setRecognizedFoods([]);
    setMealName('');
    setPhase('pick');
    setError(null);
  }

  function handleClose() {
    reset();
    onClose();
  }

  async function pickFromGallery() {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Allow photo library access to scan meals.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.8,
      allowsEditing: false,
    });
    if (!result.canceled && result.assets[0]) {
      setPhotoUri(result.assets[0].uri);
    }
  }

  async function takePhoto() {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Allow camera access to scan meals.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ['images'],
      quality: 0.8,
    });
    if (!result.canceled && result.assets[0]) {
      setPhotoUri(result.assets[0].uri);
    }
  }

  async function analyzePhoto() {
    if (!photoUri) return;
    setScanning(true);
    setError(null);
    try {
      const formData = new FormData();
      const filename = photoUri.split('/').pop() ?? 'meal.jpg';
      const ext = filename.split('.').pop()?.toLowerCase() ?? 'jpg';
      const mimeType = ext === 'png' ? 'image/png' : 'image/jpeg';
      formData.append('image', { uri: photoUri, name: filename, type: mimeType } as any);
      formData.append('meal_type', mealType);

      const { data } = await api.post('/api/v1/nutrition/recognize-meal-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const foods: FoodItem[] = (data?.recognized_foods ?? []).map((f: any) => ({
        name: f.name,
        portion_g: f.portion_g || f.portion_estimate?.grams || 100,
        quantity: f.quantity ?? f.portion_estimate?.estimated_quantity ?? 1,
        unit: (f.unit ?? f.portion_estimate?.unit ?? 'serving') as PortionUnit,
        calories: f.calories ?? 0,
        protein_g: f.protein_g ?? 0,
        carbs_g: f.carbs_g ?? 0,
        fat_g: f.fat_g ?? 0,
      }));

      if (foods.length === 0) {
        setError('No foods detected. Try a clearer photo with good lighting.');
        return;
      }

      setRecognizedFoods(foods);
      setPhase('review');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to analyze photo. Try again.');
    } finally {
      setScanning(false);
    }
  }

  function updateFood(idx: number, field: keyof FoodItem, value: string | number) {
    setRecognizedFoods((prev) => prev.map((f, i) => {
      if (i !== idx) return f;
      const updated = { ...f, [field]: value };
      // When quantity or unit changes, recompute portion_g
      if (field === 'quantity' || field === 'unit') {
        const qty = field === 'quantity' ? Number(value) || 0 : (f.quantity ?? f.portion_g);
        const u = field === 'unit' ? String(value) : (f.unit ?? 'g');
        updated.portion_g = Math.round(qty * (UNIT_TO_GRAMS[u] ?? 1));
      }
      return updated;
    }));
  }

  function removeFood(idx: number) {
    setRecognizedFoods((prev) => prev.filter((_, i) => i !== idx));
  }

  async function handleSave() {
    const validFoods = recognizedFoods.filter((f) => f.name.trim());
    if (validFoods.length === 0) {
      setError('Add at least one food item.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post('/api/v1/nutrition/log-meal', {
        meal_type: mealType,
        meal_name: mealName.trim() || undefined,
        food_items: validFoods.map((f) => ({
          name: f.name.trim(),
          portion_g: Number(f.portion_g) || 100,
          quantity: f.quantity ?? f.portion_g,
          unit: f.unit ?? 'g',
        })),
        logged_at: new Date().toISOString(),
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      const savedFoods = validFoods.map((f) => ({
        name: f.name.trim(),
        portion_g: Number(f.portion_g) || 100,
        quantity: f.quantity ?? f.portion_g,
        unit: f.unit ?? 'g',
        calories: f.calories ?? 0,
        protein_g: f.protein_g ?? 0,
        carbs_g: f.carbs_g ?? 0,
        fat_g: f.fat_g ?? 0,
      }));
      reset();
      onSaved(mealType, savedFoods);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to log meal');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={handleClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} className="flex-1 bg-obsidian-900">
        {/* Header */}
        <View className="flex-row items-center justify-between px-6 pt-14 pb-4 border-b border-surface-border">
          <TouchableOpacity onPress={phase === 'review' ? () => setPhase('pick') : handleClose}>
            <Text className="text-[#526380] font-sansMedium">{phase === 'review' ? '← Back' : 'Cancel'}</Text>
          </TouchableOpacity>
          <Text className="text-[#E8EDF5] font-sansMedium text-base">
            {phase === 'pick' ? 'Scan Meal Photo' : 'Review Foods'}
          </Text>
          {phase === 'review' ? (
            <TouchableOpacity onPress={handleSave} disabled={saving}>
              {saving ? <ActivityIndicator size="small" color="#00D4AA" /> : (
                <Text className="text-primary-500 font-sansMedium">Log Meal</Text>
              )}
            </TouchableOpacity>
          ) : (
            <View style={{ width: 50 }} />
          )}
        </View>

        <ScrollView className="flex-1 px-6 pt-5" keyboardShouldPersistTaps="handled">

          {phase === 'pick' ? (
            <>
              {/* Meal type */}
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Meal Type</Text>
              <View className="flex-row flex-wrap gap-2 mb-5">
                {(Object.keys(MEAL_TYPE_CONFIG) as MealType[]).map((type) => {
                  const cfg = MEAL_TYPE_CONFIG[type];
                  const selected = mealType === type;
                  return (
                    <TouchableOpacity
                      key={type}
                      onPress={() => setMealType(type)}
                      className="flex-row items-center gap-1.5 px-3 py-2 rounded-xl border"
                      style={{
                        backgroundColor: selected ? `${cfg.color}20` : 'transparent',
                        borderColor: selected ? cfg.color : '#1E2A3B',
                      }}
                    >
                      <Text className="text-sm">{cfg.icon}</Text>
                      <Text className="text-sm font-sansMedium" style={{ color: selected ? cfg.color : '#526380' }}>
                        {cfg.label}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              {/* Photo picker */}
              {photoUri ? (
                <View className="mb-5">
                  <Image source={{ uri: photoUri }} className="w-full rounded-2xl" style={{ height: 220 }} resizeMode="cover" />
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

              {error && <Text className="text-health-critical text-sm mb-4">{error}</Text>}

              {photoUri && (
                <TouchableOpacity
                  onPress={analyzePhoto}
                  disabled={scanning}
                  className="bg-primary-500 rounded-2xl py-4 items-center flex-row justify-center gap-2"
                  activeOpacity={0.8}
                >
                  {scanning ? (
                    <>
                      <ActivityIndicator size="small" color="#080B10" />
                      <Text className="text-obsidian-900 font-sansMedium">Analyzing…</Text>
                    </>
                  ) : (
                    <>
                      <Ionicons name="sparkles" size={18} color="#080B10" />
                      <Text className="text-obsidian-900 font-sansMedium text-base">Analyze with AI</Text>
                    </>
                  )}
                </TouchableOpacity>
              )}
            </>
          ) : (
            <>
              {/* Review phase */}
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Meal Name (optional)</Text>
              <TextInput
                className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-5"
                value={mealName}
                onChangeText={setMealName}
                placeholder="e.g. Chicken Caesar Salad"
                placeholderTextColor="#526380"
              />

              <View className="flex-row items-center justify-between mb-2">
                <Text className="text-[#526380] text-xs uppercase tracking-wider">Recognized Foods</Text>
                <Text className="text-[#526380] text-xs">Tap to edit</Text>
              </View>

              {recognizedFoods.map((food, idx) => (
                <View key={idx} className="mb-3">
                  <View className="flex-row gap-2 items-center">
                    <TextInput
                      className="bg-surface-raised border border-surface-border rounded-xl px-3 py-3 text-[#E8EDF5] flex-1"
                      value={food.name}
                      onChangeText={(v) => updateFood(idx, 'name', v)}
                      placeholder="Food name"
                      placeholderTextColor="#526380"
                    />
                    <TouchableOpacity onPress={() => removeFood(idx)}>
                      <Ionicons name="close-circle" size={20} color="#F87171" />
                    </TouchableOpacity>
                  </View>
                  <View className="flex-row gap-2 mt-1.5 items-center">
                    <View className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl px-3 py-2.5" style={{ width: 70 }}>
                      <TextInput
                        className="text-[#E8EDF5] flex-1 text-center"
                        value={String(food.quantity ?? food.portion_g)}
                        onChangeText={(v) => updateFood(idx, 'quantity', parseFloat(v) || 0)}
                        keyboardType="decimal-pad"
                        placeholder="1"
                        placeholderTextColor="#526380"
                      />
                    </View>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} className="flex-1">
                      <View className="flex-row gap-1">
                        {PORTION_UNITS.map((u) => {
                          const selected = (food.unit ?? 'g') === u.value;
                          return (
                            <TouchableOpacity
                              key={u.value}
                              onPress={() => updateFood(idx, 'unit', u.value)}
                              className="px-2.5 py-2 rounded-lg border"
                              style={{
                                backgroundColor: selected ? '#00D4AA20' : 'transparent',
                                borderColor: selected ? '#00D4AA' : '#1E2A3B',
                              }}
                            >
                              <Text
                                className="text-xs font-sansMedium"
                                style={{ color: selected ? '#00D4AA' : '#526380' }}
                              >
                                {u.label}
                              </Text>
                            </TouchableOpacity>
                          );
                        })}
                      </View>
                    </ScrollView>
                  </View>
                  <Text className="text-[#526380] text-xs mt-1 ml-1">
                    ≈ {food.portion_g}g
                  </Text>
                </View>
              ))}

              {error && <Text className="text-health-critical text-sm mt-2">{error}</Text>}
            </>
          )}

          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Log Meal Modal ───────────────────────────────────────────────────────────

function LogMealModal({
  visible,
  onClose,
  onSaved,
}: {
  visible: boolean;
  onClose: () => void;
  onSaved: (mealType?: string, foodItems?: any[]) => void;
}) {
  const [mealType, setMealType] = useState<MealType>(inferMealType());
  const [mealName, setMealName] = useState('');
  const [notes, setNotes] = useState('');
  const [foods, setFoods] = useState<FoodItem[]>([{ name: '', portion_g: 100, quantity: 1, unit: 'serving' }]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setMealType(inferMealType());
    setMealName('');
    setNotes('');
    setFoods([{ name: '', portion_g: 100, quantity: 1, unit: 'serving' }]);
    setError(null);
  }

  function handleClose() { reset(); onClose(); }

  function addFood() { setFoods((prev) => [...prev, { name: '', portion_g: 100, quantity: 1, unit: 'serving' }]); }
  function removeFood(idx: number) { setFoods((prev) => prev.filter((_, i) => i !== idx)); }
  function updateFood(idx: number, field: keyof FoodItem, value: string | number) {
    setFoods((prev) => prev.map((f, i) => {
      if (i !== idx) return f;
      const updated = { ...f, [field]: value };
      if (field === 'quantity' || field === 'unit') {
        const qty = field === 'quantity' ? Number(value) || 0 : (f.quantity ?? f.portion_g);
        const u = field === 'unit' ? String(value) : (f.unit ?? 'g');
        updated.portion_g = Math.round(qty * (UNIT_TO_GRAMS[u] ?? 1));
      }
      return updated;
    }));
  }

  async function handleSave() {
    const validFoods = foods.filter((f) => f.name.trim());
    if (validFoods.length === 0) { setError('Add at least one food item.'); return; }
    setSaving(true);
    setError(null);
    try {
      await api.post('/api/v1/nutrition/log-meal', {
        meal_type: mealType,
        meal_name: mealName.trim() || undefined,
        food_items: validFoods.map((f) => ({
          name: f.name.trim(),
          portion_g: Number(f.portion_g) || 100,
          quantity: f.quantity ?? f.portion_g,
          unit: f.unit ?? 'g',
        })),
        user_notes: notes.trim() || undefined,
        logged_at: new Date().toISOString(),
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      const savedFoods = validFoods.map((f) => ({
        name: f.name.trim(),
        portion_g: Number(f.portion_g) || 100,
        quantity: f.quantity ?? f.portion_g,
        unit: f.unit ?? 'g',
      }));
      reset();
      onSaved(mealType, savedFoods);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to log meal');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={handleClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} className="flex-1 bg-obsidian-900">
        <View className="flex-row items-center justify-between px-6 pt-14 pb-4 border-b border-surface-border">
          <TouchableOpacity onPress={handleClose}>
            <Text className="text-[#526380] font-sansMedium">Cancel</Text>
          </TouchableOpacity>
          <Text className="text-[#E8EDF5] font-sansMedium text-base">Log Meal</Text>
          <TouchableOpacity onPress={handleSave} disabled={saving}>
            {saving ? <ActivityIndicator size="small" color="#00D4AA" /> : (
              <Text className="text-primary-500 font-sansMedium">Save</Text>
            )}
          </TouchableOpacity>
        </View>

        <ScrollView className="flex-1 px-6 pt-5" keyboardShouldPersistTaps="handled">
          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Meal Type</Text>
          <View className="flex-row flex-wrap gap-2 mb-5">
            {(Object.keys(MEAL_TYPE_CONFIG) as MealType[]).map((type) => {
              const cfg = MEAL_TYPE_CONFIG[type];
              const selected = mealType === type;
              return (
                <TouchableOpacity
                  key={type}
                  onPress={() => setMealType(type)}
                  className="flex-row items-center gap-1.5 px-3 py-2 rounded-xl border"
                  style={{
                    backgroundColor: selected ? `${cfg.color}20` : 'transparent',
                    borderColor: selected ? cfg.color : '#1E2A3B',
                  }}
                >
                  <Text className="text-sm">{cfg.icon}</Text>
                  <Text className="text-sm font-sansMedium" style={{ color: selected ? cfg.color : '#526380' }}>
                    {cfg.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Meal Name (optional)</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-5"
            value={mealName}
            onChangeText={setMealName}
            placeholder="e.g. Chicken Caesar Salad"
            placeholderTextColor="#526380"
          />

          <View className="flex-row items-center justify-between mb-2">
            <Text className="text-[#526380] text-xs uppercase tracking-wider">Foods</Text>
            <TouchableOpacity onPress={addFood} className="flex-row items-center gap-1">
              <Ionicons name="add-circle-outline" size={16} color="#00D4AA" />
              <Text className="text-primary-500 text-xs font-sansMedium">Add food</Text>
            </TouchableOpacity>
          </View>

          {foods.map((food, idx) => (
            <View key={idx} className="mb-3">
              <View className="flex-row gap-2 items-center">
                <TextInput
                  className="bg-surface-raised border border-surface-border rounded-xl px-3 py-3 text-[#E8EDF5] flex-1"
                  value={food.name}
                  onChangeText={(v) => updateFood(idx, 'name', v)}
                  placeholder="Food name"
                  placeholderTextColor="#526380"
                />
                {foods.length > 1 && (
                  <TouchableOpacity onPress={() => removeFood(idx)}>
                    <Ionicons name="close-circle" size={20} color="#F87171" />
                  </TouchableOpacity>
                )}
              </View>
              <View className="flex-row gap-2 mt-1.5 items-center">
                <View className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl px-3 py-2.5" style={{ width: 70 }}>
                  <TextInput
                    className="text-[#E8EDF5] flex-1 text-center"
                    value={String(food.quantity ?? food.portion_g)}
                    onChangeText={(v) => updateFood(idx, 'quantity', parseFloat(v) || 0)}
                    keyboardType="decimal-pad"
                    placeholder="1"
                    placeholderTextColor="#526380"
                  />
                </View>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} className="flex-1">
                  <View className="flex-row gap-1">
                    {PORTION_UNITS.map((u) => {
                      const selected = (food.unit ?? 'g') === u.value;
                      return (
                        <TouchableOpacity
                          key={u.value}
                          onPress={() => updateFood(idx, 'unit', u.value)}
                          className="px-2.5 py-2 rounded-lg border"
                          style={{
                            backgroundColor: selected ? '#00D4AA20' : 'transparent',
                            borderColor: selected ? '#00D4AA' : '#1E2A3B',
                          }}
                        >
                          <Text
                            className="text-xs font-sansMedium"
                            style={{ color: selected ? '#00D4AA' : '#526380' }}
                          >
                            {u.label}
                          </Text>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </ScrollView>
              </View>
              <Text className="text-[#526380] text-xs mt-1 ml-1">
                ≈ {food.portion_g}g
              </Text>
            </View>
          ))}

          <Text className="text-[#526380] text-xs uppercase tracking-wider mt-4 mb-2">Notes (optional)</Text>
          <TextInput
            className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] mb-5"
            value={notes}
            onChangeText={setNotes}
            placeholder="e.g. Restaurant meal, leftovers…"
            placeholderTextColor="#526380"
            multiline
            numberOfLines={2}
          />

          {error && <Text className="text-health-critical text-sm mb-4">{error}</Text>}
          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Meal Card ────────────────────────────────────────────────────────────────

function MealCard({ meal, onDelete }: { meal: MealLog; onDelete: (id: string) => void }) {
  const cfg = MEAL_TYPE_CONFIG[meal.meal_type] ?? MEAL_TYPE_CONFIG.snack;

  function confirmDelete() {
    Alert.alert('Delete Meal', 'Remove this meal log?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => onDelete(meal.id) },
    ]);
  }

  return (
    <View className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2">
      <View className="flex-row items-start justify-between">
        <View className="flex-row items-center gap-2 flex-1">
          <Text className="text-lg">{cfg.icon}</Text>
          <View className="flex-1">
            <Text className="text-[#E8EDF5] font-sansMedium text-sm">{meal.meal_name ?? cfg.label}</Text>
            <Text className="text-[#526380] text-xs mt-0.5">
              {format(new Date(meal.logged_at ?? meal.timestamp ?? ''), 'h:mm a')}
              {meal.total_calories ? ` · ~${meal.total_calories} kcal` : ''}
            </Text>
          </View>
        </View>
        <TouchableOpacity onPress={confirmDelete} className="p-1">
          <Ionicons name="trash-outline" size={16} color="#526380" />
        </TouchableOpacity>
      </View>
      {meal.food_items.length > 0 && (
        <View className="mt-2 flex-row flex-wrap gap-1">
          {meal.food_items.slice(0, 5).map((f, i) => (
            <View key={i} className="bg-surface border border-surface-border rounded-full px-2 py-0.5">
              <Text className="text-[#526380] text-xs">
                {f.name} {f.quantity && f.unit && f.unit !== 'g'
                  ? `${f.quantity} ${f.unit}`
                  : `${f.portion_g}g`}
              </Text>
            </View>
          ))}
          {meal.food_items.length > 5 && (
            <Text className="text-[#526380] text-xs self-center">+{meal.food_items.length - 5} more</Text>
          )}
        </View>
      )}
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function NutritionScreen() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [showManual, setShowManual] = useState(false);
  const [showScan, setShowScan] = useState(false);
  const [insightData, setInsightData] = useState<{
    insight: string;
    macros: { calories: number; protein_g: number; carbs_g: number; fat_g: number };
    quickActions: string[];
  } | null>(null);

  const { data: meals, isLoading } = useQuery<MealLog[]>({
    queryKey: ['meals'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/nutrition/meals?days=14');
      return (data?.items ?? data?.meals ?? data ?? []) as MealLog[];
    },
    enabled: !!user,
  });

  const { data: dailyProgress } = useQuery({
    queryKey: ['daily-progress'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/nutrition-ai/daily-progress');
        return data;
      } catch { return null; }
    },
    staleTime: 30_000,
    enabled: !!user,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/nutrition/meals/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['meals'] }),
    onError: () => Alert.alert('Error', 'Could not delete meal'),
  });

  const fetchPostLogInsight = useCallback(async (mealType: string, foodItems: any[]) => {
    try {
      const { data } = await api.post('/api/v1/nutrition-ai/post-log-insight', {
        meal_type: mealType,
        food_items: foodItems,
      });
      setInsightData({
        insight: data.insight,
        macros: data.macros,
        quickActions: data.quick_actions ?? [],
      });
    } catch { /* silent — insight is bonus, not critical */ }
  }, []);

  const handleSaved = useCallback((mealType?: string, foodItems?: any[]) => {
    setShowManual(false);
    setShowScan(false);
    queryClient.invalidateQueries({ queryKey: ['meals'] });
    queryClient.invalidateQueries({ queryKey: ['daily-progress'] });
    if (mealType && foodItems?.length) {
      fetchPostLogInsight(mealType, foodItems);
    }
  }, [queryClient, fetchPostLogInsight]);

  // Session 3: Meal suggestion
  const [suggestion, setSuggestion] = useState<{
    meal_name: string;
    ingredients: any[];
    macros: { calories: number; protein_g: number; carbs_g: number; fat_g: number };
    rationale: string;
  } | null>(null);
  const [suggestionLoading, setSuggestionLoading] = useState(false);

  const fetchSuggestion = useCallback(async () => {
    setSuggestionLoading(true);
    try {
      const { data } = await api.post('/api/v1/nutrition-ai/suggest-meal', {});
      if (data?.meal_name) {
        setSuggestion(data);
      }
    } catch (e) {
      if (__DEV__) console.warn('[Nutrition] suggest-meal failed:', e);
    } finally {
      setSuggestionLoading(false);
    }
  }, []);

  // Session 4: Inline chat
  const [showChat, setShowChat] = useState(false);
  const [chatInitialMsg, setChatInitialMsg] = useState<string | undefined>();

  // Session 5: Swap
  const [swapState, setSwapState] = useState<{
    visible: boolean;
    original: string;
    alternatives: any[];
    loading: boolean;
    foodIndex: number;
    modal: 'scan' | 'manual';
  }>({ visible: false, original: '', alternatives: [], loading: false, foodIndex: -1, modal: 'scan' });

  const fetchSwap = useCallback(async (foodName: string, idx: number, modal: 'scan' | 'manual') => {
    setSwapState({ visible: true, original: foodName, alternatives: [], loading: true, foodIndex: idx, modal });
    try {
      const { data } = await api.post('/api/v1/nutrition-ai/swap', { food_name: foodName });
      setSwapState((s) => ({ ...s, alternatives: data.alternatives ?? [], loading: false }));
    } catch {
      setSwapState((s) => ({ ...s, loading: false }));
    }
  }, []);

  const handleInsightAction = useCallback((action: string) => {
    if (action === 'Ask nutrition coach') {
      setShowChat(true);
    } else if (action === 'Suggest next meal') {
      fetchSuggestion();
    }
    setInsightData(null);
  }, [fetchSuggestion]);

  const mealsList = Array.isArray(meals) ? meals : [];

  // Nutrition intelligence — personalized recommendations from health profile
  const { data: nutritionIntel, isLoading: intelLoading } = useQuery({
    queryKey: ['nutrition-intelligence'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/nutrition-ai/nutrition-intelligence');
        return data as {
          recommendations: Array<{ title: string; rationale: string; category: string; priority: string; foods: string[]; health_link: string }>;
          foods_to_prioritize: Array<{ name?: string; food?: string; why: string }>;
          foods_to_limit: Array<{ name?: string; food?: string; why: string }>;
          daily_focus: string;
          summary: string;
        };
      } catch { return null; }
    },
    staleTime: 10 * 60_000,
    retry: 2,
    enabled: mealsList.length === 0,
  });

  const grouped = mealsList.reduce<Record<string, MealLog[]>>((acc, meal) => {
    const label = formatMealDate(meal.logged_at ?? meal.timestamp ?? '');
    if (!acc[label]) acc[label] = [];
    acc[label].push(meal);
    return acc;
  }, {});

  return (
    <>
      <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ paddingBottom: 40 }}>
        {/* Header */}
        <View className="px-6 pt-14 pb-4 border-b border-surface-border">
          <View className="flex-row items-center justify-between mb-3">
            <Text className="text-xl font-display text-[#E8EDF5]">Nutrition</Text>
            <TouchableOpacity
              onPress={() => setShowChat(true)}
              className="flex-row items-center gap-1 px-2.5 py-1.5 rounded-lg"
              style={{ backgroundColor: '#00D4AA12', borderWidth: 1, borderColor: '#00D4AA25' }}
              activeOpacity={0.7}
            >
              <Ionicons name="sparkles" size={12} color="#00D4AA" />
              <Text className="text-[#00D4AA] text-[11px] font-sansMedium">Coach</Text>
            </TouchableOpacity>
          </View>
          <View className="flex-row gap-2">
            <TouchableOpacity
              onPress={() => setShowScan(true)}
              className="flex-1 bg-primary-500 rounded-xl py-2.5 flex-row items-center justify-center gap-1.5"
              activeOpacity={0.8}
            >
              <Ionicons name="camera" size={16} color="#080B10" />
              <Text className="text-obsidian-900 font-sansMedium text-sm">Scan Photo</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => setShowManual(true)}
              className="flex-1 bg-surface-raised border border-surface-border rounded-xl py-2.5 flex-row items-center justify-center gap-1.5"
              activeOpacity={0.8}
            >
              <Ionicons name="create-outline" size={16} color="#E8EDF5" />
              <Text className="text-[#E8EDF5] font-sansMedium text-sm">Manual Entry</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={fetchSuggestion}
              disabled={suggestionLoading}
              className="bg-surface-raised border border-surface-border rounded-xl py-2.5 px-3 flex-row items-center justify-center gap-1"
              activeOpacity={0.8}
            >
              <Ionicons name="bulb-outline" size={16} color="#F5A623" />
            </TouchableOpacity>
          </View>
        </View>

        <View className="px-6 pt-5">
          {/* Daily Progress */}
          {dailyProgress && (
            <DailyProgressCard
              meals={dailyProgress.meals_today ?? []}
              totals={dailyProgress.totals ?? { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 }}
              targets={dailyProgress.targets ?? { calories: 2000, protein_g: 100, carbs_g: 200, fat_g: 65 }}
              remaining={dailyProgress.remaining ?? { calories: 2000 }}
              progressPct={dailyProgress.progress_pct ?? { calories: 0, protein: 0, carbs: 0, fat: 0 }}
            />
          )}

          {/* Post-log AI insight */}
          {insightData && (
            <NutritionInsightCard
              insight={insightData.insight}
              macros={insightData.macros}
              quickActions={insightData.quickActions}
              onAction={handleInsightAction}
              onDismiss={() => setInsightData(null)}
            />
          )}

          {/* Proactive meal suggestion */}
          {suggestion && !insightData && (
            <ProactiveSuggestionCard
              mealName={suggestion.meal_name}
              ingredients={suggestion.ingredients}
              macros={suggestion.macros}
              rationale={suggestion.rationale}
              onLogThis={() => {
                // Pre-fill manual log with suggested foods
                setShowManual(true);
                setSuggestion(null);
              }}
              onSomethingElse={() => fetchSuggestion()}
              onDismiss={() => setSuggestion(null)}
            />
          )}
          {suggestionLoading && !suggestion && (
            <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3 items-center">
              <ActivityIndicator color="#F5A623" size="small" />
              <Text className="text-[#526380] text-xs mt-1">Finding the perfect meal...</Text>
            </View>
          )}

          {isLoading ? (
            <ActivityIndicator color="#00D4AA" className="mt-8" />
          ) : Object.keys(grouped).length === 0 ? (
            <>
              {intelLoading ? (
                <View className="items-center py-12">
                  <ActivityIndicator color="#6EE7B7" />
                  <Text className="text-[#526380] text-sm mt-3">Analyzing your health profile for nutrition guidance...</Text>
                </View>
              ) : nutritionIntel?.recommendations && nutritionIntel.recommendations.length > 0 ? (
                <View>
                  {/* AI Summary */}
                  {nutritionIntel.summary && (
                    <View className="bg-[#6EE7B708] border border-[#6EE7B718] rounded-2xl p-4 mb-3">
                      <View className="flex-row items-center gap-1.5 mb-2">
                        <Ionicons name="sparkles" size={14} color="#6EE7B7" />
                        <Text className="text-[#6EE7B7] text-[10px] font-sansMedium uppercase tracking-wider">Personalized Nutrition</Text>
                      </View>
                      <Text className="text-[#8B9BB4] text-xs leading-5">{nutritionIntel.summary}</Text>
                    </View>
                  )}

                  {/* Daily focus */}
                  {nutritionIntel.daily_focus && (
                    <View className="bg-[#F5A62308] border border-[#F5A62318] rounded-xl p-3 mb-3">
                      <View className="flex-row items-center gap-1.5">
                        <Ionicons name="leaf-outline" size={14} color="#F5A623" />
                        <Text className="text-[#F5A623] text-xs font-sansMedium flex-1">Today: {nutritionIntel.daily_focus}</Text>
                      </View>
                    </View>
                  )}

                  {/* Recommendation Cards */}
                  {nutritionIntel.recommendations.map((rec, i) => {
                    const priorityColor = rec.priority === 'high' ? '#F87171' : rec.priority === 'medium' ? '#FBBF24' : '#60A5FA';
                    const catIcon = rec.category === 'limit' ? 'warning-outline' : rec.category === 'timing' ? 'time-outline' : 'leaf-outline';
                    return (
                      <View key={i} className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2">
                        <View className="flex-row items-start gap-3">
                          <View className="w-9 h-9 rounded-lg items-center justify-center" style={{ backgroundColor: `${priorityColor}15` }}>
                            <Ionicons name={catIcon as any} size={18} color={priorityColor} />
                          </View>
                          <View className="flex-1">
                            <View className="flex-row items-center gap-1.5 flex-wrap mb-0.5">
                              <Text className="text-[#E8EDF5] font-sansMedium text-sm">{rec.title}</Text>
                              <View className="rounded-full px-1.5 py-0.5" style={{ backgroundColor: `${priorityColor}15` }}>
                                <Text className="text-[9px] font-sansMedium" style={{ color: priorityColor }}>{rec.priority}</Text>
                              </View>
                            </View>
                            <Text className="text-[#526380] text-xs mt-0.5 leading-5">{rec.rationale}</Text>
                            {rec.foods?.length > 0 && (
                              <View className="flex-row flex-wrap gap-1 mt-1.5">
                                {rec.foods.map((f, fi) => (
                                  <View key={fi} className="bg-[#6EE7B710] rounded px-1.5 py-0.5">
                                    <Text className="text-[#6EE7B7] text-[10px]">{f}</Text>
                                  </View>
                                ))}
                              </View>
                            )}
                            {rec.health_link && (
                              <View className="flex-row items-center gap-1 mt-1">
                                <Ionicons name="arrow-forward" size={9} color="#526380" />
                                <Text className="text-[#526380] text-[10px]">{rec.health_link}</Text>
                              </View>
                            )}
                          </View>
                        </View>
                      </View>
                    );
                  })}

                  {/* Foods to prioritize & limit */}
                  {nutritionIntel.foods_to_prioritize?.length > 0 && (
                    <View className="bg-[#6EE7B706] border border-[#6EE7B715] rounded-xl p-3 mb-2">
                      <Text className="text-[#6EE7B7] text-[10px] font-sansMedium uppercase tracking-wider mb-2">Prioritize</Text>
                      {nutritionIntel.foods_to_prioritize.slice(0, 6).map((f, i) => (
                        <Text key={i} className="text-[#8B9BB4] text-xs leading-5">
                          <Text className="text-[#6EE7B7]">+ </Text>
                          <Text className="text-[#C8D6E5] font-sansMedium">{f.name || f.food}</Text> — {f.why}
                        </Text>
                      ))}
                    </View>
                  )}
                  {nutritionIntel.foods_to_limit?.length > 0 && (
                    <View className="bg-[#F8717106] border border-[#F8717115] rounded-xl p-3 mb-3">
                      <Text className="text-[#F87171] text-[10px] font-sansMedium uppercase tracking-wider mb-2">Limit</Text>
                      {nutritionIntel.foods_to_limit.map((f, i) => (
                        <Text key={i} className="text-[#8B9BB4] text-xs leading-5">
                          <Text className="text-[#F87171]">- </Text>
                          <Text className="text-[#C8D6E5] font-sansMedium">{f.name || f.food}</Text> — {f.why}
                        </Text>
                      ))}
                    </View>
                  )}

                  {/* Meal plan CTA */}
                  <TouchableOpacity
                    onPress={() => router.push('/(tabs)/log/meal-plan')}
                    className="flex-row items-center justify-center gap-1.5 py-3 rounded-xl"
                    style={{ backgroundColor: '#818CF815', borderWidth: 1, borderColor: '#818CF830' }}
                    activeOpacity={0.7}
                  >
                    <Ionicons name="calendar-outline" size={14} color="#818CF8" />
                    <Text className="text-[#818CF8] text-xs font-sansMedium">Generate a 7-day meal plan</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <View className="items-center py-12">
                  <Ionicons name="restaurant-outline" size={40} color="#526380" />
                  <Text className="text-[#526380] text-base mt-3">No meals logged yet</Text>
                  <Text className="text-[#526380] text-sm mt-1 text-center">
                    Tap "Scan Photo" to use AI recognition or "Manual Entry" to type foods.
                  </Text>
                  <TouchableOpacity
                    onPress={() => router.push('/(tabs)/log/meal-plan')}
                    className="mt-4 flex-row items-center gap-1.5 px-4 py-2 rounded-lg"
                    style={{ backgroundColor: '#818CF815', borderWidth: 1, borderColor: '#818CF830' }}
                    activeOpacity={0.7}
                  >
                    <Ionicons name="calendar-outline" size={14} color="#818CF8" />
                    <Text className="text-[#818CF8] text-xs font-sansMedium">Generate a meal plan</Text>
                  </TouchableOpacity>
                </View>
              )}
            </>
          ) : (
            Object.entries(grouped).map(([dateLabel, dayMeals]) => (
              <View key={dateLabel} className="mb-5">
                <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">{dateLabel}</Text>
                {dayMeals.map((meal) => (
                  <MealCard key={meal.id} meal={meal} onDelete={(id) => deleteMutation.mutate(id)} />
                ))}
              </View>
            ))
          )}
        </View>
      </ScrollView>

      <PhotoScanModal visible={showScan} onClose={() => setShowScan(false)} onSaved={handleSaved} />
      <LogMealModal visible={showManual} onClose={() => setShowManual(false)} onSaved={handleSaved} />

      {/* Inline nutrition chat */}
      <InlineNutritionChat
        visible={showChat}
        onClose={() => setShowChat(false)}
        initialMessage={chatInitialMsg}
      />

      {/* Swap sheet */}
      <SwapSheet
        visible={swapState.visible}
        original={swapState.original}
        alternatives={swapState.alternatives}
        loading={swapState.loading}
        onSelect={(alt) => {
          // Close swap and user can log the alternative
          setSwapState((s) => ({ ...s, visible: false }));
        }}
        onClose={() => setSwapState((s) => ({ ...s, visible: false }))}
        onAskCoach={() => {
          setSwapState((s) => ({ ...s, visible: false }));
          setChatInitialMsg(`What's a good alternative for ${swapState.original}?`);
          setShowChat(true);
        }}
      />
    </>
  );
}
