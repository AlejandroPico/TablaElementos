export const GUIDE_OPEN_EVENT = 'tabla-elementos:open-guide';

export interface GuideOpenDetail {
  topic: string;
}

export function openScientificGuide(topic = 'vision'): void {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent<GuideOpenDetail>(GUIDE_OPEN_EVENT, {
    detail: { topic }
  }));
}
