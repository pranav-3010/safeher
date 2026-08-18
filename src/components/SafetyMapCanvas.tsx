import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { LatLng, RiskLevel, RouteOption, SafeHaven, SafetyZone } from '@/data/types';
import { RISK_META } from '@/data/types';

interface MapData {
  center?: LatLng;
  zones?: SafetyZone[];
  route?: RouteOption;
  routes?: RouteOption[];
  selectedRouteId?: string;
  havens?: SafeHaven[];
  userLocation?: LatLng;
  startLocation?: { name: string; lat: number; lng: number };
  endLocation?: { name: string; lat: number; lng: number };
  onZoneClick?: (zone: SafetyZone) => void;
  fitToRoute?: boolean;
}

const havenIcon = (category: string, online: boolean) => {
  const colors: Record<string, string> = {
    Police: '#1D4FD8',
    Hospital: '#16803A',
    Metro: '#B77900',
    'Petrol Pump': '#6B7280',
    'Open Business': '#2563EB',
  };
  const color = colors[category] ?? '#6B7280';
  const dim = online ? '' : 'opacity:0.55;';
  const glyph: Record<string, string> = {
    Police: 'P',
    Hospital: 'H',
    Metro: 'M',
    'Petrol Pump': 'F',
    'Open Business': 'B',
  };
  return L.divIcon({
    className: 'safeher-marker',
    html: `<div style="${dim}width:24px;height:24px;border-radius:50%;background:#fff;border:2px solid ${color};color:${color};display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;box-shadow:0 1px 3px rgba(0,0,0,.25);">${glyph[category] ?? 'S'}</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

const userIcon = L.divIcon({
  className: 'safeher-marker',
  html: `<div style="width:16px;height:16px;border-radius:50%;background:#2563EB;border:3px solid #fff;box-shadow:0 0 0 6px rgba(37,99,235,.18),0 1px 4px rgba(0,0,0,.3);"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const startPinIcon = L.divIcon({
  className: 'safeher-marker',
  html: `<div style="background:#16803A;color:#fff;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:800;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3);display:flex;align-items:center;gap:4px;white-space:nowrap;">📍 START</div>`,
  iconSize: [80, 24],
  iconAnchor: [40, 24],
});

const endPinIcon = L.divIcon({
  className: 'safeher-marker',
  html: `<div style="background:#DC2626;color:#fff;padding:4px 8px;border-radius:12px;font-size:11px;font-weight:800;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3);display:flex;align-items:center;gap:4px;white-space:nowrap;">🏁 END</div>`,
  iconSize: [80, 24],
  iconAnchor: [40, 24],
});

function zoneIcon(level: RiskLevel) {
  const meta = RISK_META[level];
  return L.divIcon({
    className: 'safeher-marker',
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${meta.color};border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3);"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

export default function SafetyMapCanvas({
  data,
  className = '',
}: {
  data: MapData;
  className?: string;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);

  // init once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const center: L.LatLngExpression = [
      data.center?.lat ?? 17.4305,
      data.center?.lng ?? 78.395,
    ];
    const map = L.map(containerRef.current, {
      center,
      zoom: 13,
      zoomControl: true,
      attributionControl: true,
      preferCanvas: true,
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    setTimeout(() => map.invalidateSize(), 60);
    return () => {
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
    };
  }, []);

  // draw layers when data changes
  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();

    const defaultHotspots = [
      { name: "Banjara Hills Sector 12 Incident Zone", lat: 17.4180, lng: 78.4280, riskScore: 72, label: "Chain Snatching Hotspot" },
      { name: "Hitech City Metro Night Corridor", lat: 17.4480, lng: 78.3810, riskScore: 68, label: "Moderate Lighting Stretch" },
      { name: "Mehdipatnam Commercial Hub", lat: 17.3980, lng: 78.4350, riskScore: 75, label: "Unsafe Junction Cluster" },
      { name: "Dilsukhnagar Transit Sector", lat: 17.3650, lng: 78.5200, riskScore: 82, label: "High Density Incident Zone" }
    ];

    const zones = data.zones && data.zones.length ? data.zones : defaultHotspots.map((h, idx) => ({
      id: `zone-${idx}`,
      name: h.name,
      center: { lat: h.lat, lng: h.lng },
      radiusM: 2500,
      riskScore: h.riskScore,
      riskLevel: (h.riskScore >= 80 ? 'veryhigh' : h.riskScore >= 60 ? 'high' : 'moderate') as RiskLevel,
      lighting: 'Moderate' as const,
      naturalSurveillance: 'Moderate' as const,
      policeDistanceKm: 1.2,
      hospitalDistanceKm: 2.1,
      commercialActivity: 'High' as const,
      communityRating: 3.2,
      recentIncidents: 4,
      riskFactors: [h.label],
      positiveFactors: ['CCTV Monitored Corridor']
    }));

    zones.forEach((z) => {
      const meta = RISK_META[z.riskLevel];
      const circle = L.circle([z.center.lat, z.center.lng], {
        radius: z.radiusM,
        color: meta.color,
        weight: 2,
        opacity: 0.7,
        fillColor: meta.color,
        fillOpacity: 0.18,
      });
      circle.bindPopup(
        `<div style="min-width:170px;font-family:sans-serif;">
          <div style="font-weight:700;color:#1E293B;margin-bottom:2px;">⚠️ ${z.name}</div>
          <div style="font-size:12px;color:${meta.color};font-weight:700;">${meta.label} (Risk Index: ${z.riskScore}/100)</div>
          <div style="font-size:11px;color:#64748B;margin-top:4px;">Proximity Buffer Radius: <b>2.5 km</b></div>
        </div>`
      );
      if (data.onZoneClick) {
        circle.on('click', () => data.onZoneClick?.(z));
      }
      circle.addTo(layer);

      L.marker([z.center.lat, z.center.lng], { icon: zoneIcon(z.riskLevel) })
        .addTo(layer)
        .on('click', () => data.onZoneClick?.(z));
    });


    const routeLines: L.Polyline[] = [];
    const drawRoute = (r: RouteOption, selected: boolean) => {
      const latlngs: L.LatLngExpression[] = r.path.map((p) => [p.lat, p.lng]);
      const color = (r.id.includes('safest') || r.label.toLowerCase().includes('safest'))
        ? '#16803A'
        : (r.id.includes('fastest') || r.label.toLowerCase().includes('fastest'))
        ? '#DC2626'
        : '#D97706';

      const line = L.polyline(latlngs, {
        color: color,
        weight: selected ? 7 : 4,
        opacity: selected ? 0.95 : 0.65,
        dashArray: selected ? undefined : '6,8',
        lineJoin: 'round',
      });
      line.bindPopup(
        `<div style="min-width:160px;font-family:sans-serif;">
          <div style="font-weight:800;font-size:13px;color:${color};">${r.label} ${r.recommended ? '★ RECOMMENDED' : ''}</div>
          <div style="font-size:12px;color:#1E293B;margin-top:2px;">⏱ <b>${r.durationMin} min</b> · 📏 <b>${r.distanceKm} km</b></div>
          <div style="font-size:12px;color:${color};font-weight:700;margin-top:2px;">🛡️ Location Safety Index: ${r.safetyScore}/100</div>
        </div>`
      );
      line.addTo(layer);
      routeLines.push(line);
    };


    if (data.routes && data.routes.length) {
      data.routes.forEach((r) => drawRoute(r, r.id === data.selectedRouteId));
    } else if (data.route) {
      drawRoute(data.route, true);
    }

    (data.havens ?? []).forEach((h) => {
      L.marker([h.position.lat, h.position.lng], { icon: havenIcon(h.category, true) })
        .bindPopup(
          `<div style="min-width:150px;"><div style="font-weight:600;color:#172033;">${h.name}</div>
          <div style="font-size:12px;color:#6B7280;">${h.category} · ${h.distanceKm} km</div>
          <div style="font-size:11px;color:#16803A;font-weight:600;margin-top:2px;">${h.openStatus}</div></div>`
        )
        .addTo(layer);
    });

    if (data.startLocation) {
      L.marker([data.startLocation.lat, data.startLocation.lng], { icon: startPinIcon })
        .bindPopup(`<div style="font-weight:700;color:#16803A;">START: ${data.startLocation.name}</div>`)
        .addTo(layer);
    }

    if (data.endLocation) {
      L.marker([data.endLocation.lat, data.endLocation.lng], { icon: endPinIcon })
        .bindPopup(`<div style="font-weight:700;color:#DC2626;">END: ${data.endLocation.name}</div>`)
        .addTo(layer);
    }

    if (data.userLocation && !data.startLocation) {
      L.marker([data.userLocation.lat, data.userLocation.lng], { icon: userIcon })
        .bindPopup('<div style="font-weight:600;color:#172033;">Your location</div>')
        .addTo(layer);
    }

    if (data.fitToRoute && routeLines.length) {
      const group = L.featureGroup(routeLines);
      map.fitBounds(group.getBounds().pad(0.22), { animate: false });
    }

    setTimeout(() => map.invalidateSize(), 50);
  }, [data]);

  return <div ref={containerRef} className={className} aria-label="Safety map" role="application" />;
}
