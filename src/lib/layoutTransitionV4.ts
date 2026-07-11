export type PeriodicLayout = 'short' | 'long';
type VisualStage = 'short' | 'opening' | 'long';

interface Position {
  column: number;
  row: number;
}

interface SlotRecord {
  slot: HTMLElement;
  atomicNumber: number;
  group: number;
  innerSeries: boolean;
  seriesIndex: number;
}

interface LayoutTransitionOptions {
  source: PeriodicLayout;
  target: PeriodicLayout;
  fitToViewport?: (animated: boolean, stage: VisualStage) => Promise<void> | void;
}

const SHORT_COLUMN_OFFSET = 7;

function nextFrame(): Promise<void> {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

function elementPosition(atomicNumber: number, group: number, stage: VisualStage): Position {
  if (stage === 'short') {
    if (atomicNumber >= 57 && atomicNumber <= 71) {
      return { column: atomicNumber - 54 + SHORT_COLUMN_OFFSET, row: 8 };
    }
    if (atomicNumber >= 89 && atomicNumber <= 103) {
      return { column: atomicNumber - 86 + SHORT_COLUMN_OFFSET, row: 9 };
    }
    return { column: Math.max(1, group) + SHORT_COLUMN_OFFSET, row: atomicNumber === 2 ? 1 : 0 };
  }

  if (stage === 'opening') {
    if (atomicNumber >= 57 && atomicNumber <= 71) return { column: atomicNumber - 54, row: 8 };
    if (atomicNumber >= 89 && atomicNumber <= 103) return { column: atomicNumber - 86, row: 9 };
    return { column: Math.max(1, group) <= 2 ? Math.max(1, group) : Math.max(1, group) + 14, row: 0 };
  }

  if (atomicNumber >= 57 && atomicNumber <= 71) return { column: atomicNumber - 54, row: 6 };
  if (atomicNumber >= 89 && atomicNumber <= 103) return { column: atomicNumber - 86, row: 7 };
  return { column: Math.max(1, group) <= 2 ? Math.max(1, group) : Math.max(1, group) + 14, row: 0 };
}

function correctRow(position: Position, article: HTMLElement): Position {
  if (position.row !== 0) return position;
  const atomicNumber = Number(article.dataset.atomicNumber ?? 0);
  const period = Number(article.dataset.period ?? article.getAttribute('data-period') ?? 0);
  if (period > 0) return { ...position, row: period };

  const inferredPeriod = atomicNumber <= 2
    ? 1
    : atomicNumber <= 10
      ? 2
      : atomicNumber <= 18
        ? 3
        : atomicNumber <= 36
          ? 4
          : atomicNumber <= 54
            ? 5
            : atomicNumber <= 86
              ? 6
              : 7;
  return { ...position, row: inferredPeriod };
}

function positionFor(record: SlotRecord, stage: VisualStage): Position {
  const article = record.slot.querySelector<HTMLElement>('.element-cell')!;
  return correctRow(elementPosition(record.atomicNumber, record.group, stage), article);
}

function placeholderPosition(index: number, stage: VisualStage): Position {
  return {
    column: stage === 'short' ? 3 + SHORT_COLUMN_OFFSET : 3,
    row: index === 0 ? 6 : 7
  };
}

function transformFor(position: Position, step: number): string {
  const x = (position.column - 1) * step;
  const y = (position.row - 1) * step;
  return `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0)`;
}

function collectSlots(grid: HTMLElement): SlotRecord[] {
  return Array.from(grid.querySelectorAll<HTMLElement>(':scope > .element-slot')).flatMap((slot) => {
    const article = slot.querySelector<HTMLElement>('.element-cell[data-atomic-number]');
    if (!article) return [];
    const atomicNumber = Number(article.dataset.atomicNumber ?? 0);
    const group = Number(article.dataset.group ?? 0);
    const innerSeries = (atomicNumber >= 57 && atomicNumber <= 71) || (atomicNumber >= 89 && atomicNumber <= 103);
    const seriesIndex = atomicNumber >= 89 ? atomicNumber - 89 : atomicNumber - 57;
    return [{ slot, atomicNumber, group, innerSeries, seriesIndex }];
  });
}

function transitionDelay(record: SlotRecord, stage: 'spread' | 'series' | 'collapse'): number {
  if (stage === 'series') return record.innerSeries ? Math.max(0, record.seriesIndex) * 14 : 0;
  if (record.innerSeries) return 40;
  if (record.group <= 2) return (2 - Math.max(1, record.group)) * 18;
  return Math.min(150, Math.max(0, record.group - 3) * 9);
}

async function animateSlots(
  records: SlotRecord[],
  stage: VisualStage,
  step: number,
  kind: 'spread' | 'series' | 'collapse',
  onlySeries = false
): Promise<void> {
  const animations: Animation[] = [];

  for (const record of records) {
    if (onlySeries && !record.innerSeries) continue;
    const start = getComputedStyle(record.slot).transform;
    const end = transformFor(positionFor(record, stage), step);
    const duration = kind === 'series' && record.innerSeries ? 860 : 760;
    const delay = transitionDelay(record, kind);

    const animation = record.slot.animate(
      [
        { transform: start === 'none' ? record.slot.style.transform : start },
        { transform: end }
      ],
      {
        duration,
        delay,
        easing: kind === 'series'
          ? 'cubic-bezier(0.18, 0.82, 0.2, 1)'
          : 'cubic-bezier(0.22, 1, 0.36, 1)',
        fill: 'both'
      }
    );

    animations.push(animation);
    animation.finished
      .catch(() => undefined)
      .then(() => {
        record.slot.style.transform = end;
        animation.cancel();
      });
  }

  await Promise.allSettled(animations.map((animation) => animation.finished));
}

function setSlotsImmediately(records: SlotRecord[], stage: VisualStage, step: number): void {
  records.forEach((record) => {
    record.slot.getAnimations().forEach((animation) => animation.cancel());
    record.slot.style.transform = transformFor(positionFor(record, stage), step);
  });
}

function placeholderSlots(grid: HTMLElement): HTMLElement[] {
  return Array.from(grid.querySelectorAll<HTMLElement>(':scope > .series-slot'));
}

function positionPlaceholders(grid: HTMLElement, stage: VisualStage, step: number): void {
  placeholderSlots(grid).forEach((slot, index) => {
    slot.getAnimations().forEach((animation) => animation.cancel());
    slot.style.transform = transformFor(placeholderPosition(index, stage), step);
  });
}

async function fadePlaceholders(grid: HTMLElement, visible: boolean): Promise<void> {
  const slots = placeholderSlots(grid);
  if (visible) {
    grid.classList.remove('external-layout-long');
    slots.forEach((slot) => {
      slot.style.visibility = 'visible';
      slot.style.pointerEvents = 'auto';
    });
  }

  const animations = slots.map((slot, index) => slot.animate(
    [{ opacity: visible ? 0 : Number(getComputedStyle(slot).opacity || 1) }, { opacity: visible ? 1 : 0 }],
    {
      duration: 260,
      delay: index * 35,
      easing: 'ease-out',
      fill: 'both'
    }
  ));

  await Promise.allSettled(animations.map((animation) => animation.finished));
  slots.forEach((slot) => {
    slot.style.opacity = visible ? '1' : '0';
    slot.getAnimations().forEach((animation) => animation.cancel());
    if (!visible) {
      slot.style.visibility = 'hidden';
      slot.style.pointerEvents = 'none';
    }
  });

  if (!visible) grid.classList.add('external-layout-long');
}

export async function animatePeriodicLayout(options: LayoutTransitionOptions): Promise<void> {
  const grid = document.querySelector<HTMLElement>('.absolute-periodic-grid');
  const viewport = document.querySelector<HTMLElement>('.periodic-viewport');
  const cellProbe = document.querySelector<HTMLElement>('.layout-cell-probe');
  const gapProbe = document.querySelector<HTMLElement>('.layout-gap-probe');

  if (!grid || !viewport || !cellProbe || !gapProbe) {
    throw new Error('No se encontró la geometría activa de la tabla periódica.');
  }

  const records = collectSlots(grid);
  if (records.length !== 118) {
    throw new Error(`Se esperaban 118 fichas animables y se encontraron ${records.length}.`);
  }

  const step = cellProbe.offsetWidth + gapProbe.offsetWidth;
  if (step <= 0) throw new Error('El tamaño de la celda no está disponible.');

  const targetStage: VisualStage = options.target === 'long' ? 'long' : 'short';
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

  grid.classList.add('external-layout-animating');
  viewport.classList.add('external-layout-animating');

  try {
    if (reducedMotion) {
      setSlotsImmediately(records, targetStage, step);
      positionPlaceholders(grid, targetStage, step);
      await fadePlaceholders(grid, options.target === 'short');
      await Promise.resolve(options.fitToViewport?.(false, targetStage));
      return;
    }

    if (options.source === 'short' && options.target === 'long') {
      await Promise.resolve(options.fitToViewport?.(true, 'opening'));
      await nextFrame();
      await animateSlots(records, 'opening', step, 'spread');
      await fadePlaceholders(grid, false);
      positionPlaceholders(grid, 'opening', step);
      await animateSlots(records, 'long', step, 'series', true);
      await Promise.resolve(options.fitToViewport?.(true, 'long'));
    } else {
      positionPlaceholders(grid, 'opening', step);
      await Promise.resolve(options.fitToViewport?.(true, 'opening'));
      await nextFrame();
      await animateSlots(records, 'opening', step, 'series', true);
      await animateSlots(records, 'short', step, 'collapse');
      positionPlaceholders(grid, 'short', step);
      await fadePlaceholders(grid, true);
      await Promise.resolve(options.fitToViewport?.(true, 'short'));
    }
  } catch (error) {
    console.warn('[TablaElementos] La animación explícita falló; se aplicará el diseño final.', error);
    setSlotsImmediately(records, targetStage, step);
    positionPlaceholders(grid, targetStage, step);
    await fadePlaceholders(grid, options.target === 'short');
    await Promise.resolve(options.fitToViewport?.(false, targetStage));
    throw error;
  } finally {
    grid.classList.remove('external-layout-animating');
    viewport.classList.remove('external-layout-animating');
  }
}
