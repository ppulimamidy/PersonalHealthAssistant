'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { healthConditionsService } from '@/services/healthConditions';
import { CheckCircle2, ClipboardList } from 'lucide-react';
import type { HealthQuestion, QuestionnaireData } from '@/types';

export function HealthQuestionnaire() {
  const queryClient = useQueryClient();
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [submitted, setSubmitted] = useState(false);

  const { data, isLoading } = useQuery<QuestionnaireData>({
    queryKey: ['health-questionnaire'],
    queryFn: () => healthConditionsService.getQuestionnaire(),
    staleTime: 1000 * 60 * 10,
  });

  const submitMutation = useMutation({
    mutationFn: (ans: Record<string, unknown>) =>
      healthConditionsService.submitQuestionnaire(ans),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health-questionnaire'] });
      queryClient.invalidateQueries({ queryKey: ['health-profile'] });
      setSubmitted(true);
    },
  });

  if (isLoading) {
    return (
      <Card className="animate-pulse">
        <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-slate-200 dark:bg-slate-700 rounded" />
          ))}
        </div>
      </Card>
    );
  }

  if (submitted || data?.profile_completed) {
    return (
      <Card>
        <div className="text-center py-6">
          <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {submitted ? 'Profile Updated!' : 'Questionnaire Completed'}
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Your health profile is being used to personalize recommendations.
          </p>
          {data?.profile_completed && !submitted && (
            <button
              onClick={() => setSubmitted(false)}
              className="mt-4 text-sm text-primary-600 dark:text-primary-400 hover:underline"
            >
              Update answers
            </button>
          )}
        </div>
      </Card>
    );
  }

  const questions = data?.questions || [];

  const handleAnswer = (questionId: string, value: unknown) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleMultiToggle = (questionId: string, optionValue: string) => {
    setAnswers((prev) => {
      const current = (prev[questionId] as string[]) || [];
      const updated = current.includes(optionValue)
        ? current.filter((v) => v !== optionValue)
        : [...current, optionValue];
      return { ...prev, [questionId]: updated };
    });
  };

  const handleSubmit = () => {
    submitMutation.mutate(answers);
  };

  // Group by section
  const sections = data?.sections || [];
  const groupedQuestions: Record<string, HealthQuestion[]> = {};
  for (const q of questions) {
    const cat = q.category;
    if (!groupedQuestions[cat]) groupedQuestions[cat] = [];
    groupedQuestions[cat].push(q);
  }

  const SECTION_LABELS: Record<string, string> = {
    goals: 'Health Goals',
    diet: 'Dietary Preferences',
    supplements: 'Supplements & Medications',
    medications: 'Medications',
    lifestyle: 'Lifestyle',
    condition_specific: 'Condition-Specific',
  };

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex items-center gap-2 mb-1">
          <ClipboardList className="w-5 h-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Health Questionnaire
          </h3>
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Help us personalize your recommendations by answering a few questions.
        </p>
      </Card>

      {sections.map((section) => {
        const sectionQuestions = groupedQuestions[section];
        if (!sectionQuestions || sectionQuestions.length === 0) return null;

        return (
          <Card key={section}>
            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4">
              {SECTION_LABELS[section] || section}
            </h4>
            <div className="space-y-5">
              {sectionQuestions.map((q) => (
                <QuestionField
                  key={q.id}
                  question={q}
                  value={answers[q.id]}
                  onAnswer={(val) => handleAnswer(q.id, val)}
                  onMultiToggle={(val) => handleMultiToggle(q.id, val)}
                />
              ))}
            </div>
          </Card>
        );
      })}

      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={submitMutation.isPending}
          className="px-6 py-2.5 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitMutation.isPending ? 'Saving...' : 'Save Profile'}
        </button>
      </div>
    </div>
  );
}

interface QuestionFieldProps {
  question: HealthQuestion;
  value: unknown;
  onAnswer: (value: unknown) => void;
  onMultiToggle: (value: string) => void;
}

function QuestionField({ question: q, value, onAnswer, onMultiToggle }: QuestionFieldProps) {
  return (
    <div>
      <label className="block text-sm text-slate-700 dark:text-slate-300 mb-2">
        {q.question}
        {q.required && <span className="text-red-400 ml-1">*</span>}
      </label>

      {q.type === 'single_choice' && q.options && (
        <div className="space-y-1.5">
          {q.options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onAnswer(opt.value)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm border transition-colors ${
                value === opt.value
                  ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300 dark:border-primary-600'
                  : 'border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}

      {q.type === 'multi_choice' && q.options && (
        <div className="flex flex-wrap gap-2">
          {q.options.map((opt) => {
            const selected = Array.isArray(value) && (value as string[]).includes(opt.value);
            return (
              <button
                key={opt.value}
                onClick={() => onMultiToggle(opt.value)}
                className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                  selected
                    ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300 dark:border-primary-600'
                    : 'border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      )}

      {q.type === 'text' && (
        <textarea
          value={(value as string) || ''}
          onChange={(e) => onAnswer(e.target.value)}
          rows={2}
          className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          placeholder="Type your answer..."
        />
      )}

      {q.type === 'scale' && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">{q.scale_min ?? 1}</span>
          <input
            type="range"
            min={q.scale_min ?? 1}
            max={q.scale_max ?? 10}
            value={(value as number) || q.scale_min || 1}
            onChange={(e) => onAnswer(Number(e.target.value))}
            className="flex-1 accent-primary-600"
          />
          <span className="text-xs text-slate-400">{q.scale_max ?? 10}</span>
          <span className="text-sm font-medium text-primary-600 dark:text-primary-400 w-6 text-center">
            {(value as number) || q.scale_min || 1}
          </span>
        </div>
      )}
    </div>
  );
}
