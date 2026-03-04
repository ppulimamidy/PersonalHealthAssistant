'use client';

import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const base =
      'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 ' +
      'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent ' +
      'disabled:opacity-40 disabled:cursor-not-allowed select-none';

    const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
      primary:
        'bg-primary-500 text-obsidian-900 hover:bg-primary-400 active:bg-primary-600 ' +
        'focus:ring-primary-500/40 shadow-sm font-semibold',
      secondary:
        'bg-obsidian-700 text-obsidian-50 border border-obsidian-550 ' +
        'hover:bg-obsidian-650 hover:border-obsidian-400 focus:ring-obsidian-400/30',
      outline:
        'border border-obsidian-550 text-obsidian-100 ' +
        'hover:bg-white/5 hover:border-obsidian-400 focus:ring-obsidian-400/30',
      ghost:
        'text-obsidian-100 hover:bg-white/5 focus:ring-obsidian-400/20',
      danger:
        'bg-red-500/10 text-red-400 border border-red-500/20 ' +
        'hover:bg-red-500/20 hover:border-red-400/40 focus:ring-red-400/30',
    };

    const sizes: Record<NonNullable<ButtonProps['size']>, string> = {
      sm: 'px-3 py-1.5 text-xs gap-1.5',
      md: 'px-4 py-2 text-sm gap-2',
      lg: 'px-6 py-2.5 text-base gap-2',
    };

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg className="animate-spin -ml-0.5 h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
