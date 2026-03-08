'use client';

import { api } from './api';

export const exportService = {
  downloadPdf: async () => {
    const resp = await api.get('/api/v1/export/pdf', { responseType: 'blob' });
    const url = URL.createObjectURL(resp.data);
    const a = Object.assign(document.createElement('a'), {
      href: url,
      download: 'health_export.pdf',
    });
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
