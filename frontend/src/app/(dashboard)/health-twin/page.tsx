'use client';

import { useState, useEffect } from 'react';
import { Plus, Brain, Target, History } from 'lucide-react';
import { healthTwinService } from '@/services/healthTwin';
import {
  HealthTwinProfile,
  HealthTwinSimulation,
  HealthTwinGoal,
} from '@/types';
import { HealthTwinProfileCard } from '@/components/health-twin/HealthTwinProfile';
import { SimulationCard } from '@/components/health-twin/SimulationCard';
import { GoalCard } from '@/components/health-twin/GoalCard';

export default function HealthTwinPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [profile, setProfile] = useState<HealthTwinProfile | null>(null);
  const [simulations, setSimulations] = useState<HealthTwinSimulation[]>([]);
  const [goals, setGoals] = useState<HealthTwinGoal[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'simulations' | 'goals'>('overview');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profileData, simulationsData, goalsData] = await Promise.all([
        healthTwinService.getHealthTwinProfile(),
        healthTwinService.getSimulations(),
        healthTwinService.getHealthTwinGoals('active'),
      ]);

      setProfile(profileData);
      setSimulations(simulationsData);
      setGoals(goalsData);
    } catch (error) {
      console.error('Error loading health twin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshProfile = async () => {
    setRefreshing(true);
    try {
      const refreshedProfile = await healthTwinService.refreshHealthTwinProfile();
      setProfile(refreshedProfile);
    } catch (error) {
      console.error('Error refreshing profile:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleUpdateMilestone = async (goalId: string, milestoneIndex: number, completed: boolean) => {
    try {
      const updatedGoal = await healthTwinService.updateGoalMilestone(goalId, milestoneIndex, completed);
      setGoals(goals.map(g => g.id === goalId ? updatedGoal : g));
    } catch (error) {
      console.error('Error updating milestone:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            Health Twin
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            Your digital health twin predicts and optimizes your health trajectory
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            activeTab === 'overview'
              ? 'border-primary-600 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <History className="w-4 h-4" />
            Overview
          </div>
        </button>
        <button
          onClick={() => setActiveTab('simulations')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            activeTab === 'simulations'
              ? 'border-primary-600 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Simulations ({simulations.length})
          </div>
        </button>
        <button
          onClick={() => setActiveTab('goals')}
          className={`px-4 py-2 font-medium transition-colors border-b-2 ${
            activeTab === 'goals'
              ? 'border-primary-600 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            Goals ({goals.length})
          </div>
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {profile && (
            <HealthTwinProfileCard
              profile={profile}
              onRefresh={handleRefreshProfile}
              refreshing={refreshing}
            />
          )}

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg">
              <Brain className="w-8 h-8 text-blue-600 dark:text-blue-400 mb-3" />
              <h3 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-1">
                Active Simulations
              </h3>
              <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">
                {simulations.filter(s => s.status === 'active').length}
              </p>
            </div>

            <div className="p-6 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg">
              <Target className="w-8 h-8 text-green-600 dark:text-green-400 mb-3" />
              <h3 className="text-sm font-medium text-green-900 dark:text-green-200 mb-1">
                Active Goals
              </h3>
              <p className="text-3xl font-bold text-green-900 dark:text-green-100">
                {goals.length}
              </p>
            </div>

            <div className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg">
              <History className="w-8 h-8 text-purple-600 dark:text-purple-400 mb-3" />
              <h3 className="text-sm font-medium text-purple-900 dark:text-purple-200 mb-1">
                Avg. Success Rate
              </h3>
              <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">
                {goals.length > 0
                  ? Math.round((goals.reduce((sum, g) => sum + g.success_probability, 0) / goals.length) * 100)
                  : 0}%
              </p>
            </div>
          </div>

          {/* Recent Simulations */}
          {simulations.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-4">
                Recent Simulations
              </h2>
              <div className="grid gap-4">
                {simulations.slice(0, 3).map((simulation) => (
                  <SimulationCard key={simulation.id} simulation={simulation} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'simulations' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
              What-If Simulations
            </h2>
            <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              <Plus className="w-5 h-5" />
              New Simulation
            </button>
          </div>

          {simulations.length === 0 ? (
            <div className="text-center py-12">
              <Brain className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
                No simulations yet
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">
                Create your first simulation to explore health scenarios
              </p>
              <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                Create Simulation
              </button>
            </div>
          ) : (
            <div className="grid gap-4">
              {simulations.map((simulation) => (
                <SimulationCard key={simulation.id} simulation={simulation} />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'goals' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
              Health Goals
            </h2>
            <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              <Plus className="w-5 h-5" />
              New Goal
            </button>
          </div>

          {goals.length === 0 ? (
            <div className="text-center py-12">
              <Target className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
                No active goals
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">
                Set your first health goal to track progress
              </p>
              <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                Create Goal
              </button>
            </div>
          ) : (
            <div className="grid gap-4">
              {goals.map((goal) => (
                <GoalCard
                  key={goal.id}
                  goal={goal}
                  onUpdateMilestone={(milestoneIndex, completed) =>
                    handleUpdateMilestone(goal.id, milestoneIndex, completed)
                  }
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
