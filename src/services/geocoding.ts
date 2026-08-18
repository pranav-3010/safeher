export interface LocationResult {
  label: string;
  lat: number;
  lng: number;
}

const PRESET_LOCATIONS: LocationResult[] = [
  { label: 'Banjara Hills, Hyderabad', lat: 17.4150, lng: 78.4350 },
  { label: 'Hitech City, Hyderabad', lat: 17.4435, lng: 78.3772 },
  { label: 'Madhapur, Hyderabad', lat: 17.4486, lng: 78.3908 },
  { label: 'Gachibowli, Hyderabad', lat: 17.4401, lng: 78.3489 },
  { label: 'Kukatpally, Hyderabad', lat: 17.4948, lng: 78.3996 },
  { label: 'Secunderabad, Hyderabad', lat: 17.4399, lng: 78.4983 },
  { label: 'Begumpet, Hyderabad', lat: 17.4447, lng: 78.4664 },
  { label: 'Mehdipatnam, Hyderabad', lat: 17.3916, lng: 78.4389 },
  { label: 'Jubilee Hills, Hyderabad', lat: 17.4319, lng: 78.4073 },
  { label: 'Charminar, Hyderabad', lat: 17.3616, lng: 78.4747 },
  { label: 'Koti, Hyderabad', lat: 17.3850, lng: 78.4867 },
  { label: 'Ameerpet, Hyderabad', lat: 17.4375, lng: 78.4482 },
  { label: 'LB Nagar, Hyderabad', lat: 17.3457, lng: 78.5522 },
  { label: 'Uppal, Hyderabad', lat: 17.4057, lng: 78.5602 },
  { label: 'Shamshabad, Hyderabad', lat: 17.2497, lng: 78.4299 }
];

export async function searchLocations(query: string): Promise<LocationResult[]> {
  if (!query || query.trim().length === 0) {
    return PRESET_LOCATIONS.slice(0, 5);
  }

  const q = query.toLowerCase().trim();
  const presets = PRESET_LOCATIONS.filter((loc) =>
    loc.label.toLowerCase().includes(q)
  );

  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
        query
      )}&viewbox=78.20,17.20,78.60,17.60&bounded=1&limit=5`,
      { headers: { 'Accept-Language': 'en' } }
    );
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        const fetched: LocationResult[] = data.map((item: any) => ({
          label: item.display_name,
          lat: parseFloat(item.lat),
          lng: parseFloat(item.lon),
        }));
        const combined = [...fetched, ...presets];
        const unique = combined.filter(
          (loc, index, self) =>
            index === self.findIndex((t) => t.label === loc.label || (Math.abs(t.lat - loc.lat) < 0.001 && Math.abs(t.lng - loc.lng) < 0.001))
        );
        return unique.slice(0, 6);
      }
    }
  } catch (err) {
    console.warn("Geocoding search fetch warning:", err);
  }

  return presets.length > 0 ? presets : PRESET_LOCATIONS.slice(0, 5);
}

export async function resolveLocation(
  query: string,
  fallbackLat?: number,
  fallbackLng?: number
): Promise<LocationResult> {
  if (!query || query.trim().length === 0) {
    return { label: 'Banjara Hills, Hyderabad', lat: 17.4150, lng: 78.4350 };
  }

  const q = query.toLowerCase().trim();

  // 1. Check matching presets
  const matchedPreset = PRESET_LOCATIONS.find((loc) => {
    const labelLower = loc.label.toLowerCase();
    const shortName = labelLower.split(',')[0].trim();
    return labelLower.includes(q) || q.includes(shortName);
  });

  if (matchedPreset) {
    return matchedPreset;
  }

  // 2. Parse GPS string formatted as "My GPS Location (17.4150, 78.4350)"
  const coordMatch = query.match(/\((-?\d+\.\d+),\s*(-?\d+\.\d+)\)/);
  if (coordMatch) {
    return {
      label: query,
      lat: parseFloat(coordMatch[1]),
      lng: parseFloat(coordMatch[2]),
    };
  }

  // 3. Query OpenStreetMap Nominatim live geocoding
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`,
      { headers: { 'Accept-Language': 'en' } }
    );
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return {
          label: query,
          lat: parseFloat(data[0].lat),
          lng: parseFloat(data[0].lon),
        };
      }
    }
  } catch (e) {
    console.warn("Nominatim live resolveLocation warning:", e);
  }

  if (fallbackLat && fallbackLng) {
    return { label: query, lat: fallbackLat, lng: fallbackLng };
  }

  // 4. Generate distinct coordinates inside Hyderabad bounding box for custom location names
  let hash = 0;
  for (let i = 0; i < query.length; i++) {
    hash = query.charCodeAt(i) + ((hash << 5) - hash);
  }
  const latOffset = ((Math.abs(hash) % 100) / 1000) * 0.5;
  const lngOffset = (((Math.abs(hash) >> 2) % 100) / 1000) * 0.5;

  return {
    label: query,
    lat: 17.3800 + latOffset,
    lng: 78.4000 + lngOffset,
  };
}
