/**
 * Phase 5: Care Team Sharing screen.
 * Create share links for doctors, caregivers, or family members.
 * Manage existing shares and revoke access.
 *
 * GET    /api/v1/share/            list all active share links
 * POST   /api/v1/share/            create new share link
 * DELETE /api/v1/share/{id}        revoke share link
 */

import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, ActivityIndicator,
  Alert, Share, Modal, Switch,
} from 'react-native';
import { router } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import { api } from '@/services/api';
import type { ShareLink, SharePermission, CreateShareRequest } from '@/types';

// ─── Constants ─────────────────────────────────────────────────────────────────

const PERMISSIONS: Array<{ key: SharePermission; label: string; description: string }> = [
  { key: 'summary',          label: 'Health Summary',             description: 'Overall health score and profile' },
  { key: 'medications',      label: 'Medications',                description: 'Current medications & adherence' },
  { key: 'lab_results',      label: 'Lab Results',                description: 'Blood work and test results' },
  { key: 'symptoms',         label: 'Symptom Journal',            description: 'Logged symptoms and severity' },
  { key: 'care_plans',       label: 'Care Plans',                 description: 'Active care plans and goals' },
  { key: 'insights',         label: 'AI Insights',                description: 'AI-generated health patterns' },
  { key: 'interventions',    label: 'Experiments',                description: 'N-of-1 intervention results' },
  { key: 'intelligence',     label: 'Treatment Recommendations',  description: 'AI medication & supplement recs' },
  { key: 'wearable_data',    label: 'Wearable Health Data',       description: 'Sleep, HRV, activity, recovery trends' },
  { key: 'medical_records',  label: 'Medical Records',            description: 'Pathology, genomic & imaging reports' },
  { key: 'nutrition',        label: 'Nutrition & Meals',          description: 'Meal logs with macros & calories' },
  { key: 'doctor_prep',      label: 'Visit Prep Report',          description: 'Comprehensive doctor visit report' },
  { key: 'specialist_recs',  label: 'Specialist Recommendations', description: 'AI specialist consultation summaries' },
  { key: 'cycle_tracking',   label: 'Cycle Data',                 description: 'Menstrual cycle phases & predictions' },
  { key: 'clinical_research', label: 'Clinical Research',          description: 'Personalized research topics & saved reports' },
];

const EXPIRY_OPTIONS = [
  { value: 7,   label: '7 days' },
  { value: 30,  label: '30 days' },
  { value: 90,  label: '90 days' },
  { value: 365, label: '1 year' },
  { value: 0,   label: 'No expiry' },
];

// ─── New Share Modal ──────────────────────────────────────────────────────────

