import { useEffect, useState } from 'react';
import { Star, Send, MapPin, Users, ThumbsUp } from 'lucide-react';
import { Card, PageHeader, SectionCard, EmptyState } from '@/components/ui';
import { api, communityStats } from '@/services/api';
import { useApp } from '@/context/AppContext';
import type { CommunityFactors, CommunityReport } from '@/data/types';

const CONDITIONS = [
  'Well Lit',
  'Poor Lighting',
  'Crowded',
  'Isolated',
  'Police Presence',
  'Unsafe Activity',
  'Other',
] as const;

function FactorBar({ label, value }: { label: string; value: number }) {
  const color = value >= 75 ? 'bg-safe' : value >= 50 ? 'bg-moderate' : 'bg-highrisk';
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-sm">
        <span className="text-ink">{label}</span>
        <span className="font-semibold text-navy">{value}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-canvas-subtle">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${value}%` }} aria-hidden="true" />
      </div>
    </div>
  );
}

function ReportCard({ report }: { report: CommunityReport }) {
  const tone: Record<string, string> = {
    'Well Lit': 'bg-safe-light text-safe-dark',
    'Police Presence': 'bg-accent-50 text-accent-700',
    Crowded: 'bg-accent-50 text-accent-700',
    'Poor Lighting': 'bg-moderate-light text-moderate-dark',
    Isolated: 'bg-highrisk-light text-highrisk-dark',
    'Unsafe Activity': 'bg-danger-light text-danger-dark',
    Other: 'bg-canvas-subtle text-ink-soft',
  };
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className={`badge ${tone[report.condition]}`}>{report.condition}</span>
            <span className="text-xs text-ink-soft">{report.timestamp}</span>
          </div>
          <p className="mt-2 text-sm text-ink">{report.comment}</p>
          <p className="mt-2 flex items-center gap-1 text-xs text-ink-soft">
            <MapPin className="h-3 w-3" />
            {report.location}
          </p>
        </div>
        <div className="flex flex-none items-center gap-0.5 text-moderate">
          {[1, 2, 3, 4, 5].map((n) => (
            <Star
              key={n}
              className={`h-3.5 w-3.5 ${n <= report.rating ? 'fill-moderate text-moderate' : 'text-border-strong'}`}
              aria-hidden="true"
            />
          ))}
        </div>
      </div>
    </Card>
  );
}

export default function Community() {
  const { notify } = useApp();
  const [reports, setReports] = useState<CommunityReport[]>([]);
  const [factors, setFactors] = useState<CommunityFactors | null>(null);
  const [location, setLocation] = useState('Current Location');
  const [condition, setCondition] = useState<(typeof CONDITIONS)[number]>('Well Lit');
  const [comment, setComment] = useState('');
  const [rating, setRating] = useState(4);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.getCommunityReports().then(setReports);
    api.getCommunityFactors().then(setFactors);
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const created = await api.submitCommunityReport({ location, condition, comment, rating });
    setReports((r) => [created, ...r]);
    setComment('');
    setSubmitting(false);
    notify('Safety report submitted. Thank you for contributing.', 'success');
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Community Safety" subtitle="Real safety conditions reported by people near you." />

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <SectionCard>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-semibold text-navy">{communityStats.average}</span>
                <span className="text-sm text-ink-soft">/ 5 average</span>
              </div>
              <div className="mt-1 flex items-center gap-1.5 text-sm text-ink-soft">
                <Users className="h-4 w-4" />
                {communityStats.count} reports this week
              </div>
            </div>
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-safe-light">
              <ThumbsUp className="h-7 w-7 text-safe-dark" aria-hidden="true" />
            </span>
          </div>
        </SectionCard>

        <SectionCard title="Community Factors">
          {factors ? (
            <div className="space-y-4">
              <FactorBar label="Feels Safe" value={factors.feelsSafe} />
              <FactorBar label="Well Lit" value={factors.wellLit} />
              <FactorBar label="Crowded" value={factors.crowded} />
              <FactorBar label="Police Presence" value={factors.policePresence} />
            </div>
          ) : (
            <div className="h-32 animate-pulse rounded-[8px] bg-canvas-subtle" />
          )}
        </SectionCard>
      </div>

      <SectionCard title="Submit Safety Report">
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="label" htmlFor="rpt-loc">Location</label>
            <input
              id="rpt-loc"
              className="input"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Enter location"
            />
          </div>
          <div>
            <span className="label">Condition</span>
            <div className="flex flex-wrap gap-2">
              {CONDITIONS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setCondition(c)}
                  aria-pressed={condition === c}
                  className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${
                    condition === c
                      ? 'bg-navy text-white'
                      : 'border border-border bg-canvas text-ink-soft hover:bg-canvas-subtle'
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
          <div>
            <span className="label">Rating</span>
            <div className="flex items-center gap-1.5">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setRating(n)}
                  aria-label={`${n} star${n === 1 ? '' : 's'}`}
                  className="rounded p-1 transition-transform hover:scale-110"
                >
                  <Star
                    className={`h-6 w-6 ${n <= rating ? 'fill-moderate text-moderate' : 'text-border-strong'}`}
                  />
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label" htmlFor="rpt-comment">Comment</label>
            <textarea
              id="rpt-comment"
              className="input min-h-[88px] resize-y"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Describe what you observed…"
            />
          </div>
          <button type="submit" className="btn-primary" disabled={submitting || !comment.trim()}>
            <Send className="h-4 w-4" />
            {submitting ? 'Submitting…' : 'Submit Report'}
          </button>
        </form>
      </SectionCard>

      <SectionCard title="Recent Community Reports">
        {reports.length === 0 ? (
          <EmptyState message="No community reports yet." />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {reports.map((r) => (
              <ReportCard key={r.id} report={r} />
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
