/**
 * Grocery List Sheet — shows aggregated ingredients from the meal plan.
 * Supports checkboxes, share, and copy to clipboard.
 */

import { useState } from 'react';
import {
  View, Text, TouchableOpacity, ScrollView, Modal, Alert, Share,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface GroceryItem {
  name: string;
  quantity?: string;
  for_meals?: string[];
}

interface Category {
  name: string;
  items: GroceryItem[];
}

interface Props {
  visible: boolean;
  categories: Category[];
  onClose: () => void;
}

const CATEGORY_ICONS: Record<string, string> = {
  'Produce': 'leaf-outline',
  'Protein': 'fish-outline',
  'Dairy & Eggs': 'water-outline',
  'Grains & Bread': 'nutrition-outline',
  'Pantry Staples': 'file-tray-stacked-outline',
  'Spices & Seasonings': 'flame-outline',
  'Beverages': 'cafe-outline',
  'Other': 'ellipse-outline',
};

export default function GroceryListSheet({ visible, categories, onClose }: Readonly<Props>) {
  const [checked, setChecked] = useState<Set<string>>(new Set());

  function toggleItem(key: string) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function toPlainText(): string {
    return categories.map((cat) => {
      const header = `\n${cat.name.toUpperCase()}`;
      const items = cat.items.map((item) => {
        const qty = item.quantity ? `${item.quantity} ` : '';
        return `  ${checked.has(`${cat.name}-${item.name}`) ? '✓' : '○'} ${qty}${item.name}`;
      });
      return `${header}\n${items.join('\n')}`;
    }).join('\n');
  }

  async function handleShare() {
    try {
      await Share.share({ message: toPlainText(), title: 'Grocery List' });
    } catch { /* cancelled */ }
  }

  const totalItems = categories.reduce((sum, c) => sum + c.items.length, 0);
  const checkedCount = checked.size;

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <View className="flex-1 bg-obsidian-900">
        {/* Header */}
        <View className="flex-row items-center justify-between px-6 pt-14 pb-4 border-b border-surface-border">
          <View>
            <Text className="text-xl font-display text-[#E8EDF5]">Grocery List</Text>
            <Text className="text-[#526380] text-xs mt-0.5">
              {checkedCount}/{totalItems} items checked
            </Text>
          </View>
          <View className="flex-row items-center gap-3">
            <TouchableOpacity onPress={handleShare} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
              <Ionicons name="share-outline" size={20} color="#00D4AA" />
            </TouchableOpacity>
            <TouchableOpacity onPress={onClose} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
              <Ionicons name="close" size={22} color="#526380" />
            </TouchableOpacity>
          </View>
        </View>

        <ScrollView className="flex-1 px-6 pt-4" contentContainerStyle={{ paddingBottom: 40 }}>
          {categories.length === 0 ? (
            <View className="items-center py-16">
              <Ionicons name="cart-outline" size={44} color="#526380" />
              <Text className="text-[#526380] text-sm mt-3">Generate a meal plan first to see your grocery list</Text>
            </View>
          ) : (
            categories.map((cat) => {
              const icon = CATEGORY_ICONS[cat.name] ?? 'ellipse-outline';
              return (
                <View key={cat.name} className="mb-5">
                  <View className="flex-row items-center gap-2 mb-2">
                    <Ionicons name={icon as never} size={14} color="#526380" />
                    <Text className="text-[#526380] text-xs uppercase tracking-wider font-sansMedium">
                      {cat.name}
                    </Text>
                    <Text className="text-[#3D4F66] text-[10px]">({cat.items.length})</Text>
                  </View>
                  {cat.items.map((item) => {
                    const key = `${cat.name}-${item.name}`;
                    const isChecked = checked.has(key);
                    return (
                      <TouchableOpacity
                        key={key}
                        onPress={() => toggleItem(key)}
                        className="flex-row items-center gap-3 py-2 border-b border-surface-border"
                        activeOpacity={0.7}
                      >
                        <View
                          className="w-5 h-5 rounded-md items-center justify-center"
                          style={{
                            backgroundColor: isChecked ? '#00D4AA' : 'transparent',
                            borderWidth: isChecked ? 0 : 1.5,
                            borderColor: '#3D4F66',
                          }}
                        >
                          {isChecked && <Ionicons name="checkmark" size={14} color="#080B10" />}
                        </View>
                        <View className="flex-1">
                          <Text
                            className="text-sm"
                            style={{
                              color: isChecked ? '#526380' : '#E8EDF5',
                              textDecorationLine: isChecked ? 'line-through' : 'none',
                            }}
                          >
                            {item.name}
                          </Text>
                          {item.quantity && (
                            <Text className="text-[#526380] text-[10px]">{item.quantity}</Text>
                          )}
                        </View>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              );
            })
          )}
        </ScrollView>
      </View>
    </Modal>
  );
}
