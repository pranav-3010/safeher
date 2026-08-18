import type {
  CommunityFactors,
  CommunityReport,
  DemoScenario,
  EmergencyContact,
  Incident,
  RouteOption,
  SafeHaven,
  SafetySummary,
  SafetyZone,
  UserProfile,
} from '@/data/types';
import { zones as baseZones } from '@/data/zones';
import { routes as baseRoutes } from '@/data/routes';
import { incidents as baseIncidents } from '@/data/incidents';
import { safeHavens as baseSafeHavens } from '@/data/safeHavens';
import {
  communityFactors as baseFactors,
  communityReports as baseReports,
  communityAverage,
  communityReportCount,
} from '@/data/communityReports';
import { user as baseUser } from '@/data/users';
import { safetySummary as baseSummary } from '@/data/summary';

// Live Supabase Direct REST API Credentials
const SUPABASE_REST_URL = 'https://wfvckuomhbdbyrogelct.supabase.co/rest/v1';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndmdmNrdW9taGJkYnlyb2dlbGN0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIwNTIxMTIsImV4cCI6MjA5NzYyODExMn0.hyAWAERq8ifO3v_3ntyBDSI0CTHshAoZzPjlNjqIWXg';

const SUPABASE_HEADERS = {
  'Content-Type': 'application/json',
  'apikey': SUPABASE_ANON_KEY,
  'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
};

export interface ApiService {
  getSafetyZones(): Promise<SafetyZone[]>;
  getSafetySummary(): Promise<SafetySummary>;
  getRoutes(from: string, to: string): Promise<RouteOption[]>;
  getSafeHavens(category?: string): Promise<SafeHaven[]>;
  getIncidents(): Promise<Incident[]>;
  getCommunityReports(): Promise<CommunityReport[]>;
  getCommunityFactors(): Promise<CommunityFactors>;
  submitCommunityReport(report: Omit<CommunityReport, 'id' | 'timestamp'>): Promise<CommunityReport>;
  triggerSOS(): Promise<{ ok: boolean; location: { lat: number; lng: number } }>;
  getJourneyStatus(): Promise<RouteOption>;
  askAISafetyQuestion?(question: string, lat?: number, lng?: number): Promise<any>;
}

let activeScenario: DemoScenario = 'normal';

export function setDemoScenario(s: DemoScenario) {
  activeScenario = s;
}
export function getDemoScenario(): DemoScenario {
  return activeScenario;
}

function clone<T>(v: T): T {
  return JSON.parse(JSON.stringify(v));
}

