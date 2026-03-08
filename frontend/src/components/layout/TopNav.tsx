'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, LogOut, Sun, Moon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { useTheme } from '@/contexts/ThemeContext';
import { supabase } from '@/lib/supabase';
import { SubNav, type SubNavItem } from './SubNav';

// ── Tab definitions ───────────────────────────────────────────────────────────

interface TabDef {
  name: string;
  href: string;
  subRoutes: string[];
  subItems?: SubNavItem[];
}

const TABS: TabDef[] = [
  {
    name: 'Home',
    href: '/home',
    subRoutes: ['/home'],
  },
  {
    name: 'Track',
    href: '/nutrition',
    subRoutes: ['/nutrition', '/medications', '/symptoms', '/lab-results'],
    subItems: [
      { name: 'Nutrition', href: '/nutrition' },
      { name: 'Medications', href: '/medications' },
      { name: 'Symptoms', href: '/symptoms' },
      { name: 'Lab Results', href: '/lab-results' },
    ],
  },
  {
    name: 'Insights',
    href: '/timeline',
    subRoutes: ['/timeline', '/trends', '/correlations', '/predictions', '/meta-analysis'],
    subItems: [
      { name: 'Timeline', href: '/timeline' },
      { name: 'Trends', href: '/trends' },
      { name: 'Correlations', href: '/correlations' },
      { name: 'Predictions', href: '/predictions' },
      { name: 'Meta-Analysis', href: '/meta-analysis' },
    ],
  },
  {
    name: 'Agents',
    href: '/agents',
    subRoutes: ['/agents'],
  },
  {
    name: 'Profile',
    href: '/health-profile',
    subRoutes: ['/health-profile', '/devices', '/doctor-prep', '/health-twin', '/research', '/settings'],
    subItems: [
      { name: 'Health Profile', href: '/health-profile' },
      { name: 'Devices', href: '/devices' },
      { name: 'Doctor Prep', href: '/doctor-prep' },
      { name: 'Health Twin', href: '/health-twin' },
      { name: 'Research', href: '/research' },
      { name: 'Settings', href: '/settings' },
    ],
  },
];

// ── Theme toggle ─────────────────────────────────────────────────────────────

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
        : <Sun className="w-4 h-4" />
      }
    </button>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function TopNav() {
  const pathname = usePathname();
  const { user, profile, logout } = useAuthStore();
  const tier = useSubscriptionStore((s) => s.getTier());

  const isProvider = profile?.user_role === 'provider';
  const isCaregiver = profile?.user_role === 'caregiver';
  const visibleTabs =
    isProvider
      ? [
          ...TABS,
          { name: 'Patients', href: '/patients', subRoutes: ['/patients'] } as TabDef,
        ]
      : isCaregiver
      ? [
          ...TABS,
          { name: 'Family', href: '/patients', subRoutes: ['/patients'] } as TabDef,
        ]
      : TABS;

  const handleLogout = async () => {
    await supabase.auth.signOut();
    logout();
  };

  const initials = user?.name
    ? user.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()
    : 'U';

  // Find active tab
  const activeTab = visibleTabs.find((tab) =>
    tab.subRoutes.some((r) => pathname === r || pathname.startsWith(r + '/'))
  );

  return (
    <div
      className="fixed top-0 left-0 right-0 z-30"
      style={{ backgroundColor: '#080B10' }}
    >
      {/* Main nav bar */}
      <div
        className="flex items-center h-14 px-6 gap-6"
        style={{ borderBottom: activeTab?.subItems ? 'none' : '1px solid rgba(255,255,255,0.05)' }}
      >
        {/* Logo */}
        <Link href="/home" className="flex items-center gap-2.5 flex-shrink-0 mr-2">
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
        </Link>

        {/* Tabs — centred */}
        <nav className="flex items-center gap-1 flex-1 justify-center">
          {visibleTabs.map((tab) => {
            const isActive = tab === activeTab;
            return (
              <Link
                key={tab.name}
                href={tab.href}
                className={cn(
                  'px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'text-[#00D4AA] bg-[#00D4AA]/10'
                    : 'text-[#526380] hover:text-[#8B97A8] hover:bg-white/[0.04]'
                )}
              >
                {tab.name}
              </Link>
            );
          })}
        </nav>

        {/* Right side: theme toggle + user */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <ThemeToggle />

          {/* User avatar + name */}
          <div className="flex items-center gap-2 ml-2">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold flex-shrink-0"
              style={{
                background: 'linear-gradient(135deg, rgba(0,212,170,0.25) 0%, rgba(0,212,170,0.08) 100%)',
                color: '#00D4AA',
              }}
            >
              {initials}
            </div>
            <div className="hidden sm:flex flex-col leading-none">
              <div className="flex items-center gap-1">
                <span className="text-xs font-medium text-[#C8D5E8]">{user?.name || 'User'}</span>
                {tier !== 'free' && (
                  <span className="text-[9px] font-bold uppercase px-1 py-0.5 rounded bg-[#00D4AA]/15 text-[#00D4AA] leading-none">
                    {tier === 'pro_plus' ? 'Pro+' : 'Pro'}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="p-1 rounded-md text-[#3D4F66] hover:text-[#F87171] transition-colors duration-150"
            title="Sign out"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Sub-nav */}
      {activeTab?.subItems && <SubNav items={activeTab.subItems} />}
    </div>
  );
}
