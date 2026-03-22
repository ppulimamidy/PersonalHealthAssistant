'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/services/api';
import { Search, FlaskConical, Pill, Stethoscope, Share2, ExternalLink, Sparkles, Loader2, Dna, Activity, ClipboardList, TestTube2, ArrowRight, ShieldAlert } from 'lucide-react';

interface TreatmentOption {
  name: string;
  type: string;
  evidence_level: string;
  efficacy: string;
  guideline_position: string;
  side_effects: string;
  compatibility: string;
  notes: string;
}

interface DrugProfile {
  name: string;
  drug_class: string;
  mechanism: string;
  efficacy_summary: string;
  side_effects: { common: string[]; serious: string[] };
  interactions_with_user_meds: string[];
  guideline_position: string;
}

interface Trial {
  nct_id: string;
  title: string;
  phase: string;
  status: string;
  summary: string;
  sponsor: string;
  locations: string[];
}

const TOPIC_ICONS: Record<string, any> = {
  treatment: Stethoscope,
  trial: TestTube2,
  guideline: ClipboardList,
  supplement: Pill,
  monitoring: Activity,
  genomic: Dna,
};

const URGENCY_CONFIG = {
  high: { color: '#F87171', label: 'Urgent' },
  medium: { color: '#FBBF24', label: 'Recommended' },
  low: { color: '#60A5FA', label: 'Informational' },
} as const;

