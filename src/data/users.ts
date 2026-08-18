import type { UserProfile } from './types';

export const user: UserProfile = {
  name: 'Aisha R.',
  currentLocation: { lat: 17.4435, lng: 78.3772 },
  locationLabel: 'Hitech City, Hyderabad',
  contacts: [
    { id: 'c-1', label: 'Mother', name: 'Fatima R.', phone: '+91 98765 43210' },
    { id: 'c-2', label: 'Brother', name: 'Imran R.', phone: '+91 98765 11111' },
    { id: 'c-3', label: 'Friend', name: 'Sana K.', phone: '+91 99887 76655' },
  ],
  voiceSosEnabled: true,
  voicePhrase: 'Code Red',
  routePreference: 'Safest',
  riskPriorities: {
    lighting: true,
    policeProximity: true,
    crowdActivity: false,
    safeHavens: true,
    communityRatings: true,
  },
};
