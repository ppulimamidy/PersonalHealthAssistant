'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/stores/authStore';
import { ouraService } from '@/services/oura';
import { supabase } from '@/lib/supabase';
import {
  User,
  Shield,
  Bell,
  Link2,
  LogOut,
  Check,
  X,
  RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const { user, profile, ouraConnection, setOuraConnection, logout } = useAuthStore();
  const [isSyncing, setIsSyncing] = useState(false);

  const { data: connectionStatus, refetch } = useQuery({
    queryKey: ['oura-connection'],
    queryFn: ouraService.getConnectionStatus,
  });

  const disconnectMutation = useMutation({
    mutationFn: ouraService.disconnect,
    onSuccess: () => {
      setOuraConnection(null);
      toast.success('Oura Ring disconnected');
      refetch();
    },
    onError: () => {
      toast.error('Failed to disconnect');
    },
  });

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const result = await ouraService.syncData();
      toast.success(`Synced ${result.synced_records} records`);
    } catch {
      toast.error('Sync failed');
    } finally {
      setIsSyncing(false);
    }
  };

  const handleConnectOura = async () => {
    try {
      const response = await ouraService.getAuthUrl();
      if (response.sandbox_mode) {
        toast.success('Connected to Oura (Sandbox Mode)');
        refetch();
      } else if (response.auth_url) {
        window.location.href = response.auth_url;
      }
    } catch {
      toast.error('Failed to initiate connection');
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    logout();
    window.location.href = '/';
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Settings</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">Manage your account and connections</p>
      </div>

      <div className="space-y-6 max-w-2xl">
        {/* Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Name
                </label>
                <p className="text-slate-900 dark:text-slate-100">{user?.name || 'Not set'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Email
                </label>
                <p className="text-slate-900 dark:text-slate-100">{user?.email}</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Age
                  </label>
                  <p className="text-slate-900 dark:text-slate-100">{profile?.age ?? 'Not set'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Gender
                  </label>
                  <p className="text-slate-900 dark:text-slate-100">{profile?.gender ?? 'Not set'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Weight
                  </label>
                  <p className="text-slate-900 dark:text-slate-100">
                    {profile?.weight_kg != null ? `${profile.weight_kg} kg` : 'Not set'}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Device Connections */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link2 className="w-5 h-5" />
              Connected Devices
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center">
                  <svg viewBox="0 0 24 24" className="w-6 h-6 text-slate-600 dark:text-slate-400" fill="currentColor">
                    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
                    <circle cx="12" cy="12" r="4" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">Oura Ring</p>
                  {connectionStatus?.is_active ? (
                    <div className="flex items-center gap-1 text-sm text-green-600">
                      <Check className="w-4 h-4" />
                      Connected
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
                      <X className="w-4 h-4" />
                      Not connected
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {connectionStatus?.is_active ? (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleSync}
                      isLoading={isSyncing}
                    >
                      <RefreshCw className="w-4 h-4 mr-1" />
                      Sync
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => disconnectMutation.mutate()}
                      isLoading={disconnectMutation.isPending}
                    >
                      Disconnect
                    </Button>
                  </>
                ) : (
                  <Button size="sm" onClick={handleConnectOura}>
                    Connect
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Privacy & Security */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Privacy & Security
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">Data Encryption</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Your data is encrypted at rest</p>
                </div>
                <span className="text-green-600 text-sm font-medium">Enabled</span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">HIPAA Compliant</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Healthcare data protection</p>
                </div>
                <span className="text-green-600 text-sm font-medium">Yes</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Notifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">Weekly Summary</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Get a weekly health summary email</p>
                </div>
                <input type="checkbox" defaultChecked className="w-5 h-5 rounded" />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">Health Alerts</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Notify about significant changes</p>
                </div>
                <input type="checkbox" defaultChecked className="w-5 h-5 rounded" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Logout */}
        <Button variant="outline" onClick={handleLogout} className="w-full">
          <LogOut className="w-4 h-4 mr-2" />
          Sign Out
        </Button>
      </div>
    </div>
  );
}
