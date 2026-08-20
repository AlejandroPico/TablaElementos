export type ThemeMode = 'auto' | 'morning' | 'afternoon' | 'night';
export type ThemePeriod = Exclude<ThemeMode, 'auto'>;
export type BaseTheme = 'light' | 'dark';

export interface ThemeCoordinates {
  latitude: number;
  longitude: number;
}

export interface SolarThemeState {
  period: ThemePeriod;
  elevationDegrees: number | null;
  beforeSolarNoon: boolean | null;
  source: 'solar' | 'local-time';
}

const RAD = Math.PI / 180;
const DAY_MS = 86_400_000;
const J2000 = 2_451_545;
const CIVIL_TWILIGHT_DEGREES = -6;

function normalizeRadians(value: number): number {
  const fullTurn = Math.PI * 2;
  return ((value + Math.PI) % fullTurn + fullTurn) % fullTurn - Math.PI;
}

function solarPosition(date: Date, coordinates: ThemeCoordinates): {
  elevationDegrees: number;
  beforeSolarNoon: boolean;
} {
  const julianDay = date.getTime() / DAY_MS - 0.5 + 2_440_588;
  const daysSinceJ2000 = julianDay - J2000;
  const meanAnomaly = RAD * (357.5291 + 0.98560028 * daysSinceJ2000);
  const eclipticLongitude =
    meanAnomaly +
    RAD * 1.9148 * Math.sin(meanAnomaly) +
    RAD * 0.02 * Math.sin(2 * meanAnomaly) +
    RAD * 0.0003 * Math.sin(3 * meanAnomaly) +
    RAD * 102.9372 +
    Math.PI;
  const obliquity = RAD * 23.4397;
  const rightAscension = Math.atan2(
    Math.sin(eclipticLongitude) * Math.cos(obliquity),
    Math.cos(eclipticLongitude)
  );
  const declination = Math.asin(Math.sin(eclipticLongitude) * Math.sin(obliquity));
  const siderealTime = RAD * (280.16 + 360.9856235 * daysSinceJ2000) + coordinates.longitude * RAD;
  const hourAngle = normalizeRadians(siderealTime - rightAscension);
  const latitude = coordinates.latitude * RAD;
  const altitude = Math.asin(
    Math.sin(latitude) * Math.sin(declination) +
      Math.cos(latitude) * Math.cos(declination) * Math.cos(hourAngle)
  );

  return {
    elevationDegrees: altitude / RAD,
    beforeSolarNoon: hourAngle < 0
  };
}

function fallbackPeriod(date: Date): ThemePeriod {
  const localHour = date.getHours() + date.getMinutes() / 60;
  if (localHour < 6.5 || localHour >= 20.5) return 'night';
  return localHour < 13 ? 'morning' : 'afternoon';
}

export function resolveAutomaticTheme(
  date: Date,
  coordinates: ThemeCoordinates | null
): SolarThemeState {
  if (!coordinates) {
    return {
      period: fallbackPeriod(date),
      elevationDegrees: null,
      beforeSolarNoon: null,
      source: 'local-time'
    };
  }

  const position = solarPosition(date, coordinates);
  const period =
    position.elevationDegrees <= CIVIL_TWILIGHT_DEGREES
      ? 'night'
      : position.beforeSolarNoon
        ? 'morning'
        : 'afternoon';

  return { ...position, period, source: 'solar' };
}

export function baseThemeFor(period: ThemePeriod): BaseTheme {
  return period === 'night' ? 'dark' : 'light';
}

export function migrateStoredTheme(value: string | null): ThemeMode {
  if (value === 'auto' || value === 'morning' || value === 'afternoon' || value === 'night') return value;
  if (value === 'light') return 'morning';
  if (value === 'dark') return 'night';
  return 'auto';
}
