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

// Get API Base URL from environment variables or fallback to localhost:8000
const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

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

class RealFastApiApiService implements ApiService {
  async getSafetyZones(): Promise<SafetyZone[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/map/geographic-areas`);
      if (res.ok) {
        const data = await res.json();
        if (data.geographic_areas && data.geographic_areas.length > 0) {
          return data.geographic_areas.map((a: any, idx: number) => ({
            id: a.id || `z-${idx}`,
            name: a.name,
            riskScore: Math.round((a.risk_index || 0.4) * 100),
            riskLevel: (a.risk_index || 0.4) > 0.7 ? 'veryhigh' : (a.risk_index || 0.4) > 0.5 ? 'high' : 'moderate',
            recentIncidents: 2,
            lighting: 'Good street lights',
            naturalSurveillance: 'High pedestrian traffic',
            policeDistanceKm: 1.1,
            hospitalDistanceKm: 0.5,
            commercialActivity: 'Active market corridor',
            communityRating: 4.2,
            coordinates: { lat: 17.410, lng: 78.440 },
            bounds: [[17.410, 78.435], [17.428, 78.455]],
            riskFactors: ['Dense pedestrian congestion', 'Active commercial traffic'],
            positiveFactors: ['High CCTV surveillance coverage', 'Nearby police station']
          }));
        }
      }
    } catch (e) {
      console.warn("Falling back to base zones due to backend fetch error:", e);
    }
    return clone(baseZones);
  }

  async getSafetySummary(): Promise<SafetySummary> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/map/crime-density?latitude=17.3850&longitude=78.4867&radius=1000`);
      if (res.ok) {
        const data = await res.json();
        const base = clone(baseSummary);
        base.activeAlerts = data.nearby_incident_count || base.activeAlerts;
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
      const res = await fetch(`${API_BASE_URL}/api/v1/map/emergency-services/nearby?latitude=17.3850&longitude=78.4867&radius=10000`);
      if (res.ok) {
        const data = await res.json();
        if (data.facilities && data.facilities.length > 0) {
          let list: SafeHaven[] = data.facilities.map((f: any) => ({
            id: f.id,
            name: f.name,
            category: f.facility_type === 'police' ? 'Police' : f.facility_type === 'hospital' ? 'Hospital' : 'Transit',
            address: f.address || 'Verified Emergency Facility',
            distanceKm: parseFloat((f.distance_meters / 1000).toFixed(1)),
            isOpen24h: f.is_24_hours ?? true,
            phone: f.phone || '112',
            verified: f.verification_status === 'VERIFIED',
            lat: f.latitude,
            lng: f.longitude,
            safetyScore: 92
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
      const res = await fetch(`${API_BASE_URL}/api/v1/map/incidents/nearby?latitude=17.3850&longitude=78.4867&radius=50000`);
      if (res.ok) {
        const data = await res.json();
        if (data.incidents && data.incidents.length > 0) {
          return data.incidents.map((inc: any) => ({
            id: inc.id,
            time: inc.occurred_at ? new Date(inc.occurred_at).toLocaleTimeString() : 'Recent',
            timestamp: inc.occurred_at ? new Date(inc.occurred_at).getTime() : Date.now(),
            location: inc.source_reference || 'Verified Geocoded Incident',
            type: inc.incident_type,
            source: 'Official Police Portal',
            riskImpact: Math.round((inc.severity || 0.7) * 20),
            status: inc.verification_status || 'VERIFIED',
            detail: inc.description || 'Verified geocoded incident in database.'
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

  async askAISafetyQuestion(question: string, lat: number = 17.3850, lng: number = 78.4867): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ai/safety-question`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: lat,
        longitude: lng,
        radius_meters: 2000.0,
        question: question
      })
    });
    if (res.ok) {
      return await res.json();
    }
    throw new Error("Failed to get AI safety answer");
  }
}

export const api: ApiService = new RealFastApiApiService();

export const communityStats = {
  average: communityAverage,
  count: communityReportCount,
};

export const currentUser: UserProfile = clone(baseUser);

export function updateContacts(contacts: EmergencyContact[]): void {
  currentUser.contacts = clone(contacts);
}
