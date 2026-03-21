'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/services/api';
import { Microscope, Dna, ScanLine, FlaskConical } from 'lucide-react';

type RecordType = 'pathology' | 'genomic' | 'imaging';

interface MedicalRecord {
  id: string;
  record_type: RecordType;
  title: string;
  report_date?: string;
  ai_summary?: string;
  extracted_data?: any;
}

const TYPE_CONFIG: Record<RecordType, { label: string; Icon: any; color: string }> = {
  pathology: { label: 'Pathology', Icon: Microscope, color: '#F87171' },
  genomic: { label: 'Genomic', Icon: Dna, color: '#818CF8' },
  imaging: { label: 'Imaging', Icon: ScanLine, color: '#60A5FA' },
};

export default function MedicalRecordsPage() {
  const { user } = useAuth();
  const [activeType, setActiveType] = useState<RecordType | 'all'>('all');

  const { data: records, isLoading } = useQuery({
    queryKey: ['medical-records', activeType],
    queryFn: async () => {
      const params = activeType !== 'all' ? `?record_type=${activeType}` : '';
      const { data } = await api.get(`/api/v1/medical-records${params}`);
      return (data?.records ?? []).map((r: any) => ({
        ...r,
        extracted_data: typeof r.extracted_data === 'string' ? JSON.parse(r.extracted_data) : r.extracted_data,
      })) as MedicalRecord[];
    },
    enabled: Boolean(user),
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Medical Records</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Pathology, genomic profiles, and imaging reports</p>
      </div>

      {/* Type filter */}
      <div className="flex gap-2">
        <Button
          variant={activeType === 'all' ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setActiveType('all')}
        >All</Button>
        {(Object.entries(TYPE_CONFIG) as [RecordType, typeof TYPE_CONFIG[RecordType]][]).map(([key, cfg]) => (
          <Button
            key={key}
            variant={activeType === key ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setActiveType(key)}
          >
            <cfg.Icon className="w-3.5 h-3.5 mr-1" />
            {cfg.label}
          </Button>
        ))}
      </div>

      {/* Records */}
      {isLoading ? (
        <p className="text-slate-400 py-8 text-center">Loading...</p>
      ) : !records || records.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FlaskConical className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-500 dark:text-slate-400">No medical records yet</p>
            <p className="text-sm text-slate-400 mt-1">Upload pathology, genomic, or imaging reports from the mobile app</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {records.map((rec) => {
            const cfg = TYPE_CONFIG[rec.record_type] ?? { label: rec.record_type, color: '#526380' };
            const ed = rec.extracted_data ?? {};

            return (
              <Card key={rec.id}>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: cfg.color }} />
                    <span className="text-xs font-medium uppercase tracking-wider" style={{ color: cfg.color }}>{cfg.label}</span>
                    {rec.report_date && <span className="text-xs text-slate-400 ml-auto">{rec.report_date}</span>}
                  </div>
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-1">{rec.title}</h3>

                  {/* Type-specific rendering */}
                  {rec.record_type === 'genomic' && ed.mutations?.length > 0 && (
                    <div className="space-y-2 mt-2">
                      {ed.mutations.map((m: any, i: number) => (
                        <div key={i} className="p-2 rounded-lg bg-slate-50 dark:bg-slate-700/50">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-slate-900 dark:text-slate-100">{m.gene} {m.exon ?? ''}</span>
                            {m.classification?.tier && (
                              <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: '#818CF815', color: '#818CF8' }}>{m.classification.tier}</span>
                            )}
                            {m.sensitivity && (
                              <span className="text-xs px-1.5 py-0.5 rounded" style={{
                                backgroundColor: m.sensitivity === 'Sensitive' ? '#6EE7B715' : '#F8717115',
                                color: m.sensitivity === 'Sensitive' ? '#6EE7B7' : '#F87171',
                              }}>{m.sensitivity}</span>
                            )}
                          </div>
                          {m.protein_change && <p className="text-xs text-slate-500 mt-0.5">{m.protein_change}{m.vaf ? ` · VAF ${m.vaf}` : ''}</p>}
                          {m.sensitive_therapies?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {m.sensitive_therapies.map((t: string, ti: number) => (
                                <span key={ti} className="text-xs px-1.5 py-0.5 rounded bg-green-500/10 text-green-500">{t}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {rec.record_type === 'pathology' && ed.stage?.overall && (
                    <div className="flex gap-2 mt-2">
                      <span className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-500 font-medium">{ed.stage.overall}</span>
                      {ed.grade && <span className="text-xs px-2 py-0.5 rounded bg-slate-500/10 text-slate-400">{ed.grade}</span>}
                    </div>
                  )}

                  {rec.record_type === 'imaging' && ed.findings?.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {ed.findings.slice(0, 3).map((f: any, i: number) => (
                        <p key={i} className="text-xs text-slate-500">• {f.location}: {f.description}{f.measurement_cm ? ` (${f.measurement_cm}cm)` : ''}</p>
                      ))}
                    </div>
                  )}

                  {rec.ai_summary && <p className="text-xs text-slate-500 italic mt-2">{rec.ai_summary}</p>}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
