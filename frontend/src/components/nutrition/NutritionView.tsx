'use client';

import { useMemo, useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { nutritionService } from '@/services/nutrition';
import type {
  FoodRecognitionResponse,
  LogMealRequest,
  MealFoodItemInput,
  MealType,
  MealLogItem,
  NutritionSummaryResponse,
  RecognizedFoodItem,
} from '@/types';
import { RefreshCw } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-slate-500 dark:text-slate-400">{label}</div>
      <div className="text-lg font-semibold text-slate-900 dark:text-slate-100">{value}</div>
    </div>
  );
}

export function NutritionView() {
  const { user, isLoading: isAuthLoading } = useAuth(true);
  const [mealType, setMealType] = useState<MealType>('lunch');
  const [mealName, setMealName] = useState('');
  const [foods, setFoods] = useState<MealFoodItemInput[]>([{ name: '', portion_g: 100 }]);
  const [logError, setLogError] = useState<string | null>(null);
  const [logSuccess, setLogSuccess] = useState<string | null>(null);

  const [mealPhoto, setMealPhoto] = useState<File | null>(null);
  const [mealPhotoPreviewUrl, setMealPhotoPreviewUrl] = useState<string | null>(null);
  const [recognition, setRecognition] = useState<FoodRecognitionResponse | null>(null);
  const [recognizedFoods, setRecognizedFoods] = useState<RecognizedFoodItem[]>([]);

  const { data, isLoading, refetch, isRefetching, error } = useQuery({
    queryKey: ['nutrition-summary', 14],
    queryFn: () => nutritionService.getSummary(14),
    enabled: Boolean(user) && !isAuthLoading,
  });

  const {
    data: mealsData,
    isLoading: isMealsLoading,
    refetch: refetchMeals,
  } = useQuery({
    queryKey: ['nutrition-meals', 14],
    queryFn: () => nutritionService.listMeals(14),
    enabled: Boolean(user) && !isAuthLoading,
  });

  const summary = (data as NutritionSummaryResponse | undefined)?.nutrition_summary;
  const recent = summary?.recent_nutrition_data ?? [];
  const dailyBreakdown = summary?.daily_breakdown ?? [];
  const meals = mealsData?.items ?? [];

  const [editingMealId, setEditingMealId] = useState<string | null>(null);
  const [editMealType, setEditMealType] = useState<MealType>('lunch');
  const [editMealName, setEditMealName] = useState('');
  const [editFoods, setEditFoods] = useState<MealFoodItemInput[]>([{ name: '', portion_g: 100 }]);

  const canSubmit = useMemo(() => {
    const nonEmptyFoods = foods.filter((f) => (f.name ?? '').trim().length > 0);
    return nonEmptyFoods.length > 0;
  }, [foods]);

  useEffect(() => {
    if (!mealPhoto) {
      setMealPhotoPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(mealPhoto);
    setMealPhotoPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [mealPhoto]);

  const logMealMutation = useMutation({
    mutationFn: (payload: LogMealRequest) => nutritionService.logMeal(payload),
    onSuccess: async () => {
      setLogError(null);
      setLogSuccess('Meal logged');
      await refetch();
      await refetchMeals();
    },
    onError: (e: unknown) => {
      setLogSuccess(null);
      const msg = e instanceof Error ? e.message : 'Failed to log meal';
      setLogError(msg);
    },
  });

  const updateMealMutation = useMutation({
    mutationFn: async (args: { mealId: string; payload: LogMealRequest }) =>
      nutritionService.updateMeal(args.mealId, args.payload),
    onSuccess: async () => {
      setLogError(null);
      setLogSuccess('Meal updated');
      setEditingMealId(null);
      await Promise.all([refetch(), refetchMeals()]);
    },
    onError: (e: unknown) => {
      setLogSuccess(null);
      const msg = e instanceof Error ? e.message : 'Failed to update meal';
      setLogError(msg);
    },
  });

  const deleteMealMutation = useMutation({
    mutationFn: (mealId: string) => nutritionService.deleteMeal(mealId),
    onSuccess: async () => {
      setLogError(null);
      setLogSuccess('Meal deleted');
      if (editingMealId) setEditingMealId(null);
      await Promise.all([refetch(), refetchMeals()]);
    },
    onError: (e: unknown) => {
      setLogSuccess(null);
      const msg = e instanceof Error ? e.message : 'Failed to delete meal';
      setLogError(msg);
    },
  });

  const mealsByDay = useMemo(() => {
    const map: Record<string, MealLogItem[]> = {};
    for (const m of meals) {
      const day = (m.timestamp ?? '').slice(0, 10) || '—';
      if (!map[day]) map[day] = [];
      map[day].push(m);
    }
    // sort meals within each day by timestamp desc
    for (const day of Object.keys(map)) {
      map[day].sort((a, b) => String(b.timestamp ?? '').localeCompare(String(a.timestamp ?? '')));
    }
    const days = Object.keys(map).sort((a, b) => b.localeCompare(a));
    return { map, days };
  }, [meals]);

  const recognizeMealMutation = useMutation({
    mutationFn: async () => {
      if (!mealPhoto) throw new Error('Please select a photo first');
      return await nutritionService.recognizeMealImage(mealPhoto, { meal_type: mealType });
    },
    onSuccess: (res) => {
      setRecognition(res);
      const rows = (res?.recognized_foods ?? []) as RecognizedFoodItem[];
      // Ensure editable baseline fields exist
      setRecognizedFoods(
        rows.map((r) => ({
          ...r,
          name: (r.name ?? '').toString(),
          portion_g:
            typeof r.portion_g === 'number'
              ? r.portion_g
              : typeof (r as any)?.portion_estimate?.estimated_quantity === 'number' &&
                  String((r as any)?.portion_estimate?.unit || '').toLowerCase() === 'g'
                ? (r as any).portion_estimate.estimated_quantity
                : 100,
        }))
      );
      setLogError(null);
      setLogSuccess('Photo analyzed — review and log');
    },
    onError: (e: unknown) => {
      setRecognition(null);
      setRecognizedFoods([]);
      const msg = e instanceof Error ? e.message : 'Failed to analyze photo';
      setLogSuccess(null);
      setLogError(msg);
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Nutrition</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            A simple 14-day nutrition snapshot (calories + macros).
          </p>
        </div>
        <Button onClick={() => refetch()} variant="outline" isLoading={isRefetching}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {isAuthLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : error ? (
        <Card>
          <CardHeader>
            <CardTitle>Nutrition service unavailable</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-600 dark:text-slate-300">
              We couldn’t load nutrition data yet. Make sure the Nutrition service is running and reachable from the MVP API.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Scan a meal photo</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
                <div className="md:col-span-1">
                  <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Meal photo</div>
                  <input
                    className="w-full rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"
                    type="file"
                    accept="image/*"
                    capture="environment"
                    onChange={(e) => {
                      const f = e.target.files?.[0] ?? null;
                      setMealPhoto(f);
                      setRecognition(null);
                      setRecognizedFoods([]);
                    }}
                  />
                  {mealPhotoPreviewUrl ? (
                    <div className="mt-3 rounded-md overflow-hidden border border-slate-200 dark:border-slate-700">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={mealPhotoPreviewUrl} alt="Meal preview" className="w-full h-auto" />
                    </div>
                  ) : null}

                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button
                      isLoading={recognizeMealMutation.isPending}
                      disabled={!mealPhoto || recognizeMealMutation.isPending}
                      onClick={() => recognizeMealMutation.mutate()}
                    >
                      Analyze photo
                    </Button>
                    <Button
                      variant="outline"
                      disabled={!mealPhoto}
                      onClick={() => {
                        setMealPhoto(null);
                        setRecognition(null);
                        setRecognizedFoods([]);
                      }}
                    >
                      Clear
                    </Button>
                  </div>
                </div>

                <div className="md:col-span-2">
                  {recognition ? (
                    <div>
                      <div className="text-sm text-slate-700 dark:text-slate-200">
                        {recognition.detected_cuisine ? (
                          <span className="mr-3">
                            <span className="text-slate-500 dark:text-slate-400">Cuisine:</span>{' '}
                            {recognition.detected_cuisine}
                          </span>
                        ) : null}
                        {recognition.detected_region ? (
                          <span className="mr-3">
                            <span className="text-slate-500 dark:text-slate-400">Region:</span>{' '}
                            {recognition.detected_region}
                          </span>
                        ) : null}
                        {typeof recognition.overall_confidence === 'number' ? (
                          <span>
                            <span className="text-slate-500 dark:text-slate-400">Confidence:</span>{' '}
                            {Math.round(recognition.overall_confidence * 100)}%
                          </span>
                        ) : null}
                      </div>

                      <div className="mt-4">
                        <div className="text-xs text-slate-500 dark:text-slate-400 mb-2">
                          Recognized foods (edit before logging)
                        </div>
                        {recognizedFoods.length === 0 ? (
                          <p className="text-slate-600 dark:text-slate-300 text-sm">
                            No foods detected. Try a clearer photo (good lighting, top-down, minimal clutter).
                          </p>
                        ) : (
                          <div className="space-y-2">
                            {recognizedFoods.map((f, idx) => (
                              <div key={f.id ?? idx} className="grid grid-cols-1 md:grid-cols-6 gap-2">
                                <input
                                  className="md:col-span-3 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 px-3 py-2 text-sm"
                                  value={(f.name ?? '').toString()}
                                  onChange={(e) => {
                                    const next = [...recognizedFoods];
                                    next[idx] = { ...next[idx], name: e.target.value };
                                    setRecognizedFoods(next);
                                  }}
                                  placeholder="Food name"
                                />
                                <input
                                  className="md:col-span-1 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"
                                  type="number"
                                  min={1}
                                  value={Math.round((f.portion_g as number) ?? 100)}
                                  onChange={(e) => {
                                    const next = [...recognizedFoods];
                                    next[idx] = { ...next[idx], portion_g: Number(e.target.value) };
                                    setRecognizedFoods(next);
                                  }}
                                />
                                <div className="md:col-span-1 flex items-center text-xs text-slate-600 dark:text-slate-300">
                                  {typeof f.calories === 'number' ? `${Math.round(f.calories)} kcal` : '—'}
                                </div>
                                <div className="md:col-span-1 flex gap-2">
                                  <Button
                                    variant="outline"
                                    onClick={() => setRecognizedFoods(recognizedFoods.filter((_, i) => i !== idx))}
                                  >
                                    Remove
                                  </Button>
                                </div>
                              </div>
                            ))}

                            <div className="mt-3 flex flex-wrap gap-2">
                              <Button
                                variant="outline"
                                onClick={() =>
                                  setRecognizedFoods([
                                    ...recognizedFoods,
                                    { name: '', portion_g: 100, confidence: 0.0 } as RecognizedFoodItem,
                                  ])
                                }
                              >
                                Add food
                              </Button>
                              <Button
                                variant="outline"
                                onClick={() => {
                                  // Copy recognized foods into the manual logging form
                                  const nextFoods: MealFoodItemInput[] = recognizedFoods
                                    .filter((x) => (x.name ?? '').toString().trim().length > 0)
                                    .map((x) => ({
                                      name: (x.name ?? '').toString().trim(),
                                      portion_g: typeof x.portion_g === 'number' ? x.portion_g : 100,
                                    }));
                                  setFoods(nextFoods.length ? nextFoods : [{ name: '', portion_g: 100 }]);
                                }}
                              >
                                Use in log form
                              </Button>
                              <Button
                                isLoading={logMealMutation.isPending}
                                disabled={recognizedFoods.length === 0 || logMealMutation.isPending}
                                onClick={() => {
                                  setLogError(null);
                                  setLogSuccess(null);
                                  const payload: LogMealRequest = {
                                    meal_type: mealType,
                                    meal_name: mealName.trim() ? mealName.trim() : undefined,
                                    food_items: recognizedFoods
                                      .filter((x) => (x.name ?? '').toString().trim().length > 0)
                                      .map((x) => ({
                                        name: (x.name ?? '').toString().trim(),
                                        portion_g: typeof x.portion_g === 'number' ? x.portion_g : 100,
                                      })),
                                  };
                                  logMealMutation.mutate(payload);
                                }}
                              >
                                Log recognized meal
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <p className="text-slate-600 dark:text-slate-300 text-sm">
                      Upload a photo to recognize foods, estimate portions, infer cuisine/region, and calculate macros + calories.
                      You can edit anything before logging.
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Log a meal</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Meal type</div>
                  <select
                    className="w-full rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm dark:[color-scheme:dark]"
                    value={mealType}
                    onChange={(e) => setMealType(e.target.value as MealType)}
                  >
                    <option value="breakfast">Breakfast</option>
                    <option value="lunch">Lunch</option>
                    <option value="dinner">Dinner</option>
                    <option value="snack">Snack</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </div>

                <div className="md:col-span-2">
                  <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Meal name (optional)</div>
                  <input
                    className="w-full rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 px-3 py-2 text-sm"
                    value={mealName}
                    onChange={(e) => setMealName(e.target.value)}
                    placeholder="e.g., Chicken salad"
                  />
                </div>
              </div>

              <div className="mt-4">
                <div className="text-xs text-slate-500 dark:text-slate-400 mb-2">Foods (name + grams)</div>
                <div className="space-y-2">
                  {foods.map((f, idx) => (
                    <div key={idx} className="grid grid-cols-1 md:grid-cols-5 gap-2">
                      <input
                        className="md:col-span-3 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 px-3 py-2 text-sm"
                        value={f.name}
                        onChange={(e) => {
                          const next = [...foods];
                          next[idx] = { ...next[idx], name: e.target.value };
                          setFoods(next);
                        }}
                        placeholder="Food (e.g., oatmeal)"
                      />
                      <input
                        className="md:col-span-1 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"
                        type="number"
                        min={1}
                        value={f.portion_g ?? 100}
                        onChange={(e) => {
                          const next = [...foods];
                          next[idx] = { ...next[idx], portion_g: Number(e.target.value) };
                          setFoods(next);
                        }}
                      />
                      <div className="md:col-span-1 flex gap-2">
                        <Button
                          variant="outline"
                          onClick={() => {
                            const next = foods.filter((_, i) => i !== idx);
                            setFoods(next.length ? next : [{ name: '', portion_g: 100 }]);
                          }}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setFoods([...foods, { name: '', portion_g: 100 }])}
                  >
                    Add food
                  </Button>
                  <Button
                    isLoading={logMealMutation.isPending}
                    disabled={!canSubmit || logMealMutation.isPending}
                    onClick={() => {
                      setLogError(null);
                      setLogSuccess(null);
                      const payload: LogMealRequest = {
                        meal_type: mealType,
                        meal_name: mealName.trim() ? mealName.trim() : undefined,
                        food_items: foods
                          .filter((x) => (x.name ?? '').trim().length > 0)
                          .map((x) => ({ name: x.name.trim(), portion_g: x.portion_g ?? 100 })),
                      };
                      logMealMutation.mutate(payload);
                    }}
                  >
                    Log meal
                  </Button>
                </div>

                {logError ? (
                  <p className="mt-3 text-sm text-red-600 dark:text-red-400">{logError}</p>
                ) : null}
                {logSuccess ? (
                  <p className="mt-3 text-sm text-emerald-700 dark:text-emerald-400">{logSuccess}</p>
                ) : null}
              </div>
            </CardContent>
          </Card>

          <Card className="mb-6">
            <CardHeader>
              <CardTitle>14-day averages</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <Stat
                  label="Avg calories/day"
                  value={summary ? Math.round(summary.average_daily_calories).toString() : '—'}
                />
                <Stat
                  label="Avg protein (g)"
                  value={summary ? Math.round(summary.average_daily_protein_g).toString() : '—'}
                />
                <Stat
                  label="Avg carbs (g)"
                  value={summary ? Math.round(summary.average_daily_carbs_g).toString() : '—'}
                />
                <Stat
                  label="Avg fat (g)"
                  value={summary ? Math.round(summary.average_daily_fat_g).toString() : '—'}
                />
                <Stat
                  label="Days with data"
                  value={summary ? String(summary.days_with_data) : '0'}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Daily breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              {recent.length === 0 ? (
                <p className="text-slate-600 dark:text-slate-300">
                  No nutrition logs yet. Log your first meal above.
                </p>
              ) : (
                <div className="space-y-5">
                  {(dailyBreakdown.length ? dailyBreakdown : recent.map((d) => ({ date: d.date, rows: [], total: d })))
                    .slice(0, 14)
                    .map((day, idx) => (
                      <div
                        key={`${day.date ?? 'day'}-${idx}`}
                        className="rounded-lg border border-slate-100 dark:border-slate-800 overflow-hidden"
                      >
                        <div className="px-4 py-3 bg-slate-50 dark:bg-slate-900/40 flex items-center justify-between">
                          <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                            {day.date ?? '—'}
                          </div>
                          <div className="text-xs text-slate-600 dark:text-slate-300">
                            Total: {Math.round(day.total?.total_calories ?? 0)} kcal
                          </div>
                        </div>

                        <div className="px-4 py-3">
                          {day.rows && day.rows.length ? (
                            <div className="divide-y divide-slate-100 dark:divide-slate-800">
                              {day.rows.map((row, rIdx) => (
                                <div key={`${row.meal_type ?? 'meal'}-${rIdx}`} className="py-2 flex items-center justify-between">
                                  <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                    {(row.meal_type ?? 'unknown').toString()}
                                    {row.meal_count ? (
                                      <span className="ml-2 text-xs font-normal text-slate-500 dark:text-slate-400">
                                        ({row.meal_count})
                                      </span>
                                    ) : null}
                                  </div>
                                  <div className="text-sm text-slate-700 dark:text-slate-200 flex gap-4">
                                    <span>{Math.round(row.total_calories ?? 0)} kcal</span>
                                    <span>{Math.round(row.total_protein_g ?? 0)}g P</span>
                                    <span>{Math.round(row.total_carbs_g ?? 0)}g C</span>
                                    <span>{Math.round(row.total_fat_g ?? 0)}g F</span>
                                  </div>
                                </div>
                              ))}

                              <div className="py-2 flex items-center justify-between">
                                <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">Total</div>
                                <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex gap-4">
                                  <span>{Math.round(day.total?.total_calories ?? 0)} kcal</span>
                                  <span>{Math.round(day.total?.total_protein_g ?? 0)}g P</span>
                                  <span>{Math.round(day.total?.total_carbs_g ?? 0)}g C</span>
                                  <span>{Math.round(day.total?.total_fat_g ?? 0)}g F</span>
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div className="text-sm text-slate-600 dark:text-slate-300 flex items-center justify-between">
                              <span>No meal-type breakdown available.</span>
                              <span>
                                {Math.round(day.total?.total_calories ?? 0)} kcal · {Math.round(day.total?.total_protein_g ?? 0)}g P ·{' '}
                                {Math.round(day.total?.total_carbs_g ?? 0)}g C · {Math.round(day.total?.total_fat_g ?? 0)}g F
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Meals (edit or delete)</CardTitle>
            </CardHeader>
            <CardContent>
              {isMealsLoading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
                </div>
              ) : meals.length === 0 ? (
                <p className="text-slate-600 dark:text-slate-300">No meals logged yet.</p>
              ) : (
                <div className="space-y-5">
                  {mealsByDay.days.slice(0, 14).map((day) => (
                    <div
                      key={day}
                      className="rounded-lg border border-slate-100 dark:border-slate-800 overflow-hidden"
                    >
                      <div className="px-4 py-3 bg-slate-50 dark:bg-slate-900/40 flex items-center justify-between">
                        <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">{day}</div>
                        <div className="text-xs text-slate-600 dark:text-slate-300">
                          {mealsByDay.map[day]?.length ?? 0} meal(s)
                        </div>
                      </div>

                      <div className="divide-y divide-slate-100 dark:divide-slate-800">
                        {mealsByDay.map[day].map((m) => {
                          const isEditing = editingMealId === m.id;
                          return (
                            <div key={m.id} className="px-4 py-3">
                              {isEditing ? (
                                <div className="space-y-3">
                                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    <div>
                                      <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Meal type</div>
                                      <select
                                        className="w-full rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm dark:[color-scheme:dark]"
                                        value={editMealType}
                                        onChange={(e) => setEditMealType(e.target.value as MealType)}
                                      >
                                        <option value="breakfast">Breakfast</option>
                                        <option value="lunch">Lunch</option>
                                        <option value="dinner">Dinner</option>
                                        <option value="snack">Snack</option>
                                        <option value="unknown">Unknown</option>
                                      </select>
                                    </div>
                                    <div className="md:col-span-2">
                                      <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Meal name</div>
                                      <input
                                        className="w-full rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"
                                        value={editMealName}
                                        onChange={(e) => setEditMealName(e.target.value)}
                                        placeholder="Optional"
                                      />
                                    </div>
                                  </div>

                                  <div>
                                    <div className="text-xs text-slate-500 dark:text-slate-400 mb-2">Foods</div>
                                    <div className="space-y-2">
                                      {editFoods.map((f, idx) => (
                                        <div key={idx} className="grid grid-cols-1 md:grid-cols-5 gap-2">
                                          <input
                                            className="md:col-span-3 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"
                                            value={f.name}
                                            onChange={(e) => {
                                              const next = [...editFoods];
                                              next[idx] = { ...next[idx], name: e.target.value };
                                              setEditFoods(next);
                                            }}
                                            placeholder="Food"
                                          />
                                          <input
                                            className="md:col-span-1 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm"
                                            type="number"
                                            min={1}
                                            value={f.portion_g ?? 100}
                                            onChange={(e) => {
                                              const next = [...editFoods];
                                              next[idx] = { ...next[idx], portion_g: Number(e.target.value) };
                                              setEditFoods(next);
                                            }}
                                          />
                                          <div className="md:col-span-1">
                                            <Button
                                              variant="outline"
                                              onClick={() => {
                                                const next = editFoods.filter((_, i) => i !== idx);
                                                setEditFoods(next.length ? next : [{ name: '', portion_g: 100 }]);
                                              }}
                                            >
                                              Remove
                                            </Button>
                                          </div>
                                        </div>
                                      ))}
                                    </div>

                                    <div className="mt-3 flex flex-wrap gap-2">
                                      <Button
                                        variant="outline"
                                        onClick={() => setEditFoods([...editFoods, { name: '', portion_g: 100 }])}
                                      >
                                        Add food
                                      </Button>
                                      <Button
                                        isLoading={updateMealMutation.isPending}
                                        disabled={updateMealMutation.isPending}
                                        onClick={() => {
                                          const payload: LogMealRequest = {
                                            meal_type: editMealType,
                                            meal_name: editMealName.trim() ? editMealName.trim() : undefined,
                                            food_items: editFoods
                                              .filter((x) => (x.name ?? '').trim().length > 0)
                                              .map((x) => ({ name: x.name.trim(), portion_g: x.portion_g ?? 100 })),
                                          };
                                          updateMealMutation.mutate({ mealId: m.id, payload });
                                        }}
                                      >
                                        Save changes
                                      </Button>
                                      <Button
                                        variant="outline"
                                        onClick={() => {
                                          setEditingMealId(null);
                                        }}
                                      >
                                        Cancel
                                      </Button>
                                      <Button
                                        variant="outline"
                                        onClick={() => deleteMealMutation.mutate(m.id)}
                                        disabled={deleteMealMutation.isPending}
                                      >
                                        Delete
                                      </Button>
                                    </div>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                                  <div>
                                    <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                      {(m.meal_type ?? 'unknown').toString()}
                                      {m.meal_name ? (
                                        <span className="ml-2 text-slate-600 dark:text-slate-300 font-normal">
                                          — {m.meal_name}
                                        </span>
                                      ) : null}
                                    </div>
                                    <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                      {Math.round(m.total_calories ?? 0)} kcal · {Math.round(m.total_protein_g ?? 0)}g P ·{' '}
                                      {Math.round(m.total_carbs_g ?? 0)}g C · {Math.round(m.total_fat_g ?? 0)}g F
                                    </div>
                                  </div>
                                  <div className="flex gap-2">
                                    <Button
                                      variant="outline"
                                      onClick={() => {
                                        setEditingMealId(m.id);
                                        setEditMealType(((m.meal_type as MealType) ?? 'unknown') as MealType);
                                        setEditMealName((m.meal_name ?? '').toString());
                                        const baseFoods =
                                          (m.food_items ?? []).map((x) => ({
                                            name: (x?.name ?? '').toString(),
                                            portion_g:
                                              typeof x?.portion_g === 'number'
                                                ? x.portion_g
                                                : typeof (x as any)?.portion_estimate?.estimated_quantity === 'number' &&
                                                    String((x as any)?.portion_estimate?.unit || '').toLowerCase() === 'g'
                                                  ? (x as any).portion_estimate.estimated_quantity
                                                  : 100,
                                          })) ?? [];
                                        setEditFoods(baseFoods.length ? baseFoods : [{ name: '', portion_g: 100 }]);
                                      }}
                                    >
                                      Edit
                                    </Button>
                                    <Button
                                      variant="outline"
                                      onClick={() => deleteMealMutation.mutate(m.id)}
                                      disabled={deleteMealMutation.isPending}
                                    >
                                      Delete
                                    </Button>
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

