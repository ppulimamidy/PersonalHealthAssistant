'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  RefreshCw,
  Activity,
  Heart,
  Watch,
  Wifi,
  Smartphone,
  Plus,
  Radio,
} from 'lucide-react';
import { ouraService } from '@/services/oura';
import { api } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import toast from 'react-hot-toast';

// ── Device card (full-width, for "Your Devices") ──────────────────────────────

interface DeviceCardProps {
  name: string;
  description: string;
  dataTypes: string[];
  icon: React.ReactNode;
  accentColor: string;
  connected?: boolean;
  comingSoon?: boolean;
  onConnect?: () => void;
  onSync?: () => void;
  onDisconnect?: () => void;
  isSyncing?: boolean;
  isConnecting?: boolean;
  isDisconnecting?: boolean;
}

function DeviceCard({
  name,
  description,
  dataTypes,
  icon,
  accentColor,
  connected = false,
  comingSoon = false,
  onConnect,
  onSync,
  onDisconnect,
  isSyncing,
  isConnecting,
  isDisconnecting,
}: Readonly<DeviceCardProps>) {
  return (
    <div
      className="rounded-2xl p-5 flex flex-col gap-4"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: `${accentColor}18` }}
          >
            {icon}
          </div>
          <div>
            <p className="text-sm font-semibold text-[#E8EDF5]">{name}</p>
            <p className="text-xs text-[#526380] mt-0.5">{description}</p>
          </div>
        </div>
        {/* Status badge */}
        {connected && (
          <span className="flex items-center gap-1.5 text-[11px] font-medium text-green-400 shrink-0">
            <span className="w-2 h-2 rounded-full bg-green-400" />{"Connected"}
          </span>
        )}
        {!connected && comingSoon && (
          <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-[#1E2A3B] text-[#526380] leading-none shrink-0">
            {"Coming soon"}
          </span>
        )}
        {!connected && !comingSoon && (
          <span className="flex items-center gap-1.5 text-[11px] text-[#526380] shrink-0">
            <span className="w-2 h-2 rounded-full bg-[#3A4A5C]" />{"Not linked"}
          </span>
        )}
      </div>

      {/* Data type chips */}
      <div className="flex flex-wrap gap-1.5">
        {dataTypes.map((d) => (
          <span
            key={d}
            className="px-2 py-0.5 rounded-full text-[10px] text-[#526380]"
            style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            {d}
          </span>
        ))}
      </div>

      {/* Actions */}
      {!comingSoon && (
        <div className="flex items-center gap-2">
          {connected ? (
            <>
              <Button variant="outline" size="sm" onClick={onSync} isLoading={isSyncing}>
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                Sync Now
              </Button>
              <Button variant="ghost" size="sm" onClick={onDisconnect} isLoading={isDisconnecting}>
                Disconnect
              </Button>
            </>
          ) : (
            <Button size="sm" onClick={onConnect} isLoading={isConnecting}>
              Connect
            </Button>
          )}
        </div>
      )}

      {/* Coming soon — disabled connect */}
      {comingSoon && (
        <div>
          <button
            disabled
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-[#526380] cursor-not-allowed"
            style={{ backgroundColor: '#1E2A3B', border: '1px solid #2A3A4E' }}
          >
            {"Connect "}
            <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full bg-[#526380]/20 text-[#526380] leading-none">
              {"Soon"}
            </span>
          </button>
        </div>
      )}
    </div>
  );
}

// ── Native health metrics grid ────────────────────────────────────────────────

const NATIVE_METRICS = [
  { key: 'steps',              label: 'Steps',        format: (v: number) => v.toLocaleString() },
  { key: 'sleep',              label: 'Sleep',        format: (v: number) => `${v.toFixed(1)}h` },
  { key: 'resting_heart_rate', label: 'Heart Rate',   format: (v: number) => `${Math.round(v)} bpm` },
  { key: 'hrv_sdnn',           label: 'HRV',          format: (v: number) => `${v.toFixed(1)} ms` },
  { key: 'spo2',               label: 'SpO₂',         format: (v: number) => `${v.toFixed(1)}%` },
  { key: 'respiratory_rate',   label: 'Resp. Rate',   format: (v: number) => `${v.toFixed(1)}/min` },
  { key: 'active_calories',    label: 'Active Cal.',  format: (v: number) => `${Math.round(v)} kcal` },
  { key: 'workout',            label: 'Workout',      format: (v: number) => `${Math.round(v)} min` },
  { key: 'vo2_max',            label: 'VO₂ Max',      format: (v: number) => `${v.toFixed(1)} mL/kg/min` },
];

interface MetricSummary {
  latest_value: number | null;
  avg_7d: number | null;
  avg_30d: number | null;
  avg_90d: number | null;
  trend_7d: 'up' | 'down' | 'stable' | null;
  is_anomalous: boolean;
  anomaly_severity: 'low' | 'medium' | 'high' | null;
  anomaly_detail: string | null;
}

type Summaries = Record<string, MetricSummary>;

const TREND_ARROW: Record<string, { icon: string; color: string }> = {
  up:     { icon: '↑', color: '#6EE7B7' },
  down:   { icon: '↓', color: '#F87171' },
  stable: { icon: '→', color: '#526380' },
};

function NativeMetricsGrid({
  recentData,
  summaries,
}: {
  recentData: Record<string, number>;
  summaries?: Summaries | null;
}) {
  const available = NATIVE_METRICS.filter(
    (m) => recentData[m.key] != null || summaries?.[m.key]?.latest_value != null
  );
  if (available.length === 0) return null;

  return (
    <div className="grid grid-cols-3 gap-2 pt-1">
      {available.map((m) => {
        const value = recentData[m.key] ?? summaries?.[m.key]?.latest_value;
        const summary = summaries?.[m.key];
        const trend = summary?.trend_7d;
        const trendInfo = trend ? TREND_ARROW[trend] : null;

        return (
          <div
            key={m.key}
            className="rounded-xl px-3 py-2.5 flex flex-col gap-0.5"
            style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            <div className="flex items-center justify-between">
              <p className="text-[10px] text-[#526380]">{m.label}</p>
              {trendInfo && (
                <span className="text-[10px] font-bold" style={{ color: trendInfo.color }}>
                  {trendInfo.icon}
                </span>
              )}
            </div>
            <p className="text-sm font-semibold text-[#E8EDF5]">
              {value != null ? m.format(value) : '—'}
            </p>
            {(summary?.avg_7d != null || summary?.avg_30d != null || summary?.avg_90d != null) && (
              <div className="flex gap-2 mt-0.5">
                {summary?.avg_7d != null && (
                  <p className="text-[9px] text-[#526380]">7d: {m.format(summary.avg_7d)}</p>
                )}
                {summary?.avg_30d != null && (
                  <p className="text-[9px] text-[#526380]">30d: {m.format(summary.avg_30d)}</p>
                )}
                {summary?.avg_90d != null && (
                  <p className="text-[9px] text-[#526380]">90d: {m.format(summary.avg_90d)}</p>
                )}
              </div>
            )}
            {summary?.is_anomalous && (
              <p
                className="text-[9px] mt-0.5"
                style={{ color: summary.anomaly_severity === 'high' ? '#F87171' : '#F59E0B' }}
              >
                ⚠ {summary.anomaly_severity}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Per-source metrics panel ──────────────────────────────────────────────────

function SourceMetricsPanel({
  label,
  data,
  summaries,
  isLoading,
}: Readonly<{
  label: string;
  data: Record<string, number> | undefined;
  summaries?: Summaries | null;
  isLoading: boolean;
}>) {
  const hasData = (data && Object.keys(data).length > 0) || (summaries && Object.keys(summaries).length > 0);
  return (
    <div
      className="rounded-2xl p-5"
      style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
    >
      <p className="text-[11px] font-semibold uppercase tracking-widest text-[#526380] mb-3">{label}</p>
      {isLoading && <p className="text-xs text-[#526380]">Loading…</p>}
      {!isLoading && hasData && <NativeMetricsGrid recentData={data ?? {}} summaries={summaries} />}
      {!isLoading && !hasData && (
        <p className="text-xs text-[#526380]">No data yet — open the Vitalix mobile app and tap Sync.</p>
      )}
    </div>
  );
}

// ── Wearable grid tile (compact, for "Add a Wearable") ────────────────────────

function WearableTile({
  icon,
  label,
  accentColor,
}: Readonly<{
  icon: React.ReactNode;
  label: string;
  accentColor: string;
}>) {
  return (
    <div
      className="rounded-2xl p-4 flex flex-col items-center gap-2 cursor-default"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center"
        style={{ backgroundColor: `${accentColor}15` }}
      >
        {icon}
      </div>
      <p className="text-xs font-medium text-[#E8EDF5] text-center">{label}</p>
      <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full bg-[#1E2A3B] text-[#526380] leading-none">
        Soon
      </span>
    </div>
  );
}

// ── Oura ring icon ────────────────────────────────────────────────────────────

const OuraIcon = ({ color = '#8B97A8' }: { color?: string }) => (
  <svg viewBox="0 0 24 24" className="w-6 h-6" fill={color}>
    <circle cx="12" cy="12" r="10" fill="none" stroke={color} strokeWidth="2" />
    <circle cx="12" cy="12" r="4" />
  </svg>
);

// ── Main component ────────────────────────────────────────────────────────────

export function DeviceHub() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isDisconnectingHk, setIsDisconnectingHk] = useState(false);
  const [isDisconnectingHc, setIsDisconnectingHc] = useState(false);
  const { setOuraConnection } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: connectionStatus, refetch } = useQuery({
    queryKey: ['oura-connection'],
    queryFn: ouraService.getConnectionStatus,
  });

  const { data: nativeHealthStatus } = useQuery({
    queryKey: ['native-health-status'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/health-data/status');
      return data as {
        healthkit: { connected: boolean; last_sync: string | null };
        health_connect: { connected: boolean; last_sync: string | null };
      };
    },
  });

  const fetchRecent = async (source: string): Promise<Record<string, number>> => {
    try {
      const { data } = await api.get(`/api/v1/health-data/recent?source=${source}`);
      return (data ?? {}) as Record<string, number>;
    } catch {
      return {};
    }
  };

  const disconnectMutation = useMutation({
    mutationFn: ouraService.disconnect,
    onSuccess: () => {
      // Immediately clear the cache so the UI reflects disconnected state now
      queryClient.setQueryData(['oura-connection'], null);
      setOuraConnection(null);
      toast.success('Oura Ring disconnected');
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
    setIsConnecting(true);
    try {
      const response = await ouraService.getAuthUrl();
      if (response.sandbox_mode) {
        toast.success('Connected to Oura (Sandbox Mode)');
        setOuraConnection({ id: 'sandbox', user_id: 'sandbox', is_active: true, is_sandbox: true });
        refetch();
      } else if (response.auth_url) {
        globalThis.location.href = response.auth_url;
      } else {
        toast.error('Oura integration not configured');
        setIsConnecting(false);
      }
    } catch {
      toast.error('Failed to initiate connection');
      setIsConnecting(false);
    }
  };

  const handleNativeDisconnect = async (source: 'healthkit' | 'health_connect', setLoading: (v: boolean) => void) => {
    setLoading(true);
    try {
      await api.delete(`/api/v1/health-data/source/${source}`);
      queryClient.invalidateQueries({ queryKey: ['native-health-status'] });
      queryClient.invalidateQueries({ queryKey: ['native-health-recent', source] });
      toast.success(`${source === 'healthkit' ? 'Apple Health' : 'Health Connect'} disconnected`);
    } catch {
      toast.error('Failed to disconnect');
    } finally {
      setLoading(false);
    }
  };

  const handleNativeConnect = (sourceName: string, deviceName: string) => {
    toast(`Open the Vitalix app on your ${deviceName} and tap "Sync Now" to connect ${sourceName}.`, {
      icon: '📱',
      duration: 5000,
    });
  };

  const handleNativeSync = (deviceName: string) => {
    toast(`Open the Vitalix app on your ${deviceName} and tap "Sync Now" to pull the latest data.`, {
      icon: '🔄',
      duration: 4000,
    });
  };

  const ouraConnected   = !!connectionStatus?.is_active;
  const hkConnected     = !!nativeHealthStatus?.healthkit?.connected;
  const hcConnected     = !!nativeHealthStatus?.health_connect?.connected;
  const hkLastSync      = nativeHealthStatus?.healthkit?.last_sync ?? null;
  const hcLastSync      = nativeHealthStatus?.health_connect?.last_sync ?? null;

  const { data: hkRecentData, isLoading: isLoadingHk } = useQuery({
    queryKey: ['native-health-recent', 'healthkit'],
    queryFn: () => fetchRecent('healthkit'),
    enabled: hkConnected,
    staleTime: 0,
  });

  const { data: hcRecentData, isLoading: isLoadingHc } = useQuery({
    queryKey: ['native-health-recent', 'health_connect'],
    queryFn: () => fetchRecent('health_connect'),
    enabled: hcConnected,
    staleTime: 0,
  });

  const { data: summariesData } = useQuery({
    queryKey: ['health-summaries'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/api/v1/health-data/summaries');
        return data as Summaries;
      } catch {
        return null;
      }
    },
    enabled: hkConnected || hcConnected,
    staleTime: 60_000,
  });

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Health Devices</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Connect wearables and health apps to enrich your insights
        </p>
      </div>

      <div className="space-y-8 max-w-2xl">

        {/* ── YOUR DEVICES ──────────────────────────────────────────────── */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-[#3D4F66] mb-3">
            Your Devices
          </h2>
          <div className="space-y-3">
            {/* Oura Ring — live OAuth integration */}
            <DeviceCard
              name="Oura Ring"
              description="Sleep, activity & readiness tracking"
              dataTypes={['Sleep', 'Readiness', 'Activity', 'HRV', 'Temperature']}
              icon={<OuraIcon color={ouraConnected ? '#818CF8' : '#8B97A8'} />}
              accentColor="#818CF8"
              connected={ouraConnected}
              onConnect={handleConnectOura}
              onSync={handleSync}
              onDisconnect={() => disconnectMutation.mutate()}
              isSyncing={isSyncing}
              isConnecting={isConnecting}
              isDisconnecting={disconnectMutation.isPending}
            />

            {/* Apple Health (iOS) */}
            <DeviceCard
              name="Apple Health"
              description={hkConnected ? (hkLastSync ? `Synced from iPhone · last ${hkLastSync}` : 'Synced from iPhone') : 'Connect via the Vitalix iOS app'}
              dataTypes={['Steps', 'Sleep', 'Heart Rate', 'HRV', 'SpO₂', 'Workouts', 'VO₂ Max']}
              icon={<Heart className="w-6 h-6" style={{ color: '#F87171' }} />}
              accentColor="#F87171"
              connected={hkConnected}
              onConnect={() => handleNativeConnect('Apple Health', 'iPhone')}
              onSync={() => handleNativeSync('iPhone')}
              onDisconnect={() => handleNativeDisconnect('healthkit', setIsDisconnectingHk)}
              isDisconnecting={isDisconnectingHk}
            />
            {hkConnected && (
              <SourceMetricsPanel label="Health metrics from iPhone" data={hkRecentData} summaries={summariesData} isLoading={isLoadingHk} />
            )}

            {/* Health Connect (Android) */}
            <DeviceCard
              name="Health Connect"
              description={hcConnected ? (hcLastSync ? `Synced from Android · last ${hcLastSync}` : 'Synced from Android') : 'Connect via the Vitalix Android app'}
              dataTypes={['Steps', 'Sleep', 'Heart Rate', 'HRV', 'SpO₂', 'Workouts', 'VO₂ Max']}
              icon={<Smartphone className="w-6 h-6" style={{ color: '#34D399' }} />}
              accentColor="#34D399"
              connected={hcConnected}
              onConnect={() => handleNativeConnect('Health Connect', 'Android phone')}
              onSync={() => handleNativeSync('Android phone')}
              onDisconnect={() => handleNativeDisconnect('health_connect', setIsDisconnectingHc)}
              isDisconnecting={isDisconnectingHc}
            />
            {hcConnected && (
              <SourceMetricsPanel label="Health metrics from Android" data={hcRecentData} summaries={summariesData} isLoading={isLoadingHc} />
            )}
          </div>
        </section>

        {/* ── ADD A WEARABLE ────────────────────────────────────────────── */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-[#3D4F66] mb-3">
            Add a Wearable
          </h2>
          <div className="grid grid-cols-3 gap-3">
            <WearableTile
              icon={<Watch className="w-5 h-5" style={{ color: '#00D4AA' }} />}
              label="Garmin"
              accentColor="#00D4AA"
            />
            <WearableTile
              icon={<Activity className="w-5 h-5" style={{ color: '#F5A623' }} />}
              label="Whoop"
              accentColor="#F5A623"
            />
            <WearableTile
              icon={<Radio className="w-5 h-5" style={{ color: '#60A5FA' }} />}
              label="Fitbit"
              accentColor="#60A5FA"
            />
            <WearableTile
              icon={<Smartphone className="w-5 h-5" style={{ color: '#6EE7B7' }} />}
              label="Samsung"
              accentColor="#6EE7B7"
            />
            <WearableTile
              icon={<Wifi className="w-5 h-5" style={{ color: '#F87171' }} />}
              label="Polar"
              accentColor="#F87171"
            />
            <WearableTile
              icon={<Plus className="w-5 h-5" style={{ color: '#818CF8' }} />}
              label="More"
              accentColor="#818CF8"
            />
          </div>
        </section>

        {/* Privacy note */}
        <div
          className="flex gap-3 rounded-xl px-4 py-3"
          style={{ backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}
        >
          <svg className="w-4 h-4 text-[#526380] mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <p className="text-xs text-[#526380] leading-relaxed">
            Your health data is encrypted and stored privately. It is never shared with third parties.
            You can delete your data at any time from Settings.
          </p>
        </div>

      </div>
    </div>
  );
}
