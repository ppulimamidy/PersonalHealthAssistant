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

// Nutrition types (MVP surface)
export interface NutritionSummary {
  period_days: number;
  average_daily_calories: number;
  average_daily_protein_g: number;
  average_daily_carbs_g: number;
  average_daily_fat_g: number;
  days_with_data: number;
  recent_nutrition_data: Array<{
    date?: string;
    total_calories?: number;
    total_protein_g?: number;
    total_carbs_g?: number;
    total_fat_g?: number;
  }>;
  daily_breakdown?: Array<{
    date?: string;
    rows?: Array<{
      meal_type?: MealType;
      meal_count?: number;
      total_calories?: number;
      total_protein_g?: number;
      total_carbs_g?: number;
      total_fat_g?: number;
    }>;
    total?: {
      total_calories?: number;
      total_protein_g?: number;
      total_carbs_g?: number;
      total_fat_g?: number;
    };
  }>;
}

export interface NutritionSummaryResponse {
  user_preferences?: Record<string, unknown>;
  nutrition_summary?: NutritionSummary;
  recommendations?: unknown;
}

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'unknown';

export interface MealFoodItemInput {
  name: string;
  portion_g?: number;
}

export interface LogMealRequest {
  meal_type: MealType;
  meal_name?: string;
  meal_description?: string;
  food_items: MealFoodItemInput[];
  user_notes?: string;
}

export interface LogMealResponse {
  meal_log_id?: string | null;
  totals?: {
    calories?: number;
    protein_g?: number;
    carbs_g?: number;
    fat_g?: number;
  };
}

// Food recognition (meal photo)
export interface RecognizedFoodItem {
  id?: string;
  name: string;
  confidence?: number;
  category?: string;
  cuisine?: string;
  region?: string;
  portion_g?: number;
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  nutrition_source?: string;
  // Service may return richer fields; keep it flexible.
  [key: string]: unknown;
}

export interface FoodRecognitionResponse {
  request_id?: string;
  user_id?: string;
  recognized_foods?: RecognizedFoodItem[];
  total_calories?: number;
  total_protein?: number;
  total_carbs?: number;
  total_fat?: number;
  overall_confidence?: number;
  detected_cuisine?: string | null;
  detected_region?: string | null;
  warnings?: string[] | null;
  suggestions?: string[] | null;
  image_url?: string | null;
  timestamp?: string;
}

