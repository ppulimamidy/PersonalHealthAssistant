'use client';

import { api } from './api';

export const emailService = {
  sendWeeklySummary: () =>
    api.post('/api/v1/email/send-weekly-summary').then((r) => r.data),

  sendReminder: () =>
    api.post('/api/v1/email/send-reminder').then((r) => r.data),
};
