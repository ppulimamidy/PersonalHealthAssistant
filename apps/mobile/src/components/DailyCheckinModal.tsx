/**
 * DailyCheckinModal — lightweight daily vitals prompt.
 * Shows once per day (tracked via AsyncStorage).
 * Mirrors the web app's VitalsCheckinModal pattern.
 */

import { useState, useEffect } from 'react';
import {
  View, Text, Modal, TouchableOpacity,
  ActivityIndicator, Animated,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Slider from '@react-native-community/slider';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

const STORAGE_KEY = 'daily_checkin_last_date';

function todayString(): string {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD
}

export async function shouldShowDailyCheckin(): Promise<boolean> {
  try {
    const last = await AsyncStorage.getItem(STORAGE_KEY);
    return last !== todayString();
  } catch {
    return false;
  }
}

export async function markDailyCheckinShown(): Promise<void> {
  await AsyncStorage.setItem(STORAGE_KEY, todayString()).catch(() => {});
}

interface Props {
  visible: boolean;
  onDismiss: () => void;
}

function SliderRow({
  label, value, onChange, color, low, high,
}: Readonly<{
  label: string;
  value: number;
  onChange: (v: number) => void;
  color: string;
  low: string;
  high: string;
}>) {
  return (
    <View className="mb-5">
      <View className="flex-row justify-between mb-1">
        <Text className="text-[#E8EDF5] font-sansMedium text-sm">{label}</Text>
        <Text className="font-sansMedium" style={{ color }}>{Math.round(value)}/10</Text>
      </View>
      <Slider
        minimumValue={0}
        maximumValue={10}
        step={1}
        value={value}
        onValueChange={onChange}
        minimumTrackTintColor={color}
        maximumTrackTintColor="#1E2A3B"
        thumbTintColor={color}
      />
      <View className="flex-row justify-between mt-0.5">
        <Text className="text-[#3A4A5C] text-xs">{low}</Text>
        <Text className="text-[#3A4A5C] text-xs">{high}</Text>
      </View>
    </View>
  );
}

export default function DailyCheckinModal({ visible, onDismiss }: Readonly<Props>) {
  const [energy, setEnergy] = useState(6);
  const [mood,   setMood]   = useState(6);
  const [pain,   setPain]   = useState(2);
  const [saving, setSaving] = useState(false);
  const [done,   setDone]   = useState(false);
  const queryClient = useQueryClient();

  // Reset sliders each time modal opens
  useEffect(() => {
    if (visible) { setEnergy(6); setMood(6); setPain(2); setDone(false); }
  }, [visible]);

  async function handleSave() {
    setSaving(true);
    try {
      await api.post('/api/v1/checkins', {
        energy: Math.round(energy),
        mood:   Math.round(mood),
        pain:   Math.round(pain),
      });
      await markDailyCheckinShown();
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['checkin'] });
      queryClient.invalidateQueries({ queryKey: ['batch', 'home'] });
      setDone(true);
      setTimeout(onDismiss, 1200);
    } catch {
      // still mark shown to avoid nagging on error
      await markDailyCheckinShown();
      onDismiss();
    } finally {
      setSaving(false);
    }
  }

  async function handleSkip() {
    await markDailyCheckinShown();
    onDismiss();
  }

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={handleSkip}
    >
      {/* Backdrop */}
      <TouchableOpacity
        className="flex-1 bg-black/60"
        activeOpacity={1}
        onPress={handleSkip}
      />

      {/* Sheet */}
      <View className="bg-obsidian-900 border-t border-surface-border rounded-t-3xl px-6 pt-5 pb-10">
        {/* Handle */}
        <View className="w-10 h-1 bg-surface-border rounded-full self-center mb-5" />

        {done ? (
          <View className="items-center py-6">
            <View className="w-14 h-14 rounded-full bg-primary-500/20 items-center justify-center mb-3">
              <Ionicons name="checkmark-circle" size={32} color="#00D4AA" />
            </View>
            <Text className="text-[#E8EDF5] font-sansMedium text-base">Logged!</Text>
            <Text className="text-[#526380] text-sm mt-1">Your daily vitals are recorded.</Text>
          </View>
        ) : (
          <>
            <View className="flex-row items-center justify-between mb-1">
              <Text className="text-lg font-display text-[#E8EDF5]">Daily Check-in</Text>
              <TouchableOpacity onPress={handleSkip} className="p-1">
                <Ionicons name="close" size={20} color="#526380" />
              </TouchableOpacity>
            </View>
            <Text className="text-[#526380] text-sm mb-6">How are you feeling today?</Text>

            <SliderRow label="Energy" value={energy} onChange={setEnergy} color="#00D4AA" low="Drained" high="Energised" />
            <SliderRow label="Mood"   value={mood}   onChange={setMood}   color="#818CF8" low="Low"     high="Great" />
            <SliderRow label="Pain"   value={pain}   onChange={setPain}   color="#F87171" low="None"    high="Severe" />

            <TouchableOpacity
              onPress={handleSave}
              disabled={saving}
              className="bg-primary-500 rounded-xl py-3.5 items-center mt-2"
              activeOpacity={0.8}
            >
              {saving
                ? <ActivityIndicator color="#080B10" />
                : <Text className="text-obsidian-900 font-sansMedium">Log Today's Vitals</Text>}
            </TouchableOpacity>

            <TouchableOpacity onPress={handleSkip} className="items-center py-3">
              <Text className="text-[#526380] text-sm">Skip for today</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </Modal>
  );
}
