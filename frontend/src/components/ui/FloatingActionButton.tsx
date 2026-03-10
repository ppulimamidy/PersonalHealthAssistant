'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { Plus, X, Utensils, ClipboardList, Pill, Sparkles } from 'lucide-react';

interface Props {
  onSymptomClick: () => void;
}

interface ActionItem {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  bg: string;
  action: string | (() => void);
}

export function FloatingActionButton({ onSymptomClick }: Props) {
  const [expanded, setExpanded] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const actions: ActionItem[] = [
    { label: 'Log Meal', icon: Utensils, bg: '#FB923C', action: '/nutrition' },
    { label: 'Log Symptom', icon: ClipboardList, bg: '#A78BFA', action: onSymptomClick },
    { label: 'Medications', icon: Pill, bg: '#60A5FA', action: '/medications' },
    { label: 'Ask AI', icon: Sparkles, bg: '#00D4AA', action: '/agents' },
  ];

  useEffect(() => {
    if (!expanded) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setExpanded(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [expanded]);

  return (
    <div ref={ref} className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {/* Action items — appear when expanded */}
      {expanded && actions.map(({ label, icon: Icon, bg, action }, i) => (
        <div
          key={label}
          className="flex items-center gap-3"
          style={{
            animation: `fabItemIn 150ms ease both`,
            animationDelay: `${i * 40}ms`,
          }}
        >
          {/* Label */}
          <span
            className="text-xs font-medium px-2.5 py-1 rounded-lg shadow-lg"
            style={{ backgroundColor: 'rgba(8,11,16,0.9)', color: '#C8D5E8', border: '1px solid rgba(255,255,255,0.08)' }}
          >
            {label}
          </span>
          {/* Circle button */}
          {typeof action === 'string' ? (
            <Link
              href={action}
              onClick={() => setExpanded(false)}
              className="w-10 h-10 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-110"
              style={{ backgroundColor: bg }}
            >
              <Icon className="w-4 h-4 text-white" />
            </Link>
          ) : (
            <button
              onClick={() => { action(); setExpanded(false); }}
              className="w-10 h-10 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-110"
              style={{ backgroundColor: bg }}
            >
              <Icon className="w-4 h-4 text-white" />
            </button>
          )}
        </div>
      ))}

      {/* Main FAB */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-14 h-14 rounded-full flex items-center justify-center shadow-xl transition-all duration-200 hover:scale-105"
        style={{ backgroundColor: '#00D4AA' }}
        aria-label={expanded ? 'Close quick actions' : 'Quick log'}
      >
        <div
          className="transition-transform duration-200"
          style={{ transform: expanded ? 'rotate(45deg)' : 'rotate(0deg)' }}
        >
          {expanded ? (
            <X className="w-6 h-6 text-[#080B10]" />
          ) : (
            <Plus className="w-6 h-6 text-[#080B10]" />
          )}
        </div>
      </button>

      <style>{`
        @keyframes fabItemIn {
          from { opacity: 0; transform: translateY(8px) scale(0.92); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </div>
  );
}
