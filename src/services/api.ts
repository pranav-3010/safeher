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

/**
 * API abstraction layer.
 *
 * Components consume these async functions instead of importing mock data directly.
 * This lets the future backend (FastAPI + ML model + DB) be swapped in by replacing
 * the bodies of these functions with `fetch` calls — no component rewrite needed.
 *
 * Target backend contract:
 *   GET  /safety/zones
 *   GET  /safety/score
 *   GET  /routes/safest
 *   GET  /safe-havens
 *   GET  /incidents
 *   GET  /community/reports
 *   POST /community/reports
 *   POST /emergency/sos
 *   GET  /journey/status
 */

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

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
}

// Demo scenario overrides applied to the in-memory dataset
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

class MockApiService implements ApiService {
  async getSafetyZones(): Promise<SafetyZone[]> {
    await delay(120);
    const z = clone(baseZones);
    if (activeScenario === 'high-risk-zone') {
      const mg = z.find((x) => x.id === 'z-mg-road');
      if (mg) {
        mg.riskScore = 88;
        mg.riskLevel = 'veryhigh';
        mg.recentIncidents = 3;
      }
    }
    return z;
  }

  async getSafetySummary(): Promise<SafetySummary> {
    await delay(120);
    const s = clone(baseSummary);
    if (activeScenario === 'high-risk-zone') {
      s.currentSafety = 58;
      s.activeAlerts = 5;
    } else if (activeScenario === 'new-incident') {
      s.currentSafety = 71;
      s.activeAlerts = 4;
      s.updates.unshift({
        time: 'Just now',
        event: 'New incident reported — Abids',
        risk: 'high',
      });
    } else if (activeScenario === 'emergency-sos') {
      s.currentSafety = 40;
      s.activeAlerts = 6;
    }
    return s;
  }

  async getRoutes(_from: string, _to: string): Promise<RouteOption[]> {
    await delay(160);
    const r = clone(baseRoutes);
    if (activeScenario === 'safest-route-changed') {
      const safest = r.find((x) => x.label === 'Safest');
      const balanced = r.find((x) => x.label === 'Balanced');
      if (safest && balanced) {
        safest.safetyScore = 84;
        safest.durationMin = 21;
        safest.note =
          'A new incident on the previous safest path has lowered its score. This route now adds 7 minutes but remains the safest option.';
        balanced.safetyScore = 79;
        balanced.recommended = true;
        safest.recommended = false;
      }
    }
    return r;
  }

  async getSafeHavens(category?: string): Promise<SafeHaven[]> {
    await delay(100);
    let list = clone(baseSafeHavens);
    if (category && category !== 'All') {
      list = list.filter((h) => h.category === category);
    }
    return list;
  }

  async getIncidents(): Promise<Incident[]> {
    await delay(120);
    const list = clone(baseIncidents);
    if (activeScenario === 'new-incident') {
      list.unshift({
        id: 'inc-new',
        time: 'Just now',
        timestamp: Date.now(),
        location: 'Abids',
        type: 'New Incident Reported',
        source: 'Community',
        riskImpact: 16,
        status: 'Reviewing',
        detail: 'A community member reported an unsafe approach near the bus terminal.',
      });
    }
    return list;
  }

  async getCommunityReports(): Promise<CommunityReport[]> {
    await delay(100);
    return clone(baseReports);
  }

  async getCommunityFactors(): Promise<CommunityFactors> {
    await delay(80);
    const f = clone(baseFactors);
    if (activeScenario === 'high-risk-zone') {
      f.feelsSafe = 58;
      f.wellLit = 52;
      f.policePresence = 44;
    }
    return f;
  }

  async submitCommunityReport(
    report: Omit<CommunityReport, 'id' | 'timestamp'>
  ): Promise<CommunityReport> {
    await delay(140);
    return {
      ...report,
      id: `cr-${Date.now()}`,
      timestamp: 'Just now',
    };
  }

  async triggerSOS(): Promise<{ ok: boolean; location: { lat: number; lng: number } }> {
    await delay(200);
    return { ok: true, location: { lat: 17.4435, lng: 78.3772 } };
  }

  async getJourneyStatus(): Promise<RouteOption> {
    await delay(120);
    const r = clone(baseRoutes[0]);
    if (activeScenario === 'safest-route-changed') {
      r.safetyScore = 84;
      r.durationMin = 21;
    }
    return r;
  }
}

export const api: ApiService = new MockApiService();

export const communityStats = {
  average: communityAverage,
  count: communityReportCount,
};

export const currentUser: UserProfile = clone(baseUser);

export function updateContacts(contacts: EmergencyContact[]): void {
  currentUser.contacts = clone(contacts);
}
