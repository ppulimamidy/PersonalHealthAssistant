'use client';

import { LabResult } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { FileText, Calendar, Building, User, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';

interface LabResultCardProps {
  labResult: LabResult;
  onClick?: () => void;
}

export function LabResultCard({ labResult, onClick }: LabResultCardProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'normal':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'borderline':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      case 'abnormal':
      case 'critical':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal':
        return 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400';
      case 'borderline':
        return 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'abnormal':
        return 'bg-orange-50 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400';
      case 'critical':
        return 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400';
      default:
        return 'bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-400';
    }
  };

  const abnormalCount = labResult.biomarkers.filter(
    (b) => b.status === 'abnormal' || b.status === 'critical'
  ).length;
  const borderlineCount = labResult.biomarkers.filter((b) => b.status === 'borderline').length;

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {labResult.test_type}
            </CardTitle>
            {labResult.test_category && (
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                {labResult.test_category}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
            <Calendar className="w-4 h-4" />
            {format(new Date(labResult.test_date), 'MMM d, yyyy')}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Lab and provider info */}
        <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
          {labResult.lab_name && (
            <div className="flex items-center gap-1">
              <Building className="w-4 h-4" />
              {labResult.lab_name}
            </div>
          )}
          {labResult.ordering_provider && (
            <div className="flex items-center gap-1">
              <User className="w-4 h-4" />
              {labResult.ordering_provider}
            </div>
          )}
        </div>

        {/* Status summary */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-slate-600 dark:text-slate-400">
            {labResult.biomarkers.length} biomarkers
          </span>
          {abnormalCount > 0 && (
            <span className="text-xs px-2 py-1 rounded-full bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400">
              {abnormalCount} abnormal
            </span>
          )}
          {borderlineCount > 0 && (
            <span className="text-xs px-2 py-1 rounded-full bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400">
              {borderlineCount} borderline
            </span>
          )}
        </div>

        {/* Key biomarkers preview */}
        <div className="space-y-2">
          {labResult.biomarkers.slice(0, 3).map((biomarker, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between text-sm"
            >
              <div className="flex items-center gap-2">
                {getStatusIcon(biomarker.status)}
                <span className="text-slate-700 dark:text-slate-300">
                  {biomarker.biomarker_name}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-slate-900 dark:text-slate-100">
                  {biomarker.value} {biomarker.unit}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${getStatusColor(biomarker.status)}`}
                >
                  {biomarker.status}
                </span>
              </div>
            </div>
          ))}
          {labResult.biomarkers.length > 3 && (
            <p className="text-xs text-slate-500 dark:text-slate-400 text-center">
              +{labResult.biomarkers.length - 3} more
            </p>
          )}
        </div>

        {/* AI Summary */}
        {labResult.ai_summary && (
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="flex items-start gap-2">
              <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-blue-900 dark:text-blue-200 line-clamp-2">
                {labResult.ai_summary}
              </p>
            </div>
          </div>
        )}

        {/* Flags */}
        {labResult.flags && labResult.flags.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            {labResult.flags.map((flag, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
              >
                {flag}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
