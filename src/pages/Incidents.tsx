import { useEffect, useMemo, useState } from 'react';
import { Newspaper, TriangleAlert, Info, Clock, ShieldCheck } from 'lucide-react';
import { Card, PageHeader, RiskBadge, SectionCard, SourceBadge, EmptyState } from '@/components/ui';
import { api } from '@/services/api';
import type { Incident, IncidentSource } from '@/data/types';

const SOURCE_FILTERS: (IncidentSource | 'All')[] = ['All', 'Verified', 'Community', 'News', 'AI Signal'];

function impactBadge(impact: number) {
  if (impact === 0) return <span className="text-ink-soft">—</span>;
  if (impact > 0) return <span className="badge bg-highrisk-light text-highrisk-dark">+{impact}</span>;
  return <span className="badge bg-safe-light text-safe-dark">{impact}</span>;
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    Reviewing: 'bg-moderate-light text-moderate-dark',
    Confirmed: 'bg-accent-50 text-accent-700',
    Resolved: 'bg-safe-light text-safe-dark',
    Expired: 'bg-canvas-subtle text-ink-soft',
  };
  return <span className={`badge ${map[status] ?? 'bg-canvas-subtle text-ink-soft'}`}>{status}</span>;
}

function aiSignals(incidents: Incident[]) {
  return incidents.filter((i) => i.source === 'AI Signal' || i.source === 'News');
}

export default function Incidents() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [sourceFilter, setSourceFilter] = useState<IncidentSource | 'All'>('All');

  useEffect(() => {
    api.getIncidents().then(setIncidents);
  }, []);

  const filtered = useMemo(
    () => incidents.filter((i) => (sourceFilter === 'All' ? true : i.source === sourceFilter)),
    [incidents, sourceFilter]
  );

  const signals = aiSignals(incidents);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Safety Intelligence"
        subtitle="Recent incidents, news signals and AI-generated risk updates."
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <SectionCard title="Incident Log">
          <div className="mb-4 flex flex-wrap gap-2">
            {SOURCE_FILTERS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSourceFilter(s)}
                aria-pressed={sourceFilter === s}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  sourceFilter === s
                    ? 'bg-navy text-white'
                    : 'border border-border bg-canvas text-ink-soft hover:bg-canvas-subtle'
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-ink-soft">
                  <th className="py-2.5 pr-3 font-medium">Time</th>
                  <th className="py-2.5 pr-3 font-medium">Location</th>
                  <th className="py-2.5 pr-3 font-medium">Type</th>
                  <th className="py-2.5 pr-3 font-medium">Source</th>
                  <th className="py-2.5 pr-3 font-medium">Risk Impact</th>
                  <th className="py-2.5 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((i) => (
                  <tr key={i.id} className="text-ink">
                    <td className="py-3 pr-3 whitespace-nowrap font-medium text-navy">{i.time}</td>
                    <td className="py-3 pr-3 whitespace-nowrap">{i.location}</td>
                    <td className="py-3 pr-3">{i.type}</td>
                    <td className="py-3 pr-3"><SourceBadge source={i.source} /></td>
                    <td className="py-3 pr-3">{impactBadge(i.riskImpact)}</td>
                    <td className="py-3">{statusBadge(i.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && <EmptyState message="No incidents match this filter." />}
          </div>
          <p className="mt-4 flex items-start gap-2 rounded-[8px] bg-canvas-subtle p-3 text-xs text-ink-soft">
            <Info className="mt-0.5 h-4 w-4 flex-none" aria-hidden="true" />
            Community and news signals are unverified. They adjust risk temporarily and expire automatically. Only <strong className="font-semibold text-navy">Verified</strong> incidents are confirmed by authorities.
          </p>
        </SectionCard>

        <SectionCard title="Recent AI Signals">
          {signals.length === 0 ? (
            <EmptyState message="No AI signals detected." />
          ) : (
            <div className="space-y-3">
              {signals.map((s) => (
                <div key={s.id} className="rounded-[8px] border border-border p-4">
                  <div className="flex items-center gap-2">
                    <Newspaper className="h-4 w-4 text-navy-600" aria-hidden="true" />
                    <span className="text-sm font-semibold text-navy">
                      {s.source === 'AI Signal' ? 'AI signal detected' : 'News signal detected'}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-ink">{s.detail}</p>
                  <div className="mt-3 space-y-1.5 text-xs text-ink-soft">
                    <div className="flex items-center justify-between">
                      <span>Temporary risk adjustment</span>
                      <span className="font-semibold text-highrisk-dark">+{s.riskImpact}</span>
                    </div>
                    {s.expiresAt && (
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1"><Clock className="h-3 w-3" />Expires</span>
                        <span>{s.expiresAt}</span>
                      </div>
                    )}
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <SourceBadge source={s.source} />
                    {s.status === 'Reviewing' && <RiskBadge level="moderate" />}
                    {s.status === 'Confirmed' && <RiskBadge level="high" />}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 rounded-[8px] border border-border bg-canvas-subtle p-4">
            <h4 className="flex items-center gap-2 text-sm font-semibold text-navy">
              <ShieldCheck className="h-4 w-4 text-safe-dark" />
              Verification status
            </h4>
            <ul className="mt-2 space-y-1.5 text-xs text-ink-soft">
              <li className="flex items-center gap-2"><TriangleAlert className="h-3.5 w-3.5 text-moderate" /> Unverified signals never display as confirmed fact.</li>
              <li className="flex items-center gap-2"><Info className="h-3.5 w-3.5 text-accent" /> Signals expire automatically and risk reverts.</li>
            </ul>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
