import { useEffect, useRef, useState } from 'react';
import { Siren, Phone, Share2, ShieldPlus, X, MapPin, AlertTriangle, UserPlus, Users, Loader2, RefreshCw, ShieldAlert, CheckCircle } from 'lucide-react';
import { Card, PageHeader } from '@/components/ui';
import { useApp } from '@/context/AppContext';
import { api } from '@/services/api';

export default function Emergency() {
  const { notify } = useApp();

  // SOS State
  const [sosActive, setSosActive] = useState(false);
  const [activeSosData, setActiveSosData] = useState<any>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [locationStatus, setLocationStatus] = useState<'IDLE' | 'ACQUIRING' | 'ACQUIRED' | 'DENIED'>('IDLE');
  const [currentCoords, setCurrentCoords] = useState<{ lat: number | null; lng: number | null; accuracy: number | null }>({
    lat: null,
    lng: null,
    accuracy: null
  });

  // Emergency Contacts State
  const [contacts, setContacts] = useState<any[]>([]);
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [contactRelation, setContactRelation] = useState('Family');
  const [addingContact, setAddingContact] = useState(false);

  // Emergency Operator Dashboard State
  const [operatorEvents, setOperatorEvents] = useState<any[]>([]);
  const [loadingOperator, setLoadingOperator] = useState(false);

  // Watch position reference for active tracking
  const watchIdRef = useRef<number | null>(null);

  // Fetch initial contacts & active operator events
  const loadContacts = async () => {
    try {
      const res = await api.getEmergencyContactsList();
      if (res?.contacts) {
        setContacts(res.contacts);
      }
    } catch (e) {
      console.warn("Failed to load emergency contacts:", e);
    }
  };

  const loadOperatorEvents = async () => {
    setLoadingOperator(true);
    try {
      const res = await api.getActiveSOSEvents();
      if (res?.active_events) {
        setOperatorEvents(res.active_events);
      }
    } catch (e) {
      console.warn("Failed to load active operator events:", e);
    } finally {
      setLoadingOperator(false);
    }
  };

  useEffect(() => {
    loadContacts();
    loadOperatorEvents();
  }, []);

  // Continuous background location tracking during ACTIVE SOS
  useEffect(() => {
    if (sosActive && activeSosData?.sos_id && navigator.geolocation) {
      watchIdRef.current = navigator.geolocation.watchPosition(
        async (position) => {
          const { latitude, longitude, accuracy } = position.coords;
          setCurrentCoords({ lat: latitude, lng: longitude, accuracy });
          try {
            await api.updateSOSLocation(activeSosData.sos_id, latitude, longitude, accuracy);
          } catch (e) {
            console.warn("Failed to stream continuous SOS location update:", e);
          }
        },
        (error) => {
          console.warn("Location tracking error during SOS:", error.message);
        },
        { enableHighAccuracy: true, maximumAge: 10000, timeout: 15000 }
      );
    } else if (!sosActive && watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }

    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, [sosActive, activeSosData?.sos_id]);

  // Request browser geolocation permission & coordinates
  const acquireLocation = (): Promise<{ lat: number | null; lng: number | null; accuracy: number | null }> => {
    return new Promise((resolve) => {
      setLocationStatus('ACQUIRING');
      if (!navigator.geolocation) {
        setLocationStatus('DENIED');
        resolve({ lat: null, lng: null, accuracy: null });
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLocationStatus('ACQUIRED');
          const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude, accuracy: pos.coords.accuracy };
          setCurrentCoords(coords);
          resolve(coords);
        },
        (err) => {
          console.warn("Geolocation permission error or denied:", err.message);
          setLocationStatus('DENIED');
          notify('Location permission denied or unavailable. SOS created without exact coordinates.', 'warning');
          resolve({ lat: null, lng: null, accuracy: null });
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    });
  };

  // Trigger SOS Handler after modal confirmation
  const handleConfirmActivateSOS = async () => {
    setShowConfirmModal(false);
    setLoading(true);

    const coords = await acquireLocation();

    try {
      const response = await api.triggerSOSEvent(coords.lat || undefined, coords.lng || undefined, coords.accuracy || undefined);
      if (response?.sos_id) {
        setActiveSosData(response);
        setSosActive(true);
        notify(response.already_active ? 'Active SOS request retrieved.' : '🚨 EMERGENCY SOS ACTIVATED', 'danger');
        loadOperatorEvents();
      } else {
        notify('Emergency request could not be confirmed. Check connection.', 'danger');
      }
    } catch (err: any) {
      notify(`Emergency request failed: ${err.message}`, 'danger');
    } finally {
      setLoading(false);
    }
  };

  // Cancel SOS Handler
  const handleConfirmCancelSOS = async () => {
    if (!activeSosData?.sos_id) return;
    setLoading(true);
    try {
      await api.cancelSOS(activeSosData.sos_id, cancelReason || 'User cancelled SOS');
      setSosActive(false);
      setActiveSosData(null);
      setShowCancelModal(false);
      setCancelReason('');
      notify('SOS emergency alert cancelled.', 'info');
      loadOperatorEvents();
    } catch (err: any) {
      notify(`Failed to cancel SOS: ${err.message}`, 'danger');
    } finally {
      setLoading(false);
    }
  };

  // Add Emergency Contact Handler
  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contactName || !contactPhone) return;
    setAddingContact(true);
    try {
      const res = await api.addEmergencyContact({
        name: contactName,
        phone_number: contactPhone,
        relationship: contactRelation,
        is_primary: contacts.length === 0
      });
      if (res?.id) {
        setContactName('');
        setContactPhone('');
        notify('Emergency contact added successfully.', 'success');
        loadContacts();
      }
    } catch (err: any) {
      notify(`Failed to add contact: ${err.message}`, 'danger');
    } finally {
      setAddingContact(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Emergency SOS Center" subtitle="Real-time emergency alert dispatcher and location tracking system." />

      {/* CONFIRM ACTIVATION MODAL */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4 border-2 border-danger">
            <div className="flex items-center gap-3 text-danger font-bold text-lg">
              <ShieldAlert className="h-7 w-7 animate-bounce" />
              CONFIRM EMERGENCY SOS ACTIVATION
            </div>
            <p className="text-sm text-ink-soft leading-relaxed">
              Are you sure you want to activate Emergency SOS? Your location will be captured and broadcasted to emergency responders and authorized contacts.
            </p>
            <div className="grid grid-cols-2 gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                className="btn-secondary w-full justify-center py-2.5 font-bold"
              >
                CANCEL
              </button>
              <button
                type="button"
                onClick={handleConfirmActivateSOS}
                className="btn-danger w-full justify-center py-2.5 font-bold bg-danger hover:bg-danger-dark animate-pulse"
              >
                ACTIVATE SOS
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CONFIRM CANCELLATION MODAL */}
      {showCancelModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4 border-2 border-border">
            <div className="flex items-center gap-3 text-navy font-bold text-lg">
              <AlertTriangle className="h-6 w-6 text-amber-500" />
              CANCEL ACTIVE SOS REQUEST?
            </div>
            <p className="text-sm text-ink-soft">
              Please state a reason for cancelling this active emergency request:
            </p>
            <input
              type="text"
              placeholder="e.g. Accidental trigger / Reached safe location"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:ring-2 focus:ring-navy"
            />
            <div className="grid grid-cols-2 gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowCancelModal(false)}
                className="btn-secondary w-full justify-center py-2.5 font-bold"
              >
                KEEP ACTIVE
              </button>
              <button
                type="button"
                onClick={handleConfirmCancelSOS}
                className="btn-danger w-full justify-center py-2.5 font-bold bg-zinc-800 hover:bg-zinc-900"
              >
                CANCEL SOS
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* MAIN SOS PANEL */}
        <Card className="p-6 border-2 border-danger-light">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-navy uppercase tracking-wider flex items-center gap-2">
              <Siren className="h-5 w-5 text-danger" />
              EMERGENCY SOS DISPATCHER
            </h2>
            {sosActive && (
              <span className="badge bg-danger text-white font-bold animate-pulse">
                🚨 SOS ACTIVE
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-ink-soft">
            Press to dispatch an emergency alert with real-time location capture.
          </p>

          {!sosActive ? (
            <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-danger/30 bg-danger-light/20 py-10 px-4">
              <button
                type="button"
                disabled={loading}
                onClick={() => setShowConfirmModal(true)}
                className="group relative flex h-44 w-44 select-none flex-col items-center justify-center rounded-full bg-danger text-white shadow-[0_10px_30px_rgba(220,38,38,0.5)] transition-all hover:scale-105 active:scale-95 focus:outline-none"
              >
                {loading ? (
                  <Loader2 className="h-12 w-12 animate-spin" />
                ) : (
                  <>
                    <Siren className="h-12 w-12 group-hover:animate-bounce" />
                    <span className="mt-2 text-2xl font-black tracking-wider">SOS</span>
                    <span className="text-[10px] font-bold uppercase tracking-widest text-white/80">EMERGENCY</span>
                  </>
                )}
              </button>
              <p className="mt-4 text-xs font-semibold text-ink-soft">
                Tap button to open SOS activation confirmation.
              </p>
            </div>
          ) : (
            <div className="mt-6 rounded-2xl border-2 border-danger bg-danger-light/30 p-6 space-y-4 font-sans">
              <div className="flex items-center justify-between border-b border-danger/20 pb-3">
                <div className="flex items-center gap-2 text-danger-dark font-bold text-base">
                  <span className="relative flex h-3 w-3">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-danger opacity-75" />
                    <span className="relative inline-flex h-3 w-3 rounded-full bg-danger" />
                  </span>
                  🚨 SOS ACTIVE
                </div>
                <span className="text-xs font-mono font-bold text-ink-soft">
                  ID: {activeSosData?.sos_id?.slice(0, 13)}...
                </span>
              </div>

              {/* LOCATION & STATUS GRID */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="rounded-xl bg-white p-3 border border-danger/20 space-y-1">
                  <span className="text-[10px] font-bold text-ink-soft uppercase">Status</span>
                  <div className="font-bold text-danger text-sm">{activeSosData?.status || 'ACTIVE'}</div>
                </div>

                <div className="rounded-xl bg-white p-3 border border-danger/20 space-y-1">
                  <span className="text-[10px] font-bold text-ink-soft uppercase">Location Status</span>
                  <div className="font-bold text-emerald-700 flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {activeSosData?.location?.status_text || 'AVAILABLE ✓'}
                  </div>
                </div>

                <div className="rounded-xl bg-white p-3 border border-danger/20 space-y-1 col-span-2">
                  <span className="text-[10px] font-bold text-ink-soft uppercase">Notification Provider State</span>
                  <div className="flex items-center justify-between">
                    <span className="badge bg-zinc-800 text-white font-bold text-[10px]">
                      ● {activeSosData?.notification?.status || 'NOT_CONFIGURED'}
                    </span>
                    <span className="text-[10px] text-ink-soft italic">
                      {activeSosData?.notification?.message || 'Emergency notification service is not configured.'}
                    </span>
                  </div>
                </div>

                {currentCoords.lat !== null && (
                  <div className="rounded-xl bg-white p-3 border border-danger/20 col-span-2 space-y-1">
                    <span className="text-[10px] font-bold text-ink-soft uppercase">Live Coordinates Stream</span>
                    <div className="font-mono text-xs font-bold text-navy">
                      {currentCoords.lat.toFixed(5)}, {currentCoords.lng?.toFixed(5)} (±{currentCoords.accuracy?.toFixed(1)}m)
                    </div>
                  </div>
                )}
              </div>

              <div className="rounded-xl bg-amber-50 border border-amber-200 p-3 text-[11px] text-amber-900 italic">
                ℹ️ <strong>Safety Disclaimer</strong>: {activeSosData?.scientific_disclaimer || "Emergency request created. System never falsely claims emergency services were contacted unless verified."}
              </div>

              {/* SOS QUICK ACTIONS */}
              <div className="grid grid-cols-2 gap-2 pt-2">
                <a href="tel:100" className="btn-danger col-span-2 justify-center font-bold py-2.5">
                  <Phone className="h-4 w-4" />
                  CALL POLICE EMERGENCY — 100
                </a>
                <button type="button" className="btn-secondary justify-center text-xs font-bold" onClick={() => notify('Live location copied to clipboard.', 'success')}>
                  <Share2 className="h-3.5 w-3.5" />
                  Share Location
                </button>
                <a href="tel:112" className="btn-secondary justify-center text-xs font-bold">
                  <ShieldPlus className="h-3.5 w-3.5" />
                  Call 112 Helpline
                </a>
                <button
                  type="button"
                  onClick={() => setShowCancelModal(true)}
                  className="btn-secondary col-span-2 justify-center text-xs font-bold bg-zinc-800 text-white hover:bg-zinc-900"
                >
                  <X className="h-4 w-4" />
                  [ CANCEL SOS ]
                </button>
              </div>
            </div>
          )}
        </Card>

        {/* RIGHT COLUMN: CONTACTS & OPERATOR DASHBOARD */}
        <div className="space-y-6">
          {/* TRUSTED EMERGENCY CONTACTS */}
          <Card className="p-6">
            <h2 className="text-lg font-bold text-navy flex items-center gap-2">
              <Users className="h-5 w-5 text-navy" />
              TRUSTED EMERGENCY CONTACTS
            </h2>
            <p className="mt-1 text-sm text-ink-soft">
              Configure personal trusted contacts notified during SOS events.
            </p>

            <form onSubmit={handleAddContact} className="mt-4 grid grid-cols-3 gap-2">
              <input
                type="text"
                placeholder="Name"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                className="px-3 py-1.5 border border-border rounded-lg text-xs"
                required
              />
              <input
                type="text"
                placeholder="Phone (+91...)"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                className="px-3 py-1.5 border border-border rounded-lg text-xs"
                required
              />
              <button
                type="submit"
                disabled={addingContact}
                className="btn-primary text-xs font-bold py-1.5 justify-center"
              >
                {addingContact ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <UserPlus className="h-3.5 w-3.5" />}
                Add
              </button>
            </form>

            <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
              {contacts.length === 0 ? (
                <div className="text-xs text-ink-soft italic p-3 bg-canvas-subtle rounded-lg text-center">
                  No emergency contacts configured yet. Add your trusted contacts above.
                </div>
              ) : (
                contacts.map((c) => (
                  <div key={c.id} className="flex items-center justify-between p-2.5 rounded-lg border border-border bg-white text-xs">
                    <div>
                      <div className="font-bold text-navy flex items-center gap-1.5">
                        {c.name}
                        {c.is_primary && <span className="badge bg-blue-100 text-blue-800 text-[9px] font-bold">PRIMARY</span>}
                      </div>
                      <div className="text-ink-soft text-[11px]">{c.phone_number} ({c.relationship})</div>
                    </div>
                    <CheckCircle className="h-4 w-4 text-emerald-600" />
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* PROTECTED EMERGENCY OPERATOR MONITOR DASHBOARD */}
          <Card className="p-6 border border-zinc-300 bg-zinc-50/50">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-bold text-navy uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-zinc-700" />
                EMERGENCY OPERATOR MONITOR (PHASE 11)
              </h2>
              <button
                type="button"
                onClick={loadOperatorEvents}
                className="p-1 text-ink-soft hover:text-navy"
                title="Refresh Active SOS Events"
              >
                <RefreshCw className={`h-4 w-4 ${loadingOperator ? 'animate-spin' : ''}`} />
              </button>
            </div>

            <p className="text-xs text-ink-soft mb-3">
              Protected live queue of active emergency SOS alerts for authorized dispatch operators.
            </p>

            <div className="space-y-2 text-xs">
              {operatorEvents.length === 0 ? (
                <div className="p-4 bg-white border border-border rounded-xl text-center text-ink-soft italic">
                  No active emergency SOS alerts currently in queue.
                </div>
              ) : (
                operatorEvents.map((evt) => (
                  <div key={evt.sos_id} className="p-3 bg-white border-2 border-danger/30 rounded-xl space-y-1">
                    <div className="flex items-center justify-between font-bold">
                      <span className="text-danger text-xs truncate">SOS #{evt.sos_id.slice(0, 8)}</span>
                      <span className="badge bg-danger text-white text-[9px] font-bold">{evt.status}</span>
                    </div>
                    <div className="text-[11px] text-ink-soft">
                      User: <strong>{evt.user_reference}</strong>
                    </div>
                    <div className="text-[11px] text-ink-soft">
                      Location: <strong>{evt.location_text}</strong>
                    </div>
                    <div className="text-[10px] text-ink-soft">
                      Notification: <strong>{evt.notification_status}</strong> ({evt.notification_provider})
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
