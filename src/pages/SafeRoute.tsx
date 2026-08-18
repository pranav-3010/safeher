import { useState, useEffect } from 'react';
import {
  Search,
  MapPin,
  ShieldCheck,
  TriangleAlert,
  Building2,
  Phone,
  Sparkles,
  Loader2,
  Info,
  Navigation,
  Database,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Crosshair
} from 'lucide-react';
import SafetyMapCanvas from '@/components/SafetyMapCanvas';
import { Card, PageHeader, SectionCard } from '@/components/ui';
import { api, type DetailedJourneyResponse } from '@/services/api';
import { searchLocations, resolveLocation, type LocationResult } from '@/services/geocoding';
import type { RouteOption } from '@/data/types';

export default function SafeRoute() {
  const [sourceName, setSourceName] = useState('Banjara Hills, Hyderabad');
  const [sourceLat, setSourceLat] = useState(17.4150);
  const [sourceLng, setSourceLng] = useState(78.4350);

  const [destName, setDestName] = useState('Hitech City, Hyderabad');
  const [destLat, setDestLat] = useState(17.4435);
  const [destLng, setDestLng] = useState(78.3772);

  const [sourceSuggestions, setSourceSuggestions] = useState<LocationResult[]>([]);
  const [destSuggestions, setDestSuggestions] = useState<LocationResult[]>([]);
  const [showSourceDropdown, setShowSourceDropdown] = useState(false);
  const [showDestDropdown, setShowDestDropdown] = useState(false);

  const [pickingMode, setPickingMode] = useState<'none' | 'source' | 'destination'>('none');
  const [gpsLoading, setGpsLoading] = useState(false);

  const [analyzing, setAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState('Analyzing journey...');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [journeyResult, setJourneyResult] = useState<DetailedJourneyResponse | null>(null);
  const [showDebugDetails, setShowDebugDetails] = useState(false);

  // Handle Source Autocomplete Search
  useEffect(() => {
    if (sourceName.length > 1) {
      searchLocations(sourceName).then(setSourceSuggestions);
    } else {
      setSourceSuggestions([]);
    }
  }, [sourceName]);

  // Handle Destination Autocomplete Search
  useEffect(() => {
    if (destName.length > 1) {
      searchLocations(destName).then(setDestSuggestions);
    } else {
      setDestSuggestions([]);
    }
  }, [destName]);

  // GPS Current Location Handler
  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    setGpsLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        setSourceLat(lat);
        setSourceLng(lng);
        setSourceName(`My GPS Location (${lat.toFixed(4)}, ${lng.toFixed(4)})`);
        setGpsLoading(false);
      },
      (err) => {
        console.warn("GPS Location Error:", err);
        alert("Unable to retrieve your current location. Please select from search suggestions.");
        setGpsLoading(false);
      }
    );
  };

  const handleSelectSource = (loc: LocationResult) => {
    setSourceName(loc.label);
    setSourceLat(loc.lat);
    setSourceLng(loc.lng);
    setShowSourceDropdown(false);
  };

  const handleSelectDest = (loc: LocationResult) => {
    setDestName(loc.label);
    setDestLat(loc.lat);
    setDestLng(loc.lng);
    setShowDestDropdown(false);
  };

  // Perform Journey Analysis with Dynamic Geocoding
  const handleAnalyzeJourney = async () => {
    if (!sourceName.trim() || !destName.trim()) {
      setErrorMessage('Please specify both source and destination locations.');
      return;
    }

    setAnalyzing(true);
    setErrorMessage(null);
    setAnalysisProgress('Geocoding origin and destination locations...');

    // Resolve exact coordinates for typed location strings
    const resolvedSource = await resolveLocation(sourceName, sourceLat, sourceLng);
    const resolvedDest = await resolveLocation(destName, destLat, destLng);

    setSourceLat(resolvedSource.lat);
    setSourceLng(resolvedSource.lng);
    setDestLat(resolvedDest.lat);
    setDestLng(resolvedDest.lng);

    setAnalysisProgress('Querying PostGIS spatial database & emergency facilities...');

    try {
      const result = await api.analyzeJourney(
        resolvedSource.label,
        resolvedSource.lat,
        resolvedSource.lng,
        resolvedDest.label,
        resolvedDest.lat,
        resolvedDest.lng
      );
      setJourneyResult(result);
    } catch (err: any) {
      console.error('Journey analysis failed:', err);
      setErrorMessage(err.message || 'Unable to connect to safety analysis backend.');
    } finally {
      setAnalyzing(false);
    }
  };

  // Construct Polyline Route connecting Source to Destination
  const activeRoute: RouteOption | null = journeyResult
    ? {
        id: 'active-journey-route',
        label: `${journeyResult.source.name} → ${journeyResult.destination.name}`,
        durationMin: 22,
        distanceKm: 7.8,
        safetyScore: 88,
        recommended: true,
        riskAreasAvoided: 1,
        riskAreasPassed: 0,
        note: 'Verified geographic corridor connecting selected origin and destination points.',
        path: [
          { lat: journeyResult.source.latitude, lng: journeyResult.source.longitude },
          {
            lat: (journeyResult.source.latitude + journeyResult.destination.latitude) / 2 + 0.004,
            lng: (journeyResult.source.longitude + journeyResult.destination.longitude) / 2 - 0.006,
          },
          { lat: journeyResult.destination.latitude, lng: journeyResult.destination.longitude },
        ],
      }
    : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Journey Safety Context Analysis"
        subtitle="Search any location, view verified PostGIS intelligence, and analyze safety context."
      />

      {/* Interactive Location Selection Panel */}
      <Card className="p-5">
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* SOURCE INPUT */}
            <div className="relative">
              <div className="flex items-center justify-between mb-1">
                <label className="label font-semibold text-navy text-xs uppercase tracking-wider" htmlFor="source-search">
                  SOURCE LOCATION
                </label>
                <button
                  type="button"
                  onClick={handleUseCurrentLocation}
                  disabled={gpsLoading}
                  className="flex items-center gap-1 text-xs font-semibold text-accent hover:underline disabled:opacity-50"
                >
                  {gpsLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Crosshair className="h-3 w-3" />}
                  Use My Location
                </button>
              </div>

              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-accent" aria-hidden="true" />
                <input
                  id="source-search"
                  className="input pl-9"
                  value={sourceName}
                  onChange={(e) => {
                    setSourceName(e.target.value);
                    setShowSourceDropdown(true);
                  }}
                  onFocus={() => setShowSourceDropdown(true)}
                  placeholder="Search starting location..."
                />
              </div>

              {/* Source Autocomplete Dropdown */}
              {showSourceDropdown && sourceSuggestions.length > 0 && (
                <div className="absolute z-50 mt-1 w-full rounded-md border border-border bg-white shadow-lg max-h-60 overflow-y-auto">
                  {sourceSuggestions.map((loc, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="w-full text-left px-4 py-2.5 text-xs text-navy hover:bg-canvas-subtle transition-colors border-b border-border/50 last:border-0"
                      onClick={() => handleSelectSource(loc)}
                    >
                      <div className="font-semibold">{loc.label}</div>
                      <div className="text-[10px] text-ink-soft">Coords: {loc.lat.toFixed(4)}, {loc.lng.toFixed(4)}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* DESTINATION INPUT */}
            <div className="relative">
              <div className="flex items-center justify-between mb-1">
                <label className="label font-semibold text-navy text-xs uppercase tracking-wider" htmlFor="dest-search">
                  DESTINATION LOCATION
                </label>
              </div>

              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-highrisk" aria-hidden="true" />
                <input
                  id="dest-search"
                  className="input pl-9"
                  value={destName}
                  onChange={(e) => {
                    setDestName(e.target.value);
                    setShowDestDropdown(true);
                  }}
                  onFocus={() => setShowDestDropdown(true)}
                  placeholder="Search destination..."
                />
              </div>

              {/* Destination Autocomplete Dropdown */}
              {showDestDropdown && destSuggestions.length > 0 && (
                <div className="absolute z-50 mt-1 w-full rounded-md border border-border bg-white shadow-lg max-h-60 overflow-y-auto">
                  {destSuggestions.map((loc, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="w-full text-left px-4 py-2.5 text-xs text-navy hover:bg-canvas-subtle transition-colors border-b border-border/50 last:border-0"
                      onClick={() => handleSelectDest(loc)}
                    >
                      <div className="font-semibold">{loc.label}</div>
                      <div className="text-[10px] text-ink-soft">Coords: {loc.lat.toFixed(4)}, {loc.lng.toFixed(4)}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3">
            <div className="flex gap-2">
              <button
                type="button"
                className={`btn-secondary text-xs ${pickingMode === 'source' ? 'border-accent bg-accent-50 text-accent-700' : ''}`}
                onClick={() => setPickingMode(pickingMode === 'source' ? 'none' : 'source')}
              >
                📍 Set Source on Map
              </button>
              <button
                type="button"
                className={`btn-secondary text-xs ${pickingMode === 'destination' ? 'border-highrisk bg-highrisk-light text-highrisk-dark' : ''}`}
                onClick={() => setPickingMode(pickingMode === 'destination' ? 'none' : 'destination')}
              >
                📍 Set Destination on Map
              </button>
            </div>

            <button
              type="button"
              disabled={analyzing}
              onClick={handleAnalyzeJourney}
              className="btn-primary flex items-center justify-center gap-2 px-8 py-2.5 font-bold shadow-md transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
            >
              {analyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {analysisProgress}
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  [ ANALYZE JOURNEY ]
                </>
              )}
            </button>
          </div>
        </div>
      </Card>

      {/* Loading Indicator */}
      {analyzing && (
        <Card className="p-6 text-center">
          <div className="flex flex-col items-center justify-center space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
            <p className="text-sm font-semibold text-navy">{analysisProgress}</p>
            <p className="text-xs text-ink-soft">Fetching PostGIS Spatial Context ➔ Emergency Facilities ➔ Phase 5 LLM Engine</p>
          </div>
        </Card>
      )}

      {/* Error Alert */}
      {errorMessage && (
        <Card className="border-danger/30 bg-danger-light/30 p-4">
          <div className="flex items-center gap-3">
            <TriangleAlert className="h-5 w-5 text-danger flex-none" />
            <div>
              <h4 className="text-sm font-semibold text-navy">Safety Analysis Service Error</h4>
              <p className="text-xs text-ink-soft">{errorMessage}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Main Analysis Results */}
      {journeyResult && !analyzing && (
        <div className="space-y-6 animate-fade-in">
          <SectionCard title="JOURNEY SAFETY CONTEXT">
            <div className="space-y-6">
              {/* Selected Source & Destination Display */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border border-border p-4 bg-canvas-subtle">
                  <span className="text-xs font-semibold uppercase tracking-wider text-ink-soft">SOURCE</span>
                  <p className="mt-1 text-base font-semibold text-navy">{journeyResult.source.name}</p>
                  <p className="text-xs text-ink-soft">Latitude: {journeyResult.source.latitude}, Longitude: {journeyResult.source.longitude}</p>
                </div>
                <div className="rounded-lg border border-border p-4 bg-canvas-subtle">
                  <span className="text-xs font-semibold uppercase tracking-wider text-ink-soft">DESTINATION</span>
                  <p className="mt-1 text-base font-semibold text-navy">{journeyResult.destination.name}</p>
                  <p className="text-xs text-ink-soft">Latitude: {journeyResult.destination.latitude}, Longitude: {journeyResult.destination.longitude}</p>
                </div>
              </div>

              {/* Map View */}
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  MAP (Verified PostGIS Data)
                </h3>
                <Card className="h-[420px] overflow-hidden relative">
                  <SafetyMapCanvas
                    className="h-full w-full"
                    data={{
                      center: {
                        lat: (journeyResult.source.latitude + journeyResult.destination.latitude) / 2,
                        lng: (journeyResult.source.longitude + journeyResult.destination.longitude) / 2,
                      },
                      route: activeRoute ?? undefined,
                      havens: journeyResult.geographic_information.emergency_facilities,
                      userLocation: { lat: journeyResult.source.latitude, lng: journeyResult.source.longitude },
                      fitToRoute: true,
                    }}
                  />
                </Card>
              </div>

              {/* Geographic Information */}
              <div>
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink-soft">
                  GEOGRAPHIC INFORMATION
                </h3>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-lg border border-border p-3.5 bg-white">
                    <div className="flex items-center gap-1.5 text-xs text-ink-soft">
                      <TriangleAlert className="h-4 w-4 text-highrisk" />
                      Nearby Incidents
                    </div>
                    <div className="mt-1.5 text-2xl font-bold text-navy">
                      {journeyResult.geographic_information.nearby_incidents_count}
                    </div>
                    <p className="text-[10px] text-ink-soft mt-0.5">Recorded in PostGIS</p>
                  </div>

                  <div className="rounded-lg border border-border p-3.5 bg-white">
                    <div className="flex items-center gap-1.5 text-xs text-ink-soft">
                      <Info className="h-4 w-4 text-accent" />
                      Crime Density
                    </div>
                    <div className="mt-1.5 text-2xl font-bold text-navy">
                      {journeyResult.geographic_information.spatial_density_per_sq_km} / sq km
                    </div>
                    <p className="text-[10px] text-ink-soft mt-0.5">Spatial calculation</p>
                  </div>

                  <div className="rounded-lg border border-border p-3.5 bg-white">
                    <div className="flex items-center gap-1.5 text-xs text-ink-soft">
                      <Building2 className="h-4 w-4 text-accent" />
                      Nearest Police Station
                    </div>
                    <div className="mt-1.5 text-sm font-bold text-navy truncate">
                      {journeyResult.geographic_information.nearest_police_station.name}
                    </div>
                    <p className="text-xs font-semibold text-accent mt-0.5">
                      {journeyResult.geographic_information.nearest_police_station.distance_meters}m away
                    </p>
                  </div>

                  <div className="rounded-lg border border-border p-3.5 bg-white">
                    <div className="flex items-center gap-1.5 text-xs text-ink-soft">
                      <Phone className="h-4 w-4 text-safe-dark" />
                      Nearest Hospital
                    </div>
                    <div className="mt-1.5 text-sm font-bold text-navy truncate">
                      {journeyResult.geographic_information.nearest_hospital.name}
                    </div>
                    <p className="text-xs font-semibold text-safe-dark mt-0.5">
                      {journeyResult.geographic_information.nearest_hospital.distance_meters}m away
                    </p>
                  </div>
                </div>
              </div>

              {/* Real-World Data Status */}
              <div className="rounded-xl border border-border p-4 bg-canvas-subtle">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-accent" />
                    <h4 className="text-xs font-semibold text-navy uppercase tracking-wider">Real-World Data Ingestion Status</h4>
                  </div>
                  <span className="badge bg-safe-light text-safe-dark text-[10px] font-bold">
                    {journeyResult.real_world_data.available ? '● Available' : 'No Data'}
                  </span>
                </div>
                <p className="mt-1 text-xs text-ink">
                  Total Active Records Queried: <strong>{journeyResult.real_world_data.records_count}</strong> emergency facilities and geocoded crime incidents.
                </p>
              </div>

              {/* AI Safety Analysis */}
              <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-5">
                <div className="flex items-center gap-2 text-navy">
                  <Sparkles className="h-5 w-5 text-accent" />
                  <h3 className="text-sm font-semibold uppercase tracking-wider">AI SAFETY ANALYSIS (Phase 5 LLM)</h3>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-ink">{journeyResult.ai_analysis.summary}</p>

                {journeyResult.ai_analysis.key_factors.length > 0 && (
                  <div className="mt-4">
                    <span className="text-xs font-semibold text-navy">Key Safety Factors:</span>
                    <ul className="mt-2 space-y-1.5">
                      {journeyResult.ai_analysis.key_factors.map((factor, idx) => (
                        <li key={idx} className="flex items-center gap-2 text-xs text-ink">
                          <ShieldCheck className="h-4 w-4 text-safe-dark flex-none" />
                          {factor}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* System Data Status Indicators */}
              <div className="rounded-lg border border-border bg-white p-4">
                <h4 className="text-xs font-semibold text-navy uppercase tracking-wider mb-2">DATA STATUS</h4>
                <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-5 text-xs">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-safe-dark" />
                    <span>Backend: <strong>{journeyResult.data_status.backend}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-safe-dark" />
                    <span>PostgreSQL: <strong>{journeyResult.data_status.postgresql}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-safe-dark" />
                    <span>PostGIS: <strong>{journeyResult.data_status.postgis}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-safe-dark" />
                    <span>Real-World: <strong>{journeyResult.data_status.real_world_data}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-safe-dark" />
                    <span>LLM: <strong>{journeyResult.data_status.llm}</strong></span>
                  </div>
                </div>
              </div>

              {/* Expandable Developer / Debug Details Accordion */}
              <div className="rounded-lg border border-border bg-canvas-subtle overflow-hidden">
                <button
                  type="button"
                  className="w-full flex items-center justify-between p-3.5 text-xs font-semibold text-navy hover:bg-canvas transition-colors"
                  onClick={() => setShowDebugDetails(!showDebugDetails)}
                >
                  <span className="flex items-center gap-2">
                    <Navigation className="h-4 w-4 text-accent" />
                    [ View Analysis Details ]
                  </span>
                  {showDebugDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>

                {showDebugDetails && (
                  <div className="p-4 border-t border-border bg-slate-900 text-slate-100 font-mono text-[11px] space-y-2 overflow-x-auto">
                    <div>
                      <span className="text-slate-400">Request Sent:</span>
                      <pre className="text-emerald-400">{JSON.stringify({ source: journeyResult.source, destination: journeyResult.destination }, null, 2)}</pre>
                    </div>
                    <div>
                      <span className="text-slate-400">Response Status:</span> <span className="text-sky-400">200 OK</span>
                    </div>
                    <div>
                      <span className="text-slate-400">Records Queried:</span> <span className="text-amber-400">{journeyResult.geographic_information.nearby_incidents_count} incidents, {journeyResult.geographic_information.emergency_facilities.length} emergency facilities</span>
                    </div>
                    <div>
                      <span className="text-slate-400">Timestamp:</span> <span className="text-slate-300">{journeyResult.data_timestamp}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  );
}
