// User types
export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  created_at: string;
}

export type Gender = 'male' | 'female' | 'other' | 'prefer_not_to_say';

export interface UserProfile {
  age?: number;
  gender?: Gender;
  weight_kg?: number;
  profile_completed?: boolean;
}

// Oura data types
export interface OuraConnection {
  id: string;
  user_id: string;
  is_active: boolean;
  is_sandbox?: boolean;
  connected_at?: string;
  expires_at?: string;
  // Only present in production mode
  access_token?: string;
  refresh_token?: string;
}

export interface SleepData {
  id: string;
  date: string;
  total_sleep_duration: number;
  deep_sleep_duration: number;
  rem_sleep_duration: number;
  light_sleep_duration: number;
  sleep_efficiency: number;
  sleep_score: number;
  bedtime_start: string;
  bedtime_end: string;
}

export interface ActivityData {
  id: string;
  date: string;
  steps: number;
  active_calories: number;
  total_calories: number;
  activity_score: number;
  high_activity_time: number;
  medium_activity_time: number;
  low_activity_time: number;
  sedentary_time: number;
}

export interface ReadinessData {
  id: string;
  date: string;
  readiness_score: number;
  temperature_deviation: number;
  hrv_balance: number;
  recovery_index: number;
  resting_heart_rate: number;
}

export interface HeartRateData {
  timestamp: string;
  bpm: number;
  source: string;
}

// Timeline entry combining all data
export interface TimelineEntry {
  date: string;
  sleep?: SleepData;
  activity?: ActivityData;
  readiness?: ReadinessData;
  insights?: AIInsight[];
}

// AI Insights types
export interface AIInsight {
  id: string;
  type: 'trend' | 'recommendation' | 'alert';
  category: 'sleep' | 'activity' | 'readiness' | 'general';
  title: string;
  summary: string;
  explanation: string;
  confidence: number;
  data_points: DataPoint[];
  created_at: string;
}

export interface DataPoint {
  metric: string;
  value: number;
  date: string;
  trend: 'up' | 'down' | 'stable';
}

// Doctor Visit Prep types
export interface DoctorPrepReport {
  id: string;
  user_id: string;
  generated_at: string;
  date_range: {
    start: string;
    end: string;
  };
  summary: {
    overall_health_score: number;
    key_metrics: KeyMetric[];
    trends: TrendSummary[];
    concerns: string[];
    improvements: string[];
  };
  detailed_data: {
    sleep: SleepSummary;
    activity: ActivitySummary;
    readiness: ReadinessSummary;
  };
  ai_insights: AIInsight[];
}

export interface KeyMetric {
  name: string;
  value: number;
  unit: string;
  status: 'excellent' | 'good' | 'moderate' | 'poor';
  comparison_to_average: number;
}

export interface TrendSummary {
  metric: string;
  direction: 'improving' | 'declining' | 'stable';
  percentage_change: number;
  period: string;
}

export interface SleepSummary {
  average_duration: number;
  average_score: number;
  average_efficiency: number;
  best_night: string;
  worst_night: string;
}

export interface ActivitySummary {
  average_steps: number;
  average_active_calories: number;
  average_score: number;
  most_active_day: string;
  least_active_day: string;
}

export interface ReadinessSummary {
  average_score: number;
  average_hrv: number;
  average_resting_hr: number;
  highest_readiness_day: string;
  lowest_readiness_day: string;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}