export interface MealLogItem {
  id: string;
  meal_type?: MealType;
  meal_name?: string | null;
  meal_description?: string | null;
  food_items?: Array<{
    name?: string;
    portion_g?: number;
    calories?: number;
    protein_g?: number;
    carbs_g?: number;
    fat_g?: number;
    nutrition_source?: string;
    [key: string]: unknown;
  }>;
  total_calories?: number;
  total_protein_g?: number;
  total_carbs_g?: number;
  total_fat_g?: number;
  total_fiber_g?: number;
  total_sodium_mg?: number;
  total_sugar_g?: number;
  micronutrients?: Record<string, number> | null;
  timestamp?: string | null;
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
export interface HealthIntelligenceIndicators {
  sleep_score_trend: 'improving' | 'declining' | 'stable';
  hrv_trend: 'improving' | 'declining' | 'stable';
  nutrition_quality_score: number;
  inflammation_risk: 'low' | 'moderate' | 'elevated' | 'high';
  stress_index: number;
  personalized_actions: string[];
}

export interface CorrelationHighlight {
  metric_a_label: string;
  metric_b_label: string;
  correlation_coefficient: number;
  effect_description: string;
  strength: string;
}

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
  health_intelligence?: HealthIntelligenceIndicators;
  nutrition_correlations?: CorrelationHighlight[];
  condition_specific_notes?: string[];
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

// Subscription & Billing types
export type SubscriptionTier = 'free' | 'pro' | 'pro_plus';
export type SubscriptionStatus = 'active' | 'past_due' | 'canceled' | 'trialing' | 'incomplete';

export interface UsageInfo {
  used: number;
  limit: number; // -1 means unlimited
  period: 'week';
}

export interface SubscriptionData {
  tier: SubscriptionTier;
  status: SubscriptionStatus;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  usage: {
    ai_insights: UsageInfo;
    nutrition_scans: UsageInfo;
    doctor_prep: UsageInfo;
    pdf_export: UsageInfo;
  };
}

// Health Score types
export interface HealthScoreBreakdown {
  score: number;
  weight: number;
  weighted: number;
}

export interface DailyHealthScore {
  score: number | null;
  breakdown: {
    sleep?: HealthScoreBreakdown;
    readiness?: HealthScoreBreakdown;
    activity?: HealthScoreBreakdown;
  };
  trend: 'up' | 'down' | 'stable';
  change_from_yesterday: number;
  date: string | null;
}

// Referral types
export interface ReferralInfo {
  code: string | null;
  referral_count: number;
  credits_earned: number;
  share_url: string | null;
}

export interface ReferralStats extends ReferralInfo {
  recent_referrals: Array<{
    redeemed_by: string;
    created_at: string;
  }>;
}

// Correlation Engine types
export type CorrelationStrength = 'strong' | 'moderate' | 'weak';
export type CorrelationDirection = 'positive' | 'negative';
export type CorrelationCategory = 'nutrition_sleep' | 'nutrition_readiness' | 'nutrition_activity';

export interface CorrelationDataPoint {
  date: string;
  a_value: number;
  b_value: number;
}

export interface Correlation {
  id: string;
  metric_a: string;
  metric_a_label: string;
  metric_b: string;
  metric_b_label: string;
  correlation_coefficient: number;
  p_value: number;
  sample_size: number;
  lag_days: number;
  effect_description: string;
  category: CorrelationCategory;
  strength: CorrelationStrength;
  direction: CorrelationDirection;
  data_points: CorrelationDataPoint[];
}

export interface CorrelationResults {
  correlations: Correlation[];
  summary: string | null;
  data_quality_score: number;
  oura_days_available: number;
  nutrition_days_available: number;
  computed_at: string;
  period_days: number;
}

export interface CorrelationSummary {
  summary: string | null;
  top_correlations: Correlation[];
  data_quality_score: number;
  has_data: boolean;
}

export interface CausalEdge {
  from_metric: string;
  from_label: string;
  to_metric: string;
  to_label: string;
  causality_score: number;
  correlation: number;
  granger_p_value?: number;
  optimal_lag_days: number;
  strength: 'strong' | 'moderate' | 'weak';
  evidence: string[];
}

export interface CausalGraphNode {
  id: string;
  label: string;
  type: 'nutrition' | 'oura';
}

export interface CausalGraph {
  nodes: CausalGraphNode[];
  edges: CausalEdge[];
  computed_at: string;
  confidence_threshold: number;
}

// Health Condition types
export type ConditionCategory = 'metabolic' | 'cardiovascular' | 'autoimmune' | 'digestive' | 'mental_health' | 'other';

export interface HealthCondition {
  id: string;
  condition_name: string;
  condition_category: ConditionCategory;
  severity: 'mild' | 'moderate' | 'severe';
  diagnosed_date?: string;
  notes?: string;
  is_active: boolean;
  tracked_variables?: string[];
  watch_metrics?: string[];
}

export interface ConditionCatalogItem {
  key: string;
  label: string;
  category: string;
  tracked_variable_count: number;
}

export interface UserHealthProfile {
  health_goals: string[];
  dietary_preferences: string[];
  supplements: Array<{ name: string; dose: string; frequency: string }>;
  medications: Array<{ name: string; dose: string; frequency: string }>;
  questionnaire_completed_at?: string;
}

// Recommendation types
export interface FoodSuggestion {
  name: string;
  reason: string;
  category: string;
}

export interface PatternDetection {
  pattern: string;
  label: string;
  severity: 'mild' | 'moderate' | 'high';
  signals: string[];
  food_suggestions: FoodSuggestion[];
}

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  category: string;
  foods: FoodSuggestion[];
  rationale: string;
}

export interface RecommendationsResponse {
  patterns_detected: PatternDetection[];
  recommendations: Recommendation[];
  ai_summary?: string;
  data_quality: string;
  generated_at: string;
}

export interface RecoveryPlan {
  title: string;
  overview: string;
  daily_plan: Array<{ day: string; focus: string; meals: string }>;
  key_focus_areas: string[];
  foods_to_emphasize: FoodSuggestion[];
  foods_to_limit: string[];
  generated_at: string;
}

// Questionnaire types
export interface QuestionOption {
  value: string;
  label: string;
}

export interface HealthQuestion {
  id: string;
  question: string;
  type: 'single_choice' | 'multi_choice' | 'text' | 'scale';
  category: string;
  options?: QuestionOption[];
  scale_min?: number;
  scale_max?: number;
  required: boolean;
}

export interface QuestionnaireData {
  questions: HealthQuestion[];
  profile_completed: boolean;
  sections: string[];
}

