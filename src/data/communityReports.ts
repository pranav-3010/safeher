import type { CommunityFactors, CommunityReport } from './types';

export const communityFactors: CommunityFactors = {
  feelsSafe: 82,
  wellLit: 76,
  crowded: 69,
  policePresence: 61,
};

export const communityReports: CommunityReport[] = [
  {
    id: 'cr-1',
    location: 'Banjara Hills, Road No. 12',
    condition: 'Well Lit',
    comment: 'Streetlights all working, felt safe walking to the metro.',
    rating: 5,
    timestamp: '10 minutes ago',
  },
  {
    id: 'cr-2',
    location: 'MG Road, East Exit',
    condition: 'Unsafe Activity',
    comment: 'Group of men loitering near the dimly lit stretch, felt uncomfortable.',
    rating: 1,
    timestamp: '25 minutes ago',
  },
  {
    id: 'cr-3',
    location: 'Jubilee Hills, Road No. 36',
    condition: 'Police Presence',
    comment: 'Saw a patrol vehicle pass twice in 20 minutes.',
    rating: 4,
    timestamp: '1 hour ago',
  },
  {
    id: 'cr-4',
    location: 'Abids Bus Terminal',
    condition: 'Poor Lighting',
    comment: 'Three streetlights out near the terminal entrance.',
    rating: 2,
    timestamp: '2 hours ago',
  },
  {
    id: 'cr-5',
    location: 'Hitech City, Service Road',
    condition: 'Isolated',
    comment: 'Very few people after 8 PM behind the tech park.',
    rating: 2,
    timestamp: '3 hours ago',
  },
  {
    id: 'cr-6',
    location: 'Gachibowli Stadium Road',
    condition: 'Crowded',
    comment: 'Event crowd — busy and well lit, felt secure.',
    rating: 4,
    timestamp: '4 hours ago',
  },
];

export const communityAverage = 4.4;
export const communityReportCount = 127;
