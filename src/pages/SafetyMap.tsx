import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Filter, Layers, X, ArrowRight, Lightbulb, Eye, Building2, Users, Phone, Navigation, ShieldPlus } from 'lucide-react';
import SafetyMapCanvas from '@/components/SafetyMapCanvas';
import { Card, PageHeader, RiskBadge, SafetyScoreBadge, SourceBadge } from '@/components/ui';
import { api } from '@/services/api';
import { RISK_META, type SafeHaven, type SafetyZone } from '@/data/types';
import { user as userData } from '@/data/users';

const FILTERS = [
  { id: 'risk', label: 'Safety Risk' },
  { id: 'lighting', label: 'Lighting' },
  { id: 'incidents', label: 'Incidents' },
  { id: 'police', label: 'Police' },
  { id: 'havens', label: 'Safe Havens' },
  { id: 'community', label: 'Community' },
] as const;

const LEGEND: { level: keyof typeof RISK_META; label: string }[] = [
  { level: 'low', label: 'Low' },
  { level: 'moderate', label: 'Moderate' },
  { level: 'high', label: 'High' },
  { level: 'veryhigh', label: 'Very High' },
];

function ZoneDetail({ zone, havens, onClose }: { zone: SafetyZone; havens: SafeHaven[]; onClose: () => void }) {
  const nearbyHavens = havens.filter((h) => h.distanceKm <= 2).slice(0, 3);
  const rows: { label: string; value: string; icon: typeof Lightbulb }[] = [
    { label: 'Lighting', value: zone.lighting, icon: Lightbulb },
    { label: 'Natural Surveillance', value: zone.naturalSurveillance, icon: Eye },
    { label: 'Police Distance', value: `${zone.policeDistanceKm} km`, icon: ShieldPlus },
    { label: 'Hospital Distance', value: `${zone.hospitalDistanceKm} km`, icon: Phone },
    { label: 'Commercial Activity', value: zone.commercialActivity, icon: Building2 },
    { label: 'Community Rating', value: `${zone.communityRating} / 5`, icon: Users },
  ];
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-start justify-between gap-3 border-b border-border p-5">
        <div>
          <h2 className="text-lg font-semibold text-navy">{zone.name}</h2>
          <p className="text-xs text-ink-soft">Safety Analysis</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-[8px] p-1.5 text-ink-soft hover:bg-canvas-subtle hover:text-navy"
          aria-label="Close zone details"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto p-5">
        <div className="flex items-center justify-between rounded-[8px] bg-canvas-subtle p-4">
          <div>
            <div className="text-xs font-medium uppercase tracking-wide text-ink-soft">Risk Score</div>
            <div className="mt-1 flex items-baseline gap-1.5">
              <span className="text-3xl font-semibold text-navy">{zone.riskScore}</span>
              <span className="text-sm text-ink-soft">/ 100</span>
            </div>
          </div>
          <RiskBadge level={zone.riskLevel} score={zone.riskScore} size="md" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          {rows.map((r) => (
            <div key={r.label} className="rounded-[8px] border border-border p-3">
              <div className="flex items-center gap-1.5 text-xs text-ink-soft">
                <r.icon className="h-3.5 w-3.5" aria-hidden="true" />
                {r.label}
              </div>
              <div className="mt-1 text-sm font-medium text-navy">{r.value}</div>
            </div>
          ))}
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wide text-ink-soft">Recent Incidents</span>
            <span className="text-sm font-semibold text-navy">{zone.recentIncidents}</span>
          </div>
        </div>

        <div className="rounded-[8px] border border-border p-4">
          <h3 className="text-sm font-semibold text-navy">Why is this area risky?</h3>
          <ul className="mt-2 space-y-2">
            {zone.riskFactors.map((f, i) => (
              <li key={i} className="flex gap-2 text-sm text-ink">
                <span className="mt-2 h-1.5 w-1.5 flex-none rounded-full bg-highrisk" aria-hidden="true" />
                {f}
              </li>
            ))}
          </ul>
          {zone.positiveFactors.length > 0 && (
            <>
              <h3 className="mt-4 text-sm font-semibold text-navy">Safety strengths</h3>
              <ul className="mt-2 space-y-2">
                {zone.positiveFactors.map((f, i) => (
                  <li key={i} className="flex gap-2 text-sm text-ink">
                    <span className="mt-2 h-1.5 w-1.5 flex-none rounded-full bg-safe" aria-hidden="true" />
                    {f}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>

        {nearbyHavens.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-semibold text-navy">Nearby safe havens</h3>
            <div className="space-y-2">
              {nearbyHavens.map((h) => (
                <Link
                  key={h.id}
                  to="/safe-havens"
                  className="flex items-center justify-between rounded-[8px] border border-border px-3 py-2 text-sm transition-colors hover:border-accent hover:bg-accent-50"
                >
                  <span className="flex items-center gap-2 text-navy">
                    <ShieldPlus className="h-4 w-4 text-accent" aria-hidden="true" />
                    {h.name}
                  </span>
                  <span className="text-xs text-ink-soft">{h.distanceKm} km</span>
                </Link>
              ))}
            </div>
          </div>
        )}

        <Link to="/safe-route" className="btn-accent w-full">
          <Navigation className="h-4 w-4" />
          Plan safe route from here
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}

function InfoPanel({ zones, selected, onSelect }: { zones: SafetyZone[]; selected: SafetyZone | null; onSelect: (z: SafetyZone) => void }) {
  const sorted = useMemo(() => [...zones].sort((a, b) => b.riskScore - a.riskScore), [zones]);
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-4 py-3">
        <h3 className="text-sm font-semibold text-navy">Safety Zones</h3>
        <p className="text-xs text-ink-soft">Tap a zone to view analysis</p>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {sorted.map((z) => {
          const meta = RISK_META[z.riskLevel];
          return (
            <button
              key={z.id}
              type="button"
              onClick={() => onSelect(z)}
              className={`mb-1.5 flex w-full items-center justify-between rounded-[8px] border px-3 py-2.5 text-left transition-colors ${
                selected?.id === z.id
                  ? 'border-accent bg-accent-50'
                  : 'border-transparent hover:bg-canvas-subtle'
              }`}
            >
              <span className="flex items-center gap-2.5">
                <span className={`h-2.5 w-2.5 rounded-full ${meta.dot}`} aria-hidden="true" />
                <span className="text-sm font-medium text-navy">{z.name}</span>
              </span>
              <span className="text-xs font-semibold text-ink-soft">{z.riskScore}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function SafetyMap() {
  const [zones, setZones] = useState<SafetyZone[]>([]);
  const [havens, setHavens] = useState<SafeHaven[]>([]);
  const [selected, setSelected] = useState<SafetyZone | null>(null);
  const [filters, setFilters] = useState<Record<string, boolean>>({
    risk: true,
    lighting: false,
    incidents: true,
    police: true,
    havens: true,
    community: false,
  });

  useEffect(() => {
    api.getSafetyZones().then(setZones);
    api.getSafeHavens().then(setHavens);
  }, []);

  const toggle = (id: string) => setFilters((f) => ({ ...f, [id]: !f[id] }));

  const visibleZones = filters.risk ? zones : [];
  const visibleHavens = filters.havens ? havens.filter((h) => (filters.police ? true : h.category !== 'Police')) : [];
  const policeOnly = filters.police && !filters.havens ? havens.filter((h) => h.category === 'Police') : [];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Safety Intelligence Map"
        subtitle="Explore predicted safety conditions across the city."
        actions={
          <span className="hidden items-center gap-1.5 text-xs text-ink-soft sm:inline-flex">
            <Layers className="h-3.5 w-3.5" />
            {zones.length} zones mapped
          </span>
        }
      />

      {/* Filters */}
      <Card className="p-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="flex items-center gap-1.5 text-xs font-medium text-ink-soft">
            <Filter className="h-3.5 w-3.5" />
            Layers:
          </span>
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => toggle(f.id)}
              aria-pressed={filters[f.id]}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                filters[f.id]
                  ? 'bg-navy text-white'
                  : 'border border-border bg-canvas text-ink-soft hover:bg-canvas-subtle'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 rounded-[8px] bg-canvas px-4 py-2.5 text-xs">
        <span className="font-medium text-ink-soft">Risk legend:</span>
        {LEGEND.map((l) => (
          <span key={l.level} className="inline-flex items-center gap-1.5 text-ink">
            <span className={`h-2.5 w-2.5 rounded-full ${RISK_META[l.level].dot}`} aria-hidden="true" />
            {l.label}
          </span>
        ))}
      </div>

      {/* Map + panels */}
      <div className="grid gap-4 lg:grid-cols-[280px_1fr] xl:grid-cols-[280px_1fr_320px]">
        {/* Zones list — hidden on mobile, shown as bottom sheet behavior via stacking */}
        <Card className="hidden h-[600px] overflow-hidden lg:block">
          <InfoPanel zones={zones} selected={selected} onSelect={setSelected} />
        </Card>

        <Card className="h-[480px] overflow-hidden lg:h-[600px]">
          <SafetyMapCanvas
            className="h-full w-full"
            data={{
              center: userData.currentLocation,
              zones: visibleZones,
              havens: [...visibleHavens, ...policeOnly],
              userLocation: userData.currentLocation,
              onZoneClick: setSelected,
            }}
          />
        </Card>

        {/* Zone details */}
        {selected && (
          <Card className="h-[480px] overflow-hidden lg:h-[600px] lg:col-span-2 xl:col-span-1 animate-slide-in-right">
            <ZoneDetail zone={selected} havens={havens} onClose={() => setSelected(null)} />
          </Card>
        )}
      </div>

      {/* Mobile zones list */}
      <Card className="overflow-hidden lg:hidden">
        <InfoPanel zones={zones} selected={selected} onSelect={setSelected} />
      </Card>
    </div>
  );
}
