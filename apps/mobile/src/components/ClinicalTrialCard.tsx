/**
 * Clinical Trial Card — shows trial info from ClinicalTrials.gov
 * with phase badge, status, sponsor, and eligibility check.
 */

import { useState } from 'react';
import { View, Text, TouchableOpacity, Linking } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Trial {
  nct_id: string;
  title: string;
  phase: string;
  status: string;
  summary: string;
  sponsor: string;
  enrollment?: number;
  locations: string[];
  eligibility_criteria: string;
  start_date?: string;
  completion_date?: string;
}

interface Props {
  trial: Trial;
}

const PHASE_COLORS: Record<string, string> = {
  PHASE1: '#F5A623',
  PHASE2: '#60A5FA',
  PHASE3: '#6EE7B7',
  PHASE4: '#818CF8',
};

const STATUS_COLORS: Record<string, string> = {
  RECRUITING: '#6EE7B7',
  ACTIVE_NOT_RECRUITING: '#F5A623',
  COMPLETED: '#526380',
  NOT_YET_RECRUITING: '#60A5FA',
};

export default function ClinicalTrialCard({ trial }: Readonly<Props>) {
  const [expanded, setExpanded] = useState(false);

  const phaseLabel = trial.phase?.replace('PHASE', 'Phase ').replace(',', ' / ') || 'Phase N/A';
  const phaseColor = Object.entries(PHASE_COLORS).find(([k]) => trial.phase?.includes(k))?.[1] ?? '#526380';
  const statusColor = STATUS_COLORS[trial.status] ?? '#526380';
  const statusLabel = trial.status?.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()) ?? '';

  return (
    <TouchableOpacity
      onPress={() => setExpanded((e) => !e)}
      className="bg-surface-raised border border-surface-border rounded-xl p-4 mb-2"
      activeOpacity={0.8}
    >
      {/* Header */}
      <View className="flex-row items-start gap-2 mb-1">
        <View className="rounded px-1.5 py-0.5" style={{ backgroundColor: `${phaseColor}15` }}>
          <Text className="text-[9px] font-sansMedium" style={{ color: phaseColor }}>{phaseLabel}</Text>
        </View>
        <View className="rounded px-1.5 py-0.5" style={{ backgroundColor: `${statusColor}15` }}>
          <Text className="text-[9px] font-sansMedium" style={{ color: statusColor }}>{statusLabel}</Text>
        </View>
      </View>

      {/* Title */}
      <Text className="text-[#E8EDF5] text-sm font-sansMedium leading-5 mb-1" numberOfLines={expanded ? undefined : 2}>
        {trial.title}
      </Text>

      {/* Sponsor */}
      <Text className="text-[#526380] text-[10px]">{trial.sponsor}</Text>

      {expanded && (
        <View className="mt-3 pt-3 border-t border-surface-border">
          {/* Summary */}
          {trial.summary && (
            <Text className="text-[#8B9BB4] text-xs leading-5 mb-2">{trial.summary}</Text>
          )}

          {/* Locations */}
          {trial.locations?.length > 0 && (
            <View className="mb-2">
              <Text className="text-[#526380] text-[10px] font-sansMedium mb-0.5">Locations</Text>
              {trial.locations.map((loc, i) => (
                <Text key={i} className="text-[#8B9BB4] text-[10px]">• {loc}</Text>
              ))}
            </View>
          )}

          {/* Enrollment */}
          {trial.enrollment && (
            <Text className="text-[#526380] text-[10px] mb-1">Enrollment: {trial.enrollment} participants</Text>
          )}

          {/* Dates */}
          {(trial.start_date || trial.completion_date) && (
            <Text className="text-[#3D4F66] text-[10px] mb-2">
              {trial.start_date && `Started: ${trial.start_date}`}
              {trial.start_date && trial.completion_date && ' · '}
              {trial.completion_date && `Est. completion: ${trial.completion_date}`}
            </Text>
          )}

          {/* View on ClinicalTrials.gov */}
          <TouchableOpacity
            onPress={() => Linking.openURL(`https://clinicaltrials.gov/study/${trial.nct_id}`)}
            className="mt-1 flex-row items-center gap-1 self-start"
            activeOpacity={0.7}
          >
            <Ionicons name="open-outline" size={12} color="#818CF8" />
            <Text className="text-[#818CF8] text-xs font-sansMedium">{trial.nct_id} — View on ClinicalTrials.gov</Text>
          </TouchableOpacity>
        </View>
      )}
    </TouchableOpacity>
  );
}
