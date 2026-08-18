import { CheckCircle2, AlertTriangle, Info, X, XCircle } from 'lucide-react';
import { useApp } from '@/context/AppContext';

const ICONS = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: XCircle,
} as const;

const STYLES = {
  info: 'border-l-accent',
  success: 'border-l-safe',
  warning: 'border-l-moderate',
  danger: 'border-l-danger',
} as const;

const ICON_COLOR = {
  info: 'text-accent',
  success: 'text-safe',
  warning: 'text-moderate',
  danger: 'text-danger',
} as const;

export default function Toaster() {
  const { toasts, dismissToast } = useApp();
  if (!toasts.length) return null;
  return (
    <div
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((t) => {
        const Icon = ICONS[t.kind];
        return (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-[10px] border border-border border-l-4 bg-canvas p-3.5 shadow-popover animate-slide-in-right ${STYLES[t.kind]}`}
            role="status"
          >
            <Icon className={`mt-0.5 h-5 w-5 flex-none ${ICON_COLOR[t.kind]}`} aria-hidden="true" />
            <p className="flex-1 text-sm text-ink">{t.msg}</p>
            <button
              type="button"
              onClick={() => dismissToast(t.id)}
              className="rounded p-0.5 text-ink-soft transition-colors hover:bg-canvas-subtle hover:text-navy"
              aria-label="Dismiss notification"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