// Medications & Supplements types
export interface Medication {
  id: string;
  medication_name: string;
  generic_name?: string;
  dosage: string;
  frequency: string;
  route: string;
  indication?: string;
  prescribing_doctor?: string;
  pharmacy?: string;
  prescription_number?: string;
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  refill_reminder_enabled: boolean;
  refill_reminder_days_before: number;
  side_effects_experienced: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Supplement {
  id: string;
  supplement_name: string;
  brand?: string;
  dosage: string;
  frequency: string;
  form: string;
  purpose?: string;
  taken_with_food?: boolean;
  time_of_day?: string;
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface MedicationAdherenceLog {
  id: string;
  medication_id?: string;
  supplement_id?: string;
  scheduled_time: string;
  taken_time?: string;
  was_taken: boolean;
  missed_reason?: string;
  side_effects_noted?: string;
  created_at: string;
}

export interface AdherenceStats {
  medications: Array<{
    medication_id: string;
    medication_name: string;
    total_scheduled: number;
    total_taken: number;
    adherence_rate: number;
    missed_count: number;
  }>;
  supplements: Array<{
    supplement_id: string;
    supplement_name: string;
    total_scheduled: number;
    total_taken: number;
    adherence_rate: number;
    missed_count: number;
  }>;
  overall_adherence_rate: number;
}

export interface CreateMedicationRequest {
  medication_name: string;
  generic_name?: string;
  dosage: string;
  frequency: string;
  route?: string;
  indication?: string;
  prescribing_doctor?: string;
  pharmacy?: string;
  prescription_number?: string;
  start_date?: string;
  end_date?: string;
  is_active?: boolean;
  refill_reminder_enabled?: boolean;
  refill_reminder_days_before?: number;
  side_effects_experienced?: string[];
  notes?: string;
}

export interface CreateSupplementRequest {
  supplement_name: string;
  brand?: string;
  dosage: string;
  frequency: string;
  form?: string;
  purpose?: string;
  taken_with_food?: boolean;
  time_of_day?: string;
  start_date?: string;
  end_date?: string;
  is_active?: boolean;
  notes?: string;
}

// Symptom Journal types
export type SymptomType = 'pain' | 'fatigue' | 'nausea' | 'headache' | 'digestive' | 'mental_health' | 'respiratory' | 'skin' | 'other';
export type MoodType = 'happy' | 'anxious' | 'stressed' | 'sad' | 'neutral' | 'irritable' | 'energetic';

export interface SymptomJournalEntry {
  id: string;
  symptom_date: string;
  symptom_time?: string;
  symptom_type: SymptomType | string;
  severity: number;
  location?: string;
  duration_minutes?: number;
  triggers: string[];
  associated_symptoms: string[];
  medications_taken: string[];
  notes?: string;
  mood?: MoodType | string;
  weather_conditions?: string;
  stress_level?: number;
  sleep_hours_previous_night?: number;
  photo_url?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateSymptomRequest {
  symptom_date: string;
  symptom_time?: string;
  symptom_type: string;
  severity: number;
  location?: string;
  duration_minutes?: number;
  triggers?: string[];
  associated_symptoms?: string[];
  medications_taken?: string[];
  notes?: string;
  mood?: string;
  weather_conditions?: string;
  stress_level?: number;
  sleep_hours_previous_night?: number;
}

export interface SymptomAnalytics {
  total_entries: number;
  date_range: {
    start: string;
    end: string;
  };
  symptom_types: Array<{
    symptom_type: string;
    count: number;
  }>;
  severity_distribution: {
    mild: number;
    moderate: number;
    severe: number;
  };
  average_severity: number;
  most_common_triggers: Array<{
    trigger: string;
    count: number;
  }>;
  mood_correlations?: {
    [mood: string]: number;
  };
  stress_correlations?: {
    [level: string]: number[];
  };
}

export interface SymptomPattern {
  id: string;
  pattern_type: 'time_based' | 'trigger_based' | 'cyclic' | 'correlation';
  symptom_type: string;
  pattern_description?: string;
  confidence_score: number;
  supporting_entries: string[];
  recommendations: string[];
  detected_at: string;
  is_active: boolean;
}

// Medical Literature & RAG types
export interface ResearchArticle {
  id: string;
  pubmed_id?: string;
  doi?: string;
  title: string;
  abstract?: string;
  authors: string[];
  journal?: string;
  publication_date?: string;
  keywords: string[];
  relevance_score?: number;
  citation_count: number;
  source_url?: string;
  fetched_at: string;
}

export interface PubMedSearchRequest {
  query: string;
  max_results?: number;
  date_from?: string;
  date_to?: string;
  sort?: 'relevance' | 'date';
}

export interface SearchResultsResponse {
  query: string;
  total_results: number;
  articles: ResearchArticle[];
  query_id?: string;
}

export interface ArticleBookmark {
  id: string;
  article_id: string;
  user_notes?: string;
  tags: string[];
  relevance_rating?: number;
  bookmarked_at: string;
}

export interface BookmarkArticleRequest {
  article_id: string;
  user_notes?: string;
  tags?: string[];
  relevance_rating?: number;
}

export interface RAGMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources: string[];
}

export interface RAGConversation {
  id: string;
  title?: string;
  messages: RAGMessage[];
  context_articles: string[];
  created_at: string;
  updated_at: string;
}

export interface RAGMessageRequest {
  conversation_id?: string;
  message: string;
  context_article_ids?: string[];
}

export interface ResearchInsight {
  id: string;
  insight_type: string;
  topic: string;
  summary: string;
  key_findings: string[];
  recommendations: string[];
  source_article_ids: string[];
  confidence_score: number;
  generated_at: string;
}

export interface ResearchInsightRequest {
  topic: string;
  insight_type?: string;
  article_ids?: string[];
}

// Beta signup
export interface BetaSignupResponse {
  success: boolean;
  message: string;
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
