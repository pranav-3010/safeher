import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Navigation, Phone, MapPin, ShieldPlus, Clock, Search } from 'lucide-react';
import SafetyMapCanvas from '@/components/SafetyMapCanvas';
import { Card, PageHeader, SectionCard } from '@/components/ui';
import { api } from '@/services/api';
import type { SafeHaven, SafeHavenCategory } from '@/data/types';
import { user as userData } from '@/data/users';

const CATEGORIES: (SafeHavenCategory | 'All')[] = [
  'All',
  'Police',
  'Hospital',
  'Metro',
  'Petrol Pump',
  'Open Business',
];

const CATEGORY_COLOR: Record<SafeHavenCategory, string> = {
  Police: 'bg-accent-50 text-accent-700',
  Hospital: 'bg-safe-light text-safe-dark',
  Metro: 'bg-moderate-light text-moderate-dark',
  'Petrol Pump': 'bg-navy-50 text-navy-600',
  'Open Business': 'bg-canvas-subtle text-navy',
};

function HavenCard({ haven }: { haven: SafeHaven }) {
  return (
    <Card className="p-5" hover>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className={`flex h-10 w-10 flex-none items-center justify-center rounded-[8px] ${CATEGORY_COLOR[haven.category]}`}>
            <ShieldPlus className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <h3 className="text-base font-semibold text-navy">{haven.name}</h3>
            <span className={`badge mt-1 ${CATEGORY_COLOR[haven.category]}`}>{haven.category}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 text-sm font-semibold text-navy">
            <MapPin className="h-3.5 w-3.5 text-ink-soft" />
            {haven.distanceKm} km
          </div>
        </div>
      </div>

      <div className="mt-3 flex items-center gap-1.5 text-xs text-ink-soft">
        <Clock className="h-3.5 w-3.5" />
        {haven.openStatus}
        {haven.open247 && (
          <span className="badge bg-safe-light text-safe-dark ml-1">24/7</span>
        )}
      </div>

      <div className="mt-4 flex gap-2">
        <Link to="/journey" className="btn-accent flex-1 !py-2 !text-xs">
          <Navigation className="h-3.5 w-3.5" />
          Navigate
        </Link>
        {haven.phone && (
          <a href={`tel:${haven.phone}`} className="btn-secondary flex-1 !py-2 !text-xs">
            <Phone className="h-3.5 w-3.5" />
            Call
          </a>
        )}
      </div>
    </Card>
  );
}

export default function SafeHavens() {
  const [havens, setHavens] = useState<SafeHaven[]>([]);
  const [category, setCategory] = useState<(SafeHavenCategory | 'All')>('All');
  const [query, setQuery] = useState('');

  useEffect(() => {
    api.getSafeHavens().then(setHavens);
  }, []);

  const filtered = useMemo(() => {
    return havens
      .filter((h) => (category === 'All' ? true : h.category === category))
      .filter((h) => (query ? h.name.toLowerCase().includes(query.toLowerCase()) : true))
      .sort((a, b) => a.distanceKm - b.distanceKm);
  }, [havens, category, query]);

  const mapHavens = filtered.slice(0, 12);

  return (
    <div className="space-y-6">
      <PageHeader title="Nearby Safe Havens" subtitle="Find accessible places where help is available." />

      <Card className="p-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-soft" aria-hidden="true" />
            <input
              className="input pl-9"
              placeholder="Search safe havens…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search safe havens"
            />
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setCategory(c)}
              aria-pressed={category === c}
              className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${
                category === c
                  ? 'bg-navy text-white'
                  : 'border border-border bg-canvas text-ink-soft hover:bg-canvas-subtle'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div>
          <div className="mb-3 text-sm text-ink-soft">
            {filtered.length} safe haven{filtered.length === 1 ? '' : 's'} within range
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {filtered.map((h) => (
              <HavenCard key={h.id} haven={h} />
            ))}
            {filtered.length === 0 && (
              <Card className="col-span-full p-8 text-center text-sm text-ink-soft">
                No safe havens match your search.
              </Card>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <SectionCard title="Map View">
            <Card className="h-[340px] overflow-hidden">
              <SafetyMapCanvas
                className="h-full w-full"
                data={{
                  center: userData.currentLocation,
                  havens: mapHavens,
                  userLocation: userData.currentLocation,
                }}
              />
            </Card>
            <p className="mt-3 text-xs text-ink-soft">
              Markers show nearby safe havens. Your location is shown in blue.
            </p>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
