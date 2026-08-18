import { ShieldCheck, TriangleAlert, ShieldPlus, Users, ArrowRight, Siren, Route as RouteIcon, Map as MapIcon, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts';
import { useEffect, useState } from 'react';
import { Card, PageHeader, RiskBadge, SectionCard } from '@/components/ui';
import { api } from '@/services/api';
import type { SafetySummary } from '@/data/types';
import { RISK_META } from '@/data/types';

function SummaryCard({
  label,
  value,
  unit,
  icon: Icon,
  tone = 'neutral',
  hint,
}: {
  label: string;
  value: string | number;
  unit?: string;
  icon: typeof ShieldCheck;
  tone?: 'neutral' | 'safe' | 'moderate' | 'high' | 'danger';
  hint?: string;
}) {
  const tones: Record<string, string> = {
    neutral: 'text-navy',
    safe: 'text-safe-dark',
    moderate: 'text-moderate-dark',
    high: 'text-highrisk-dark',
    danger: 'text-danger-dark',
  };
  const iconBg: Record<string, string> = {
    neutral: 'bg-accent-50 text-accent',
    safe: 'bg-safe-light text-safe-dark',
    moderate: 'bg-moderate-light text-moderate-dark',
    high: 'bg-highrisk-light text-highrisk-dark',
    danger: 'bg-danger-light text-danger-dark',
  };
  return (
    <Card className="p-5" hover>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-ink-soft">{label}</div>
          <div className="mt-2 flex items-baseline gap-1.5">
            <span className={`stat-num ${tones[tone]}`}>{value}</span>
            {unit && <span className="text-sm font-medium text-ink-soft">{unit}</span>}
          </div>
          {hint && <div className="mt-1 text-xs text-ink-soft">{hint}</div>}
        </div>
        <span className={`flex h-10 w-10 flex-none items-center justify-center rounded-[8px] ${iconBg[tone]}`}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      </div>
    </Card>
  );
}

const QUICK_ACTIONS = [
  { to: '/safety-map', label: 'View Safety Map', icon: MapIcon },
  { to: '/safe-route', label: 'Find Safest Route', icon: RouteIcon },
  { to: '/safe-havens', label: 'Find Safe Haven', icon: ShieldPlus },
  { to: '/emergency', label: 'Open Emergency Center', icon: Siren, danger: true },
];

export default function Dashboard() {
  const [summary, setSummary] = useState<SafetySummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    api.getSafetySummary().then((s) => {
      if (active) {
        setSummary(s);
        setLoading(false);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  const safetyTone =
    summary == null
      ? 'neutral'
      : summary.currentSafety >= 80
        ? 'safe'
        : summary.currentSafety >= 60
          ? 'moderate'
          : 'danger';

  return (
    <div className="space-y-6">
      <PageHeader
        title="Safety Overview"
        subtitle="AI-powered safety intelligence for your journey"
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <SummaryCard
          label="Current Safety"
          value={loading ? '—' : summary!.currentSafety}
          unit="/ 100"
          icon={ShieldCheck}
          tone={safetyTone as 'neutral'}
          hint={loading ? 'Calculating…' : summary!.currentSafety >= 80 ? 'Low Risk' : summary!.currentSafety >= 60 ? 'Moderate' : 'High Risk'}
        />
        <SummaryCard
          label="Active Alerts"
          value={loading ? '—' : summary!.activeAlerts}
          icon={TriangleAlert}
          tone="high"
          hint="Nearby"
        />
        <SummaryCard
          label="Safe Havens"
          value={loading ? '—' : summary!.safeHavens}
          icon={ShieldPlus}
          tone="neutral"
          hint="Within 2 km"
        />
        <SummaryCard
          label="Community Reports"
          value={loading ? '—' : summary!.communityReports}
          icon={Users}
          tone="neutral"
          hint="This Week"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <SectionCard
          title="Safety Risk — Last 24 Hours"
          className="lg:col-span-2"
          action={<span className="inline-flex items-center gap-1.5 text-xs text-ink-soft"><Activity className="h-3.5 w-3.5" />Updated live</span>}
        >
          {summary ? (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={summary.trend} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="riskFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#2563EB" stopOpacity={0.22} />
                      <stop offset="100%" stopColor="#2563EB" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#EEF2F7" vertical={false} />
                  <XAxis dataKey="time" stroke="#9CA3AF" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis domain={[40, 100]} stroke="#9CA3AF" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 10,
                      border: '1px solid #E5E7EB',
                      boxShadow: '0 8px 24px -6px rgba(17,24,39,.12)',
                      fontSize: 12,
                    }}
                    formatter={(v: number) => [`${v}/100`, 'Safety score']}
                    labelStyle={{ color: '#172033', fontWeight: 600 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#2563EB"
                    strokeWidth={2.5}
                    fill="url(#riskFill)"
                    dot={{ r: 2.5, fill: '#2563EB', strokeWidth: 0 }}
                    activeDot={{ r: 5, fill: '#2563EB', stroke: '#fff', strokeWidth: 2 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 animate-pulse rounded-[8px] bg-canvas-subtle" />
          )}
          <p className="mt-3 text-xs text-ink-soft">
            Lower scores indicate higher risk. The score dips during evening hours when lighting and crowd activity decrease.
          </p>
        </SectionCard>

        <SectionCard title="Quick Actions">
          <div className="space-y-2.5">
            {QUICK_ACTIONS.map((a) => (
              <Link
                key={a.to}
                to={a.to}
                className={`group flex items-center justify-between rounded-[8px] border px-4 py-3 text-sm font-medium transition-colors ${
                  a.danger
                    ? 'border-danger/30 text-danger hover:bg-danger-light/60'
                    : 'border-border text-navy hover:border-accent hover:bg-accent-50'
                }`}
              >
                <span className="flex items-center gap-2.5">
                  <a.icon className={`h-[18px] w-[18px] ${a.danger ? 'text-danger' : 'text-accent'}`} aria-hidden="true" />
                  {a.label}
                </span>
                <ArrowRight className="h-4 w-4 text-ink-soft transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
              </Link>
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Recent Safety Updates">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-ink-soft">
                <th className="py-2.5 pr-4 font-medium">Time</th>
                <th className="py-2.5 pr-4 font-medium">Event</th>
                <th className="py-2.5 font-medium">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {(summary?.updates ?? []).map((u, i) => {
                const meta = RISK_META[u.risk];
                return (
                  <tr key={i} className="text-ink">
                    <td className="py-3 pr-4 whitespace-nowrap font-medium text-navy">{u.time}</td>
                    <td className="py-3 pr-4">{u.event}</td>
                    <td className="py-3">
                      <RiskBadge level={u.risk} />
                    </td>
                  </tr>
                );
              })}
              {!summary && (
                <tr>
                  <td colSpan={3} className="py-8 text-center text-ink-soft">Loading updates…</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}
