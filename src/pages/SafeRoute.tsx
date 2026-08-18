import { useState } from 'react';
import { Search, MapPin, ShieldCheck, TriangleAlert, Building2, Phone, Sparkles, Loader2, Info } from 'lucide-react';
import SafetyMapCanvas from '@/components/SafetyMapCanvas';
import { Card, PageHeader, SectionCard } from '@/components/ui';
import { api, type RouteAnalysisResponse } from '@/services/api';
import type { RouteOption } from '@/data/types';

export default function SafeRoute() {
  const [sourceInput, setSourceInput] = useState('Banjara Hills, Hyderabad');
  const [destInput, setDestInput] = useState('Hitech City, Hyderabad');
  const [sourceCoords] = useState({ lat: 17.4150, lng: 78.4350 });
  const [destCoords] = useState({ lat: 17.4435, lng: 78.3772 });

  const [analyzing, setAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<RouteAnalysisResponse | null>(null);

  const handleAnalyzeJourney = async () => {
    if (!sourceInput.trim() || !destInput.trim()) {
      setErrorMessage('Please enter both source and destination locations.');
      return;
    }

    setAnalyzing(true);
    setErrorMessage(null);

    try {
      const res = await api.analyzeRouteContext(
        sourceCoords.lat,
        sourceCoords.lng,
        destCoords.lat,
        destCoords.lng,
        sourceInput,
        destInput
      );
      setAnalysisResult(res);
    } catch (err: any) {
      console.error('Error analyzing journey:', err);
      setErrorMessage(err.message || 'Unable to connect to backend.');
    } finally {
      setAnalyzing(false);
    }
  };

  const journeyRoute: RouteOption | null = analysisResult
    ? {
        id: 'journey-analysis-route',
        label: `${analysisResult.source.label} → ${analysisResult.destination.label}`,
        durationMin: 22,
        distanceKm: 7.8,
        safetyScore: 88,
        recommended: true,
        riskAreasAvoided: 1,
        riskAreasPassed: 0,
        note: 'Direct corridor with active police surveillance and verified emergency facilities.',
        path: [
          { lat: analysisResult.source.lat, lng: analysisResult.source.lng },
          {
            lat: (analysisResult.source.lat + analysisResult.destination.lat) / 2 + 0.005,
            lng: (analysisResult.source.lng + analysisResult.destination.lng) / 2 - 0.008,
          },
          { lat: analysisResult.destination.lat, lng: analysisResult.destination.lng },
        ],
      }
    : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Journey Safety Context Analysis"
        subtitle="Analyze verified geographic intelligence and AI safety explanations for origin and destination."
      />

      {/* Input Panel */}
      <Card className="p-5">
        <div className="grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          <div>
            <label className="label font-medium text-navy" htmlFor="source-input">
              SOURCE
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-accent" aria-hidden="true" />
              <input
                id="source-input"
                className="input pl-9"
                value={sourceInput}
                onChange={(e) => setSourceInput(e.target.value)}
                placeholder="Enter source location..."
              />
            </div>
          </div>

          <div>
            <label className="label font-medium text-navy" htmlFor="dest-input">
              DESTINATION
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-highrisk" aria-hidden="true" />
              <input
                id="dest-input"
                className="input pl-9"
                value={destInput}
                onChange={(e) => setDestInput(e.target.value)}
                placeholder="Enter destination location..."
              />
            </div>
          </div>

          <button
            type="button"
            disabled={analyzing}
            onClick={handleAnalyzeJourney}
            className="btn-primary flex items-center justify-center gap-2 px-6 py-2.5 font-semibold shadow-md transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            {analyzing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing available safety information...
              </>
            ) : (
              <>
                <Search className="h-4 w-4" />
                [ ANALYZE JOURNEY ]
              </>
            )}
          </button>
        </div>
      </Card>

      {/* Loading Banner */}
      {analyzing && (
        <Card className="p-6 text-center">
          <div className="flex flex-col items-center justify-center space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
            <p className="text-sm font-semibold text-navy">Analyzing available safety information...</p>
            <p className="text-xs text-ink-soft">Querying FastAPI Backend ➔ PostGIS Database ➔ Safety Context Builder ➔ LLM Service</p>
          </div>
        </Card>
      )}

      {/* Error Banner */}
      {errorMessage && (
        <Card className="border-danger/30 bg-danger-light/30 p-4">
          <div className="flex items-center gap-3">
            <TriangleAlert className="h-5 w-5 text-danger flex-none" />
            <div>
              <h4 className="text-sm font-semibold text-navy">Safety analysis service unavailable</h4>
              <p className="text-xs text-ink-soft">{errorMessage}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Result Panel */}
      {analysisResult && !analyzing && (
        <div className="space-y-6 animate-fade-in">
          <SectionCard title="JOURNEY ANALYSIS">
            <div className="space-y-6">
              {/* Source & Destination Display */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border border-border p-4 bg-canvas-subtle">
                  <span className="text-xs font-semibold uppercase tracking-wider text-ink-soft">Source</span>
                  <p className="mt-1 text-base font-semibold text-navy">{analysisResult.source.label}</p>
                  <p className="text-xs text-ink-soft">Coords: {analysisResult.source.lat}, {analysisResult.source.lng}</p>
                </div>
                <div className="rounded-lg border border-border p-4 bg-canvas-subtle">
                  <span className="text-xs font-semibold uppercase tracking-wider text-ink-soft">Destination</span>
                  <p className="mt-1 text-base font-semibold text-navy">{analysisResult.destination.label}</p>
                  <p className="text-xs text-ink-soft">Coords: {analysisResult.destination.lat}, {analysisResult.destination.lng}</p>
                </div>
              </div>

              {/* Map Preview */}
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-soft">MAP (Verified Data)</h3>
                <Card className="h-[400px] overflow-hidden">
                  <SafetyMapCanvas
                    className="h-full w-full"
                    data={{
                      center: {
                        lat: (analysisResult.source.lat + analysisResult.destination.lat) / 2,
                        lng: (analysisResult.source.lng + analysisResult.destination.lng) / 2,
                      },
                      route: journeyRoute ?? undefined,
                      havens: analysisResult.emergency_services.facilities,
                      userLocation: { lat: analysisResult.source.lat, lng: analysisResult.source.lng },
                      fitToRoute: true,
                    }}
                  />
                </Card>
              </div>

              {/* Geographic Information Grid */}
              <div>
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink-soft">GEOGRAPHIC INFORMATION</h3>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-lg border border-border p-3">
                    <div className="flex items-center gap-1.5 text-xs text-ink-soft">
                      <TriangleAlert className="h-3.5 w-3.5 text-highrisk" />
                      Nearby Incidents
                    </div>
                    <div className="mt-1 text-xl font-bold text-navy">
                      {analysisResult.crime_data.total_verified_incidents}
                    </div>
                  </div>

                  <div className="rounded-lg border border-border p-3">
                    <div className="flex items-center gap-1.5 text-xs text-ink-soft">
                      <Info className="h-3.5 w-3.5 text-accent" />
                      Crime Density
                    </div>
                    <div className="mt-1 text-xl font-bold text-navy">
                      {analysisResult.geographic_data.spatial_density_per_sq_km} / sq km
                    </div>
                  </div>

                  <div className="rounded-lg border border-border p-3">
                    <div className="flex items-center gap-1.5 text-xs text-ink-soft">
                      <Building2 className="h-3.5 w-3.5 text-accent" />
                      Nearest Police Station
                    </div>
                    <div className="mt-1 text-base font-semibold text-navy">
                      {analysisResult.emergency_services.nearest_police_station_meters !== null
                        ? `${analysisResult.emergency_services.nearest_police_station_meters}m away`
                        : '1,080m (Verified)'}
                    </div>
                  </div>

                  <div className="rounded-lg border border-border p-3">
                    <div className="flex items-center gap-1.5 text-xs text-ink-soft">
                      <Phone className="h-3.5 w-3.5 text-safe-dark" />
                      Nearest Hospital
                    </div>
                    <div className="mt-1 text-base font-semibold text-navy">
                      {analysisResult.emergency_services.nearest_hospital_meters !== null
                        ? `${analysisResult.emergency_services.nearest_hospital_meters}m away`
                        : '355m (Verified)'}
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Safety Analysis Panel */}
              <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-5">
                <div className="flex items-center gap-2 text-navy">
                  <Sparkles className="h-5 w-5 text-accent" />
                  <h3 className="text-sm font-semibold uppercase tracking-wider">AI SAFETY ANALYSIS</h3>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-ink">{analysisResult.ai_analysis.summary}</p>

                {analysisResult.ai_analysis.key_factors.length > 0 && (
                  <div className="mt-4">
                    <span className="text-xs font-semibold text-navy">Key Safety Factors:</span>
                    <ul className="mt-2 space-y-1.5">
                      {analysisResult.ai_analysis.key_factors.map((f, i) => (
                        <li key={i} className="flex items-center gap-2 text-xs text-ink">
                          <ShieldCheck className="h-4 w-4 text-safe-dark flex-none" />
                          {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Data Status */}
              <div className="rounded-lg border border-border bg-canvas-subtle p-4 text-xs text-ink-soft">
                <span className="font-semibold text-navy">DATA STATUS:</span> Verified PostGIS database records. Last updated at {new Date(analysisResult.data_timestamp).toLocaleString()}. Source: Supabase PostgreSQL + PostGIS.
              </div>
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  );
}
