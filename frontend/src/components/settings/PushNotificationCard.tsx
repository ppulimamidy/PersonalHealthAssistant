'use client';

import { useState, useEffect } from 'react';
import { Bell, BellOff, Loader2, CheckCircle } from 'lucide-react';
import { api } from '@/services/api';
import toast from 'react-hot-toast';

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || '';

function urlBase64ToUint8Array(base64String: string): ArrayBuffer {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const arr = Uint8Array.from(rawData, (c) => c.charCodeAt(0));
  return arr.buffer;
}

export function PushNotificationCard() {
  const [supported, setSupported] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [subscribed, setSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [testSending, setTestSending] = useState(false);

  useEffect(() => {
    const isSupported = 'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window;
    setSupported(isSupported);
    if (isSupported) {
      setPermission(Notification.permission);
      // Check if already subscribed
      navigator.serviceWorker.ready
        .then((reg) => reg.pushManager.getSubscription())
        .then((sub) => setSubscribed(!!sub))
        .catch(() => {});
    }
  }, []);

  const handleEnable = async () => {
    setLoading(true);
    try {
      const perm = await Notification.requestPermission();
      setPermission(perm);
      if (perm !== 'granted') {
        toast.error('Notification permission denied');
        return;
      }

      const reg = await navigator.serviceWorker.ready;

      // If VAPID public key is configured, use it; otherwise use basic subscription
      const subscribeOptions: PushSubscriptionOptionsInit = { userVisibleOnly: true };
      if (VAPID_PUBLIC_KEY) {
        subscribeOptions.applicationServerKey = urlBase64ToUint8Array(VAPID_PUBLIC_KEY);
      }

      const subscription = await reg.pushManager.subscribe(subscribeOptions);
      const subJson = subscription.toJSON();

      await api.post('/api/v1/notifications/subscribe', {
        endpoint: subJson.endpoint,
        keys: {
          p256dh: subJson.keys?.p256dh,
          auth: subJson.keys?.auth,
        },
      });

      setSubscribed(true);
      toast.success('Browser reminders enabled');
    } catch (err) {
      console.error(err);
      toast.error('Failed to enable push notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async () => {
    setLoading(true);
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) await sub.unsubscribe();
      await api.delete('/api/v1/notifications/subscribe');
      setSubscribed(false);
      toast.success('Browser reminders disabled');
    } catch {
      toast.error('Failed to disable push notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleTestPush = async () => {
    setTestSending(true);
    try {
      await api.post('/api/v1/notifications/test-push', {
        title: 'Health Assistant',
        body: 'Push notifications are working correctly!',
      });
      toast.success('Test notification sent');
    } catch {
      toast.error('Failed to send test notification');
    } finally {
      setTestSending(false);
    }
  };

  if (!supported) return null;

  return (
    <div
      className="rounded-xl p-4"
      style={{
        backgroundColor: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
            style={{ backgroundColor: subscribed ? 'rgba(0,212,170,0.12)' : 'rgba(255,255,255,0.05)' }}
          >
            {subscribed
              ? <Bell className="w-4 h-4" style={{ color: '#00D4AA' }} />
              : <BellOff className="w-4 h-4" style={{ color: '#526380' }} />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium" style={{ color: '#E8EDF5' }}>
                Browser Reminders
              </h3>
              {subscribed && (
                <CheckCircle className="w-3.5 h-3.5" style={{ color: '#00D4AA' }} />
              )}
            </div>
            <p className="text-xs mt-0.5" style={{ color: '#526380' }}>
              {subscribed
                ? 'You\'ll receive medication reminders in your browser'
                : 'Get medication reminders even when the app is closed'}
            </p>
            {permission === 'denied' && (
              <p className="text-xs mt-1" style={{ color: '#F87171' }}>
                Notifications blocked — enable them in browser settings
              </p>
            )}
          </div>
        </div>

        {/* Toggle */}
        {permission !== 'denied' && (
          <button
            type="button"
            onClick={subscribed ? handleDisable : handleEnable}
            disabled={loading}
            className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
            style={subscribed
              ? { backgroundColor: 'rgba(248,113,113,0.08)', color: '#F87171', border: '1px solid rgba(248,113,113,0.2)' }
              : { backgroundColor: 'rgba(0,212,170,0.1)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.2)' }}
          >
            {loading
              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
              : subscribed ? <BellOff className="w-3.5 h-3.5" /> : <Bell className="w-3.5 h-3.5" />}
            {subscribed ? 'Disable' : 'Enable'}
          </button>
        )}
      </div>

      {/* Test push button */}
      {subscribed && (
        <div className="mt-3 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <button
            type="button"
            onClick={handleTestPush}
            disabled={testSending}
            className="text-xs flex items-center gap-1.5 transition-colors disabled:opacity-50"
            style={{ color: '#526380' }}
          >
            {testSending
              ? <Loader2 className="w-3 h-3 animate-spin" />
              : <Bell className="w-3 h-3" />}
            Send test notification
          </button>
        </div>
      )}
    </div>
  );
}
