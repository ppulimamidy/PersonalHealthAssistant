'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/stores/authStore';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { billingService } from '@/services/billing';
import { supabase } from '@/lib/supabase';
import Link from 'next/link';
import {
  User,
  Shield,
  Cpu,
  LogOut,
  CreditCard,
  Zap,
  ArrowRight,
  Download,
  Users,
  Link2,
  Trash2,
  Copy,
  Check,
  GitCompare,
  Heart,
  Plus,
  Lightbulb,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { ReferralCard } from '@/components/referral/ReferralCard';
import { exportService } from '@/services/export';
import { api } from '@/services/api';
import { sharingService } from '@/services/sharing';
import { caregiverService } from '@/services/caregiver';
import type { UserRole, ShareLink, SharePermission, ManagedProfile } from '@/types';

const ALL_PERMISSIONS: { key: SharePermission; label: string }[] = [
  { key: 'summary', label: 'Profile & Conditions' },
  { key: 'medications', label: 'Medications' },
  { key: 'lab_results', label: 'Lab Results' },
  { key: 'symptoms', label: 'Symptoms' },
  { key: 'care_plans', label: 'Care Plans' },
  { key: 'insights', label: 'AI Insights' },
  { key: 'interventions', label: 'Experiments' },
  { key: 'intelligence', label: 'Treatment Recommendations' },
  { key: 'wearable_data', label: 'Wearable Health Data' },
  { key: 'medical_records', label: 'Medical Records' },
  { key: 'nutrition', label: 'Nutrition & Meals' },
  { key: 'doctor_prep', label: 'Visit Prep Report' },
  { key: 'specialist_recs', label: 'Specialist Recommendations' },
  { key: 'cycle_tracking', label: 'Cycle Data' },
];

// ── Data Sources Card ─────────────────────────────────────────────────────────

type SourceOption = 'auto' | 'oura' | 'healthkit' | 'dexcom' | 'whoop' | 'garmin' | 'fitbit';

interface DataSourcePrefs {
  steps: SourceOption;
  sleep: SourceOption;
  hrv: SourceOption;
  heart_rate: SourceOption;
}

const DS_DEFAULT: DataSourcePrefs = { steps: 'auto', sleep: 'auto', hrv: 'auto', heart_rate: 'auto' };
const DS_KEY = 'vitalix_data_source_prefs';

const DS_METRICS: Array<{ key: keyof DataSourcePrefs; label: string; hint: string }> = [
  { key: 'steps',      label: 'Steps',              hint: 'Auto prefers Apple Health — wrist step counting is typically more accurate.' },
  { key: 'sleep',      label: 'Sleep',              hint: 'Auto picks the best connected source — ring sensors offer richer sleep staging.' },
  { key: 'hrv',        label: 'HRV',                hint: 'Auto picks the best connected source — overnight HRV from a ring has less motion artifact.' },
  { key: 'heart_rate', label: 'Resting Heart Rate', hint: 'Auto picks the best connected source — overnight resting HR is more stable.' },
];

const DS_OPTIONS: Array<{ value: SourceOption; label: string }> = [
  { value: 'auto',      label: 'Auto (recommended)' },
  { value: 'oura',      label: 'Oura Ring' },
  { value: 'healthkit', label: 'Apple Health' },
  { value: 'dexcom',    label: 'Dexcom' },
  { value: 'whoop',     label: 'WHOOP' },
  { value: 'garmin',    label: 'Garmin' },
  { value: 'fitbit',    label: 'Fitbit' },
];

function DataSourcesCard() {
  const [prefs, setPrefs] = useState<DataSourcePrefs>(DS_DEFAULT);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const raw = globalThis.localStorage?.getItem(DS_KEY);
      if (raw) setPrefs({ ...DS_DEFAULT, ...JSON.parse(raw) });
    } catch { /* ignore */ }
  }, []);

  const handleChange = (key: keyof DataSourcePrefs, val: SourceOption) => {
    setPrefs((p) => ({ ...p, [key]: val }));
    setSaved(false);
  };

  const handleSave = () => {
    globalThis.localStorage?.setItem(DS_KEY, JSON.stringify(prefs));
    setSaved(true);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitCompare className="w-5 h-5" />
          Data Sources
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          When multiple devices track the same metric, choose which source is authoritative
          for your insights — or run a self-experiment to compare them.
        </p>
        <div className="space-y-4">
          {DS_METRICS.map(({ key, label, hint }) => (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor={`ds-${key}`} className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {label}
                </label>
                <select
                  id={`ds-${key}`}
                  value={prefs[key]}
                  onChange={(e) => handleChange(key, e.target.value as SourceOption)}
                  className="text-sm px-2 py-1 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  {DS_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              {prefs[key] === 'auto' && (
                <p className="text-xs text-slate-400 dark:text-slate-500">{hint}</p>
              )}
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
          <Button size="sm" onClick={handleSave} variant={saved ? 'outline' : 'primary'}>
            {saved ? '✓ Saved' : 'Save Preferences'}
          </Button>
          {!saved && (
            <p className="text-xs text-slate-400 mt-2">
              Changes apply to Timeline and Trends immediately after saving.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function HealthProfileSummary() {
  const { user } = useAuthStore();
  const { data } = useQuery({
    queryKey: ['health-summary'],
    queryFn: async () => {
      try { const { data: resp } = await api.get('/api/v1/profile-intelligence/health-summary'); return resp; }
      catch { return null; }
    },
    enabled: Boolean(user),
    staleTime: 2 * 60_000,
  });

  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Heart className="w-4 h-4 text-primary-500" />
            <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">My Health Profile</span>
          </div>
          <Link href="/health-profile" className="text-xs text-primary-500 hover:underline">Manage →</Link>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Conditions</span>
              <Link href="/health-profile" className="text-primary-500"><Plus className="w-3 h-3" /></Link>
            </div>
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mt-0.5">
              {data?.conditions_count ?? 0}
            </p>
            {data?.conditions?.length > 0 && (
              <p className="text-xs text-slate-400 truncate mt-0.5">
                {data.conditions.map((c: any) => c.name).join(', ')}
              </p>
            )}
          </div>
          <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
            <span className="text-xs text-slate-500">Goals</span>
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mt-0.5">
              {data?.active_goals_count ?? 0} active
            </p>
          </div>
          <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
            <span className="text-xs text-slate-500">Specialists</span>
            <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mt-0.5">
              {data?.specialists_count ?? 0}
            </p>
            {data?.specialists?.length > 0 && (
              <div className="flex gap-1 mt-0.5 flex-wrap">
                {data.specialists.slice(0, 2).map((s: any, i: number) => (
                  <span key={i} className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: `${s.color}15`, color: s.color }}>
                    {s.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        {data?.hint && (
          <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
            <Lightbulb className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
            <p className="text-xs text-amber-600 dark:text-amber-400">{data.hint}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function SettingsPage() {
  const { user, profile, setProfile, logout } = useAuthStore();
  const subscription = useSubscriptionStore((s) => s.subscription);
  const setSubscription = useSubscriptionStore((s) => s.setSubscription);
  const tier = useSubscriptionStore((s) => s.getTier());
  const [portalLoading, setPortalLoading] = useState(false);
  const [forceActivating, setForceActivating] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [savingRole, setSavingRole] = useState(false);

  // Sharing state
  const [shares, setShares] = useState<ShareLink[]>([]);
  const [sharesLoading, setSharesLoading] = useState(false);
  const [creatingShare, setCreatingShare] = useState(false);
  const [showNewShare, setShowNewShare] = useState(false);
  const [newShareLabel, setNewShareLabel] = useState('');
  const [newSharePerms, setNewSharePerms] = useState<SharePermission[]>(
    ALL_PERMISSIONS.map((p) => p.key)
  );
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Caregiver managed profiles state
  const [managedProfiles, setManagedProfiles] = useState<ManagedProfile[]>([]);
  const [managedLoading, setManagedLoading] = useState(false);
  const [showLinkForm, setShowLinkForm] = useState(false);
  const [linkToken, setLinkToken] = useState('');
  const [linkRelationship, setLinkRelationship] = useState('');
  const [linkDisplayName, setLinkDisplayName] = useState('');
  const [linkingProfile, setLinkingProfile] = useState(false);

  // Edit profile form state
  const [editDob, setEditDob] = useState('');
  const [editSex, setEditSex] = useState<'male' | 'female' | 'other' | 'prefer_not_to_say' | ''>('');
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
    setEditDob(profile?.date_of_birth ?? '');
    setEditSex(profile?.biological_sex ?? '');

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
    setEditDob('');
    setEditSex('');
    setEditWeight('');
  };

  const handleSaveProfile = async () => {
    if (!editDob) {
      toast.error('Please enter a date of birth');
      return;
    }
    if (!editSex) {
      toast.error('Please select a biological sex');
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

      const { error } = await supabase
        .from('profiles')
        .update({
          date_of_birth: editDob,
          biological_sex: editSex,
          weight_kg: roundedWeightKg,
        })
        .eq('id', user?.id);

      if (error) throw error;

      // Update local store
      setProfile({
        date_of_birth: editDob,
        biological_sex: editSex as 'male' | 'female' | 'other' | 'prefer_not_to_say',
        weight_kg: roundedWeightKg,
      });

      toast.success('Profile updated');
      setIsEditingProfile(false);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to update profile');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    logout();
    window.location.href = '/';
  };

  const handleExportPdf = async () => {
    setExportingPdf(true);
    try {
      await exportService.downloadPdf();
      toast.success('PDF downloaded!');
    } catch {
      toast.error('Failed to generate PDF export');
    } finally {
      setExportingPdf(false);
    }
  };

  const handleUpdateRole = async (role: UserRole) => {
    if (profile?.user_role === role) return;
    setSavingRole(true);
    try {
      await api.patch('/api/v1/profile/role', { user_role: role });
      setProfile({ ...profile, user_role: role });
      toast.success(`Role updated to ${role}`);
    } catch {
      toast.error('Failed to update role');
    } finally {
      setSavingRole(false);
    }
  };

  // Load shares when user is available
  useEffect(() => {
    if (!user) return;
    setSharesLoading(true);
    sharingService.listShares().then(setShares).catch(() => {}).finally(() => setSharesLoading(false));
  }, [user]);

  const handleCreateShare = async () => {
    setCreatingShare(true);
    try {
      const link = await sharingService.createShare({
        label: newShareLabel || undefined,
        permissions: newSharePerms,
      });
      setShares((prev) => [link, ...prev]);
      setShowNewShare(false);
      setNewShareLabel('');
      setNewSharePerms(ALL_PERMISSIONS.map((p) => p.key));
      toast.success('Share link created');
    } catch {
      toast.error('Failed to create share link');
    } finally {
      setCreatingShare(false);
    }
  };

  const handleRevokeShare = async (linkId: string) => {
    try {
      await sharingService.revokeShare(linkId);
      setShares((prev) => prev.filter((s) => s.id !== linkId));
      toast.success('Share link revoked');
    } catch {
      toast.error('Failed to revoke link');
    }
  };

  const handleCopyLink = (token: string, linkId: string) => {
    const url = `${window.location.origin}/share/${token}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopiedId(linkId);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  // Load managed profiles for caregivers
  useEffect(() => {
    if (profile?.user_role !== 'caregiver') return;
    setManagedLoading(true);
    caregiverService.listManaged().then(setManagedProfiles).catch(() => {}).finally(() => setManagedLoading(false));
  }, [profile?.user_role]);

  const handleLinkProfile = async () => {
    if (!linkToken.trim()) return;
    setLinkingProfile(true);
    try {
      const linked = await caregiverService.linkProfile({
        token: linkToken.trim(),
        relationship: linkRelationship || undefined,
        display_name: linkDisplayName || undefined,
      });
      setManagedProfiles((prev) => [linked, ...prev]);
      setShowLinkForm(false);
      setLinkToken('');
      setLinkRelationship('');
      setLinkDisplayName('');
      toast.success('Profile linked');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to link profile';
      toast.error(msg);
    } finally {
      setLinkingProfile(false);
    }
  };

  const handleUnlinkProfile = async (linkId: string) => {
    try {
      await caregiverService.unlinkProfile(linkId);
      setManagedProfiles((prev) => prev.filter((p) => p.id !== linkId));
      toast.success('Profile unlinked');
    } catch {
      toast.error('Failed to unlink profile');
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Settings</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">Manage your account and connections</p>
      </div>

      <div className="space-y-6 max-w-2xl">
        {/* Health Profile Summary */}
        <HealthProfileSummary />

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
                <p className="text-slate-900 dark:text-slate-100">{user?.name && user.name !== 'User' ? user.name : profile?.full_name || 'Not set'}</p>
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
                        Date of Birth
                      </label>
                      <input
                        type="date"
                        value={editDob}
                        onChange={(e) => setEditDob(e.target.value)}
                        max={(() => { const d = new Date(); d.setFullYear(d.getFullYear() - 13); return d.toISOString().split('T')[0]; })()}
                        className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Biological Sex
                      </label>
                      <select
                        value={editSex}
                        onChange={(e) => setEditSex(e.target.value as 'male' | 'female' | 'other' | 'prefer_not_to_say')}
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
                    <p className="text-slate-900 dark:text-slate-100">
                      {profile?.date_of_birth
                        ? (() => {
                            const dob = new Date(profile.date_of_birth);
                            const now = new Date();
                            let a = now.getFullYear() - dob.getFullYear();
                            const m = now.getMonth() - dob.getMonth();
                            if (m < 0 || (m === 0 && now.getDate() < dob.getDate())) a--;
                            return `${a} yrs`;
                          })()
                        : 'Not set'}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Biological Sex
                    </label>
                    <p className="text-slate-900 dark:text-slate-100 capitalize">
                      {profile?.biological_sex === 'prefer_not_to_say'
                        ? 'Prefer not to say'
                        : profile?.biological_sex ?? 'Not set'}
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

        {/* Account Capabilities */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Account Capabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {/* Personal — always on */}
              <div className="flex items-center gap-3 p-3 rounded-lg border border-primary-500/30 bg-primary-500/5">
                <div className="w-8 h-8 rounded-lg bg-primary-500/15 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-primary-500" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Personal Health Tracking</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Track your sleep, nutrition, medications, labs & symptoms</p>
                </div>
                <span className="text-xs font-medium text-primary-500 bg-primary-500/10 px-2 py-0.5 rounded-full">Always on</span>
              </div>

              {/* Patient Monitoring */}
              <div className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/15 flex items-center justify-center flex-shrink-0">
                  <Shield className="w-4 h-4 text-indigo-500" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Patient Monitoring</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">View health data shared by your patients</p>
                </div>
                <button
                  disabled={savingRole}
                  onClick={() => handleUpdateRole((profile?.user_role ?? 'patient') === 'provider' ? 'patient' : 'provider')}
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    (profile?.user_role ?? 'patient') === 'provider' ? 'bg-indigo-500' : 'bg-slate-300 dark:bg-slate-600'
                  }`}
                >
                  <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                    (profile?.user_role ?? 'patient') === 'provider' ? 'translate-x-5' : ''
                  }`} />
                </button>
              </div>

              {/* Family Caregiving */}
              <div className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="w-8 h-8 rounded-lg bg-pink-500/15 flex items-center justify-center flex-shrink-0">
                  <Users className="w-4 h-4 text-pink-500" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">Family Caregiving</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Monitor family members' health & sharing</p>
                </div>
                <button
                  disabled={savingRole}
                  onClick={() => handleUpdateRole((profile?.user_role ?? 'patient') === 'caregiver' ? 'patient' : 'caregiver')}
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    (profile?.user_role ?? 'patient') === 'caregiver' ? 'bg-pink-500' : 'bg-slate-300 dark:bg-slate-600'
                  }`}
                >
                  <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                    (profile?.user_role ?? 'patient') === 'caregiver' ? 'translate-x-5' : ''
                  }`} />
                </button>
              </div>
            </div>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-3">
              Your personal health data is always available regardless of which capabilities you enable.
            </p>
          </CardContent>
        </Card>

        {/* Managed Profiles — caregiver only */}
        {profile?.user_role === 'caregiver' && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Managed Profiles
                </CardTitle>
                <Button size="sm" variant="outline" onClick={() => setShowLinkForm((v) => !v)}>
                  {showLinkForm ? 'Cancel' : '+ Link Profile'}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                Link family members or patients you care for. They need to share their access
                token from Settings → Share with Care Team.
              </p>

              {/* Link form */}
              {showLinkForm && (
                <div className="mb-4 p-4 rounded-lg border border-slate-200 dark:border-slate-700 space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Share code or link *
                    </label>
                    <input
                      type="text"
                      value={linkToken}
                      onChange={(e) => setLinkToken(e.target.value)}
                      placeholder="Paste their share code or URL…"
                      className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Relationship
                      </label>
                      <input
                        type="text"
                        value={linkRelationship}
                        onChange={(e) => setLinkRelationship(e.target.value)}
                        placeholder="e.g. parent, child, spouse"
                        className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                        Display name
                      </label>
                      <input
                        type="text"
                        value={linkDisplayName}
                        onChange={(e) => setLinkDisplayName(e.target.value)}
                        placeholder="e.g. Mom"
                        className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                  </div>
                  <Button size="sm" onClick={handleLinkProfile} isLoading={linkingProfile}>
                    Link Profile
                  </Button>
                </div>
              )}

              {/* Linked profiles list */}
              {managedLoading ? (
                <p className="text-sm text-slate-400">Loading…</p>
              ) : managedProfiles.length === 0 ? (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  No profiles linked yet.
                </p>
              ) : (
                <div className="space-y-2">
                  {managedProfiles.map((mp) => (
                    <div
                      key={mp.id}
                      className="flex items-center justify-between gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-700"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                          {mp.display_name || mp.label || 'Unnamed'}
                        </p>
                        {mp.relationship && (
                          <p className="text-xs text-slate-500 dark:text-slate-400 capitalize">
                            {mp.relationship}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => handleUnlinkProfile(mp.id)}
                        title="Unlink"
                        className="p-1.5 rounded-md text-slate-500 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Share with Care Team */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Link2 className="w-5 h-5" />
                Share with Care Team
              </CardTitle>
              <Button size="sm" variant="outline" onClick={() => setShowNewShare((v) => !v)}>
                {showNewShare ? 'Cancel' : '+ New Link'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
              Generate a secure read-only link to share your health data with your doctor,
              nutritionist, or care team — no account required on their end.
            </p>

            {/* New share form */}
            {showNewShare && (
              <div className="mb-4 p-4 rounded-lg border border-slate-200 dark:border-slate-700 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Label (optional)
                  </label>
                  <input
                    type="text"
                    value={newShareLabel}
                    onChange={(e) => setNewShareLabel(e.target.value)}
                    placeholder="e.g. Dr. Smith – Primary Care"
                    className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    What to share
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {ALL_PERMISSIONS.map(({ key, label }) => {
                      const active = newSharePerms.includes(key);
                      return (
                        <button
                          key={key}
                          type="button"
                          onClick={() =>
                            setNewSharePerms((prev) =>
                              active ? prev.filter((p) => p !== key) : [...prev, key]
                            )
                          }
                          className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                            active
                              ? 'bg-primary-500/10 border-primary-500 text-primary-600 dark:text-primary-400'
                              : 'border-slate-300 dark:border-slate-600 text-slate-500 dark:text-slate-400'
                          }`}
                        >
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <Button size="sm" onClick={handleCreateShare} isLoading={creatingShare}>
                  Generate Link
                </Button>
              </div>
            )}

            {/* Existing shares */}
            {sharesLoading ? (
              <p className="text-sm text-slate-400">Loading…</p>
            ) : shares.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">
                No active share links. Create one above.
              </p>
            ) : (
              <div className="space-y-3">
                {shares.map((share) => (
                  <div
                    key={share.id}
                    className="flex items-start justify-between gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-700"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                        {share.label || 'Unnamed link'}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        {share.access_count} view{share.access_count !== 1 ? 's' : ''}
                        {share.last_accessed_at &&
                          ` · Last viewed ${new Date(share.last_accessed_at).toLocaleDateString()}`}
                        {share.expires_at &&
                          ` · Expires ${new Date(share.expires_at).toLocaleDateString()}`}
                      </p>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {share.permissions.map((p) => (
                          <span
                            key={p}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                          >
                            {ALL_PERMISSIONS.find((x) => x.key === p)?.label ?? p}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <button
                        onClick={() => handleCopyLink(share.token, share.id)}
                        title="Copy link"
                        className="p-1.5 rounded-md text-slate-500 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                      >
                        {copiedId === share.id ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => handleRevokeShare(share.id)}
                        title="Revoke link"
                        className="p-1.5 rounded-md text-slate-500 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Devices — link to Device Hub */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="w-5 h-5" />
              Connected Devices
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Manage wearables and health app connections
              </p>
              <Link
                href="/devices"
                className="flex items-center gap-1.5 text-sm font-medium text-primary-600 dark:text-primary-400 hover:underline"
              >
                Manage devices
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Data Sources */}
        <DataSourcesCard />

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

        {/* Two-Factor Authentication */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Two-Factor Authentication
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-slate-900 dark:text-slate-100">Authenticator App (TOTP)</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Add an extra layer of security with Google Authenticator or similar
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  try {
                    const { data, error } = await supabase.auth.mfa.enroll({ factorType: 'totp', friendlyName: 'Vitalix Auth' });
                    if (error) { toast.error(error.message); return; }
                    if (data?.totp?.qr_code) {
                      // Show QR code in a new window for scanning
                      const win = window.open('', '_blank', 'width=400,height=500');
                      if (win) {
                        win.document.write(`
                          <html><head><title>Set up 2FA</title><style>body{font-family:system-ui;text-align:center;padding:40px;background:#0F1720;color:#E8EDF5}img{margin:20px auto;border-radius:12px}code{background:#1E2A3B;padding:4px 8px;border-radius:4px;font-size:13px}</style></head>
                          <body>
                            <h2>Scan with Authenticator App</h2>
                            <img src="${data.totp.qr_code}" width="200" height="200" />
                            <p>Or enter manually:<br/><code>${data.totp.secret}</code></p>
                            <p style="color:#526380;font-size:12px;margin-top:20px">After scanning, enter the 6-digit code in the app to verify.</p>
                          </body></html>
                        `);
                      }
                      toast.success('Scan the QR code with your authenticator app');
                    }
                  } catch { toast.error('Failed to set up 2FA'); }
                }}
              >
                Set Up 2FA
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Data & Export */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="w-5 h-5" />
              Data &amp; Export
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">Export Health Data</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Download your full health history as a PDF
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExportPdf}
                  isLoading={exportingPdf}
                >
                  <Download className="w-4 h-4 mr-1.5" />
                  Download PDF
                </Button>
              </div>
              <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  <strong>Data Retention Policy:</strong> Your health data is retained as long as your account is active.
                  Inactive accounts (no login for 24 months) will receive email warnings before data is archived.
                  You can export or delete your data at any time.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone — Delete Account */}
        <Card className="border-red-500/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-400">
              <Trash2 className="w-5 h-5" />
              Danger Zone
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-red-400">Delete Account</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Permanently delete your account and all health data. This cannot be undone.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                onClick={() => {
                  if (window.confirm('Are you sure you want to permanently delete your account and ALL health data? This action cannot be undone.')) {
                    if (window.confirm('This is your final confirmation. Type DELETE in the next prompt to proceed.')) {
                      const input = window.prompt('Type DELETE to confirm account deletion:');
                      if (input === 'DELETE') {
                        api.delete('/api/v1/profile/account')
                          .then(() => {
                            toast.success('Account deleted. Redirecting...');
                            setTimeout(() => { window.location.href = '/'; }, 2000);
                          })
                          .catch(() => toast.error('Failed to delete account. Please contact support.'));
                      } else {
                        toast('Account deletion cancelled');
                      }
                    }
                  }
                }}
              >
                <Trash2 className="w-4 h-4 mr-1.5" />
                Delete Account
              </Button>
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