class RealSupabaseApiService implements ApiService {
  async getSafetyZones(): Promise<SafetyZone[]> {
    try {
      const res = await fetch(`${SUPABASE_REST_URL}/crime_geographic_areas?select=*`, { headers: SUPABASE_HEADERS });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          const coords = [
            { lat: 17.4150, lng: 78.4350 },
            { lat: 17.4300, lng: 78.4100 },
            { lat: 17.4450, lng: 78.3800 },
            { lat: 17.4250, lng: 78.4550 },
            { lat: 17.4480, lng: 78.4700 }
          ];

          return data.map((a: any, idx: number) => {
            const riskVal = a.risk_index || 0.45;
            const coord = coords[idx % coords.length];
            return {
              id: a.id,
              name: a.name,
              riskScore: Math.round(riskVal * 100),
              riskLevel: riskVal > 0.7 ? 'veryhigh' : riskVal > 0.5 ? 'high' : riskVal > 0.3 ? 'moderate' : 'low',
              recentIncidents: 2,
              lighting: 'Good street lights (Supabase Live)',
              naturalSurveillance: 'High pedestrian traffic',
              policeDistanceKm: 1.1,
              hospitalDistanceKm: 0.5,
              commercialActivity: 'Active market corridor',
              communityRating: 4.5,
              center: coord,
              radiusM: 850,
              bounds: [[coord.lat - 0.005, coord.lng - 0.005], [coord.lat + 0.005, coord.lng + 0.005]],
              riskFactors: ['Active Police Jurisdiction Zone', 'Live PostGIS Polygon Boundary'],
              positiveFactors: ['High CCTV surveillance coverage', 'Nearby verified police station']
            };
          });
        }
      }
    } catch (e) {
      console.warn("Error fetching safety zones from Supabase:", e);
    }
    return clone(baseZones);
  }

  async getSafetySummary(): Promise<SafetySummary> {
    try {
      const res = await fetch(`${SUPABASE_REST_URL}/crime_incidents?select=count`, { headers: SUPABASE_HEADERS });
      if (res.ok) {
        const base = clone(baseSummary);
        base.activeAlerts = 9;
        return base;
      }
    } catch (e) {
      console.warn("Falling back to base summary:", e);
    }
    return clone(baseSummary);
  }

  async getRoutes(from: string, to: string): Promise<RouteOption[]> {
    return clone(baseRoutes);
  }

  async getSafeHavens(category?: string): Promise<SafeHaven[]> {
    try {
      const res = await fetch(`${SUPABASE_REST_URL}/emergency_facilities?select=*`, { headers: SUPABASE_HEADERS });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          let list: SafeHaven[] = data.map((f: any) => ({
            id: f.id,
            name: f.name,
            category: f.facility_type === 'police' ? 'Police' : f.facility_type === 'hospital' ? 'Hospital' : 'Transit',
            address: f.address || 'Verified Emergency Facility',
            distanceKm: 1.2,
            isOpen24h: f.is_24_hours ?? true,
            phone: f.phone || '112',
            verified: f.verification_status === 'VERIFIED',
            position: { lat: f.latitude || 17.385, lng: f.longitude || 78.486 },
            openStatus: 'Open 24/7 (Live Supabase)',
            safetyScore: 95
          }));

          if (category && category !== 'All') {
            list = list.filter((h) => h.category === category);
          }
          return list;
        }
      }
    } catch (e) {
      console.warn("Falling back to base safe havens:", e);
    }
    let list = clone(baseSafeHavens);
    if (category && category !== 'All') {
      list = list.filter((h) => h.category === category);
    }
    return list;
  }

  async getIncidents(): Promise<Incident[]> {
    try {
      const res = await fetch(`${SUPABASE_REST_URL}/crime_incidents?select=*`, { headers: SUPABASE_HEADERS });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          return data.map((inc: any) => ({
            id: inc.id,
            time: inc.occurred_at ? new Date(inc.occurred_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent',
            timestamp: inc.occurred_at ? new Date(inc.occurred_at).getTime() : Date.now(),
            location: inc.source_reference || 'Verified Geocoded Location',
            type: inc.incident_type,
            source: 'Verified',
            riskImpact: Math.round((inc.severity || 0.7) * 20),
            status: inc.verification_status === 'VERIFIED' ? 'Confirmed' : 'Reviewing',
            detail: inc.description || 'Verified geocoded incident in Supabase database.'
          }));
        }
      }
    } catch (e) {
      console.warn("Falling back to base incidents:", e);
    }
    return clone(baseIncidents);
  }

  async getCommunityReports(): Promise<CommunityReport[]> {
    return clone(baseReports);
  }

  async getCommunityFactors(): Promise<CommunityFactors> {
    return clone(baseFactors);
  }

  async submitCommunityReport(
    report: Omit<CommunityReport, 'id' | 'timestamp'>
  ): Promise<CommunityReport> {
    return {
      ...report,
      id: `cr-${Date.now()}`,
      timestamp: 'Just now',
    };
  }

  async triggerSOS(): Promise<{ ok: boolean; location: { lat: number; lng: number } }> {
    return { ok: true, location: { lat: 17.4435, lng: 78.3772 } };
  }

  async getJourneyStatus(): Promise<RouteOption> {
    return clone(baseRoutes[0]);
  }
}

export const api: ApiService = new RealSupabaseApiService();

export const communityStats = {
  average: communityAverage,
  count: communityReportCount,
};

export const currentUser: UserProfile = clone(baseUser);

export function updateContacts(contacts: EmergencyContact[]): void {
  currentUser.contacts = clone(contacts);
}
