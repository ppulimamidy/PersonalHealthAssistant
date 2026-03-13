import { View, Text } from 'react-native';
import { Link, Stack } from 'expo-router';

export default function NotFoundScreen() {
  return (
    <>
      <Stack.Screen options={{ title: 'Not Found' }} />
      <View className="flex-1 items-center justify-center bg-obsidian-900">
        <Text className="text-lg font-sans text-[#E8EDF5] mb-4">Screen not found</Text>
        <Link href="/(tabs)/home" className="text-primary-500">
          Go home
        </Link>
      </View>
    </>
  );
}
