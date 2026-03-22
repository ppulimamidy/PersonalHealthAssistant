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
          // When user taps the already-active tab, reset its stack to the root screen
          const state = navigation.getState();
          const currentRoute = state.routes[state.index];
          if (currentRoute.name === route.name && currentRoute.state?.index && currentRoute.state.index > 0) {
            e.preventDefault();
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