export default function ClinicalResearchPage() {
  const { user } = useAuth();
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [synthesis, setSynthesis] = useState<string | null>(null);
  const [report, setReport] = useState<any>(null);
  const [drugs, setDrugs] = useState<DrugProfile[]>([]);
  const [trials, setTrials] = useState<Trial[]>([]);
  const [articles, setArticles] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Personalized research topics
  const { data: topicsData, isLoading: topicsLoading } = useQuery({
    queryKey: ['research-topics'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/research/personalized-topics');
      return data as {
        topics: Array<{
          title: string;
          description: string;
          category: string;
          urgency: 'high' | 'medium' | 'low';
          search_query: string;
          key_finding: string;
        }>;
        treatment_ladders: Array<{ condition: string; ladder: Array<{ step: string; treatment: string }> }>;
        summary: string;
      };
    },
    staleTime: 10 * 60 * 1000,
    enabled: Boolean(user),
  });

  async function doSearch(searchQuery: string) {
    if (!searchQuery.trim() || searchQuery.length < 3) return;
    setSearching(true);
    setError(null);
    setSynthesis(null);
    setReport(null);
    setDrugs([]);
    setTrials([]);
    setArticles([]);

    try {
      // Phase 1: Fast synthesis
      const { data: synthData } = await api.post('/api/v1/research/clinical-search',
        { query: searchQuery.trim(), search_type: 'all' },
        { timeout: 60000 },
      );
      setSynthesis(synthData?.ai_synthesis ?? null);
      setArticles(synthData?.articles ?? []);
      setSearching(false);

      // Phase 2: Detailed treatment options + trials (background)
      const [detailsResp, trialsResp] = await Promise.allSettled([
        api.post('/api/v1/research/clinical-search/details', { query: searchQuery.trim() }, { timeout: 90000 }),
        api.get('/api/v1/research/trials', { params: { condition: searchQuery.trim(), max_results: 5 }, timeout: 15000 }),
      ]);
      if (detailsResp.status === 'fulfilled') {
        setReport(detailsResp.value.data?.treatment_report ?? null);
        setDrugs(detailsResp.value.data?.drugs_mentioned ?? []);
      }
      if (trialsResp.status === 'fulfilled') {
        setTrials(trialsResp.value.data?.trials ?? []);
      }
    } catch {
      setError('Search failed or timed out. Try a shorter query.');
      setSearching(false);
    }
  }

  function handleSearch() { doSearch(query); }
  function handleSearchWithQuery(q: string) { setQuery(q); doSearch(q); }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Clinical Research</h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Treatments, drugs, clinical trials & guidelines — personalized to your health profile</p>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search treatments, drugs, trials..."
                className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <Button onClick={handleSearch} isLoading={searching}>
              {searching ? 'Searching...' : 'Search'}
            </Button>
          </div>

          {/* Quick suggestions — personalized from topics */}
          {!synthesis && !searching && (
            <div className="flex flex-wrap gap-2 mt-3">
              {(topicsData?.topics ?? []).slice(0, 4).map((t) => (
                <button
                  key={t.search_query}
                  onClick={() => { setQuery(t.search_query); }}
                  className="px-3 py-1.5 text-xs rounded-full border border-indigo-500/30 text-indigo-500 hover:bg-indigo-500/10 transition-colors"
                >
                  {t.title}
                </button>
              ))}
              {(!topicsData?.topics || topicsData.topics.length === 0) && !topicsLoading && (
                <>
                  {['PCOS treatments', 'Metformin alternatives', 'Latest cancer immunotherapy', 'Statin comparison'].map((s) => (
                    <button key={s} onClick={() => setQuery(s)} className="px-3 py-1.5 text-xs rounded-full border border-indigo-500/30 text-indigo-500 hover:bg-indigo-500/10 transition-colors">
                      {s}
                    </button>
                  ))}
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Personalized Research Intelligence */}
      {!synthesis && !searching && (
        <>
          {topicsLoading ? (
            <div className="flex flex-col items-center py-8 gap-3">
              <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
              <p className="text-sm text-slate-400">Analyzing your health profile for research recommendations...</p>
            </div>
          ) : topicsData?.topics && topicsData.topics.length > 0 ? (
            <div className="space-y-4">
              {/* Summary */}
              {topicsData.summary && (
                <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10">
                  <div className="flex items-start gap-2.5">
                    <Sparkles className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" />
                    <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{topicsData.summary}</p>
                  </div>
                </div>
              )}

              {/* Topic Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {topicsData.topics.map((topic, i) => {
                  const urgency = URGENCY_CONFIG[topic.urgency] ?? URGENCY_CONFIG.medium;
                  const Icon = TOPIC_ICONS[topic.category] ?? FlaskConical;
                  return (
                    <button
                      key={i}
                      onClick={() => { setQuery(topic.search_query); handleSearchWithQuery(topic.search_query); }}
                      className="text-left p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50/50 dark:hover:bg-slate-800/30 hover:border-indigo-500/30 transition-all group"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${urgency.color}15` }}>
                          <Icon className="w-4.5 h-4.5" style={{ color: urgency.color }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{topic.title}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium uppercase tracking-wider" style={{ backgroundColor: `${urgency.color}15`, color: urgency.color }}>
                              {urgency.label}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{topic.description}</p>
                          {topic.key_finding && (
                            <p className="text-xs text-indigo-500 mt-1.5 flex items-center gap-1">
                              <ArrowRight className="w-3 h-3" />
                              {topic.key_finding}
                            </p>
                          )}
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-300 dark:text-slate-600 group-hover:text-indigo-500 transition-colors shrink-0 mt-1" />
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Treatment Ladders */}
              {topicsData.treatment_ladders?.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm flex items-center gap-2">
                      <ClipboardList className="w-4 h-4 text-indigo-500" />
                      <span>Guideline-Based Treatment Pathways</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {topicsData.treatment_ladders.map((ladder, i) => (
                        <div key={i}>
                          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">{ladder.condition}</p>
                          <div className="flex items-center flex-wrap gap-1">
                            {ladder.ladder.map((step, si) => (
                              <div key={si} className="flex items-center gap-1">
                                <span className="px-2.5 py-1 rounded-lg text-xs bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                                  <span className="text-indigo-500 font-medium">{step.step}:</span> {step.treatment}
                                </span>
                                {si < ladder.ladder.length - 1 && <ArrowRight className="w-3 h-3 text-slate-400" />}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : null}
        </>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* AI Synthesis */}
      {synthesis && (
        <Card className="border-indigo-500/30 bg-indigo-500/5">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <FlaskConical className="w-4 h-4 text-indigo-500" />
              <span className="text-indigo-500 uppercase tracking-wider text-xs">AI Synthesis</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">{synthesis}</p>
          </CardContent>
        </Card>
      )}

      {/* Guidelines referenced */}
      {report?.guidelines_referenced?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {report.guidelines_referenced.map((g: string, i: number) => (
            <span key={i} className="px-2.5 py-1 text-xs rounded-full bg-indigo-500/10 text-indigo-500 font-medium">
              {g}
            </span>
          ))}
        </div>
      )}

      {/* Treatment Options */}
      {report?.treatment_options?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Stethoscope className="w-4 h-4" />
              Treatment Options
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {report.treatment_options.map((opt: TreatmentOption, i: number) => {
                const evidenceColor = opt.evidence_level === 'strong' ? 'text-green-500' : opt.evidence_level === 'moderate' ? 'text-amber-500' : 'text-slate-400';
                return (
                  <div key={i} className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-slate-400 text-sm font-medium">{i + 1}.</span>
                      <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{opt.name}</span>
                      <span className={`text-xs ${evidenceColor} font-medium`}>{opt.evidence_level}</span>
                    </div>
                    {opt.guideline_position && (
                      <p className="text-indigo-500 text-xs mb-1">{opt.guideline_position}</p>
                    )}
                    <p className="text-slate-600 dark:text-slate-400 text-xs leading-5">{opt.efficacy}</p>
                    {opt.side_effects && (
                      <p className="text-amber-600 dark:text-amber-400 text-xs mt-1">Side effects: {opt.side_effects}</p>
                    )}
                    {opt.notes && (
                      <p className="text-slate-500 text-xs mt-1 italic">{opt.notes}</p>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Drug Profiles */}
      {drugs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Pill className="w-4 h-4" />
              Drug Profiles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {drugs.map((drug, i) => (
                <div key={i} className="p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{drug.name}</span>
                    {drug.interactions_with_user_meds?.length > 0 ? (
                      <span className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-500">Interaction</span>
                    ) : (
                      <span className="text-xs px-2 py-0.5 rounded bg-green-500/10 text-green-500">Compatible</span>
                    )}
                  </div>
                  <p className="text-slate-500 text-xs">{drug.drug_class}</p>
                  {drug.guideline_position && (
                    <p className="text-indigo-500 text-xs mt-1">{drug.guideline_position}</p>
                  )}
                  <p className="text-slate-600 dark:text-slate-400 text-xs mt-2 leading-5">{drug.efficacy_summary}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Doctor Questions */}
      {report?.doctor_questions?.length > 0 && (
        <Card className="border-primary-500/30">
          <CardHeader>
            <CardTitle className="text-base text-primary-500">Questions for Your Doctor</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-2">
              {report.doctor_questions.map((q: string, i: number) => (
                <li key={i} className="flex gap-2 text-sm text-slate-700 dark:text-slate-300">
                  <span className="text-primary-500 font-medium">{i + 1}.</span>
                  <span className="leading-relaxed">{q}</span>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}

      {/* Clinical Trials */}
      {trials.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Clinical Trials ({trials.length} recruiting)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {trials.map((trial, i) => (
                <div key={trial.nct_id || i} className="p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500 font-medium">
                      {trial.phase?.replace('PHASE', 'Phase ') || 'Phase N/A'}
                    </span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-green-500/10 text-green-500 font-medium">
                      {trial.status?.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100 leading-5">{trial.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{trial.sponsor}</p>
                  {trial.nct_id && (
                    <a
                      href={`https://clinicaltrials.gov/study/${trial.nct_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-indigo-500 hover:underline mt-2"
                    >
                      <ExternalLink className="w-3 h-3" />
                      {trial.nct_id}
                    </a>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Articles */}
      {articles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Research Articles ({articles.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {articles.slice(0, 5).map((a: any, i: number) => (
                <div key={i} className="p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                  <p className="text-sm text-slate-900 dark:text-slate-100 leading-5">{a.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{a.journal} · {a.publication_date?.slice(0, 4)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Disclaimer */}
      {(synthesis || report) && (
        <p className="text-center text-xs text-slate-400 py-4">
          This is not medical advice. Discuss all findings with your healthcare provider before making any treatment changes.
        </p>
      )}
    </div>
  );
}
