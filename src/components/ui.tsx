import { type ReactNode } from 'react';
import { RISK_META, type RiskLevel } from '@/data/types';

export function RiskBadge({
  level,
  score,
  size = 'sm',
}: {
  level: RiskLevel;
  score?: number;
  size?: 'sm' | 'md';
}) {
  const meta = RISK_META[level];
  const pad = size === 'md' ? 'px-3 py-1 text-sm' : 'px-2.5 py-0.5 text-xs';
  return (
    <span
      className={`badge ${meta.bg} ${meta.text} ${pad}`}
      aria-label={`${meta.label}${score !== undefined ? ` — ${score}/100` : ''}`}
    >
      <span className={`h-2 w-2 rounded-full ${meta.dot}`} aria-hidden="true" />
      {meta.label}
      {score !== undefined && <span className="opacity-75">— {score}/100</span>}
    </span>
  );
}

export function SafetyScoreBadge({ score, size = 'md' }: { score: number; size?: 'sm' | 'md' }) {
  const level: RiskLevel = score >= 85 ? 'low' : score >= 65 ? 'moderate' : score >= 45 ? 'high' : 'veryhigh';
  const meta = RISK_META[level];
  const pad = size === 'md' ? 'px-3 py-1 text-sm' : 'px-2.5 py-0.5 text-xs';
  const label = score >= 85 ? 'Low Risk' : score >= 65 ? 'Moderate' : score >= 45 ? 'High Risk' : 'Very High';
  return (
    <span className={`badge ${meta.bg} ${meta.text} ${pad}`} aria-label={`Safety score ${score} of 100, ${label}`}>
      <span className={`h-2 w-2 rounded-full ${meta.dot}`} aria-hidden="true" />
      {label} — {score}/100
    </span>
  );
}

export function StatusDot({ level }: { level: RiskLevel }) {
  const meta = RISK_META[level];
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`h-2 w-2 rounded-full ${meta.dot}`} aria-hidden="true" />
      <span className={meta.text}>{meta.label}</span>
    </span>
  );
}

export function Card({
  children,
  className = '',
  hover = false,
  as: Tag = 'div',
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  as?: 'div' | 'section' | 'article';
}) {
  const hoverCls = hover ? 'card-hover' : '';
  return <Tag className={`card ${hoverCls} ${className}`}>{children}</Tag>;
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="mt-1.5 text-sm text-ink-soft">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function SectionCard({
  title,
  action,
  children,
  className = '',
}: {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`card p-5 ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between gap-3">
          {title && <h2 className="section-title">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center rounded-[8px] border border-dashed border-border py-12 text-sm text-ink-soft">
      {message}
    </div>
  );
}

export function SourceBadge({ source }: { source: string }) {
  const styles: Record<string, string> = {
    Verified: 'bg-safe-light text-safe-dark',
    Community: 'bg-accent-50 text-accent-700',
    News: 'bg-moderate-light text-moderate-dark',
    'AI Signal': 'bg-navy-50 text-navy-600',
  };
  return <span className={`badge ${styles[source] ?? 'bg-canvas-subtle text-ink-soft'}`}>{source}</span>;
}
