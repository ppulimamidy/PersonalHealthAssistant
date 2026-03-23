import { Tabs, useRouter } from 'expo-router';
import { Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
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
  const router = useRouter();

  // When tapping an already-focused tab, navigate to its root screen
  function makeTabListeners(tabRoot: string) {
    return ({ navigation }: any) => ({
      tabPress: (e: any) => {
        const state = navigation.getState();
        const tabRoute = state.routes.find((r: any) => r.name === tabRoot);
        // If this tab has a nested stack with depth > 0, go to root
        if (tabRoute?.state && tabRoute.state.routes && tabRoute.state.routes.length > 1) {
          e.preventDefault();
          router.replace(`/(tabs)/${tabRoot}` as any);
        }
      },
    });
  }

  return (
    <Tabs
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
      <Tabs.Screen name="home" options={{ title: 'Home' }} listeners={makeTabListeners('home')} />
      <Tabs.Screen name="log" options={{ title: 'Track' }} listeners={makeTabListeners('log')} />
      <Tabs.Screen name="insights" options={{ title: 'Insights' }} listeners={makeTabListeners('insights')} />
      <Tabs.Screen name="chat" options={{ title: 'Ask AI' }} listeners={makeTabListeners('chat')} />
      <Tabs.Screen name="profile" options={{ title: 'Profile' }} listeners={makeTabListeners('profile')} />
    </Tabs>
  );
}