function CreateShareModal({ onClose, onCreate }: {
  onClose: () => void;
  onCreate: (req: CreateShareRequest) => void;
}) {
  const [label, setLabel] = useState('');
  const [expiryDays, setExpiryDays] = useState(30);
  const [permissions, setPermissions] = useState<Set<SharePermission>>(
    new Set(['summary', 'medications', 'lab_results', 'symptoms'])
  );

  const togglePerm = (perm: SharePermission) => {
    setPermissions((prev) => {
      const next = new Set(prev);
      if (next.has(perm)) next.delete(perm);
      else next.add(perm);
      return next;
    });
  };

  return (
    <Modal visible animationType="slide" transparent>
      <View className="flex-1 justify-end bg-black/60">
        <View className="bg-obsidian-900 rounded-t-3xl border-t border-surface-border" style={{ maxHeight: '90%' }}>
          <ScrollView>
            <View className="p-6">
              <View className="flex-row items-center mb-5">
                <Text className="text-[#E8EDF5] font-display text-lg flex-1">New Share Link</Text>
                <TouchableOpacity onPress={onClose}>
                  <Ionicons name="close" size={22} color="#526380" />
                </TouchableOpacity>
              </View>

              {/* Label */}
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Label (optional)</Text>
              <View className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 mb-4">
                <Text
                  className="text-[#E8EDF5] text-sm"
                  onPress={() => {/* TextInput would go here */}}
                >
                  {label || 'e.g. Dr. Smith, Mom, Physical Therapist'}
                </Text>
              </View>

              {/* Permissions */}
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-3">Access Permissions</Text>
              <View className="bg-surface-raised border border-surface-border rounded-2xl overflow-hidden mb-4">
                {PERMISSIONS.map((perm, i) => (
                  <TouchableOpacity
                    key={perm.key}
                    onPress={() => togglePerm(perm.key)}
                    className="flex-row items-center px-4 py-3"
                    style={{ borderTopWidth: i > 0 ? 1 : 0, borderTopColor: 'rgba(255,255,255,0.04)' }}
                    activeOpacity={0.7}
                  >
                    <View className="flex-1 mr-3">
                      <Text className="text-[#E8EDF5] text-sm">{perm.label}</Text>
                      <Text className="text-[#526380] text-xs mt-0.5">{perm.description}</Text>
                    </View>
                    <View
                      className="w-5 h-5 rounded-md items-center justify-center"
                      style={{
                        backgroundColor: permissions.has(perm.key) ? 'rgba(0,212,170,0.2)' : 'rgba(255,255,255,0.06)',
                        borderWidth: 1,
                        borderColor: permissions.has(perm.key) ? 'rgba(0,212,170,0.4)' : 'rgba(255,255,255,0.1)',
                      }}
                    >
                      {permissions.has(perm.key) && (
                        <Ionicons name="checkmark" size={13} color="#00D4AA" />
                      )}
                    </View>
                  </TouchableOpacity>
                ))}
              </View>

              {/* Expiry */}
              <Text className="text-[#526380] text-xs uppercase tracking-wider mb-2">Link Expires After</Text>
              <View className="flex-row flex-wrap gap-2 mb-6">
                {EXPIRY_OPTIONS.map((opt) => (
                  <TouchableOpacity
                    key={opt.value}
                    onPress={() => setExpiryDays(opt.value)}
                    className="rounded-xl px-3 py-2"
                    style={{
                      backgroundColor: expiryDays === opt.value ? 'rgba(0,212,170,0.15)' : 'rgba(255,255,255,0.04)',
                      borderWidth: 1,
                      borderColor: expiryDays === opt.value ? 'rgba(0,212,170,0.3)' : 'rgba(255,255,255,0.06)',
                    }}
                  >
                    <Text style={{ color: expiryDays === opt.value ? '#00D4AA' : '#526380', fontSize: 13 }}>
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TouchableOpacity
                onPress={() => onCreate({
                  label: label.trim() || undefined,
                  permissions: Array.from(permissions),
                  expires_days: expiryDays > 0 ? expiryDays : undefined,
                })}
                disabled={permissions.size === 0}
                className="bg-primary-500 rounded-2xl py-4 items-center"
                style={{ opacity: permissions.size === 0 ? 0.5 : 1 }}
                activeOpacity={0.8}
              >
                <Text className="text-obsidian-900 font-sansMedium">Create Share Link</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

// ─── Share card ────────────────────────────────────────────────────────────────

function ShareCard({ link, onRevoke }: { link: ShareLink; onRevoke: (id: string) => void }) {
  const isExpired = link.expires_at ? new Date(link.expires_at) < new Date() : false;
  const frontendUrl = process.env.EXPO_PUBLIC_FRONTEND_URL ?? 'http://localhost:3000';
  const shareUrl = `${frontendUrl}/share/${link.token}`;

  const handleShare = async () => {
    try {
      await Share.share({ message: `View my health summary: ${shareUrl}`, url: shareUrl });
    } catch { /* dismissed */ }
  };

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3"
      style={{ opacity: isExpired ? 0.6 : 1 }}>
      <View className="flex-row items-start justify-between mb-2">
        <View className="flex-1 mr-3">
          <Text className="text-[#E8EDF5] font-sansMedium">
            {link.label || 'Unnamed share'}
          </Text>
          <Text className="text-[#526380] text-xs mt-0.5">
            {link.access_count > 0
              ? `${link.access_count} view${link.access_count !== 1 ? 's' : ''}${link.last_accessed_at ? ` · Last viewed ${formatDistanceToNow(parseISO(link.last_accessed_at), { addSuffix: true })}` : ''}`
              : 'Not viewed yet'
            } · Created {format(parseISO(link.created_at), 'MMM d')}
          </Text>
        </View>
        {isExpired ? (
          <View className="rounded-full px-2.5 py-1 bg-surface-border">
            <Text className="text-[#526380] text-xs">Expired</Text>
          </View>
        ) : (
          <View className="rounded-full px-2.5 py-1 bg-primary-500/10">
            <Text className="text-primary-500 text-xs">Active</Text>
          </View>
        )}
      </View>

      {/* Permissions */}
      <View className="flex-row flex-wrap gap-1.5 mb-3">
        {link.permissions.map((perm) => (
          <View key={perm} className="rounded-full px-2 py-0.5" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}>
            <Text className="text-[#526380] text-[10px]">
              {PERMISSIONS.find((p) => p.key === perm)?.label ?? perm}
            </Text>
          </View>
        ))}
      </View>

      {link.expires_at && (
        <Text className="text-[#526380] text-xs mb-3">
          {isExpired ? 'Expired' : 'Expires'} {format(parseISO(link.expires_at), 'MMM d, yyyy')}
        </Text>
      )}

      {/* Actions */}
      <View className="flex-row gap-2 pt-3 border-t border-surface-border">
        {!isExpired && (
          <TouchableOpacity
            onPress={handleShare}
            className="flex-1 flex-row items-center justify-center gap-1.5 py-2.5 rounded-xl"
            style={{ backgroundColor: 'rgba(0,212,170,0.12)' }}
            activeOpacity={0.7}
          >
            <Ionicons name="share-outline" size={16} color="#00D4AA" />
            <Text className="text-primary-500 text-sm font-sansMedium">Share Link</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          onPress={() => Alert.alert('Revoke Access', 'Remove this share link? The recipient will no longer be able to view your health data.', [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Revoke', style: 'destructive', onPress: () => onRevoke(link.id) },
          ])}
          className="px-4 py-2.5 rounded-xl items-center"
          style={{ backgroundColor: 'rgba(248,113,113,0.08)' }}
          activeOpacity={0.7}
        >
          <Ionicons name="trash-outline" size={16} color="#F87171" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

// ─── Screen ────────────────────────────────────────────────────────────────────

export default function SharingScreen() {
  const [showModal, setShowModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: links = [], isLoading } = useQuery({
    queryKey: ['share-links'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/share/');
      return (Array.isArray(data) ? data : (data?.links ?? [])) as ShareLink[];
    },
  });

  const { mutate: create, isPending: isCreating } = useMutation({
    mutationFn: async (req: CreateShareRequest) => {
      const { data } = await api.post('/api/v1/share/', req);
      return data as ShareLink;
    },
    onSuccess: (newLink) => {
      queryClient.setQueryData<ShareLink[]>(['share-links'], (prev = []) => [newLink, ...prev]);
      setShowModal(false);
    },
    onError: () => {
      Alert.alert('Error', 'Failed to create share link. Please try again.');
    },
  });

  const { mutate: revoke } = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/share/${id}`);
    },
    onSuccess: (_, id) => {
      queryClient.setQueryData<ShareLink[]>(['share-links'], (prev = []) =>
        prev.filter((l) => l.id !== id)
      );
    },
  });

  return (
    <View className="flex-1 bg-obsidian-900">
      {/* Header */}
      <View className="flex-row items-center px-6 pt-14 pb-4 border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-4 p-1">
          <Ionicons name="chevron-back" size={24} color="#E8EDF5" />
        </TouchableOpacity>
        <View className="flex-1">
          <Text className="text-xl font-display text-[#E8EDF5]">Care Team Sharing</Text>
          <Text className="text-[#526380] text-xs mt-0.5">Share your health data with doctors & family</Text>
        </View>
        <TouchableOpacity
          onPress={() => setShowModal(true)}
          className="flex-row items-center gap-1.5 bg-primary-500 rounded-xl px-3 py-2"
          activeOpacity={0.8}
        >
          <Ionicons name="add" size={18} color="#080B10" />
          <Text className="text-obsidian-900 text-sm font-sansMedium">New</Text>
        </TouchableOpacity>
      </View>

      <ScrollView className="flex-1" contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
        {/* Explainer */}
        <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-5 flex-row gap-3">
          <Ionicons name="lock-closed-outline" size={18} color="#526380" style={{ marginTop: 1 }} />
          <Text className="text-[#526380] text-xs leading-5 flex-1">
            Share links give read-only access to selected health data. You control exactly what they can see.
            Revoke access at any time.
          </Text>
        </View>

        {isLoading ? (
          <View className="items-center py-12">
            <ActivityIndicator color="#00D4AA" />
          </View>
        ) : links.length === 0 ? (
          <View className="items-center py-12">
            <View className="w-20 h-20 rounded-full bg-primary-500/10 items-center justify-center mb-5">
              <Ionicons name="share-social-outline" size={36} color="#00D4AA" />
            </View>
            <Text className="text-[#E8EDF5] font-sansMedium text-base mb-2">No Active Share Links</Text>
            <Text className="text-[#526380] text-sm text-center px-6 leading-5">
              Create a share link to give your doctor, caregiver, or family member read-only access to your health data.
            </Text>
            <TouchableOpacity
              onPress={() => setShowModal(true)}
              className="mt-5 bg-primary-500 rounded-2xl px-6 py-3"
              activeOpacity={0.8}
            >
              <Text className="text-obsidian-900 font-sansMedium">Create First Share Link</Text>
            </TouchableOpacity>
          </View>
        ) : (
          links.map((link) => (
            <ShareCard key={link.id} link={link} onRevoke={(id) => revoke(id)} />
          ))
        )}
      </ScrollView>

      {showModal && (
        <CreateShareModal
          onClose={() => setShowModal(false)}
          onCreate={(req) => create(req)}
        />
      )}
    </View>
  );
}
