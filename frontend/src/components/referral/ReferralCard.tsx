'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { referralService } from '@/services/referral';
import { Gift, Copy, Check, Users } from 'lucide-react';
import toast from 'react-hot-toast';
import type { ReferralStats } from '@/types';

export function ReferralCard() {
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    referralService
      .getStats()
      .then(setStats)
      .catch(() => {
        // If no referral code exists yet, fetch/create one
        referralService
          .getCode()
          .then((info) =>
            setStats({ ...info, recent_referrals: [] })
          )
          .catch(() => {});
      })
      .finally(() => setLoading(false));
  }, []);

  const handleCopy = async () => {
    if (!stats?.share_url) return;
    try {
      await navigator.clipboard.writeText(stats.share_url);
      setCopied(true);
      toast.success('Referral link copied!');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy');
    }
  };

  const handleShare = async () => {
    if (!stats?.share_url) return;
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Join HealthAssist',
          text: 'Track your health with AI-powered insights. Use my referral link to sign up!',
          url: stats.share_url,
        });
      } catch {
        // User cancelled share
      }
    } else {
      handleCopy();
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gift className="w-5 h-5" />
            Refer a Friend
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
            <div className="h-10 bg-slate-200 dark:bg-slate-700 rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Gift className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          Refer a Friend
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Invite friends and earn <strong>1 month free</strong> for each signup!
          </p>

          {/* Referral link */}
          {stats?.share_url && (
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm text-slate-700 dark:text-slate-300 font-mono truncate">
                {stats.share_url}
              </div>
              <Button variant="outline" size="sm" onClick={handleCopy}>
                {copied ? (
                  <Check className="w-4 h-4 text-green-500" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </Button>
            </div>
          )}

          {/* Share button */}
          <Button onClick={handleShare} className="w-full">
            <Gift className="w-4 h-4 mr-2" />
            Share Invite Link
          </Button>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 pt-3 border-t border-slate-200 dark:border-slate-700">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
                <Users className="w-5 h-5 text-primary-500" />
                {stats?.referral_count ?? 0}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">Friends joined</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
                <Gift className="w-5 h-5 text-green-500" />
                {stats?.credits_earned ?? 0}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">Months earned</p>
            </div>
          </div>

          {/* Recent referrals */}
          {stats?.recent_referrals && stats.recent_referrals.length > 0 && (
            <div className="pt-3 border-t border-slate-200 dark:border-slate-700">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Recent Referrals
              </p>
              <div className="space-y-1">
                {stats.recent_referrals.slice(0, 5).map((r, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400"
                  >
                    <span>Friend #{stats.referral_count - i}</span>
                    <span>
                      {new Date(r.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Referral code */}
          {stats?.code && (
            <p className="text-xs text-center text-slate-400 dark:text-slate-500">
              Your code: <span className="font-mono font-medium">{stats.code}</span>
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
