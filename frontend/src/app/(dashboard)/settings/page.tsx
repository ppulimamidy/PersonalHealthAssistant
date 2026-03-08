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
  Bell,
  Cpu,
  LogOut,
  CreditCard,
  Zap,
  ArrowRight,
  Download,
  Mail,
  Users,
  Link2,
  Trash2,
  Copy,
  Check,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { ReferralCard } from '@/components/referral/ReferralCard';
import { PushNotificationCard } from '@/components/settings/PushNotificationCard';
import { emailService } from '@/services/email';
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
];

export default function SettingsPage() {
  const { user, profile, setProfile, logout } = useAuthStore();
  const subscription = useSubscriptionStore((s) => s.subscription);
  const setSubscription = useSubscriptionStore((s) => s.setSubscription);
  const tier = useSubscriptionStore((s) => s.getTier());
  const [portalLoading, setPortalLoading] = useState(false);
  const [forceActivating, setForceActivating] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [sendingSummary, setSendingSummary] = useState(false);
  const [sendingReminder, setSendingReminder] = useState(false);
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

  const handleSendSummary = async () => {
    setSendingSummary(true);
    try {
      await emailService.sendWeeklySummary();
      toast.success('Weekly summary sent!');
    } catch {
      toast.error('Failed to send weekly summary');
    } finally {
      setSendingSummary(false);
    }
  };

  const handleSendReminder = async () => {
    setSendingReminder(true);
    try {
      await emailService.sendReminder();
      toast.success('Reminder sent!');
    } catch {
      toast.error('Failed to send reminder');
    } finally {
      setSendingReminder(false);
    }
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

        {/* Account Role */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Account Role
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
              Choose how you use HealthAI — your role adapts the interface to your needs.
            </p>
            <div className="grid grid-cols-3 gap-2">
              {(
                [
                  { role: 'patient', label: 'Patient', desc: 'Tracking my own health' },
                  { role: 'provider', label: 'Provider', desc: 'Clinician / practitioner' },
                  { role: 'caregiver', label: 'Caregiver', desc: 'Supporting someone else' },
                ] as { role: UserRole; label: string; desc: string }[]
              ).map(({ role, label, desc }) => {
                const isActive = (profile?.user_role ?? 'patient') === role;
                return (
                  <button
                    key={role}
                    disabled={savingRole}
                    onClick={() => handleUpdateRole(role)}
                    className={`flex flex-col items-start p-3 rounded-lg border text-left transition-all ${
                      isActive
                        ? 'border-primary-500 bg-primary-500/10 text-primary-600 dark:text-primary-400'
                        : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <span className="text-sm font-medium">{label}</span>
                    <span className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{desc}</span>
                  </button>
                );
              })}
            </div>
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

        {/* Email & Notifications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Email &amp; Notifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">Weekly Summary</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Send a weekly health digest to your email
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSendSummary}
                  isLoading={sendingSummary}
                >
                  <Mail className="w-4 h-4 mr-1.5" />
                  Send Now
                </Button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">Daily Reminder</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    One-click reminder to log meals, symptoms, and medications
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSendReminder}
                  isLoading={sendingReminder}
                >
                  <Bell className="w-4 h-4 mr-1.5" />
                  Send Reminder
                </Button>
              </div>
              <PushNotificationCard />
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
