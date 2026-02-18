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

// Medication Intelligence types
export interface InteractionSource {
  title: string;
  url?: string;
  pubmed_id?: string;
}

export interface MedicationInteraction {
  id: string;
  medication_name: string;
  medication_generic_name?: string;
  medication_class?: string;
  interaction_type: string;
  interacts_with: string;
  interacts_with_category?: string;
  severity: 'critical' | 'high' | 'moderate' | 'low';
  evidence_level: 'strong' | 'moderate' | 'limited' | 'theoretical';
  mechanism?: string;
  clinical_significance?: string;
  recommendation: string;
  timing_recommendation?: string;
  sources: InteractionSource[];
}

export interface UserMedicationAlert {
  id: string;
  user_id: string;
  interaction_id?: string;
  medication_id?: string;
  supplement_id?: string;
  nutrition_item?: string;
  alert_type: 'drug_nutrient' | 'drug_supplement' | 'drug_food' | 'supplement_nutrient';
  severity: 'critical' | 'high' | 'moderate' | 'low';
  title: string;
  description: string;
  recommendation: string;
  is_acknowledged: boolean;
  is_dismissed: boolean;
  detected_at: string;
  medication_name?: string;
  interacts_with?: string;
}

export interface InteractionAlertsResponse {
  alerts: UserMedicationAlert[];
  total_critical: number;
  total_high: number;
  total_unacknowledged: number;
}

export interface MedicationVitalsCorrelation {
  id: string;
  medication_id: string;
  medication_name: string;
  vital_metric: string;
  vital_label: string;
  correlation_coefficient: number;
  p_value: number;
  sample_size: number;
  lag_hours: number;
  optimal_timing_window?: string;
  effect_type: 'positive' | 'negative' | 'neutral';
  effect_magnitude?: 'large' | 'moderate' | 'small';
  effect_description: string;
  clinical_significance?: string;
  recommendation?: string;
  data_quality_score: number;
  days_analyzed: number;
  computed_at: string;
}

export interface MedicationCorrelationsResponse {
  correlations: MedicationVitalsCorrelation[];
  total_significant: number;
  data_quality_score: number;
}

// Symptom Correlation types
export interface SymptomCorrelation {
  id: string;
  symptom_type: string;
  symptom_metric: string;
  correlation_type: 'symptom_nutrition' | 'symptom_oura' | 'symptom_medication' | 'symptom_symptom';
  correlated_variable: string;
  correlated_variable_label: string;
  correlation_coefficient: number;
  p_value: number;
  sample_size: number;
  lag_days: number;
  effect_type: 'positive' | 'negative' | 'neutral';
  effect_magnitude?: 'large' | 'moderate' | 'small';
  effect_description: string;
  clinical_significance?: string;
  recommendation?: string;
  trigger_identified: boolean;
  trigger_confidence?: number;
  data_quality_score: number;
  days_analyzed: number;
  computed_at: string;
}

export interface TriggerVariable {
  variable: string;
  label: string;
  coefficient: number;
  p_value: number;
}

export interface SymptomTriggerPattern {
  id: string;
  symptom_type: string;
  pattern_type: 'food_trigger' | 'medication_side_effect' | 'stress_trigger' | 'sleep_trigger' | 'activity_trigger' | 'weather_trigger' | 'multi_factor';
  trigger_variables: TriggerVariable[];
  pattern_strength: number;
  confidence_score: number;
  pattern_description: string;
  trigger_threshold?: Record<string, any>;
  recommendations: string[];
  times_observed: number;
  times_validated: number;
  last_observed_at?: string;
  is_active: boolean;
  user_acknowledged: boolean;
  created_at: string;
}

