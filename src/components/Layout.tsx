import { type ReactNode, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Map,
  Route,
  Navigation,
  ShieldPlus,
  TriangleAlert,
  Users,
  Siren,
  Settings,
  HelpCircle,
  Bell,
  MapPin,
  User as UserIcon,
  Menu,
  X,
  ShieldCheck,
} from 'lucide-react';
import { useApp } from '@/context/AppContext';
import DemoModeControl from './DemoModeControl';
import Toaster from './Toaster';

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/safety-map', label: 'Safety Map', icon: Map },
  { to: '/safe-route', label: 'Safe Route', icon: Route },
  { to: '/journey', label: 'Journey', icon: Navigation },
  { to: '/safe-havens', label: 'Safe Havens', icon: ShieldPlus },
  { to: '/incidents', label: 'Incidents', icon: TriangleAlert },
  { to: '/community', label: 'Community', icon: Users },
  { to: '/emergency', label: 'Emergency', icon: Siren, danger: true },
];

const SECONDARY = [
  { to: '/settings', label: 'Settings', icon: Settings },
];

function NavItem({
  to,
  label,
  icon: Icon,
  end,
  danger,
  onClick,
}: {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
  danger?: boolean;
  onClick?: () => void;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onClick}
      className={({ isActive }) =>
        `group relative flex items-center gap-3 rounded-[8px] px-3 py-2.5 text-sm font-medium transition-colors ${
          isActive
            ? 'bg-accent-50 text-navy'
            : danger
              ? 'text-danger hover:bg-danger-light/60'
              : 'text-ink-soft hover:bg-canvas-subtle hover:text-navy'
        }`
      }
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <span
              className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-accent"
              aria-hidden="true"
            />
          )}
          <Icon
            className={`h-[18px] w-[18px] flex-none ${danger ? 'text-danger' : ''}`}
            aria-hidden="true"
          />
          <span>{label}</span>
        </>
      )}
    </NavLink>
  );
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 px-4 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-[8px] bg-navy text-white">
          <ShieldCheck className="h-5 w-5" aria-hidden="true" />
        </div>
        <div className="leading-tight">
          <div className="text-base font-semibold text-navy">SafeHer</div>
          <div className="text-[11px] text-ink-soft">Women's Safety Intelligence</div>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 px-2 py-2" aria-label="Primary">
        {NAV.map((n) => (
          <NavItem key={n.to} {...n} onClick={onNavigate} />
        ))}
      </nav>

      <div className="my-2 mx-3 border-t border-border" />
      <div className="px-2 pb-2 space-y-0.5">
        {SECONDARY.map((n) => (
          <NavItem key={n.to} {...n} onClick={onNavigate} />
        ))}
        <a
          href="#help"
          onClick={(e) => e.preventDefault()}
          className="flex items-center gap-3 rounded-[8px] px-3 py-2.5 text-sm font-medium text-ink-soft transition-colors hover:bg-canvas-subtle hover:text-navy"
        >
          <HelpCircle className="h-[18px] w-[18px]" aria-hidden="true" />
          Help
        </a>
      </div>
    </div>
  );
}

function ConnectivityIndicator() {
  const { online } = useApp();
  return (
    <span
      className={`hidden items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium sm:inline-flex ${
        online ? 'bg-safe-light text-safe-dark' : 'bg-danger-light text-danger-dark'
      }`}
      aria-label={online ? 'Internet connected' : 'Internet unavailable'}
    >
      <span className={`h-2 w-2 rounded-full ${online ? 'bg-safe' : 'bg-danger'}`} aria-hidden="true" />
      {online ? 'Connected' : 'Offline'}
    </span>
  );
}

function MobileNav() {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-30 border-t border-border bg-canvas/95 backdrop-blur md:hidden"
      aria-label="Mobile primary"
    >
      <div className="grid grid-cols-5">
        {NAV.slice(0, 4).map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.end}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 py-2.5 text-[10px] font-medium ${
                isActive ? 'text-accent' : 'text-ink-soft'
              }`
            }
          >
            <n.icon className="h-5 w-5" aria-hidden="true" />
            {n.label}
          </NavLink>
        ))}
        <NavLink
          to="/emergency"
          className={({ isActive }) =>
            `flex flex-col items-center gap-0.5 py-2.5 text-[10px] font-medium ${
              isActive ? 'text-danger' : 'text-danger'
            }`
          }
        >
          <Siren className="h-5 w-5" aria-hidden="true" />
          SOS
        </NavLink>
      </div>
    </nav>
  );
}

export default function Layout({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const { sosActive } = useApp();

  return (
    <div className="min-h-screen bg-canvas-subtle">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 border-r border-border bg-canvas md:block">
        <Sidebar />
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-modal="true" aria-label="Menu">
          <div
            className="absolute inset-0 bg-navy-900/40 animate-fade-in"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 w-72 max-w-[85%] bg-canvas shadow-popover animate-slide-in-right">
            <button
              type="button"
              onClick={() => setMobileOpen(false)}
              className="absolute right-2 top-3 rounded p-1.5 text-ink-soft hover:bg-canvas-subtle hover:text-navy"
              aria-label="Close menu"
            >
              <X className="h-5 w-5" />
            </button>
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </div>
        </div>
      )}

      <div className="md:pl-60">
        {/* Top header */}
        <header className="sticky top-0 z-20 border-b border-border bg-canvas/95 backdrop-blur">
          <div className="flex h-14 items-center gap-3 px-4 sm:px-6">
            <button
              type="button"
              className="rounded-[8px] p-2 text-navy hover:bg-canvas-subtle md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-2 md:hidden">
              <div className="flex h-7 w-7 items-center justify-center rounded-[6px] bg-navy text-white">
                <ShieldCheck className="h-4 w-4" aria-hidden="true" />
              </div>
              <span className="text-sm font-semibold text-navy">SafeHer</span>
            </div>

            <div className="hidden flex-1 items-center gap-2 md:flex">
              <span className="inline-flex items-center gap-1.5 text-sm text-ink-soft">
                <MapPin className="h-4 w-4 text-accent" aria-hidden="true" />
                Hitech City, Hyderabad
              </span>
            </div>

            <div className="ml-auto flex items-center gap-2 sm:gap-3">
              <ConnectivityIndicator />
              <DemoModeControl />
              <button
                type="button"
                className="relative rounded-[8px] p-2 text-ink-soft transition-colors hover:bg-canvas-subtle hover:text-navy"
                aria-label="Notifications"
              >
                <Bell className="h-[18px] w-[18px]" />
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-danger" aria-hidden="true" />
              </button>
              <div className="hidden h-8 w-8 items-center justify-center rounded-full bg-navy-50 text-xs font-semibold text-navy sm:flex">
                <UserIcon className="h-4 w-4" aria-hidden="true" />
              </div>
              <NavLink
                to="/emergency"
                className={`btn !px-3 !py-1.5 !text-xs sm:!px-4 ${
                  sosActive ? 'btn-danger animate-sos-pulse' : 'btn-danger'
                }`}
                aria-label={sosActive ? 'SOS active — emergency center' : 'Open emergency center'}
              >
                <Siren className="h-4 w-4" />
                {sosActive ? 'SOS ACTIVE' : 'SOS'}
              </NavLink>
            </div>
          </div>
        </header>

        <main key={location.pathname} className="mx-auto w-full max-w-6xl px-4 pb-24 pt-6 sm:px-6 md:pb-10 animate-fade-in">
          {children}
        </main>
      </div>

      <MobileNav />
      <Toaster />
    </div>
  );
}
