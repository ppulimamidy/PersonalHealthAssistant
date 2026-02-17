import { api } from './api';
import type {
  HealthTwinProfile,
  HealthTwinSimulation,
  HealthTwinSnapshot,
  HealthTwinGoal,
  CreateSimulationRequest,
  CreateHealthTwinGoalRequest,
} from '@/types';

export const healthTwinService = {
  // Get health twin profile
  async getHealthTwinProfile(): Promise<HealthTwinProfile> {
    const response = await api.get<HealthTwinProfile>('/health-twin/profile');
    return response.data;
  },

  // Refresh health twin profile (recompute)
  async refreshHealthTwinProfile(): Promise<HealthTwinProfile> {
    const response = await api.post<HealthTwinProfile>('/health-twin/profile/refresh');
    return response.data;
  },

  // Get simulations
  async getSimulations(status?: 'draft' | 'active' | 'completed'): Promise<HealthTwinSimulation[]> {
    const url = status
      ? `/health-twin/simulations?status=${status}`
      : '/health-twin/simulations';

    const response = await api.get<HealthTwinSimulation[]>(url);
    return response.data;
  },

  // Get single simulation
  async getSimulation(id: string): Promise<HealthTwinSimulation> {
    const response = await api.get<HealthTwinSimulation>(`/health-twin/simulations/${id}`);
    return response.data;
  },

  // Create new simulation
  async createSimulation(data: CreateSimulationRequest): Promise<HealthTwinSimulation> {
    const response = await api.post<HealthTwinSimulation>('/health-twin/simulations', data);
    return response.data;
  },

  // Update simulation
  async updateSimulation(
    id: string,
    data: Partial<CreateSimulationRequest>
  ): Promise<HealthTwinSimulation> {
    const response = await api.put<HealthTwinSimulation>(`/health-twin/simulations/${id}`, data);
    return response.data;
  },

  // Delete simulation
  async deleteSimulation(id: string): Promise<void> {
    await api.delete(`/health-twin/simulations/${id}`);
  },

  // Get snapshots
  async getSnapshots(limit?: number): Promise<HealthTwinSnapshot[]> {
    const url = limit
      ? `/health-twin/snapshots?limit=${limit}`
      : '/health-twin/snapshots';

    const response = await api.get<HealthTwinSnapshot[]>(url);
    return response.data;
  },

  // Create snapshot
  async createSnapshot(notes?: string): Promise<HealthTwinSnapshot> {
    const response = await api.post<HealthTwinSnapshot>('/health-twin/snapshots', { notes });
    return response.data;
  },

  // Get health twin goals
  async getHealthTwinGoals(status?: 'active' | 'achieved' | 'abandoned'): Promise<HealthTwinGoal[]> {
    const url = status
      ? `/health-twin/goals?status=${status}`
      : '/health-twin/goals';

    const response = await api.get<HealthTwinGoal[]>(url);
    return response.data;
  },

  // Get single goal
  async getHealthTwinGoal(id: string): Promise<HealthTwinGoal> {
    const response = await api.get<HealthTwinGoal>(`/health-twin/goals/${id}`);
    return response.data;
  },

  // Create new goal
  async createHealthTwinGoal(data: CreateHealthTwinGoalRequest): Promise<HealthTwinGoal> {
    const response = await api.post<HealthTwinGoal>('/health-twin/goals', data);
    return response.data;
  },

  // Update goal
  async updateHealthTwinGoal(
    id: string,
    data: Partial<CreateHealthTwinGoalRequest>
  ): Promise<HealthTwinGoal> {
    const response = await api.put<HealthTwinGoal>(`/health-twin/goals/${id}`, data);
    return response.data;
  },

  // Delete goal
  async deleteHealthTwinGoal(id: string): Promise<void> {
    await api.delete(`/health-twin/goals/${id}`);
  },

  // Update goal milestone
  async updateGoalMilestone(
    goalId: string,
    milestoneIndex: number,
    completed: boolean
  ): Promise<HealthTwinGoal> {
    const response = await api.post<HealthTwinGoal>(
      `/health-twin/goals/${goalId}/milestones/${milestoneIndex}`,
      { completed }
    );
    return response.data;
  },
};