export interface SymptomCorrelationsResponse {
  correlations: SymptomCorrelation[];
  trigger_patterns: SymptomTriggerPattern[];
  total_significant: number;
  data_quality_score: number;
  analysis_summary?: string;
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

// AI Agents types
export interface AgentInfo {
  id: string;
  agent_type: string;
  agent_name: string;
  agent_description: string;
  capabilities: string[];
  is_active: boolean;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  agent_id?: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface AgentConversation {
  id: string;
  title?: string;
  conversation_type: string;
  primary_agent_id: string;
  primary_agent_name: string;
  participating_agents: string[];
  status: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
  last_message_at: string;
}

export interface SendMessageRequest {
  conversation_id?: string;
  message: string;
  agent_type?: string;
  conversation_type?: string;
}

export interface AgentAction {
  id: string;
  agent_id: string;
  agent_name: string;
  action_type: string;
  action_description: string;
  action_data: Record<string, any>;
  priority: string;
  category?: string;
  status: string;
  created_at: string;
}

// Beta signup
export interface BetaSignupResponse {
  success: boolean;
  message: string;
}

// Predictive Health types (Phase 4)
export interface PredictionRange {
  lower: number;
  upper: number;
}

export interface HealthPrediction {
  id: string;
  prediction_type: string; // sleep_score, readiness_score, hrv_forecast, etc.
  metric_name: string;
  prediction_date: string;
  prediction_horizon_days: number;
  predicted_value: number;
  confidence_score: number;
  prediction_range?: PredictionRange;
  actual_value?: number;
  prediction_error?: number;
  model_type: string; // statistical, ml, hybrid
  model_version: string;
  features_used: string[];
  contributing_factors: Array<{
    factor: string;
    value: string | number;
  }>;
  recommendations: Array<{
    priority: string;
    action: string;
    rationale?: string;
  }>;
  status: string; // pending, confirmed, inaccurate
  created_at: string;
}

export interface PredictionsResponse {
  predictions: HealthPrediction[];
  generated_at: string;
  days_of_data: number;
  data_quality_score: number;
}

export interface RiskFactor {
  factor: string;
  impact_score: number; // 0-1
  description: string;
}

export interface HealthRiskAssessment {
  id: string;
  risk_type: string; // symptom_flare, sleep_decline, recovery_decline, burnout
  risk_category: string; // cardiovascular, metabolic, mental_health, sleep, recovery
  risk_score: number; // 0-1
  risk_level: string; // low, moderate, high, critical
  risk_window_start: string;
  risk_window_end: string;
  contributing_factors: RiskFactor[];
  protective_factors: RiskFactor[];
  recommendations: Array<{
    priority: string;
    action: string;
    rationale: string;
  }>;
  early_warning_signs: string[];
  historical_patterns: Array<{
    date?: string;
    description?: string;
  }>;
  confidence_score: number;
  user_acknowledged: boolean;
  is_active: boolean;
  created_at: string;
}

export interface RisksResponse {
  risks: HealthRiskAssessment[];
  overall_risk_level: string;
  generated_at: string;
}

export interface HealthTrend {
  id: string;
  metric_name: string;
  trend_type: string; // improving, declining, stable, fluctuating
  analysis_start_date: string;
  analysis_end_date: string;
  window_days: number;
  slope: number; // rate of change
  r_squared: number; // trend strength
  average_value: number;
  std_deviation: number;
  percent_change: number;
  absolute_change: number;
  detected_patterns: string[];
  anomalies: Array<{
    date: string;
    value: number;
    z_score: number;
  }>;
  forecast_7d?: number;
  forecast_14d?: number;
  forecast_30d?: number;
  interpretation: string;
  significance: string; // clinically_significant, notable, minor, noise
  created_at: string;
}

export interface TrendsResponse {
  trends: HealthTrend[];
  generated_at: string;
}

export interface PersonalizedHealthScore {
  id: string;
  score_date: string;
  score_type: string; // overall_health, recovery_capacity, resilience, metabolic_health
  score_value: number; // 0-100
  percentile?: number;
  component_scores: {
    [key: string]: number;
  };
  positive_factors: string[];
  negative_factors: string[];
  trend_7d: string; // up, down, stable
  change_7d: number;
  improvement_recommendations: Array<{
    priority: string;
    action: string;
  }>;
  created_at: string;
}

// Lab Results types (Phase 5)
export interface BiomarkerReference {
  id: string;
  biomarker_code: string;
  biomarker_name: string;
  unit: string;
  reference_range_min: number;
  reference_range_max: number;
  optimal_range_min?: number;
  optimal_range_max?: number;
  age_group?: string;
  gender?: string;
  interpretation_low?: string;
  interpretation_normal?: string;
  interpretation_high?: string;
}

export interface Biomarker {
  biomarker_code: string;
  biomarker_name: string;
  value: number;
  unit: string;
  reference_range: string;
  status: 'normal' | 'borderline' | 'abnormal' | 'critical';
  interpretation?: string;
}

export interface LabResult {
  id: string;
  test_date: string;
  test_type: string;
  test_category?: string;
  lab_name?: string;
  ordering_provider?: string;
  biomarkers: Biomarker[];
  pdf_url?: string;
  notes?: string;
  ai_summary?: string;
  flags?: string[];
  created_at: string;
  updated_at: string;
}

export interface BiomarkerTrend {
  biomarker_code: string;
  biomarker_name: string;
  unit: string;
  data_points: Array<{
    test_date: string;
    value: number;
    status: string;
  }>;
  trend_direction: 'improving' | 'declining' | 'stable';
  slope?: number;
  r_squared?: number;
  percent_change?: number;
  statistical_significance?: number;
}

export interface LabInsight {
  id: string;
  insight_type: 'trend' | 'anomaly' | 'recommendation' | 'alert';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  biomarkers_involved: string[];
  recommendations: string[];
  sources: string[];
  created_at: string;
  is_acknowledged: boolean;
}

export interface LabTestCategory {
  category_code: string;
  category_name: string;
  description?: string;
  common_biomarkers: string[];
  test_frequency_recommendation?: string;
}

export interface CreateLabResultRequest {
  test_date: string;
  test_type: string;
  test_category?: string;
  lab_name?: string;
  ordering_provider?: string;
  biomarkers: Array<{
    biomarker_code: string;
    biomarker_name: string;
    value: number;
    unit: string;
  }>;
  notes?: string;
}

export interface LabResultsResponse {
  lab_results: LabResult[];
  total: number;
}

export interface BiomarkerTrendsResponse {
  trends: BiomarkerTrend[];
}

export interface LabInsightsResponse {
  insights: LabInsight[];
  total: number;
}

// Health Twin types (Phase 5)
export interface HealthTwinProfile {
  id: string;
  health_age: number;
  chronological_age: number;
  health_age_trend: 'improving' | 'declining' | 'stable';
  resilience_score: number;
  adaptability_score: number;
  recovery_capacity: number;
  metabolic_age: number;
  biological_age_factors: {
    [key: string]: number;
  };
  recent_changes: Array<{
    date: string;
    metric: string;
    change: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface HealthTwinSimulation {
  id: string;
  simulation_name: string;
  simulation_type: 'lifestyle_change' | 'intervention' | 'risk_scenario' | 'goal_projection';
  parameters: {
    [key: string]: any;
  };
  predicted_outcomes: {
    [key: string]: number;
  };
  timeline_predictions: Array<{
    days_from_now: number;
    predicted_health_age: number;
    predicted_scores: {
      [key: string]: number;
    };
  }>;
  confidence_score: number;
  recommendations: string[];
  warnings: string[];
  status: 'draft' | 'active' | 'completed';
  created_at: string;
  updated_at: string;
}

export interface HealthTwinSnapshot {
  id: string;
  snapshot_date: string;
  health_age: number;
  resilience_score: number;
  key_metrics: {
    [key: string]: number;
  };
  notes?: string;
  created_at: string;
}

export interface HealthTwinGoal {
  id: string;
  goal_type: string;
  goal_description: string;
  target_metric: string;
  target_value: number;
  current_value: number;
  target_date?: string;
  strategies: string[];
  success_probability: number;
  estimated_timeline_days?: number;
  milestones: Array<{
    milestone: string;
    target_value: number;
    target_date?: string;
    completed: boolean;
  }>;
  status: 'active' | 'achieved' | 'abandoned';
  created_at: string;
  updated_at: string;
}

export interface CreateSimulationRequest {
  simulation_name: string;
  simulation_type: 'lifestyle_change' | 'intervention' | 'risk_scenario' | 'goal_projection';
  parameters: {
    [key: string]: any;
  };
}

export interface CreateHealthTwinGoalRequest {
  goal_type: string;
  goal_description: string;
  target_metric: string;
  target_value: number;
  target_date?: string;
  strategies?: string[];
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
