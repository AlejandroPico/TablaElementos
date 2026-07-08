export const VISIBLE_MIN_NM = 380;
export const VISIBLE_MAX_NM = 750;

export function isVisibleWavelength(wavelengthNm: number): boolean {
  return wavelengthNm >= VISIBLE_MIN_NM && wavelengthNm <= VISIBLE_MAX_NM;
}

export function wavelengthRegion(wavelengthNm: number): 'UV' | 'Visible' | 'IR' {
  if (wavelengthNm < VISIBLE_MIN_NM) return 'UV';
  if (wavelengthNm > VISIBLE_MAX_NM) return 'IR';
  return 'Visible';
}

export function formatNm(value: number): string {
  return `${value.toFixed(2)} nm`;
}

export function formatEv(value: number): string {
  return `${value.toFixed(2)} eV`;
}
