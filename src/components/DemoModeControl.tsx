import { useEffect, useRef, useState } from 'react';
import { ChevronDown, FlaskConical, Check } from 'lucide-react';
import { useApp } from '@/context/AppContext';
import type { DemoScenario } from '@/data/types';

const SCENARIOS: { id: DemoScenario; label: string; hint: string }[] = [
  { id: 'normal', label: 'Normal', hint: 'Baseline safety state' },
  { id: 'high-risk-zone', label: 'High Risk Zone', hint: 'MG Road escalates to very high' },
  { id: 'new-incident', label: 'New Incident', hint: 'Fresh community report appears' },
  { id: 'safest-route-changed', label: 'Safest Route Changed', hint: 'Route recommendation updates' },
  { id: 'internet-lost', label: 'Internet Lost', hint: 'Offline emergency fallback' },
  { id: 'voice-sos', label: 'Voice SOS', hint: 'Voice phrase detected' },
  { id: 'emergency-sos', label: 'Emergency SOS', hint: 'SOS activated' },
];

export default function DemoModeControl() {
  const { scenario, setScenario, notify } = useApp();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  const current = SCENARIOS.find((s) => s.id === scenario) ?? SCENARIOS[0];

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="btn-secondary !py-1.5 !text-xs"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <FlaskConical className="h-3.5 w-3.5 text-accent" aria-hidden="true" />
        Demo: <span className="text-navy">{current.label}</span>
        <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
      </button>
      {open && (
        <div
          className="absolute right-0 z-40 mt-2 w-72 rounded-[10px] border border-border bg-canvas p-1.5 shadow-popover animate-fade-in"
          role="listbox"
        >
          <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-ink-soft">
            Demo Scenario
          </div>
          {SCENARIOS.map((s) => (
            <button
              key={s.id}
              type="button"
              role="option"
              aria-selected={scenario === s.id}
              onClick={() => {
                setScenario(s.id);
                setOpen(false);
                notify(`Demo scenario: ${s.label}`, 'info');
              }}
              className="flex w-full items-start gap-2 rounded-[8px] px-3 py-2 text-left transition-colors hover:bg-canvas-subtle"
            >
              <span
                className={`mt-0.5 flex h-4 w-4 flex-none items-center justify-center rounded-full border ${
                  scenario === s.id ? 'border-accent bg-accent text-white' : 'border-border-strong'
                }`}
                aria-hidden="true"
              >
                {scenario === s.id && <Check className="h-3 w-3" />}
              </span>
              <span className="flex flex-col">
                <span className="text-sm font-medium text-navy">{s.label}</span>
                <span className="text-xs text-ink-soft">{s.hint}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
