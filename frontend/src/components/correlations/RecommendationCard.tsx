'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { ChevronDown, ChevronUp, Apple, AlertTriangle, Lightbulb } from 'lucide-react';
import type { Recommendation } from '@/types';

const PRIORITY_STYLES: Record<string, { bg: string; text: string }> = {
  high: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300' },
  medium: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-300' },
  low: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300' },
};

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export function RecommendationCard({ recommendation: r }: RecommendationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const style = PRIORITY_STYLES[r.priority] || PRIORITY_STYLES.medium;

  return (
    <Card className="transition-all hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${style.bg} ${style.text}`}>
              {r.priority}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 capitalize">
              {r.category}
            </span>
          </div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {r.title}
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
            {r.description}
          </p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="ml-2 p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Food suggestions preview */}
      {r.foods.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {r.foods.slice(0, expanded ? r.foods.length : 3).map((food, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300"
            >
              <Apple className="w-3 h-3" />
              {food.name}
            </span>
          ))}
          {!expanded && r.foods.length > 3 && (
            <span className="text-xs text-slate-400">+{r.foods.length - 3} more</span>
          )}
        </div>
      )}

      {/* Expanded detail */}
      {expanded && (
        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700 space-y-3">
          {r.foods.map((food, i) => (
            <div key={i} className="flex items-start gap-2">
              <Apple className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <div>
                <span className="text-sm font-medium text-slate-800 dark:text-slate-200">{food.name}</span>
                <p className="text-xs text-slate-500 dark:text-slate-400">{food.reason}</p>
              </div>
            </div>
          ))}
          {r.rationale && (
            <div className="flex items-start gap-2 pt-2">
              <Lightbulb className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
              <p className="text-xs text-slate-500 dark:text-slate-400 italic">{r.rationale}</p>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

interface PatternBannerProps {
  pattern: string;
  label: string;
  severity: string;
  signals: string[];
}

export function PatternBanner({ label, severity, signals }: PatternBannerProps) {
  const sevColor = severity === 'high'
    ? 'border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
    : 'border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20';

  return (
    <div className={`rounded-lg border p-3 ${sevColor}`}>
      <div className="flex items-center gap-2">
        <AlertTriangle className={`w-4 h-4 ${severity === 'high' ? 'text-red-500' : 'text-amber-500'}`} />
        <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">{label}</span>
        <span className={`text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded ${
          severity === 'high'
            ? 'bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200'
            : 'bg-amber-200 text-amber-800 dark:bg-amber-800 dark:text-amber-200'
        }`}>
          {severity}
        </span>
      </div>
      <ul className="mt-1.5 space-y-0.5">
        {signals.map((s, i) => (
          <li key={i} className="text-xs text-slate-600 dark:text-slate-400">• {s}</li>
        ))}
      </ul>
    </div>
  );
}
