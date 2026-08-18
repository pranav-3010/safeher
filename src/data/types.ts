export type RiskLevel = 'low' | 'moderate' | 'high' | 'veryhigh';

export interface LatLng {
  lat: number;
  lng: number;
}

export interface SafetyZone {
  id: string;
  name: string;
  center: LatLng;
  radiusM: number;
  riskScore: number; // 0-100, higher = riskier
  riskLevel: RiskLevel;
  lighting: 'Good' | 'Moderate' | 'Poor';
  naturalSurveillance: 'High' | 'Moderate' | 'Low';
  policeDistanceKm: number;
  hospitalDistanceKm: number;
  commercialActivity: 'High' | 'Moderate' | 'Low';
  communityRating: number; // 0-5
  recentIncidents: number;
  riskFactors: string[];
  positiveFactors: string[];
}

export interface RouteOption {
  id: string;
  label: 'Safest' | 'Balanced' | 'Fastest';
  durationMin: number;
  distanceKm: number;
  safetyScore: number; // 0-100, higher = safer
  riskAreasAvoided: number;
  riskAreasPassed: number;
  path: LatLng[];
  note: string;
  recommended: boolean;
}

export type IncidentSource = 'Verified' | 'Community' | 'News' | 'AI Signal';
export type IncidentStatus = 'Reviewing' | 'Confirmed' | 'Resolved' | 'Expired';

export interface Incident {
  id: string;
  time: string; // display time
  timestamp: number;
  location: string;
  type: string;
  source: IncidentSource;
  riskImpact: number; // +/- points
  status: IncidentStatus;
  detail: string;
  expiresAt?: string;
}

export type SafeHavenCategory =
  | 'Police'
  | 'Hospital'
  | 'Metro'
  | 'Petrol Pump'
  | 'Open Business';

export interface SafeHaven {
  id: string;
  name: string;
  category: SafeHavenCategory;
  distanceKm: number;
  openStatus: string;
  open247: boolean;
  phone?: string;
  position: LatLng;
}

export interface CommunityReport {
  id: string;
  location: string;
  condition:
    | 'Well Lit'
    | 'Poor Lighting'
    | 'Crowded'
    | 'Isolated'
    | 'Police Presence'
    | 'Unsafe Activity'
    | 'Other';
  comment: string;
  rating: number; // 1-5
  timestamp: string;
}

export interface CommunityFactors {
  feelsSafe: number;
  wellLit: number;
  crowded: number;
  policePresence: number;
}

export interface EmergencyContact {
  id: string;
  label: string;
  name: string;
  phone: string;
}

export interface UserProfile {
  name: string;
  currentLocation: LatLng;
  locationLabel: string;
  contacts: EmergencyContact[];
  voiceSosEnabled: boolean;
  voicePhrase: string;
  routePreference: 'Safest' | 'Balanced' | 'Fastest';
  riskPriorities: {
    lighting: boolean;
    policeProximity: boolean;
    crowdActivity: boolean;
    safeHavens: boolean;
    communityRatings: boolean;
  };
}

export type DemoScenario =
  | 'normal'
  | 'high-risk-zone'
  | 'new-incident'
  | 'safest-route-changed'
  | 'internet-lost'
  | 'voice-sos'
  | 'emergency-sos';

export interface SafetySummary {
  currentSafety: number;
  activeAlerts: number;
  safeHavens: number;
  communityReports: number;
  trend: { time: string; score: number }[];
  updates: {
    time: string;
    event: string;
    risk: RiskLevel;
  }[];
}

export const RISK_META: Record<
  RiskLevel,
  { label: string; color: string; bg: string; text: string; dot: string }
> = {
  low: {
    label: 'Low Risk',
    color: '#16803A',
    bg: 'bg-safe-light',
    text: 'text-safe-dark',
    dot: 'bg-safe',
  },
  moderate: {
    label: 'Moderate',
    color: '#B77900',
    bg: 'bg-moderate-light',
    text: 'text-moderate-dark',
    dot: 'bg-moderate',
  },
  high: {
    label: 'High Risk',
    color: '#C2410C',
    bg: 'bg-highrisk-light',
    text: 'text-highrisk-dark',
    dot: 'bg-highrisk',
  },
  veryhigh: {
    label: 'Very High',
    color: '#B91C1C',
    bg: 'bg-danger-light',
    text: 'text-danger-dark',
    dot: 'bg-danger',
  },
};

export function riskLevelFromScore(score: number): RiskLevel {
  if (score >= 80) return 'veryhigh';
  if (score >= 60) return 'high';
  if (score >= 40) return 'moderate';
  return 'low';
}

export function safetyScoreLevel(score: number): RiskLevel {
  // safety score: higher = safer. Convert to risk level for color use.
  if (score >= 85) return 'low';
  if (score >= 65) return 'moderate';
  if (score >= 45) return 'high';
  return 'veryhigh';
}
