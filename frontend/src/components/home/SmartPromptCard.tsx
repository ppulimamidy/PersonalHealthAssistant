'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { Stethoscope, X, ChevronRight } from 'lucide-react';
import { api } from '@/services/api';

interface SmartPrompt {
  type: string;
  title: string;
  body: string;
  action: string;
  priority: number;
}

interface DataCompleteness {
  score: number;
  level: string;
}

const ACTION_HREFS: Record<string, string> = {
  devices: '/devices',
  medications: '/medications',
  cycle: '/cycle',
  'lab-results': '/lab-results',
  nutrition: '/nutrition',
  symptoms: '/symptoms',
  chat: '/agents',
};

export function SmartPromptCard() {
  const queryClient = useQueryClient();

  const { data: completeness } = useQuery<DataCompleteness>({
    queryKey: ['data-completeness'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/onboarding/data-completeness');
      return data;
    },
    staleTime: 5 * 60_000,
  });

  const { data: prompt } = useQuery<SmartPrompt | null>({
    queryKey: ['smart-prompt'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/onboarding/smart-prompt');
      return data || null;
    },
    staleTime: 5 * 60_000,
  });

  const dismissMutation = useMutation({
    mutationFn: async (type: string) => {
      await api.post(`/api/v1/onboarding/smart-prompt/${type}/dismiss`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['smart-prompt'] });
    },
  });

  if (!prompt) return null;

  const href = ACTION_HREFS[prompt.action] || '/home';

  return (
    <div
      className="rounded-xl p-4"
      style={{ backgroundColor: 'rgba(0,212,170,0.04)', border: '1px solid rgba(0,212,170,0.12)' }}
    >
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(0,212,170,0.1)' }}>
          <Stethoscope className="w-4 h-4 text-[#00D4AA]" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[#E8EDF5]">{prompt.title}</p>
          <p className="text-xs text-[#526380] mt-0.5">{prompt.body}</p>
          <Link
            href={href}
            className="inline-flex items-center gap-1 mt-2 text-xs font-medium text-[#00D4AA] hover:text-[#00D4AA]/80 transition-colors"
          >
            Get started <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
        <button
          onClick={() => dismissMutation.mutate(prompt.type)}
          className="text-[#3D4F66] hover:text-[#526380] transition-colors p-0.5 flex-shrink-0"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      {completeness && completeness.score < 80 && (
        <div className="mt-3 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-[#526380]">Your health picture</span>
            <span className="text-[10px] text-[#526380]">{completeness.score}%</span>
          </div>
          <div className="h-1 rounded-full bg-white/5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${completeness.score}%`, backgroundColor: '#00D4AA' }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
