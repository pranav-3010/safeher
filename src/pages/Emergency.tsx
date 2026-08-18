import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Siren, Phone, Share2, ShieldPlus, X, Mic, MicOff, Wifi, WifiOff, Check, MapPin, AlertTriangle } from 'lucide-react';
import { Card, PageHeader, SectionCard } from '@/components/ui';
import { useApp } from '@/context/AppContext';
import { api } from '@/services/api';
import { user as userData } from '@/data/users';

function HoldSOSButton({ onActivate }: { onActivate: () => void }) {
  const [holding, setHolding] = useState(false);
  const [progress, setProgress] = useState(0);
  const timerRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const startRef = useRef<number>(0);
  const HOLD_MS = 2000;

  const startHold = () => {
    setHolding(true);
    startRef.current = performance.now();
    const tick = () => {
      const elapsed = performance.now() - startRef.current;
      const pct = Math.min(100, (elapsed / HOLD_MS) * 100);
      setProgress(pct);
      if (pct >= 100) {
        finish();
        return;
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    timerRef.current = window.setTimeout(finish, HOLD_MS);
  };

  const finish = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    setHolding(false);
    setProgress(100);
    if (performance.now() - startRef.current >= HOLD_MS - 50) {
      onActivate();
    }
    setTimeout(() => setProgress(0), 400);
  };

  const cancel = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    setHolding(false);
    setProgress(0);
  };

  return (
    <div className="flex flex-col items-center">
      <button
        type="button"
        onPointerDown={startHold}
        onPointerUp={cancel}
        onPointerLeave={cancel}
        onPointerCancel={cancel}
        className="relative flex h-40 w-40 select-none items-center justify-center rounded-full bg-danger text-white shadow-[0_8px_24px_-4px_rgba(185,28,28,0.45)] transition-transform active:scale-95 focus-visible:ring-danger"
        aria-label="Hold for 2 seconds to activate SOS"
      >
        {holding && (
          <span
            className="absolute inset-0 rounded-full border-4 border-white/40"
            style={{
              background: `conic-gradient(rgba(255,255,255,0.55) ${progress * 3.6}deg, transparent 0deg)`,
              mask: 'radial-gradient(farthest-side, transparent calc(100% - 8px), #000 calc(100% - 8px))',
              WebkitMask: 'radial-gradient(farthest-side, transparent calc(100% - 8px), #000 calc(100% - 8px))',
            }}
            aria-hidden="true"
          />
        )}
        <span className="flex flex-col items-center">
          <Siren className="h-10 w-10" aria-hidden="true" />
          <span className="mt-1.5 text-lg font-bold tracking-wide">SOS</span>
        </span>
      </button>
      <p className="mt-4 text-sm font-medium text-ink-soft">
        {holding ? `Hold for ${((2000 - (progress / 100) * 2000) / 1000).toFixed(1)}s…` : 'Hold for 2 seconds'}
      </p>
    </div>
  );
}

