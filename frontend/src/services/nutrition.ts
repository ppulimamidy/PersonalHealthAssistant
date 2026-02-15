'use client';

import { api } from './api';
import type {
  NutritionSummaryResponse,
  LogMealRequest,
  LogMealResponse,
  FoodRecognitionResponse,
  MealLogItem,
} from '@/types';

export const nutritionService = {
  getSummary: async (days: 14 | 30 = 14): Promise<NutritionSummaryResponse> => {
    const response = await api.get('/api/v1/nutrition/summary', {
      params: { days },
    });
    return response.data;
  },

  logMeal: async (payload: LogMealRequest): Promise<LogMealResponse> => {
    const response = await api.post('/api/v1/nutrition/log-meal', payload);
    return response.data;
  },

  listMeals: async (days: 14 | 30 = 14): Promise<{ items: MealLogItem[] }> => {
    const response = await api.get('/api/v1/nutrition/meals', { params: { days } });
    return response.data;
  },

  updateMeal: async (mealId: string, payload: LogMealRequest): Promise<LogMealResponse> => {
    const response = await api.put(`/api/v1/nutrition/meals/${mealId}`, payload);
    return response.data;
  },

  deleteMeal: async (mealId: string): Promise<{ success: boolean }> => {
    const response = await api.delete(`/api/v1/nutrition/meals/${mealId}`);
    return response.data;
  },

  recognizeMealImage: async (file: File, opts?: { meal_type?: string }): Promise<FoodRecognitionResponse> => {
    const form = new FormData();
    form.append('image', file);
    if (opts?.meal_type) form.append('meal_type', opts.meal_type);
    // Use best-available models in backend (it will skip those without keys)
    form.append('models_to_use', 'openai_vision,google_vision,azure_vision');
    form.append('enable_portion_estimation', 'true');
    form.append('enable_nutrition_lookup', 'true');
    form.append('enable_cultural_recognition', 'true');

    const response = await api.post('/api/v1/nutrition/recognize-meal-image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

