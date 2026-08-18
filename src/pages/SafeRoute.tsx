import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Clock, MapPin, ShieldCheck, TriangleAlert, Check, ArrowRight, Navigation, Info } from 'lucide-react';
import SafetyMapCanvas from '@/components/SafetyMapCanvas';
import { Card, PageHeader, SafetyScoreBadge, SectionCard } from '@/components/ui';
import { api } from '@/services/api';
import { useApp } from '@/context/AppContext';
import type { RouteOption } from '@/data/types';
import { user as userData } from '@/data/users';

function RouteCard({
  route,
  selected,
  onSelect,
}: {
  route: RouteOption;
  selected: boolean;
  onSelect: () => void;
}) {
  const isSafe = route.safetyScore >= 85;
  const isRisky = route.safetyScore < 65;
  const tone = isSafe ? 'border-safe/40' : isRisky ? 'border-highrisk/40' : 'border-border';
  return (
    <div
      className={`rounded-[10px] border-2 bg-canvas p-5 transition-all ${
        selected ? 'border-accent shadow-cardHover' : `${tone} hover:border-accent/50`
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isSafe ? (
            <ShieldCheck className="h-5 w-5 text-safe-dark" aria-hidden="true" />
          ) : isRisky ? (
            <TriangleAlert className="h-5 w-5 text-highrisk-dark" aria-hidden="true" />
          ) : (
            <Clock className="h-5 w-5 text-moderate-dark" aria-hidden="true" />
          )}
          <h3 className="text-base font-semibold text-navy">{route.label} Route</h3>
          {route.recommended && (
            <span className="badge bg-accent-50 text-accent-700">Recommended</span>
          )}
        </div>
      </div>

      <div className="mt-4 flex items-baseline gap-4">
        <div>
          <div className="flex items-center gap-1.5 text-xs text-ink-soft">
            <Clock className="h-3.5 w-3.5" />
            Duration
          </div>
          <div className="mt-0.5 text-xl font-semibold text-navy">{route.durationMin} min</div>
        </div>
        <div>
          <div className="flex items-center gap-1.5 text-xs text-ink-soft">
            <MapPin className="h-3.5 w-3.5" />
            Distance
          </div>
          <div className="mt-0.5 text-xl font-semibold text-navy">{route.distanceKm} km</div>
        </div>
      </div>

      <div className="mt-4 border-t border-border pt-4">
        <div className="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-soft">Safety Score</div>
        <div className="flex items-center justify-between">
          <SafetyScoreBadge score={route.safetyScore} />
          <span className="text-2xl font-semibold text-navy">{route.safetyScore}<span className="text-sm text-ink-soft">/100</span></span>
        </div>
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-canvas-subtle">
          <div
            className={`h-full rounded-full ${isSafe ? 'bg-safe' : isRisky ? 'bg-highrisk' : 'bg-moderate'}`}
            style={{ width: `${route.safetyScore}%` }}
            aria-hidden="true"
          />
        </div>
      </div>

      <div className="mt-4 space-y-1.5 text-sm">
        {route.riskAreasAvoided > 0 ? (
          <p className="flex items-center gap-1.5 text-safe-dark">
            <Check className="h-4 w-4" />
            Avoids {route.riskAreasAvoided} high-risk area{route.riskAreasAvoided === 1 ? '' : 's'}
          </p>
        ) : (
          <p className="flex items-center gap-1.5 text-ink-soft">
            <Check className="h-4 w-4" />
            No high-risk areas to avoid
          </p>
        )}
        {route.riskAreasPassed > 0 && (
          <p className="flex items-center gap-1.5 text-highrisk-dark">
            <TriangleAlert className="h-4 w-4" />
            Passes {route.riskAreasPassed} high-risk area{route.riskAreasPassed === 1 ? '' : 's'}
          </p>
        )}
      </div>

      <button
        type="button"
        onClick={onSelect}
        className={`mt-5 w-full ${selected ? 'btn-accent' : 'btn-secondary'}`}
        aria-pressed={selected}
      >
        {selected ? (
          <>
            <Check className="h-4 w-4" />
            Selected
          </>
        ) : (
          'Select route'
        )}
      </button>
    </div>
  );
}

export default function SafeRoute() {
  const { setJourneyActive, notify } = useApp();
  const [routes, setRoutes] = useState<RouteOption[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [destination, setDestination] = useState('Banjara Hills');

  useEffect(() => {
    setLoading(true);
    api.getRoutes('Current Location', destination).then((r) => {
      setRoutes(r);
      setSelectedId(r.find((x) => x.recommended)?.id ?? r[0]?.id ?? null);
      setLoading(false);
    });
  }, [destination]);

  const selected = routes.find((r) => r.id === selectedId) ?? null;

  const startJourney = () => {
    setJourneyActive(true);
    notify('Journey started. Stay safe — we are monitoring your route.', 'success');
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Find the Safest Route" subtitle="Compare routes by safety, time, and distance." />

      <Card className="p-5">
        <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          <div>
            <label className="label" htmlFor="from">From</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-accent" aria-hidden="true" />
              <input id="from" className="input pl-9" defaultValue="Current Location" readOnly />
            </div>
          </div>
          <div>
            <label className="label" htmlFor="to">To</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-highrisk" aria-hidden="true" />
              <input
                id="to"
                className="input pl-9"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
              />
            </div>
          </div>
          <button type="button" className="btn-primary" onClick={() => notify('Routes refreshed.', 'info')}>
            <Search className="h-4 w-4" />
            Find Routes
          </button>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="space-y-4">
          <h2 className="section-title">Route Comparison</h2>
          {loading ? (
            <div className="space-y-4">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-56 animate-pulse rounded-[10px] bg-canvas-subtle" />
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {routes.map((r) => (
                <RouteCard
                  key={r.id}
                  route={r}
                  selected={r.id === selectedId}
                  onSelect={() => setSelectedId(r.id)}
                />
              ))}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <h2 className="section-title">Route Preview</h2>
          <Card className="h-[360px] overflow-hidden">
            {selected ? (
              <SafetyMapCanvas
                className="h-full w-full"
                data={{
                  center: userData.currentLocation,
                  route: selected,
                  userLocation: userData.currentLocation,
                  fitToRoute: true,
                }}
              />
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-ink-soft">Select a route to preview</div>
            )}
          </Card>

          {selected && (
            <SectionCard>
              <div className="flex items-start gap-3">
                <Info className="mt-0.5 h-5 w-5 flex-none text-accent" aria-hidden="true" />
                <div>
                  <h3 className="text-sm font-semibold text-navy">Why this route?</h3>
                  <p className="mt-1 text-sm text-ink">{selected.note}</p>
                </div>
              </div>
              <Link to="/journey" className="btn-accent mt-4 w-full" onClick={startJourney}>
                <Navigation className="h-4 w-4" />
                Start Journey
                <ArrowRight className="h-4 w-4" />
              </Link>
            </SectionCard>
          )}
        </div>
      </div>
    </div>
  );
}
