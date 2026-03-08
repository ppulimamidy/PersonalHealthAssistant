'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

export interface SubNavItem {
  name: string;
  href: string;
}

interface SubNavProps {
  items: SubNavItem[];
}

export function SubNav({ items }: SubNavProps) {
  const pathname = usePathname();

  return (
    <div
      className="flex items-center h-10 px-6 gap-1"
      style={{
        backgroundColor: '#080B10',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}
    >
      {items.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'px-3 py-1 rounded-full text-xs font-medium transition-all duration-150',
              isActive
                ? 'bg-[#00D4AA]/15 text-[#00D4AA]'
                : 'text-[#526380] hover:text-[#8B97A8] hover:bg-white/[0.04]'
            )}
          >
            {item.name}
          </Link>
        );
      })}
    </div>
  );
}
