'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Check,
  X,
  RefreshCw,
  Wifi,
  Activity,
  Moon,
  Heart,
  Droplets,
} from 'lucide-react';
import { ouraService } from '@/services/oura';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import toast from 'react-hot-toast';

// ── Device card ───────────────────────────────────────────────────────────────

interface DeviceCardProps {
  name: string;
  description: string;
  dataTypes: string[];
  icon: React.ReactNode;
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
  connected = false,
  comingSoon = false,
  onConnect,
  onSync,
  onDisconnect,
  isSyncing,
  isConnecting,
  isDisconnecting,
}: DeviceCardProps) {
  return (
    <div
      className="rounded-xl p-5 flex flex-col gap-4"
      style={{
        backgroundColor: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
        opacity: comingSoon ? 0.65 : 1,
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}
          >
            {icon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-[#E8EDF5]">{name}</p>
              {comingSoon && (
                <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-[#526380]/20 text-[#526380] leading-none">
                  Coming soon
                </span>
              )}
              {connected && (
                <span className="flex items-center gap-1 text-[10px] text-green-400">
                  <Check className="w-3 h-3" />
                  Connected
                </span>
              )}
              {!connected && !comingSoon && (
                <span className="flex items-center gap-1 text-[10px] text-[#526380]">
                  <X className="w-3 h-3" />
                  Not connected
                </span>
              )}
            </div>
            <p className="text-xs text-[#526380] mt-0.5">{description}</p>
          </div>
        </div>
      </div>

      {/* Data types */}
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

      {/* Action buttons */}
      {!comingSoon && (
        <div className="flex items-center gap-2">
          {connected ? (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={onSync}
                isLoading={isSyncing}
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                Sync
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={onDisconnect}
                isLoading={isDisconnecting}
              >
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
    </div>
  );
}

// ── Oura ring SVG icon ────────────────────────────────────────────────────────

const OuraIcon = () => (
  <svg viewBox="0 0 24 24" className="w-6 h-6 text-[#8B97A8]" fill="currentColor">
    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
    <circle cx="12" cy="12" r="4" />
  </svg>
);

// ── Main component ────────────────────────────────────────────────────────────

export function DeviceHub() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const { setOuraConnection } = useAuthStore();
  const queryClient = useQueryClient();

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
      queryClient.invalidateQueries({ queryKey: ['oura-connection'] });
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
        window.location.href = response.auth_url;
      } else {
        toast.error('Oura integration not configured');
        setIsConnecting(false);
      }
    } catch {
      toast.error('Failed to initiate connection');
      setIsConnecting(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Devices</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Connect wearables and health apps to enrich your insights
        </p>
      </div>

      <div className="space-y-8 max-w-2xl">
        {/* Connected / active devices */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-[#3D4F66] mb-3">
            Available Devices
          </h2>
          <div className="space-y-3">
            <DeviceCard
              name="Oura Ring"
              description="Sleep, activity & readiness tracking"
              dataTypes={['Sleep', 'Activity', 'Readiness', 'HRV', 'Temperature']}
              icon={<OuraIcon />}
              connected={!!connectionStatus?.is_active}
              onConnect={handleConnectOura}
              onSync={handleSync}
              onDisconnect={() => disconnectMutation.mutate()}
              isSyncing={isSyncing}
              isConnecting={isConnecting}
              isDisconnecting={disconnectMutation.isPending}
            />
          </div>
        </section>

        {/* Coming soon */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-[#3D4F66] mb-3">
            More Devices
          </h2>
          <div className="space-y-3">
            <DeviceCard
              name="Apple Health"
              description="Sync data from iPhone and Apple Watch"
              dataTypes={['Steps', 'Heart Rate', 'Sleep', 'Workouts', 'Blood Oxygen']}
              icon={<Heart className="w-6 h-6 text-[#8B97A8]" />}
              comingSoon
            />
            <DeviceCard
              name="Garmin Connect"
              description="Import fitness and health metrics from Garmin devices"
              dataTypes={['GPS', 'Heart Rate', 'VO2 Max', 'Stress', 'Body Battery']}
              icon={<Activity className="w-6 h-6 text-[#8B97A8]" />}
              comingSoon
            />
            <DeviceCard
              name="WHOOP"
              description="Recovery, strain, and sleep coaching"
              dataTypes={['Recovery', 'Strain', 'Sleep', 'HRV', 'Respiratory Rate']}
              icon={<Wifi className="w-6 h-6 text-[#8B97A8]" />}
              comingSoon
            />
            <DeviceCard
              name="FreeStyle Libre"
              description="Continuous glucose monitoring"
              dataTypes={['Blood Glucose', 'Glucose Trends', 'Time in Range']}
              icon={<Droplets className="w-6 h-6 text-[#8B97A8]" />}
              comingSoon
            />
          </div>
        </section>
      </div>
    </div>
  );
}
