'use client';

import { cn } from '@/lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  readonly children: React.ReactNode;
  /** Adds a subtle teal glow on hover */
  glow?: boolean;
}

export function Card({ className, children, glow, ...props }: Readonly<CardProps>) {
  return (
    <div
      className={cn(
        'rounded-xl border p-6 transition-all duration-200',
        glow && 'hover:shadow-glow-teal hover:border-primary-500/20',
        className
      )}
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderColor: 'var(--border)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.25)',
      }}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...props }: Readonly<Omit<CardProps, 'glow'>>) {
  return (
    <div className={cn('mb-4', className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ className, children, ...props }: Readonly<Omit<CardProps, 'glow'>>) {
  return (
    <h3
      className={cn('text-base font-semibold tracking-tight leading-snug', className)}
      style={{
        fontFamily: 'var(--font-syne, system-ui, sans-serif)',
        color: 'var(--text-primary)',
      }}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({ className, children, ...props }: Readonly<Omit<CardProps, 'glow'>>) {
  return (
    <p
      className={cn('text-xs mt-1 leading-relaxed', className)}
      style={{ color: 'var(--text-secondary)' }}
      {...props}
    >
      {children}
    </p>
  );
}

export function CardContent({ className, children, ...props }: Readonly<Omit<CardProps, 'glow'>>) {
  return (
    <div className={cn('', className)} {...props}>
      {children}
    </div>
  );
}
