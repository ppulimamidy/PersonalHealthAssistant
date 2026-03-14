'use client';

import { useState, useEffect } from 'react';
import { healthTwinService } from '@/services/healthTwin';
import { HealthTwinProfileCard } from '@/components/health-twin/HealthTwinProfile';
import { SimulationCard } from '@/components/health-twin/SimulationCard';
import { GoalCard } from '@/components/health-twin/GoalCard';
import type { HealthTwinProfile, HealthTwinSimulation, HealthTwinGoal } from '@/types';
import toast from 'react-hot-toast';
import { Brain, Plus, Target, Loader2 } from 'lucide-react';

type Tab = 'overview' | 'simulations' | 'goals';

export default function HealthTwinPage() {
  const [profile, setProfile] = useState<HealthTwinProfile | null>(null);
  const [simulations, setSimulations] = useState<HealthTwinSimulation[]>([]);
  const [goals, setGoals] = useState<HealthTwinGoal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [proRequired, setProRequired] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setIsLoading(true);
    setProRequired(false);
    try {
      const [profileData, simsData, goalsData] = await Promise.all([
        healthTwinService.getHealthTwinProfile(),
        healthTwinService.getSimulations().catch(() => []),
        healthTwinService.getHealthTwinGoals().catch(() => []),
      ]);
      setProfile(profileData);
      setSimulations(simsData);
      setGoals(goalsData);
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } };
      if (err?.response?.status === 403) {
        setProRequired(true);
      } else {
        const msg = err?.response?.data?.detail || 'Failed to load health twin data.';
        toast.error(msg);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshProfile = async () => {
    setIsRefreshing(true);
    try {
      const updated = await healthTwinService.getHealthTwinProfile();
      setProfile(updated);
      toast.success('Profile refreshed');
    } catch {
      toast.error('Failed to refresh profile');
    } finally {
      setIsRefreshing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <Loader2
            className="w-8 h-8 animate-spin"
            style={{ color: '#00D4AA' }}
          />
          <p className="text-sm" style={{ color: '#526380' }}>
            Loading your health twin…
          </p>
        </div>
      </div>
    );
  }

  if (proRequired) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6"
          style={{
            backgroundColor: 'rgba(0,212,170,0.08)',
            border: '1px solid rgba(0,212,170,0.15)',
          }}
        >
          <Brain className="w-8 h-8" style={{ color: '#00D4AA' }} />
        </div>
        <div
          className="text-xs font-semibold uppercase tracking-widest mb-3"
          style={{ color: '#00D4AA' }}
        >
          Pro+ Required
        </div>
        <h2 className="text-xl font-bold mb-3" style={{ color: '#E8EDF5' }}>
          Health Twin
        </h2>
        <p
          className="text-sm max-w-sm leading-relaxed mb-6"
          style={{ color: '#526380' }}
        >
          Health Twin requires a Pro+ subscription. Upgrade to access digital twin
          modeling, what-if simulations, and health trajectory predictions.
        </p>
        <a
          href="/billing"
          className="px-6 py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-90"
          style={{
            background: 'linear-gradient(135deg, #00D4AA, #00A8BF)',
            color: '#080B10',
          }}
        >
          Upgrade to Pro+
        </a>
      </div>
    );
  }

  const TABS: { key: Tab; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'simulations', label: `Simulations${simulations.length ? ` (${simulations.length})` : ''}` },
    { key: 'goals', label: `Goals${goals.length ? ` (${goals.length})` : ''}` },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1" style={{ color: '#E8EDF5' }}>
          Simulate Changes
        </h1>
        <p className="text-sm" style={{ color: '#526380' }}>
          What if you changed something? Explore how lifestyle adjustments affect your health.
        </p>
      </div>

      {/* Tab bar */}
      <div
        className="flex gap-1 mb-6 p-1 rounded-xl"
        style={{
          backgroundColor: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all"
            style={{
              backgroundColor: activeTab === tab.key ? '#00D4AA' : 'transparent',
              color: activeTab === tab.key ? '#080B10' : '#526380',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview — profile card */}
      {activeTab === 'overview' && profile && (
        <HealthTwinProfileCard
          profile={profile}
          onRefresh={handleRefreshProfile}
          refreshing={isRefreshing}
        />
      )}

      {/* Simulations */}
      {activeTab === 'simulations' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm" style={{ color: '#526380' }}>
              What-if scenarios and trajectory predictions
            </p>
            <button
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all"
              style={{
                backgroundColor: 'rgba(0,212,170,0.10)',
                color: '#00D4AA',
                border: '1px solid rgba(0,212,170,0.20)',
              }}
              onClick={() =>
                toast('Simulation builder coming soon', { icon: '🧪' })
              }
            >
              <Plus className="w-4 h-4" />
              New Simulation
            </button>
          </div>

          {simulations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div
                className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4"
                style={{
                  backgroundColor: 'rgba(0,212,170,0.08)',
                  border: '1px solid rgba(0,212,170,0.15)',
                }}
              >
                <Brain className="w-6 h-6" style={{ color: '#00D4AA' }} />
              </div>
              <p className="text-sm font-medium mb-1" style={{ color: '#E8EDF5' }}>
                No simulations yet
              </p>
              <p className="text-xs" style={{ color: '#526380' }}>
                Create a what-if scenario to model health outcomes before making
                changes
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {simulations.map((sim) => (
                <SimulationCard key={sim.id} simulation={sim} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Goals */}
      {activeTab === 'goals' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm" style={{ color: '#526380' }}>
              Health goals tracked by your digital twin
            </p>
            <button
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all"
              style={{
                backgroundColor: 'rgba(0,212,170,0.10)',
                color: '#00D4AA',
                border: '1px solid rgba(0,212,170,0.20)',
              }}
              onClick={() => toast('Goal builder coming soon', { icon: '🎯' })}
            >
              <Plus className="w-4 h-4" />
              New Goal
            </button>
          </div>

          {goals.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div
                className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4"
                style={{
                  backgroundColor: 'rgba(0,212,170,0.08)',
                  border: '1px solid rgba(0,212,170,0.15)',
                }}
              >
                <Target className="w-6 h-6" style={{ color: '#00D4AA' }} />
              </div>
              <p className="text-sm font-medium mb-1" style={{ color: '#E8EDF5' }}>
                No goals yet
              </p>
              <p className="text-xs" style={{ color: '#526380' }}>
                Set health goals to track progress with AI-powered predictions
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {goals.map((goal) => (
                <GoalCard key={goal.id} goal={goal} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
