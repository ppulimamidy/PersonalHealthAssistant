import { TimelineView } from '@/components/timeline/TimelineView';
import { HealthScoreCard } from '@/components/dashboard/HealthScoreCard';

export default function TimelinePage() {
  return (
    <>
      <HealthScoreCard />
      <TimelineView />
    </>
  );
}
