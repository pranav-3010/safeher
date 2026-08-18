import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, MapPin, ShieldCheck, TriangleAlert, Check, Navigation, Siren, Phone } from 'lucide-react';
import SafetyMapCanvas from '@/components/SafetyMapCanvas';
import { Card, PageHeader, SafetyScoreBadge, SectionCard } from '@/components/ui';
import { api } from '@/services/api';
import { useApp } from '@/context/AppContext';
import type { SafeHaven, SafetyZone, RouteOption } from '@/data/types';
import { user as userData } from '@/data/users';

const MONITORING = [
  { label: 'Street lighting', status: 'Good', good: true },
  { label: 'Police coverage', status: 'Good', good: true },
  { label: 'Crowd activity', status: 'Moderate', good: true },
  { label: 'Emergency access', status: 'Good', good: true },
];

export default function Journey() {
  const { journeyActive, setJourneyActive, notify } = useApp();
  const [route, setRoute] = useState<RouteOption | null>(null);
  const [zones, setZones] = useState<SafetyZone[]>([]);
  const [havens, setHavens] = useState<SafeHaven[]>([]);

  useEffect(() => {
    api.getJourneyStatus().then(setRoute);
    api.getSafetyZones().then(setZones);
    api.getSafeHavens().then(setHavens);
  }, []);

  const endJourney = () => {
    setJourneyActive(false);
    notify('Journey ended. You have reached safely.', 'success');
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Active Journey"
        subtitle="Live monitoring of your selected safe route."
        actions={
          <span
            className={`badge px-3 py-1 text-sm ${
              journeyActive ? 'bg-safe-light text-safe-dark' : 'bg-canvas-subtle text-ink-soft'
            }`}
          >
            <span className={`h-2 w-2 rounded-full ${journeyActive ? 'bg-safe animate-pulse' : 'bg-ink-soft'}`} aria-hidden="true" />
            {journeyActive ? 'Journey Protected' : 'No active journey'}
          </span>
        }
      />

      {!journeyActive && (
        <Card className="border-accent/30 bg-accent-50/40 p-5">
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <Navigation className="mt-0.5 h-5 w-5 text-accent" aria-hidden="true" />
              <div>
                <h3 className="text-sm font-semibold text-navy">No journey in progress</h3>
                <p className="text-sm text-ink-soft">Plan a safe route first to enable live monitoring.</p>
              </div>
            </div>
            <Link to="/safe-route" className="btn-accent">
              <Navigation className="h-4 w-4" />
              Plan Route
            </Link>
          </div>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          <Card className="h-[420px] overflow-hidden">
            <SafetyMapCanvas
              className="h-full w-full"
              data={{
                center: userData.currentLocation,
                route: route ?? undefined,
                zones,
                havens,
                userLocation: userData.currentLocation,
                fitToRoute: true,
              }}
            />
          </Card>

          <SectionCard title="Journey Monitoring">
            <ul className="space-y-2.5">
              {MONITORING.map((m) => (
                <li key={m.label} className="flex items-center justify-between rounded-[8px] border border-border px-4 py-3">
                  <span className="flex items-center gap-2.5 text-sm text-ink">
                    <span className={`flex h-6 w-6 items-center justify-center rounded-full ${m.good ? 'bg-safe-light text-safe-dark' : 'bg-moderate-light text-moderate-dark'}`}>
                      <Check className="h-3.5 w-3.5" />
                    </span>
                    {m.label}
                  </span>
                  <span className={`text-sm font-medium ${m.good ? 'text-safe-dark' : 'text-moderate-dark'}`}>{m.status}</span>
                </li>
              ))}
            </ul>
          </SectionCard>
        </div>

        <div className="space-y-4">
          <SectionCard title="Journey Information">
            <dl className="space-y-3">
              {[
                { label: 'ETA', value: route ? `${route.durationMin} min` : '—', icon: Clock },
                { label: 'Distance', value: route ? `${route.distanceKm} km` : '—', icon: MapPin },
                { label: 'Safety Score', value: route ? `${route.safetyScore}/100` : '—', icon: ShieldCheck },
                { label: 'Risk Zones Avoided', value: route ? route.riskAreasAvoided : '—', icon: TriangleAlert },
              ].map((row) => (
                <div key={row.label} className="flex items-center justify-between border-b border-border pb-3 last:border-0 last:pb-0">
                  <dt className="flex items-center gap-2 text-sm text-ink-soft">
                    <row.icon className="h-4 w-4" aria-hidden="true" />
                    {row.label}
                  </dt>
                  <dd className="text-sm font-semibold text-navy">{row.value}</dd>
                </div>
              ))}
            </dl>
            {route && <SafetyScoreBadge score={route.safetyScore} />}
          </SectionCard>

          <SectionCard title="Quick Emergency">
            <div className="space-y-2.5">
              <Link to="/emergency" className="btn-danger w-full">
                <Siren className="h-4 w-4" />
                Activate SOS
              </Link>
              <a href="tel:100" className="btn-secondary w-full">
                <Phone className="h-4 w-4" />
                Call Police — 100
              </a>
              {journeyActive && (
                <button type="button" onClick={endJourney} className="btn-ghost w-full">
                  End Journey
                </button>
              )}
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
