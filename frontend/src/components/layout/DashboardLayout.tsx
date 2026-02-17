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
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { supabase } from '@/lib/supabase';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { UpgradeModal } from '@/components/billing/UpgradeModal';
import { useAuth } from '@/hooks/useAuth';

const navigation = [
  { name: 'Timeline', href: '/timeline', icon: LayoutDashboard },
  { name: 'Insights', href: '/insights', icon: Brain },
  { name: 'Trends', href: '/trends', icon: TrendingUp },
  { name: 'Nutrition', href: '/nutrition', icon: Utensils },
  { name: 'Metabolic AI', href: '/correlations', icon: Zap },
  { name: 'Health Profile', href: '/health-profile', icon: HeartPulse },
  { name: 'Medications', href: '/medications', icon: Pill },
  { name: 'Symptom Journal', href: '/symptoms', icon: ClipboardList },
  { name: 'Research', href: '/research', icon: BookOpen },
  { name: 'AI Agents', href: '/agents', icon: Sparkles },
  { name: 'Predictions', href: '/predictions', icon: LineChart },
  { name: 'Doctor Prep', href: '/doctor-prep', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isLoading } = useAuth(true);
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const tier = useSubscriptionStore((s) => s.getTier());

  const handleLogout = async () => {
    await supabase.auth.signOut();
    logout();
  };

  // Prevent hydration issues by rendering a stable loading UI until auth is resolved.
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-200 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-200">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transition-colors duration-200">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-slate-200 dark:border-slate-700">
            <div className="flex items-center">
              <Activity className="w-8 h-8 text-primary-600 dark:text-primary-400" />
              <span className="ml-2 text-lg font-bold text-slate-900 dark:text-slate-100">
                Health Assistant
              </span>
            </div>
            <ThemeToggle />
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
                      : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700'
                  )}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                <span className="text-primary-700 dark:text-primary-400 font-medium">
                  {user?.name?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="ml-3 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100">{user?.name || 'User'}</p>
                  {tier !== 'free' && (
                    <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
                      {tier === 'pro_plus' ? 'Pro+' : 'Pro'}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64 min-h-screen">
        <div className="p-8">{children}</div>
      </main>

      {/* Upgrade modal (triggered by 403 interceptor) */}
      <UpgradeModal />
    </div>
  );
}
