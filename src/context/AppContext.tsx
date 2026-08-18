import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { getDemoScenario, setDemoScenario as setApiScenario } from '@/services/api';
import type { DemoScenario } from '@/data/types';

interface AppContextValue {
  scenario: DemoScenario;
  setScenario: (s: DemoScenario) => void;
  online: boolean;
  setOnline: (v: boolean) => void;
  sosActive: boolean;
  setSosActive: (v: boolean) => void;
  journeyActive: boolean;
  setJourneyActive: (v: boolean) => void;
  notify: (msg: string, kind?: 'info' | 'success' | 'warning' | 'danger') => void;
  toasts: Toast[];
  dismissToast: (id: string) => void;
}

interface Toast {
  id: string;
  msg: string;
  kind: 'info' | 'success' | 'warning' | 'danger';
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [scenario, setScenarioState] = useState<DemoScenario>(() => getDemoScenario());
  const [online, setOnline] = useState(true);
  const [sosActive, setSosActive] = useState(false);
  const [journeyActive, setJourneyActive] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const setScenario = useCallback((s: DemoScenario) => {
    setApiScenario(s);
    setScenarioState(s);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const notify = useCallback(
    (msg: string, kind: 'info' | 'success' | 'warning' | 'danger' = 'info') => {
      const id = `t-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      setToasts((t) => [...t, { id, msg, kind }]);
      setTimeout(() => {
        setToasts((t) => t.filter((x) => x.id !== id));
      }, 4500);
    },
    []
  );

  // Scenario side-effects
  useEffect(() => {
    if (scenario === 'internet-lost') {
      setOnline(false);
      notify('Internet connection lost. Mobile emergency fallback available.', 'warning');
    } else {
      setOnline(true);
    }
    if (scenario === 'emergency-sos') {
      setSosActive(true);
    } else if (scenario === 'voice-sos') {
      setSosActive(true);
      notify('Voice SOS detected — "Code Red" recognized.', 'danger');
    }
  }, [scenario, notify]);

  const value = useMemo(
    () => ({
      scenario,
      setScenario,
      online,
      setOnline,
      sosActive,
      setSosActive,
      journeyActive,
      setJourneyActive,
      notify,
      toasts,
      dismissToast,
    }),
    [scenario, setScenario, online, sosActive, journeyActive, notify, toasts, dismissToast]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