function Checklist({ items, done }: { items: string[]; done: boolean }) {
  return (
    <ul className="space-y-2.5">
      {items.map((item) => (
        <li key={item} className="flex items-center gap-2.5 text-sm">
          <span
            className={`flex h-5 w-5 flex-none items-center justify-center rounded-full ${
              done ? 'bg-safe text-white' : 'bg-canvas-subtle text-ink-soft'
            }`}
            aria-hidden="true"
          >
            {done && <Check className="h-3 w-3" />}
          </span>
          <span className={done ? 'text-ink' : 'text-ink-soft'}>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default function Emergency() {
  const { sosActive, setSosActive, online, setOnline, scenario, setScenario, notify } = useApp();
  const [listening, setListening] = useState(false);
  const [voiceDetected, setVoiceDetected] = useState(false);

  useEffect(() => {
    if (scenario === 'voice-sos') {
      setVoiceDetected(true);
      setSosActive(true);
    }
  }, [scenario, setSosActive]);

  const activate = async () => {
    notify('SOS activated. Emergency contacts are being notified.', 'danger');
    await api.triggerSOS();
    setSosActive(true);
  };

  const cancelSos = () => {
    setSosActive(false);
    setVoiceDetected(false);
    setScenario('normal');
    notify('SOS cancelled.', 'info');
  };

  const toggleListen = () => {
    if (listening) {
      setListening(false);
      return;
    }
    setListening(true);
    notify('Voice SOS listening for "Code Red".', 'info');
    setTimeout(() => {
      setListening(false);
      setVoiceDetected(true);
      setSosActive(true);
      notify('Voice SOS detected — "Code Red" recognized.', 'danger');
    }, 2500);
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Emergency Center" subtitle="Quick access to emergency assistance." />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* SOS panel */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-navy">Emergency Assistance</h2>
          <p className="mt-1 text-sm text-ink-soft">
            If you feel unsafe, activate SOS. Your location and emergency contacts will be notified immediately.
          </p>

          {!sosActive ? (
            <div className="mt-6 flex flex-col items-center rounded-[10px] border border-border bg-canvas-subtle/60 py-8">
              <HoldSOSButton onActivate={activate} />
            </div>
          ) : (
            <div className="mt-6 rounded-[10px] border-2 border-danger/30 bg-danger-light/40 p-6">
              <div className="flex items-center gap-2.5">
                <span className="relative flex h-3 w-3">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-danger opacity-75" />
                  <span className="relative inline-flex h-3 w-3 rounded-full bg-danger" />
                </span>
                <h3 className="text-base font-bold uppercase tracking-wide text-danger-dark">SOS Activated</h3>
              </div>
              <div className="mt-4">
                <Checklist
                  items={[
                    'Location acquired',
                    'Emergency contacts notified',
                    'Nearby help identified',
                  ]}
                  done={true}
                />
              </div>
              <div className="mt-4 rounded-[8px] bg-canvas p-3 text-xs text-ink-soft">
                <span className="flex items-center gap-1.5 font-medium text-navy">
                  <MapPin className="h-3.5 w-3.5 text-accent" />
                  Live location
                </span>
                <span className="mt-1 block font-mono">
                  {userData.currentLocation.lat.toFixed(4)}, {userData.currentLocation.lng.toFixed(4)}
                </span>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2">
                <a href="tel:100" className="btn-danger col-span-2">
                  <Phone className="h-4 w-4" />
                  Call Police — 100
                </a>
                <button type="button" className="btn-secondary" onClick={() => notify('Location link copied to clipboard.', 'success')}>
                  <Share2 className="h-4 w-4" />
                  Share Location
                </button>
                <Link to="/safe-havens" className="btn-secondary">
                  <ShieldPlus className="h-4 w-4" />
                  Safe Havens
                </Link>
                <button type="button" onClick={cancelSos} className="btn-ghost col-span-2">
                  <X className="h-4 w-4" />
                  Cancel SOS
                </button>
              </div>
            </div>
          )}
        </Card>

        <div className="space-y-6">
          {/* Voice SOS */}
          <Card className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-navy">Voice SOS</h2>
                <p className="mt-1 text-sm text-ink-soft">Speak your emergency phrase to trigger SOS hands-free.</p>
              </div>
              <span className="badge bg-safe-light text-safe-dark">
                <span className="h-2 w-2 rounded-full bg-safe" />
                Enabled
              </span>
            </div>
            <div className="mt-4 rounded-[8px] border border-border bg-canvas-subtle/60 p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-ink-soft">Emergency phrase</span>
                <span className="rounded-[6px] bg-navy px-2.5 py-0.5 font-mono text-sm font-semibold text-white">"{userData.voicePhrase}"</span>
              </div>
              <div className="mt-3 flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm text-ink-soft">
                  Microphone
                  <span className={`badge ${listening ? 'bg-danger-light text-danger-dark' : 'bg-canvas-subtle text-ink-soft'}`}>
                    <span className={`h-2 w-2 rounded-full ${listening ? 'bg-danger animate-pulse' : 'bg-ink-soft'}`} />
                    {listening ? 'Listening' : 'Off'}
                  </span>
                </span>
                <button type="button" onClick={toggleListen} className={listening ? 'btn-danger !py-1.5 !text-xs' : 'btn-secondary !py-1.5 !text-xs'}>
                  {listening ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
                  {listening ? 'Stop' : 'Start listening'}
                </button>
              </div>
            </div>
            {voiceDetected && (
              <div className="mt-3 rounded-[8px] border border-danger/30 bg-danger-light/50 p-3 animate-fade-in">
                <p className="flex items-center gap-2 text-sm font-semibold text-danger-dark">
                  <AlertTriangle className="h-4 w-4" />
                  Voice SOS Detected
                </p>
                <p className="mt-1 text-xs text-ink">Emergency procedure started.</p>
              </div>
            )}
            <p className="mt-3 text-xs text-ink-soft">
              Uses on-device speech recognition. Enable microphone permission to activate live detection.
            </p>
          </Card>

          {/* Offline connectivity */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold text-navy">Emergency Connectivity</h2>
            <div className="mt-3 flex items-center justify-between rounded-[8px] border border-border p-3">
              <span className="flex items-center gap-2 text-sm text-ink">
                {online ? <Wifi className="h-4 w-4 text-safe-dark" /> : <WifiOff className="h-4 w-4 text-danger-dark" />}
                Internet
              </span>
              <span className={`badge ${online ? 'bg-safe-light text-safe-dark' : 'bg-danger-light text-danger-dark'}`}>
                <span className={`h-2 w-2 rounded-full ${online ? 'bg-safe' : 'bg-danger'}`} />
                {online ? 'Connected' : 'Unavailable'}
              </span>
            </div>

            {!online && (
              <div className="mt-3 rounded-[8px] border border-moderate/30 bg-moderate-light/40 p-3 text-sm text-moderate-dark">
                Mobile emergency fallback available.
              </div>
            )}

            <p className="mt-3 text-xs leading-relaxed text-ink-soft">
              On supported mobile implementations, emergency alerts can fall back to cellular SMS when internet connectivity is unavailable. A standard web browser cannot silently send SMS without appropriate permissions or integration.
            </p>

            <div className="mt-4 rounded-[8px] bg-navy p-4 font-mono text-xs leading-relaxed text-white">
              <div className="text-white/60">SOS ALERT</div>
              <div className="mt-1">Possible emergency.</div>
              <div className="mt-2 text-white/60">Location:</div>
              <div>{userData.currentLocation.lat.toFixed(4)}, {userData.currentLocation.lng.toFixed(4)}</div>
              <div className="mt-2 break-all text-accent-300">
                maps.google.com/?q={userData.currentLocation.lat.toFixed(4)},{userData.currentLocation.lng.toFixed(4)}
              </div>
            </div>

            <button
              type="button"
              className="btn-ghost mt-3 w-full !text-xs"
              onClick={() => {
                setOnline(!online);
                notify(online ? 'Simulating offline mode.' : 'Back online.', online ? 'warning' : 'success');
              }}
            >
              Simulate {online ? 'offline' : 'online'} (demo)
            </button>
          </Card>
        </div>
      </div>
    </div>
  );
}
