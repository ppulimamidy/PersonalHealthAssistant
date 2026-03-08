'use client';

import Link from 'next/link';
import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div
        className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
        style={{ backgroundColor: 'rgba(0,212,170,0.12)' }}
      >
        <Icon className="w-8 h-8 text-[#00D4AA]" />
      </div>
      <h3 className="text-base font-semibold text-[#E8EDF5] mb-2">{title}</h3>
      <p className="text-sm text-[#526380] max-w-xs mb-6">{description}</p>
      {actionLabel && (
        actionHref ? (
          <Link
            href={actionHref}
            className="px-4 py-2 rounded-lg text-sm font-medium text-[#00D4AA] border border-[#00D4AA]/40 hover:bg-[#00D4AA]/10 transition-colors"
          >
            {actionLabel}
          </Link>
        ) : (
          <button
            onClick={onAction}
            className="px-4 py-2 rounded-lg text-sm font-medium text-[#00D4AA] border border-[#00D4AA]/40 hover:bg-[#00D4AA]/10 transition-colors"
          >
            {actionLabel}
          </button>
        )
      )}
    </div>
  );
}
