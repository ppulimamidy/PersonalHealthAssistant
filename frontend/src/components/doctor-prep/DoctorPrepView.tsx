'use client';

import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { HealthScoreRing } from '@/components/ui/HealthScoreRing';
import { doctorPrepService } from '@/services/doctorPrep';
import {
  FileText,
  Download,
  Calendar,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertCircle,
  CheckCircle,
  Printer,
  Activity,
  Heart,
  Flame,
  Brain,
  Zap,
  Utensils,
  HeartPulse,
} from 'lucide-react';
import { formatDate } from '@/lib/utils';
import type { DoctorPrepReport, KeyMetric, TrendSummary, HealthIntelligenceIndicators, CorrelationHighlight } from '@/types';
import toast from 'react-hot-toast';
import jsPDF from 'jspdf';
import { useAuthStore } from '@/stores/authStore';

function buildDoctorQuestions(report: DoctorPrepReport): string[] {
  const questions: string[] = [];

  // Prefer the report's own "areas to discuss" as clinician-facing questions.
  for (const c of report.summary.concerns ?? []) {
    if (questions.length >= 3) break;
    questions.push(c.endsWith('?') ? c : `${c}?`);
  }

  // Fallback: turn top AI insight titles into questions.
  if (questions.length < 3) {
    for (const i of report.ai_insights ?? []) {
      if (questions.length >= 3) break;
      const q = `Could you help me interpret: ${i.title}?`;
      if (!questions.includes(q)) questions.push(q);
    }
  }

  // Final fallback.
  if (questions.length < 3) {
    questions.push('Are these recent changes something I should monitor more closely?');
  }

  return questions.slice(0, 3);
}

