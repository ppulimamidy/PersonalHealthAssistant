'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/stores/authStore';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { ouraService } from '@/services/oura';
import { billingService } from '@/services/billing';
import { supabase } from '@/lib/supabase';
import {
  User,
  Shield,
  Bell,
  Link2,
  LogOut,
  Check,
  X,
  RefreshCw,
  CreditCard,
  Zap
} from 'lucide-react';
import toast from 'react-hot-toast';
import { ReferralCard } from '@/components/referral/ReferralCard';

export default function SettingsPage() {
  const { user, profile, ouraConnection, setOuraConnection, setProfile, logout } = useAuthStore();
  const subscription = useSubscriptionStore((s) => s.subscription);
  const setSubscription = useSubscriptionStore((s) => s.setSubscription);
  const tier = useSubscriptionStore((s) => s.getTier());
  const [isSyncing, setIsSyncing] = useState(false);
  const [portalLoading, setPortalLoading] = useState(false);
  const [forceActivating, setForceActivating] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  // Edit profile form state
  const [editAge, setEditAge] = useState<number | ''>('');
  const [editGender, setEditGender] = useState<'male' | 'female' | 'other' | 'prefer_not_to_say' | ''>('');
  const [editWeight, setEditWeight] = useState<number | ''>('');
  const [editWeightUnit, setEditWeightUnit] = useState<'kg' | 'lb'>('lb');

  const handleManageBilling = async () => {
    setPortalLoading(true);
    try {
      const url = await billingService.createPortalSession();
      window.location.href = url;
    } catch {
      toast.error('Failed to open billing portal');
    } finally {
      setPortalLoading(false);
    }
  };

  const handleForceActivate = async (targetTier: 'pro' | 'pro_plus' = 'pro') => {
    setForceActivating(true);
    try {
      await billingService.forceActivatePro(targetTier);
      const tierName = targetTier === 'pro_plus' ? 'Pro+' : 'Pro';
      toast.success(`${tierName} subscription activated!`);
      // Refetch subscription
      const freshSub = await billingService.getSubscription();
      setSubscription(freshSub);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to activate subscription');
    } finally {
      setForceActivating(false);
    }
  };

  const handleEditProfile = () => {
    // Initialize edit form with current values
    setEditAge(profile?.age ?? '');
    setEditGender(profile?.gender ?? '');

    // Convert weight to lb for display if present
    if (profile?.weight_kg != null) {
      setEditWeightUnit('lb');
      setEditWeight(Math.round(profile.weight_kg * 2.20462));
    } else {
      setEditWeight('');
    }

    setIsEditingProfile(true);
  };

  const handleCancelEdit = () => {
    setIsEditingProfile(false);
    setEditAge('');
    setEditGender('');
    setEditWeight('');
  };

  const handleSaveProfile = async () => {
    if (typeof editAge !== 'number' || editAge < 13 || editAge > 120) {
      toast.error('Please enter a valid age (13-120)');
      return;
    }
    if (!editGender) {
      toast.error('Please select a gender');
      return;
    }
    if (typeof editWeight !== 'number' || editWeight <= 0) {
      toast.error('Please enter a valid weight');
      return;
    }

    setIsSavingProfile(true);
    try {
      // Convert weight to kg
      const weightKg = editWeightUnit === 'kg' ? editWeight : editWeight / 2.20462;
      const roundedWeightKg = Math.round(weightKg * 10) / 10;

      const { error } = await supabase.auth.updateUser({
        data: {
          age: editAge,
          gender: editGender,
          weight_kg: roundedWeightKg,
        },
      });

      if (error) throw error;

      // Update local state
      setProfile({
        age: editAge,
        gender: editGender as 'male' | 'female' | 'other' | 'prefer_not_to_say',
        weight_kg: roundedWeightKg,
        profile_completed: true,
      });

      toast.success('Profile updated');
      setIsEditingProfile(false);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to update profile');
    } finally {
      setIsSavingProfile(false);
    }
  };

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
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                Profile
              </CardTitle>
              {!isEditingProfile && (
                <Button variant="outline" size="sm" onClick={handleEditProfile}>
                  Edit
                </Button>
              )}
            </div>
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

              {isEditingProfile ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Age
                      </label>
                      <input
                        type="number"
                        value={editAge}
                        onChange={(e) => setEditAge(e.target.value === '' ? '' : Number(e.target.value))}
                        min={13}
                        max={120}
                        className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        placeholder="e.g. 32"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Gender
                      </label>
                      <select
                        value={editGender}
                        onChange={(e) => setEditGender(e.target.value as 'male' | 'female' | 'other' | 'prefer_not_to_say')}
                        className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Select…</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other</option>
                        <option value="prefer_not_to_say">Prefer not to say</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Weight
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="number"
                          value={editWeight}
                          onChange={(e) => setEditWeight(e.target.value === '' ? '' : Number(e.target.value))}
                          min={1}
                          className="flex-1 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                          placeholder={editWeightUnit === 'lb' ? '160' : '72'}
                        />
                        <select
                          value={editWeightUnit}
                          onChange={(e) => setEditWeightUnit(e.target.value as 'kg' | 'lb')}
                          className="w-16 px-2 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <option value="lb">lb</option>
                          <option value="kg">kg</option>
                        </select>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button onClick={handleSaveProfile} isLoading={isSavingProfile}>
                      Save Changes
                    </Button>
                    <Button variant="outline" onClick={handleCancelEdit}>
                      Cancel
                    </Button>
                  </div>
                </>
              ) : (
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
                    <p className="text-slate-900 dark:text-slate-100">
                      {profile?.gender === 'prefer_not_to_say' ? 'Prefer not to say' : profile?.gender ?? 'Not set'}
                    </p>
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
              )}
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

        {/* Subscription */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="w-5 h-5" />
              Subscription
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">
                    Current Plan
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {tier === 'free' ? 'Free' : tier === 'pro' ? 'Pro' : 'Pro+'}
                    {subscription?.status === 'active' && tier !== 'free' && ' — Active'}
                    {subscription?.status === 'incomplete' && ' — Incomplete'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {tier !== 'free' && subscription?.status === 'active' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleManageBilling}
                      isLoading={portalLoading}
                    >
                      Manage Billing
                    </Button>
                  )}
                  {subscription?.status === 'incomplete' && (
                    <>
                      <Button
                        size="sm"
                        onClick={() => handleForceActivate('pro')}
                        isLoading={forceActivating}
                        variant="outline"
                      >
                        <Zap className="w-4 h-4 mr-1" />
                        Activate Pro
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleForceActivate('pro_plus')}
                        isLoading={forceActivating}
                      >
                        <Zap className="w-4 h-4 mr-1" />
                        Activate Pro+
                      </Button>
                    </>
                  )}
                  {tier === 'free' && subscription?.status !== 'incomplete' && (
                    <Button size="sm" onClick={() => (window.location.href = '/pricing')}>
                      <Zap className="w-4 h-4 mr-1" />
                      Upgrade
                    </Button>
                  )}
                </div>
              </div>

              {subscription?.usage && (
                <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Weekly Usage
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(subscription.usage).map(([key, usage]) => (
                      <div key={key} className="text-sm">
                        <span className="text-slate-500 dark:text-slate-400">
                          {key.replace(/_/g, ' ')}
                        </span>
                        <span className="ml-2 text-slate-900 dark:text-slate-100">
                          {usage.used}{usage.limit === -1 ? '' : ` / ${usage.limit}`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Referral */}
        <ReferralCard />

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
