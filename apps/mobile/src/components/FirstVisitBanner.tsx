/**
 * FirstVisitBanner — shows a plain-english explainer on the first visit to an advanced screen.
 * Dismissed permanently via AsyncStorage key `tooltip_dismissed_<screenKey>`.
 */

import { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, Animated } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  screenKey: string;
  text: string;
}

export default function FirstVisitBanner({ screenKey, text }: Readonly<Props>) {
  const [visible, setVisible] = useState(false);
  const opacity = useRef(new Animated.Value(1)).current;
  const storageKey = `tooltip_dismissed_${screenKey}`;

  useEffect(() => {
    AsyncStorage.getItem(storageKey).then((val) => {
      if (val !== 'true') setVisible(true);
    }).catch(() => {});
  }, [storageKey]);

  function dismiss() {
    Animated.timing(opacity, {
      toValue: 0,
      duration: 250,
      useNativeDriver: true,
    }).start(() => {
      setVisible(false);
      AsyncStorage.setItem(storageKey, 'true').catch(() => {});
    });
  }

  if (!visible) return null;

  return (
    <Animated.View style={{ opacity }} className="mx-6 mb-4">
      <View className="flex-row items-start gap-3 bg-primary-500/10 border border-primary-500/25 rounded-xl px-4 py-3">
        <Ionicons name="information-circle-outline" size={18} color="#00D4AA" style={{ marginTop: 1 }} />
        <Text className="flex-1 text-[#A8C0D0] text-sm leading-5">{text}</Text>
        <TouchableOpacity onPress={dismiss} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
          <Ionicons name="close" size={16} color="#526380" />
        </TouchableOpacity>
      </View>
    </Animated.View>
  );
}
