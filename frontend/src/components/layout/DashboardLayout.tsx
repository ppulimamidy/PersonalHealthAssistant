'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Activity,
  Brain,
  FileText,
  Utensils,
  TrendingUp,
  Zap,
  HeartPulse,
  Pill,
  ClipboardList,
  BookOpen,
  Sparkles,
  Settings,
  LogOut,
  LineChart,
  FlaskConical,
  Users,
  Network,
  Sun,
  Moon,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { supabase } from '@/lib/supabase';
import { useTheme } from '@/contexts/ThemeContext';
import { UpgradeModal } from '@/components/billing/UpgradeModal';
import { useAuth } from '@/hooks/useAuth';

// Navigation grouped by category
const navGroups = [
  {
    label: 'Overview',
    items: [
      { name: 'Timeline',     href: '/timeline',      icon: LayoutDashboard },
      { name: 'Insights',     href: '/insights',      icon: Brain },
      { name: 'Trends',       href: '/trends',        icon: TrendingUp },
    ],
  },
  {
    label: 'Health Data',
    items: [
      { name: 'Nutrition',       href: '/nutrition',     icon: Utensils },
      { name: 'Medications',     href: '/medications',   icon: Pill },
      { name: 'Symptom Journal', href: '/symptoms',      icon: ClipboardList },
      { name: 'Lab Results',     href: '/lab-results',   icon: FlaskConical },
      { name: 'Health Profile',  href: '/health-profile',icon: HeartPulse },
    ],
  },
  {
    label: 'AI & Research',
    items: [
      { name: 'Metabolic AI',  href: '/correlations',  icon: Zap },
      { name: 'AI Agents',     href: '/agents',        icon: Sparkles },
      { name: 'Predictions',   href: '/predictions',   icon: LineChart },
      { name: 'Research',      href: '/research',      icon: BookOpen },
      { name: 'Meta-Analysis', href: '/meta-analysis', icon: Network },
    ],
  },
  {
    label: 'Care',
    items: [
      { name: 'Health Twin', href: '/health-twin',  icon: Users },
      { name: 'Doctor Prep', href: '/doctor-prep',  icon: FileText },
      { name: 'Settings',    href: '/settings',     icon: Settings },
    ],
  },
];

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      className="p-1.5 rounded-md text-[#526380] hover:text-[#8B97A8] hover:bg-white/5 transition-all duration-150"
      aria-label="Toggle theme"
    >
      {theme === 'light'
        ? <Moon className="w-4 h-4" />
        : <Sun  className="w-4 h-4" />
      }
    </button>
  );
}

export function DashboardLayout({ children }: { readonly children: React.ReactNode }) {
  const { isLoading } = useAuth(true);
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const tier = useSubscriptionStore((s) => s.getTier());

  const handleLogout = async () => {
    await supabase.auth.signOut();
    logout();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#080B10' }}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-transparent border-t-[#00D4AA] animate-spin" />
          <span className="text-xs text-[#526380] font-mono tracking-wider uppercase">Loading</span>
        </div>
      </div>
    );
  }

  const initials = user?.name
    ? user.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()
    : 'U';

  return (
    <div className="min-h-screen flex transition-colors duration-200" style={{ backgroundColor: 'var(--bg-base)' }}>
      {/* ── Sidebar ──────────────────────────────────────────── */}
      <aside
        className="fixed inset-y-0 left-0 w-60 flex flex-col z-30"
        style={{
          backgroundColor: '#080B10',
          borderRight: '1px solid rgba(255,255,255,0.05)',
        }}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-14 px-5" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <div className="flex items-center gap-2.5">
            {/* Pulse logo mark */}
            <div className="relative flex items-center justify-center w-7 h-7">
              <div className="absolute inset-0 rounded-lg bg-[#00D4AA]/10" />
              <Activity className="w-4 h-4 text-[#00D4AA] relative z-10" strokeWidth={2} />
            </div>
            <span
              className="text-sm font-semibold text-[#E8EDF5] tracking-tight"
              style={{ fontFamily: 'var(--font-syne), system-ui, sans-serif' }}
            >
              Health<span className="text-[#00D4AA]">AI</span>
            </span>
          </div>
          <ThemeToggle />
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-5 scrollbar-thin">
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="px-2 mb-1.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#3D4F66]">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        'group flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-sm transition-all duration-150',
                        isActive
                          ? 'bg-[#00D4AA]/10 text-[#00D4AA]'
                          : 'text-[#526380] hover:text-[#8B97A8] hover:bg-white/[0.04]'
                      )}
                    >
                      <item.icon
                        className={cn(
                          'w-4 h-4 flex-shrink-0 transition-colors duration-150',
                          isActive ? 'text-[#00D4AA]' : 'text-[#3D4F66] group-hover:text-[#6B7A8D]'
                        )}
                        strokeWidth={isActive ? 2 : 1.75}
                      />
                      <span className="font-medium leading-none">{item.name}</span>
                      {isActive && (
                        <span className="ml-auto w-1 h-1 rounded-full bg-[#00D4AA]" />
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* User section */}
        <div
          className="p-3 mx-3 mb-3 rounded-xl"
          style={{
            backgroundColor: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          <div className="flex items-center gap-2.5">
            {/* Avatar */}
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold"
              style={{
                background: 'linear-gradient(135deg, rgba(0,212,170,0.25) 0%, rgba(0,212,170,0.08) 100%)',
                color: '#00D4AA',
                fontFamily: 'var(--font-syne), sans-serif',
              }}
            >
              {initials}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <p className="text-xs font-semibold text-[#C8D5E8] truncate leading-none">
                  {user?.name || 'User'}
                </p>
                {tier !== 'free' && (
                  <span className="flex-shrink-0 text-[9px] font-bold uppercase px-1 py-0.5 rounded bg-[#00D4AA]/15 text-[#00D4AA] leading-none">
                    {tier === 'pro_plus' ? 'Pro+' : 'Pro'}
                  </span>
                )}
              </div>
              <p className="text-[10px] text-[#3D4F66] truncate mt-0.5 leading-none">
                {user?.email}
              </p>
            </div>

            <button
              onClick={handleLogout}
              className="p-1 rounded-md text-[#3D4F66] hover:text-[#F87171] transition-colors duration-150 flex-shrink-0"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────── */}
      <main className="ml-60 flex-1 min-h-screen">
        <div className="max-w-7xl mx-auto px-8 py-8 animate-fade-in">
          {children}
        </div>
      </main>

      <UpgradeModal />
    </div>
  );
}
