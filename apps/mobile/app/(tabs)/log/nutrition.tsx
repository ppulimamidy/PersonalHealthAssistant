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

// ─── Types ────────────────────────────────────────────────────────────────────

type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

interface FoodItem {
  name: string;
  portion_g: number;
}

interface RecognizedFood {
  name: string;
  confidence?: number;
  portion_g?: number;
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
  onSaved: () => void;
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

      const foods: FoodItem[] = (data?.recognized_foods ?? []).map((f: RecognizedFood) => ({
        name: f.name,
        portion_g: f.portion_g ?? 100,
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
    setRecognizedFoods((prev) => prev.map((f, i) => (i === idx ? { ...f, [field]: value } : f)));
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
        })),
        logged_at: new Date().toISOString(),
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      reset();
      onSaved();
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
                <View key={idx} className="flex-row gap-2 mb-2 items-center">
                  <TextInput
                    className="bg-surface-raised border border-surface-border rounded-xl px-3 py-3 text-[#E8EDF5] flex-1"
                    value={food.name}
                    onChangeText={(v) => updateFood(idx, 'name', v)}
                    placeholder="Food name"
                    placeholderTextColor="#526380"
                  />
                  <View className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl px-3 py-3" style={{ width: 90 }}>
                    <TextInput
                      className="text-[#E8EDF5] flex-1 text-right"
                      value={String(food.portion_g)}
                      onChangeText={(v) => updateFood(idx, 'portion_g', parseInt(v) || 0)}
                      keyboardType="numeric"
                      placeholder="100"
                      placeholderTextColor="#526380"
                    />
                    <Text className="text-[#526380] text-xs ml-1">g</Text>
                  </View>
                  <TouchableOpacity onPress={() => removeFood(idx)}>
                    <Ionicons name="close-circle" size={20} color="#F87171" />
                  </TouchableOpacity>
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
  onSaved: () => void;
}) {
  const [mealType, setMealType] = useState<MealType>(inferMealType());
  const [mealName, setMealName] = useState('');
  const [notes, setNotes] = useState('');
  const [foods, setFoods] = useState<FoodItem[]>([{ name: '', portion_g: 100 }]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setMealType(inferMealType());
    setMealName('');
    setNotes('');
    setFoods([{ name: '', portion_g: 100 }]);
    setError(null);
  }

  function handleClose() { reset(); onClose(); }

  function addFood() { setFoods((prev) => [...prev, { name: '', portion_g: 100 }]); }
  function removeFood(idx: number) { setFoods((prev) => prev.filter((_, i) => i !== idx)); }
  function updateFood(idx: number, field: keyof FoodItem, value: string | number) {
    setFoods((prev) => prev.map((f, i) => (i === idx ? { ...f, [field]: value } : f)));
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
        food_items: validFoods.map((f) => ({ name: f.name.trim(), portion_g: Number(f.portion_g) || 100 })),
        user_notes: notes.trim() || undefined,
        logged_at: new Date().toISOString(),
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      reset();
      onSaved();
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
            <View key={idx} className="flex-row gap-2 mb-2 items-center">
              <TextInput
                className="bg-surface-raised border border-surface-border rounded-xl px-3 py-3 text-[#E8EDF5] flex-1"
                value={food.name}
                onChangeText={(v) => updateFood(idx, 'name', v)}
                placeholder="Food name"
                placeholderTextColor="#526380"
              />
              <View className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl px-3 py-3" style={{ width: 90 }}>
                <TextInput
                  className="text-[#E8EDF5] flex-1 text-right"
                  value={String(food.portion_g)}
                  onChangeText={(v) => updateFood(idx, 'portion_g', parseInt(v) || 0)}
                  keyboardType="numeric"
                  placeholder="100"
                  placeholderTextColor="#526380"
                />
                <Text className="text-[#526380] text-xs ml-1">g</Text>
              </View>
              {foods.length > 1 && (
                <TouchableOpacity onPress={() => removeFood(idx)}>
                  <Ionicons name="close-circle" size={20} color="#F87171" />
                </TouchableOpacity>
              )}
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
              <Text className="text-[#526380] text-xs">{f.name} {f.portion_g}g</Text>
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
  const queryClient = useQueryClient();
  const [showManual, setShowManual] = useState(false);
  const [showScan, setShowScan] = useState(false);

  const { data: meals, isLoading } = useQuery<MealLog[]>({
    queryKey: ['meals'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/nutrition/meals?days=14');
      return (data?.items ?? data?.meals ?? data ?? []) as MealLog[];
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/nutrition/meals/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['meals'] }),
    onError: () => Alert.alert('Error', 'Could not delete meal'),
  });

  const handleSaved = useCallback(() => {
    setShowManual(false);
    setShowScan(false);
    queryClient.invalidateQueries({ queryKey: ['meals'] });
  }, [queryClient]);

  const mealsList = Array.isArray(meals) ? meals : [];
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
          </View>
          <View className="flex-row gap-3">
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
          </View>
        </View>

        <View className="px-6 pt-5">
          {isLoading ? (
            <ActivityIndicator color="#00D4AA" className="mt-8" />
          ) : Object.keys(grouped).length === 0 ? (
            <View className="items-center py-12">
              <Ionicons name="restaurant-outline" size={40} color="#526380" />
              <Text className="text-[#526380] text-base mt-3">No meals logged yet</Text>
              <Text className="text-[#526380] text-sm mt-1 text-center">
                Tap "Scan Photo" to use AI recognition or "Manual Entry" to type foods.
              </Text>
            </View>
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
    </>
  );
}
