import type { SafetySummary } from './types';

export const safetySummary: SafetySummary = {
  currentSafety: 82,
  activeAlerts: 3,
  safeHavens: 12,
  communityReports: 127,
  trend: [
    { time: '12 AM', score: 88 },
    { time: '3 AM', score: 92 },
    { time: '6 AM', score: 86 },
    { time: '9 AM', score: 80 },
    { time: '12 PM', score: 78 },
    { time: '3 PM', score: 75 },
    { time: '6 PM', score: 70 },
    { time: '9 PM', score: 64 },
    { time: 'Now', score: 82 },
  ],
  updates: [
    { time: '9:42 PM', event: 'Incident reported — MG Road', risk: 'high' },
    { time: '8:18 PM', event: 'Police patrol detected — Banjara Hills', risk: 'low' },
    { time: '7:10 PM', event: 'Lighting issue reported — Abids', risk: 'moderate' },
    { time: '6:30 PM', event: 'Community safety update — Jubilee Hills', risk: 'low' },
    { time: '5:05 PM', event: 'News signal detected — Old City', risk: 'high' },
  ],
};
