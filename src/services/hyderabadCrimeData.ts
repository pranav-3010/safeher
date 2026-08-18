export interface CrimeSpot {
  name: string;
  lat: number;
  lng: number;
  rating: number;
  category: string;
  description: string;
}

export const HYDERABAD_CRIME_HOTSPOTS: CrimeSpot[] = [
  { name: 'Banjara Hills Sector 12', lat: 17.4180, lng: 78.4280, rating: 4.2, category: 'Chain Snatching', description: 'Frequent chain snatching reported near Road No 12' },
  { name: 'Hitech City Metro Corridor', lat: 17.4480, lng: 78.3810, rating: 3.8, category: 'Harassment', description: 'Poorly lit stretch under Metro station after 10 PM' },
  { name: 'Mehdipatnam Bus Junction', lat: 17.3980, lng: 78.4350, rating: 4.5, category: 'Unsafe Crowd', description: 'High density junction with frequent eve teasing reports' },
  { name: 'Dilsukhnagar Transit Hub', lat: 17.3650, lng: 78.5200, rating: 4.8, category: 'High Theft', description: 'Reported pickpocketing and mobile snatching' },
  { name: 'Gachibowli Outer Ring Road', lat: 17.4400, lng: 78.3480, rating: 3.5, category: 'Isolated Stretch', description: 'Isolated highway connector with low foot traffic' },
  { name: 'Secunderabad Station Exit', lat: 17.4390, lng: 78.4980, rating: 4.0, category: 'Unsafe Night Area', description: 'Late night harassment reports near railway exit' },
  { name: 'Charminar Old City Corridor', lat: 17.3610, lng: 78.4740, rating: 4.6, category: 'Crowded Incident Zone', description: 'Narrow unlit alleys with high crime reports' },
  { name: 'Kukatpally Housing Board', lat: 17.4850, lng: 78.4130, rating: 3.6, category: 'Minor Incidents', description: 'Reported vehicle theft and harassment' },
  { name: 'Narsingi Outer Bypass', lat: 17.3910, lng: 78.3590, rating: 3.9, category: 'Poor Lighting', description: 'Unlit junction stretch near expressway' },
  { name: 'Sun City Bandlaguda Junction', lat: 17.3630, lng: 78.3970, rating: 3.7, category: 'Isolated Area', description: 'Low surveillance corridor at night' },
  { name: 'Ameerpet Metro Station', lat: 17.4375, lng: 78.4482, rating: 4.1, category: 'Crowded Unsafe Area', description: 'High congestion area with harassment reports' },
  { name: 'Begumpet Main Road', lat: 17.4447, lng: 78.4664, rating: 3.4, category: 'Speeding Hazard', description: 'Accident prone stretch at night' },
  { name: 'Kondapur RTA Junction', lat: 17.4618, lng: 78.3672, rating: 3.8, category: 'Poor Street Lighting', description: 'Dark stretches near flyover construction' },
  { name: 'Miyapur Bus Depot', lat: 17.4969, lng: 78.3614, rating: 4.3, category: 'Late Night Hazard', description: 'Isolated bus shelter area' },
  { name: 'Tolichowki Flyover', lat: 17.4018, lng: 78.4131, rating: 4.0, category: 'Heavy Traffic / Unlit', description: 'Under-flyover dark corridors' }
];

export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371.0;
  const dLat = (lat2 - lat1) * (Math.PI / 180.0);
  const dLon = (lon2 - lon1) * (Math.PI / 180.0);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180.0)) *
      Math.cos(lat2 * (Math.PI / 180.0)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export function calculatePathSafetyScore(path: { lat: number; lng: number }[], radiusKm: number = 2.5): number {
  if (!path || path.length === 0) return 85;

  let totalPenalty = 0;
  const step = Math.max(1, Math.floor(path.length / 12));

  for (let i = 0; i < path.length; i += step) {
    const pt = path[i];
    for (const spot of HYDERABAD_CRIME_HOTSPOTS) {
      const dist = haversineKm(pt.lat, pt.lng, spot.lat, spot.lng);
      if (dist <= radiusKm) {
        const penalty = spot.rating * (1.0 - dist / radiusKm);
        totalPenalty += penalty;
      }
    }
  }

  const score = Math.round(96 - totalPenalty * 3.2);
  return Math.max(40, Math.min(96, score));
}
