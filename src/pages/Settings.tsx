import { useState } from 'react';
import { Phone, User, Plus, Trash2, Mic, Save, Route as RouteIcon, Lightbulb, ShieldPlus, Users, Building2, Star } from 'lucide-react';
import { Card, PageHeader, SectionCard } from '@/components/ui';
import { useApp } from '@/context/AppContext';
import { currentUser } from '@/services/api';
import type { EmergencyContact } from '@/data/types';

const ROUTE_PREFS: { id: 'Safest' | 'Balanced' | 'Fastest'; label: string; desc: string }[] = [
  { id: 'Safest', label: 'Safest', desc: 'Prioritizes safety score above all' },
  { id: 'Balanced', label: 'Balanced', desc: 'Weighs safety and time equally' },
  { id: 'Fastest', label: 'Fastest', desc: 'Minimizes travel time' },
];

const RISK_PRIORITIES = [
  { id: 'lighting', label: 'Lighting', icon: Lightbulb },
  { id: 'policeProximity', label: 'Police proximity', icon: ShieldPlus },
  { id: 'crowdActivity', label: 'Crowd activity', icon: Users },
  { id: 'safeHavens', label: 'Safe havens nearby', icon: Building2 },
  { id: 'communityRatings', label: 'Community ratings', icon: Star },
] as const;

function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-6 w-11 flex-none rounded-full transition-colors ${checked ? 'bg-accent' : 'bg-border-strong'}`}
    >
      <span
        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-[22px]' : 'translate-x-0.5'}`}
      />
    </button>
  );
}

export default function Settings() {
  const { notify } = useApp();
  const [contacts, setContacts] = useState<EmergencyContact[]>(currentUser.contacts);
  const [voiceEnabled, setVoiceEnabled] = useState(currentUser.voiceSosEnabled);
  const [voicePhrase, setVoicePhrase] = useState(currentUser.voicePhrase);
  const [routePref, setRoutePref] = useState(currentUser.routePreference);
  const [priorities, setPriorities] = useState(currentUser.riskPriorities);

  const addContact = () => {
    setContacts((c) => [...c, { id: `c-${Date.now()}`, label: 'Contact', name: '', phone: '' }]);
  };
  const removeContact = (id: string) => setContacts((c) => c.filter((x) => x.id !== id));
  const updateContact = (id: string, field: keyof EmergencyContact, value: string) =>
    setContacts((c) => c.map((x) => (x.id === id ? { ...x, [field]: value } : x)));

  const save = () => {
    currentUser.contacts = contacts;
    currentUser.voiceSosEnabled = voiceEnabled;
    currentUser.voicePhrase = voicePhrase;
    currentUser.routePreference = routePref;
    currentUser.riskPriorities = priorities;
    notify('Safety preferences saved.', 'success');
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Safety preferences and emergency contacts."
        actions={
          <button type="button" className="btn-primary" onClick={save}>
            <Save className="h-4 w-4" />
            Save Changes
          </button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Emergency contacts */}
        <SectionCard
          title="Emergency Contacts"
          action={
            <button type="button" onClick={addContact} className="btn-ghost !py-1.5 !text-xs">
              <Plus className="h-3.5 w-3.5" />
              Add
            </button>
          }
        >
          <div className="space-y-3">
            {contacts.map((c) => (
              <div key={c.id} className="rounded-[8px] border border-border p-3">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-ink-soft">
                    <User className="h-3.5 w-3.5" />
                    <input
                      className="w-24 rounded-[6px] border border-border px-2 py-0.5 text-xs uppercase tracking-wide text-navy focus:border-accent focus:outline-none"
                      value={c.label}
                      onChange={(e) => updateContact(c.id, 'label', e.target.value)}
                    />
                  </span>
                  <button
                    type="button"
                    onClick={() => removeContact(c.id)}
                    className="rounded p-1 text-ink-soft hover:bg-danger-light hover:text-danger"
                    aria-label={`Remove ${c.label}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  <input
                    className="input !py-2"
                    placeholder="Name"
                    value={c.name}
                    onChange={(e) => updateContact(c.id, 'name', e.target.value)}
                  />
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-soft" aria-hidden="true" />
                    <input
                      className="input !py-2 pl-9"
                      placeholder="Phone number"
                      value={c.phone}
                      onChange={(e) => updateContact(c.id, 'phone', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            ))}
            {contacts.length === 0 && (
              <p className="rounded-[8px] border border-dashed border-border py-6 text-center text-sm text-ink-soft">
                No emergency contacts yet.
              </p>
            )}
          </div>
        </SectionCard>

        <div className="space-y-6">
          {/* Voice SOS */}
          <SectionCard title="Voice SOS">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-[8px] bg-accent-50 text-accent">
                  <Mic className="h-5 w-5" />
                </span>
                <div>
                  <div className="text-sm font-medium text-navy">Voice activation</div>
                  <div className="text-xs text-ink-soft">Trigger SOS by speaking your phrase</div>
                </div>
              </div>
              <Toggle checked={voiceEnabled} onChange={setVoiceEnabled} label="Voice SOS enabled" />
            </div>
            <div className="mt-4">
              <label className="label" htmlFor="phrase">Emergency phrase</label>
              <input
                id="phrase"
                className="input"
                value={voicePhrase}
                onChange={(e) => setVoicePhrase(e.target.value)}
                disabled={!voiceEnabled}
              />
            </div>
          </SectionCard>

          {/* Route preference */}
          <SectionCard title="Default Route Preference">
            <div className="space-y-2.5">
              {ROUTE_PREFS.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => setRoutePref(r.id)}
                  className={`flex w-full items-center gap-3 rounded-[8px] border px-4 py-3 text-left transition-colors ${
                    routePref === r.id ? 'border-accent bg-accent-50' : 'border-border hover:bg-canvas-subtle'
                  }`}
                  aria-pressed={routePref === r.id}
                >
                  <span
                    className={`flex h-5 w-5 flex-none items-center justify-center rounded-full border ${
                      routePref === r.id ? 'border-accent bg-accent text-white' : 'border-border-strong'
                    }`}
                  >
                    {routePref === r.id && <span className="h-2 w-2 rounded-full bg-white" />}
                  </span>
                  <span className="flex flex-1 items-center gap-2">
                    <RouteIcon className="h-4 w-4 text-ink-soft" />
                    <span>
                      <span className="block text-sm font-medium text-navy">{r.label}</span>
                      <span className="block text-xs text-ink-soft">{r.desc}</span>
                    </span>
                  </span>
                </button>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>

      {/* Risk priorities */}
      <SectionCard title="Risk Priorities">
        <p className="mb-4 text-sm text-ink-soft">Choose which factors influence your safety scores most.</p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {RISK_PRIORITIES.map((p) => (
            <div
              key={p.id}
              className="flex items-center justify-between rounded-[8px] border border-border p-3"
            >
              <span className="flex items-center gap-2.5 text-sm text-ink">
                <p.icon className="h-4 w-4 text-accent" />
                {p.label}
              </span>
              <Toggle
                checked={priorities[p.id]}
                onChange={(v) => setPriorities((prev) => ({ ...prev, [p.id]: v }))}
                label={p.label}
              />
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
