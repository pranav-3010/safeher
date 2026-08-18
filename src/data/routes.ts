import type { RouteOption } from './types';

export const routes: RouteOption[] = [
  {
    id: 'route-safest',
    label: 'Safest',
    durationMin: 18,
    distanceKm: 6.2,
    safetyScore: 91,
    riskAreasAvoided: 2,
    riskAreasPassed: 0,
    path: [
      { lat: 17.4435, lng: 78.3772 },
      { lat: 17.4404, lng: 78.3489 },
      { lat: 17.4239, lng: 78.4083 },
      { lat: 17.4155, lng: 78.4347 },
    ],
    note: 'Recommended because it reduces exposure to high-risk areas while adding only 4 minutes to the journey.',
    recommended: true,
  },
  {
    id: 'route-balanced',
    label: 'Balanced',
    durationMin: 16,
    distanceKm: 5.8,
    safetyScore: 76,
    riskAreasAvoided: 1,
    riskAreasPassed: 1,
    path: [
      { lat: 17.4435, lng: 78.3772 },
      { lat: 17.4239, lng: 78.4083 },
      { lat: 17.4155, lng: 78.4347 },
    ],
    note: 'A reasonable trade-off between time and safety, passing one moderate-risk stretch.',
  },
  {
    id: 'route-fastest',
    label: 'Fastest',
    durationMin: 14,
    distanceKm: 5.2,
    safetyScore: 58,
    riskAreasAvoided: 0,
    riskAreasPassed: 2,
    path: [
      { lat: 17.4435, lng: 78.3772 },
      { lat: 17.4123, lng: 78.4012 },
      { lat: 17.4155, lng: 78.4347 },
    ],
    note: 'Fastest option, but it passes through two high-risk areas including MG Road.',
  },
];
