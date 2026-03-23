import { Tabs } from 'expo-router';
import { Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { CommonActions } from '@react-navigation/native';
import { colors } from '@/constants/theme';

type IconName = React.ComponentProps<typeof Ionicons>['name'];

const TAB_ICON: Record<string, { active: IconName; inactive: IconName }> = {
  home: { active: 'home', inactive: 'home-outline' },
  log: { active: 'add-circle', inactive: 'add-circle-outline' },
  insights: { active: 'bulb', inactive: 'bulb-outline' },
  chat: { active: 'hardware-chip', inactive: 'hardware-chip-outline' },
  profile: { active: 'person', inactive: 'person-outline' },
};

export default function TabsLayout() {
  return (
    <Tabs
      screenListeners={({ navigation, route }) => ({
        tabPress: (e) => {
          // When user taps an already-focused tab, reset its nested stack to root
          const state = navigation.getState();
          const currentTab = state.routes[state.index];
          if (currentTab.name !== route.name) return;

          // Check if nested stack has depth > 0 (screens pushed beyond root)
          const nested = currentTab.state as any;
          const hasDepth = nested && ((nested.index != null && nested.index > 0) || (nested.routes?.length > 1));
          if (hasDepth) {
            e.preventDefault();
            // Clear the nested state entirely — forces remount of root screen
            navigation.dispatch(
              CommonActions.reset({
                index: state.index,
                routes: state.routes.map((r: any) =>
                  r.name === route.name ? { ...r, state: undefined } : r
                ),
              })
            );
          }
        },
      })}
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.obsidian[800],
          borderTopColor: colors.surface.border,
          borderTopWidth: 1,
          height: Platform.OS === 'ios' ? 83 : 60,
          paddingBottom: Platform.OS === 'ios' ? 28 : 8,
          paddingTop: 8,
        },
        tabBarActiveTintColor: colors.primary[500],
        tabBarInactiveTintColor: colors.obsidian[400],
        tabBarIcon: ({ focused, color, size }) => {
          const icons = TAB_ICON[route.name] ?? { active: 'help', inactive: 'help-outline' };
          return (
            <Ionicons
              name={focused ? icons.active : icons.inactive}
              size={size}
              color={color}
            />
          );
        },
      })}
    >
      <Tabs.Screen name="home" options={{ title: 'Home' }} />
      <Tabs.Screen name="log" options={{ title: 'Track' }} />
      <Tabs.Screen name="insights" options={{ title: 'Insights' }} />
      <Tabs.Screen name="chat" options={{ title: 'Ask AI' }} />
      <Tabs.Screen name="profile" options={{ title: 'Profile' }} />
    </Tabs>
  );
}
