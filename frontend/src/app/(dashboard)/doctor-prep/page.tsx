import { DoctorPrepView } from '@/components/doctor-prep/DoctorPrepView';
import { Suspense } from 'react';

export default function DoctorPrepPage() {
  return (
    <Suspense fallback={null}>
      <DoctorPrepView />
    </Suspense>
  );
}