function MetricCard({ metric }: { metric: KeyMetric }) {
  const statusColors = {
    excellent: 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20',
    good: 'border-lime-200 dark:border-lime-800 bg-lime-50 dark:bg-lime-900/20',
    moderate: 'border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20',
    poor: 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20',
  };

  const statusIcons = {
    excellent: <CheckCircle className="w-5 h-5 text-green-500" />,
    good: <CheckCircle className="w-5 h-5 text-lime-500" />,
    moderate: <AlertCircle className="w-5 h-5 text-amber-500" />,
    poor: <AlertCircle className="w-5 h-5 text-red-500" />,
  };

  return (
    <div className={`p-4 rounded-lg border ${statusColors[metric.status]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-600 dark:text-slate-300">{metric.name}</span>
        {statusIcons[metric.status]}
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">{metric.value}</span>
        <span className="text-sm text-slate-500 dark:text-slate-400">{metric.unit}</span>
      </div>
      {metric.comparison_to_average !== 0 && (
        <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          {metric.comparison_to_average > 0 ? '+' : ''}
          {metric.comparison_to_average}% vs average
        </div>
      )}
    </div>
  );
}

function TrendItem({ trend }: { trend: TrendSummary }) {
  const icons = {
    improving: <TrendingUp className="w-4 h-4 text-green-500" />,
    declining: <TrendingDown className="w-4 h-4 text-red-500" />,
    stable: <Minus className="w-4 h-4 text-slate-400" />,
  };

  const colors = {
    improving: 'text-green-600 dark:text-green-400',
    declining: 'text-red-600 dark:text-red-400',
    stable: 'text-slate-600 dark:text-slate-400',
  };

  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-slate-600 dark:text-slate-300">{trend.metric}</span>
      <div className="flex items-center gap-2">
        {icons[trend.direction]}
        <span className={`text-sm font-medium ${colors[trend.direction]}`}>
          {trend.direction === 'stable' ? 'Stable' : `${Math.abs(trend.percentage_change)}%`}
        </span>
      </div>
    </div>
  );
}

const TREND_ICONS: Record<string, React.ReactNode> = {
  improving: <TrendingUp className="w-4 h-4 text-green-500" />,
  declining: <TrendingDown className="w-4 h-4 text-red-500" />,
  stable: <Minus className="w-4 h-4 text-slate-400" />,
};

const INFLAMMATION_STYLES: Record<string, { bg: string; text: string }> = {
  low: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300' },
  moderate: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-300' },
  elevated: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-300' },
  high: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300' },
};

function IntelligencePanel({ indicators }: { indicators: HealthIntelligenceIndicators }) {
  const inflStyle = INFLAMMATION_STYLES[indicators.inflammation_risk] || INFLAMMATION_STYLES.moderate;
  const stressColor = indicators.stress_index > 60
    ? 'text-red-600 dark:text-red-400'
    : indicators.stress_index > 40
      ? 'text-amber-600 dark:text-amber-400'
      : 'text-green-600 dark:text-green-400';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          Health Intelligence
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {/* Sleep Trend */}
          <div className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
            <Activity className="w-5 h-5 text-indigo-500 mx-auto mb-1" />
            <p className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">Sleep Trend</p>
            <div className="flex items-center justify-center gap-1 mt-1">
              {TREND_ICONS[indicators.sleep_score_trend]}
              <span className="text-sm font-medium text-slate-800 dark:text-slate-200 capitalize">
                {indicators.sleep_score_trend}
              </span>
            </div>
          </div>

          {/* HRV Trend */}
          <div className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
            <Heart className="w-5 h-5 text-pink-500 mx-auto mb-1" />
            <p className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">HRV Trend</p>
            <div className="flex items-center justify-center gap-1 mt-1">
              {TREND_ICONS[indicators.hrv_trend]}
              <span className="text-sm font-medium text-slate-800 dark:text-slate-200 capitalize">
                {indicators.hrv_trend}
              </span>
            </div>
          </div>

          {/* Nutrition Quality */}
          <div className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
            <Utensils className="w-5 h-5 text-emerald-500 mx-auto mb-1" />
            <p className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">Nutrition</p>
            <p className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1">
              {indicators.nutrition_quality_score}
            </p>
            <p className="text-[10px] text-slate-400">/100</p>
          </div>

          {/* Inflammation Risk */}
          <div className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
            <Flame className="w-5 h-5 text-orange-500 mx-auto mb-1" />
            <p className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">Inflammation</p>
            <span className={`inline-block mt-1 text-xs font-semibold px-2 py-0.5 rounded-full ${inflStyle.bg} ${inflStyle.text} capitalize`}>
              {indicators.inflammation_risk}
            </span>
          </div>

          {/* Stress Index */}
          <div className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
            <Brain className="w-5 h-5 text-purple-500 mx-auto mb-1" />
            <p className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">Stress</p>
            <p className={`text-lg font-bold mt-1 ${stressColor}`}>
              {indicators.stress_index}
            </p>
            <p className="text-[10px] text-slate-400">/100</p>
          </div>
        </div>

        {/* Personalized Actions */}
        {indicators.personalized_actions.length > 0 && (
          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700">
            <p className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-2">Recommended Actions</p>
            <ul className="space-y-1.5">
              {indicators.personalized_actions.map((action, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-300">
                  <CheckCircle className="w-4 h-4 text-primary-500 mt-0.5 shrink-0" />
                  {action}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function CorrelationsPanel({ correlations }: { correlations: CorrelationHighlight[] }) {
  const STRENGTH_COLORS: Record<string, string> = {
    strong: 'text-purple-600 dark:text-purple-400',
    moderate: 'text-blue-600 dark:text-blue-400',
    weak: 'text-slate-500 dark:text-slate-400',
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <HeartPulse className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          Key Nutrition Correlations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {correlations.map((c, idx) => (
            <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                  {c.effect_description || `${c.metric_a_label} vs ${c.metric_b_label}`}
                </p>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {c.metric_a_label} &harr; {c.metric_b_label}
                  </span>
                  <span className={`text-xs font-semibold capitalize ${STRENGTH_COLORS[c.strength] || STRENGTH_COLORS.weak}`}>
                    {c.strength}
                  </span>
                  <span className="text-xs text-slate-400">
                    r={c.correlation_coefficient.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ReportView({ report }: { report: DoctorPrepReport }) {
  const { user, profile } = useAuthStore();
  const doctorQuestions = buildDoctorQuestions(report);

  const handleExportPDF = async () => {
    const doc = new jsPDF();
    let yPos = 20;

    // Title
    doc.setFontSize(20);
    doc.text('Health Summary Report', 20, yPos);
    yPos += 15;

    // Date range
    doc.setFontSize(12);
    doc.text(
      `Period: ${formatDate(report.date_range.start)} - ${formatDate(report.date_range.end)}`,
      20,
      yPos
    );
    yPos += 20;

    // Patient profile (if available)
    if (user || profile) {
      doc.setFontSize(12);
      const lines: string[] = [];
      if (user?.name) lines.push(`Name: ${user.name}`);
      if (profile?.age != null) lines.push(`Age: ${profile.age}`);
      if (profile?.gender) lines.push(`Gender: ${profile.gender}`);
      if (profile?.weight_kg != null) lines.push(`Weight: ${profile.weight_kg} kg`);
      if (lines.length > 0) {
        doc.text('Patient profile:', 20, yPos);
        yPos += 8;
        doc.setFontSize(11);
        lines.forEach((l) => {
          doc.text(`• ${l}`, 25, yPos);
          yPos += 7;
        });
        yPos += 10;
      }
    }

    // Overall Score
    doc.setFontSize(16);
    doc.text(`Overall Health Score: ${report.summary.overall_health_score}`, 20, yPos);
    yPos += 15;

    // Key Metrics
    doc.setFontSize(14);
    doc.text('Key Metrics:', 20, yPos);
    yPos += 10;
    doc.setFontSize(11);
    report.summary.key_metrics.forEach((metric) => {
      doc.text(`• ${metric.name}: ${metric.value} ${metric.unit} (${metric.status})`, 25, yPos);
      yPos += 7;
    });
    yPos += 10;

    // Trends
    doc.setFontSize(14);
    doc.text('Trends:', 20, yPos);
    yPos += 10;
    doc.setFontSize(11);
    report.summary.trends.forEach((trend) => {
      doc.text(
        `• ${trend.metric}: ${trend.direction} (${trend.percentage_change}%)`,
        25,
        yPos
      );
      yPos += 7;
    });
    yPos += 10;

    // Concerns
    if (report.summary.concerns.length > 0) {
      doc.setFontSize(14);
      doc.text('Areas of Concern:', 20, yPos);
      yPos += 10;
      doc.setFontSize(11);
      report.summary.concerns.forEach((concern) => {
        doc.text(`• ${concern}`, 25, yPos);
        yPos += 7;
      });
      yPos += 10;
    }

    // Improvements
    if (report.summary.improvements.length > 0) {
      doc.setFontSize(14);
      doc.text('Improvements:', 20, yPos);
      yPos += 10;
      doc.setFontSize(11);
      report.summary.improvements.forEach((improvement) => {
        doc.text(`• ${improvement}`, 25, yPos);
        yPos += 7;
      });
      yPos += 10;
    }

    // Health Intelligence
    if (report.health_intelligence) {
      const hi = report.health_intelligence;
      doc.setFontSize(14);
      doc.text('Health Intelligence:', 20, yPos);
      yPos += 10;
      doc.setFontSize(11);
      doc.text(`• Sleep Trend: ${hi.sleep_score_trend}`, 25, yPos); yPos += 7;
      doc.text(`• HRV Trend: ${hi.hrv_trend}`, 25, yPos); yPos += 7;
      doc.text(`• Nutrition Quality: ${hi.nutrition_quality_score}/100`, 25, yPos); yPos += 7;
      doc.text(`• Inflammation Risk: ${hi.inflammation_risk}`, 25, yPos); yPos += 7;
      doc.text(`• Stress Index: ${hi.stress_index}/100`, 25, yPos); yPos += 7;
      if (hi.personalized_actions.length > 0) {
        yPos += 3;
        doc.text('Actions:', 25, yPos); yPos += 7;
        hi.personalized_actions.forEach((a) => {
          doc.text(`  - ${a}`, 28, yPos); yPos += 7;
        });
      }
      yPos += 10;
    }

    // Nutrition Correlations
    if (report.nutrition_correlations && report.nutrition_correlations.length > 0) {
      doc.setFontSize(14);
      doc.text('Key Nutrition Correlations:', 20, yPos);
      yPos += 10;
      doc.setFontSize(11);
      report.nutrition_correlations.forEach((c) => {
        const desc = c.effect_description || `${c.metric_a_label} vs ${c.metric_b_label}`;
        doc.text(`• ${desc} (r=${c.correlation_coefficient.toFixed(2)}, ${c.strength})`, 25, yPos);
        yPos += 7;
      });
      yPos += 10;
    }

    // Condition Notes
    if (report.condition_specific_notes && report.condition_specific_notes.length > 0) {
      doc.setFontSize(14);
      doc.text('Health Conditions:', 20, yPos);
      yPos += 10;
      doc.setFontSize(11);
      report.condition_specific_notes.forEach((n) => {
        doc.text(`• ${n}`, 25, yPos);
        yPos += 7;
      });
      yPos += 10;
    }

    // Questions for clinician
    doc.setFontSize(14);
    doc.text('Questions to ask your clinician:', 20, yPos);
    yPos += 10;
    doc.setFontSize(11);
    doctorQuestions.forEach((q) => {
      doc.text(`• ${q}`, 25, yPos);
      yPos += 7;
    });

    doc.save(`health-report-${report.date_range.end}.pdf`);
    toast.success('PDF exported successfully');
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6" id="report-content">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Health Summary</h2>
          <p className="text-slate-500 dark:text-slate-400">
            {formatDate(report.date_range.start)} - {formatDate(report.date_range.end)}
          </p>
        </div>
        <div className="flex gap-2 print:hidden">
          <Button onClick={handlePrint} variant="outline">
            <Printer className="w-4 h-4 mr-2" />
            Print
          </Button>
          <Button onClick={handleExportPDF}>
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* Patient profile */}
      {(user || profile) && (
        <Card>
          <CardHeader>
            <CardTitle>Patient profile</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-slate-500 dark:text-slate-400">Name</div>
                <div className="font-medium text-slate-900 dark:text-slate-100">{user?.name ?? '—'}</div>
              </div>
              <div>
                <div className="text-slate-500 dark:text-slate-400">Age</div>
                <div className="font-medium text-slate-900 dark:text-slate-100">{profile?.age ?? '—'}</div>
              </div>
              <div>
                <div className="text-slate-500 dark:text-slate-400">Gender</div>
                <div className="font-medium text-slate-900 dark:text-slate-100">{profile?.gender ?? '—'}</div>
              </div>
              <div>
                <div className="text-slate-500 dark:text-slate-400">Weight</div>
                <div className="font-medium text-slate-900 dark:text-slate-100">
                  {profile?.weight_kg != null ? `${profile.weight_kg} kg` : '—'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overall Score */}
      <Card>
        <div className="flex items-center gap-8">
          <HealthScoreRing
            score={report.summary.overall_health_score}
            size="lg"
            label="Overall Health"
          />
          <div className="flex-1">
            <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-4">Key Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {report.summary.key_metrics.map((metric, idx) => (
                <MetricCard key={idx} metric={metric} />
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Health Intelligence Indicators */}
      {report.health_intelligence && (
        <IntelligencePanel indicators={report.health_intelligence} />
      )}

      {/* Nutrition Correlations */}
      {report.nutrition_correlations && report.nutrition_correlations.length > 0 && (
        <CorrelationsPanel correlations={report.nutrition_correlations} />
      )}

      {/* Condition-Specific Notes */}
      {report.condition_specific_notes && report.condition_specific_notes.length > 0 && (
        <Card className="border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-900/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HeartPulse className="w-5 h-5 text-purple-500" />
              Health Conditions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {report.condition_specific_notes.map((note, idx) => (
                <li key={idx} className="text-sm text-slate-700 dark:text-slate-300">
                  • {note}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Trends */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-slate-100 dark:divide-slate-700">
              {report.summary.trends.map((trend, idx) => (
                <TrendItem key={idx} trend={trend} />
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          {/* Questions */}
          <Card className="border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                Questions to ask your clinician
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {doctorQuestions.map((q, idx) => (
                  <li key={idx} className="text-sm text-slate-700 dark:text-slate-300">
                    • {q}
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                This report is for discussion support only and is not medical advice.
              </p>
            </CardContent>
          </Card>

          {/* Concerns */}
          {report.summary.concerns.length > 0 && (
            <Card className="border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-amber-500" />
                  Areas to Discuss
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {report.summary.concerns.map((concern, idx) => (
                    <li key={idx} className="text-sm text-slate-700 dark:text-slate-300">
                      • {concern}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Improvements */}
          {report.summary.improvements.length > 0 && (
            <Card className="border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  Positive Progress
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {report.summary.improvements.map((improvement, idx) => (
                    <li key={idx} className="text-sm text-slate-700 dark:text-slate-300">
                      • {improvement}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export function DoctorPrepView() {
  const [selectedDays, setSelectedDays] = useState<7 | 30 | 90>(30);
  const [generatedReport, setGeneratedReport] = useState<DoctorPrepReport | null>(null);
  const searchParams = useSearchParams();
  const autoTriggeredRef = useRef(false);

  const generateMutation = useMutation({
    mutationFn: (days: 7 | 30 | 90) => doctorPrepService.generateReport(days),
    onSuccess: (data) => {
      setGeneratedReport(data);
      toast.success('Report generated successfully');
    },
    onError: () => {
      toast.error('Failed to generate report');
    },
  });

  const reportsQuery = useQuery({
    queryKey: ['doctor-prep-reports'],
    queryFn: doctorPrepService.getReports,
  });

  const latestReport = reportsQuery.data?.[0];

  useEffect(() => {
    if (autoTriggeredRef.current) return;

    const auto = searchParams.get('autogenerate');
    if (auto !== '1') return;

    const daysParam = Number(searchParams.get('days') ?? '30');
    const days: 7 | 30 | 90 = daysParam === 7 ? 7 : daysParam === 90 ? 90 : 30;

    autoTriggeredRef.current = true;
    setSelectedDays(days);
    generateMutation.mutate(days);
  }, [searchParams, generateMutation]);

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Doctor Visit Prep</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Generate a summary to share with your healthcare provider
          </p>
        </div>
      </div>

      {/* Generate Section */}
      <Card className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
              <FileText className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-100">Generate New Report</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Create a comprehensive health summary for your doctor
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={selectedDays}
              onChange={(e) => setSelectedDays(Number(e.target.value) as 7 | 30 | 90)}
              className="px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
            <Button
              onClick={() => generateMutation.mutate(selectedDays)}
              isLoading={generateMutation.isPending}
            >
              <Calendar className="w-4 h-4 mr-2" />
              Generate Report
            </Button>
          </div>
        </div>
      </Card>

      {/* Report Display */}
      {generatedReport ? (
        <ReportView report={generatedReport} />
      ) : generateMutation.data ? (
        <ReportView report={generateMutation.data} />
      ) : latestReport ? (
        <ReportView report={latestReport} />
      ) : reportsQuery.isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : generateMutation.isError ? (
        <Card className="text-center py-12">
          <FileText className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-700 dark:text-slate-200 font-medium">Couldn’t generate the report.</p>
          <p className="text-sm text-slate-400 dark:text-slate-500 mt-2">
            Try again, or check that your backend is reachable and CORS is configured.
          </p>
        </Card>
      ) : (
        <Card className="text-center py-12">
          <FileText className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">No reports generated yet.</p>
          <p className="text-sm text-slate-400 dark:text-slate-500 mt-2">
            Generate your first report to prepare for your doctor visit.
          </p>
        </Card>
      )}
    </div>
  );
}
