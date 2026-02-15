import { TrendCharts } from '@/components/trends/TrendCharts';
import { TrendingUp } from 'lucide-react';

export default function TrendsPage() {
  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Trends</h1>
        </div>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Track your health metrics over time
        </p>
      </div>
      <TrendCharts />
    </div>
  );
}
