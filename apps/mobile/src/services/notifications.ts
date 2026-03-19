/**
 * Mobile push notification service.
 *
 * Registers the device's Expo push token with the backend
 * (POST /api/v1/notifications/register) and removes it on logout
 * (DELETE /api/v1/notifications/unregister).
 *
 * Call registerForPushNotifications() after login.
 * Call unregisterPushToken() in logout flow before supabase.auth.signOut().
 */

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import { api } from './api';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export async function registerForPushNotifications(): Promise<string | null> {
  // Push notifications don't work on simulators
  if (!Device.isDevice) {
    console.log('[notifications] Skipping — not a physical device');
    return null;
  }

  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;

  if (existing !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.log('[notifications] Permission not granted');
    return null;
  }

  const projectId = process.env.EXPO_PUBLIC_EXPO_PROJECT_ID;
  if (!projectId) {
    console.warn('[notifications] EXPO_PUBLIC_EXPO_PROJECT_ID not set — skipping token registration');
    return null;
  }

  const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
  const token = tokenData.data;

  try {
    await api.post('/api/v1/notifications/register', {
      token,
      platform: Platform.OS,
    });
    console.log('[notifications] Push token registered:', token.slice(0, 30) + '...');
  } catch (err) {
    console.warn('[notifications] Failed to register token with backend:', err);
  }

  return token;
}

/**
 * Set up notification response listener for deep linking.
 * Call once from root layout. Returns cleanup function.
 */
export function setupNotificationListeners(
  navigate: (screen: string) => void,
): () => void {
  // When user taps a notification
  const responseSubscription = Notifications.addNotificationResponseReceivedListener(
    (response) => {
      const data = response.notification.request.content.data as Record<string, unknown>;
      const screen = (data?.screen as string) || 'home';
      const nudgeId = data?.nudge_id as string | undefined;

      // Mark nudge as opened (fire and forget)
      if (nudgeId) {
        api.post(`/api/v1/nudges/${nudgeId}/opened`).catch(() => {});
      }

      // Navigate to the appropriate screen
      navigate(screen);
    },
  );

  // When notification received while app is foregrounded
  const receivedSubscription = Notifications.addNotificationReceivedListener(
    (notification) => {
      console.log('[notifications] Received in foreground:', notification.request.content.title);
    },
  );

  return () => {
    responseSubscription.remove();
    receivedSubscription.remove();
  };
}

export async function unregisterPushToken(): Promise<void> {
  try {
    const projectId = process.env.EXPO_PUBLIC_EXPO_PROJECT_ID;
    if (!projectId || !Device.isDevice) return;

    const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
    await api.delete('/api/v1/notifications/unregister', {
      data: { token: tokenData.data, platform: Platform.OS },
    });
    console.log('[notifications] Push token unregistered');
  } catch {
    // Non-critical on logout
  }
}
