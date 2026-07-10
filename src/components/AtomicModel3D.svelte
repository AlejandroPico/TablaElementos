<script lang="ts">
  import { onMount } from 'svelte';
  import type { DataRow, ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';

  export let element: ElementWithLines | null = null;
  export let elementData: ElementDataPayload | null = null;

  interface Particle3D {
    x: number;
    y: number;
    z: number;
    proton: boolean;
  }

  interface ElectronPoint {
    shell: number;
    index: number;
    count: number;
  }

  let canvas: HTMLCanvasElement;
  let frame = 0;
  let paused = false;
  let resizeObserver: ResizeObserver | null = null;
  let themeObserver: MutationObserver | null = null;

  $: protonCount = element?.atomic_number ?? 0;
  $: neutronCount = estimateNeutrons(element, elementData);
  $: shellCounts = distributeElectrons(protonCount);
  $: nucleus = buildNucleus(protonCount, neutronCount);
  $: electrons = buildElectrons(shellCounts);

  function parseNumber(value: unknown): number {
    const match = String(value ?? '')
      .replace(',', '.')
      .match(/-?\d+(?:\.\d+)?/);
    return match ? Number(match[0]) : Number.NaN;
  }

  function normalizedKey(key: string): string {
    return key.toLowerCase().replace(/[^a-z0-9]+/g, '');
  }

  function valueFromRow(row: DataRow, candidates: string[]): string {
    const wanted = new Set(candidates.map(normalizedKey));
    for (const [key, value] of Object.entries(row)) {
      if (wanted.has(normalizedKey(key))) return value;
    }
    return '';
  }

  function estimateNeutrons(
    currentElement: ElementWithLines | null,
    payload: ElementDataPayload | null
  ): number {
    if (!currentElement) return 0;
    const z = currentElement.atomic_number;
    const isotopes = payload?.domains.isotopes?.rows ?? [];

    let bestMass = Number.NaN;
    let bestAbundance = -1;

    for (const row of isotopes) {
      const abundance = parseNumber(
        valueFromRow(row, ['abundance', 'abundance_percent', 'natural_abundance'])
      );
      const massNumber = parseNumber(valueFromRow(row, ['a', 'mass_number', 'massnumber']));
      const neutrons = parseNumber(valueFromRow(row, ['n', 'neutrons']));

      const candidateMass = Number.isFinite(massNumber)
        ? massNumber
        : Number.isFinite(neutrons)
          ? neutrons + z
          : Number.NaN;

      const candidateAbundance = Number.isFinite(abundance) ? abundance : 0;
      if (Number.isFinite(candidateMass) && candidateAbundance >= bestAbundance) {
        bestMass = candidateMass;
        bestAbundance = candidateAbundance;
      }
    }

    if (!Number.isFinite(bestMass)) {
      const atomicRows = payload?.domains.atomic?.rows ?? [];
      const massRow = atomicRows.find((row) => row.property === 'atomic_mass');
      bestMass = parseNumber(massRow?.value);
    }

    if (!Number.isFinite(bestMass)) bestMass = z * 2;
    return Math.max(0, Math.round(bestMass) - z);
  }

  function distributeElectrons(total: number): number[] {
    const capacities = [2, 8, 18, 32, 32, 18, 8];
    const result: number[] = [];
    let remaining = Math.max(0, total);

    for (const capacity of capacities) {
      if (remaining <= 0) break;
      const count = Math.min(capacity, remaining);
      result.push(count);
      remaining -= count;
    }

    return result;
  }

  function buildNucleus(protons: number, neutrons: number): Particle3D[] {
    const total = Math.max(1, protons + neutrons);
    const particles: Particle3D[] = [];
    const golden = Math.PI * (3 - Math.sqrt(5));
    const radius = 20 + Math.cbrt(total) * 5.2;

    for (let index = 0; index < total; index += 1) {
      const fraction = (index + 0.5) / total;
      const radial = Math.cbrt(fraction) * radius;
      const y = 1 - 2 * fraction;
      const ring = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = index * golden;
      const shuffled = (index * 37) % total;

      particles.push({
        x: Math.cos(theta) * ring * radial,
        y: y * radial,
        z: Math.sin(theta) * ring * radial,
        proton: shuffled < protons
      });
    }

    return particles;
  }

  function buildElectrons(shells: number[]): ElectronPoint[] {
    const result: ElectronPoint[] = [];
    shells.forEach((count, shell) => {
      for (let index = 0; index < count; index += 1) {
        result.push({ shell, index, count });
      }
    });
    return result;
  }

  function resizeCanvas(): void {
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const ratio = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.max(1, Math.round(rect.width * ratio));
    canvas.height = Math.max(1, Math.round(rect.height * ratio));
    draw(performance.now());
  }

  function rotatePoint(
    x: number,
    y: number,
    z: number,
    rotationY: number,
    rotationX: number
  ): { x: number; y: number; z: number } {
    const cosY = Math.cos(rotationY);
    const sinY = Math.sin(rotationY);
    const x1 = x * cosY + z * sinY;
    const z1 = -x * sinY + z * cosY;

    const cosX = Math.cos(rotationX);
    const sinX = Math.sin(rotationX);

    return {
      x: x1,
      y: y * cosX - z1 * sinX,
      z: y * sinX + z1 * cosX
    };
  }

  function drawOrbit(
    context: CanvasRenderingContext2D,
    centerX: number,
    centerY: number,
    radius: number,
    tilt: number,
    rotation: number,
    scale: number,
    color: string
  ): void {
    context.save();
    context.translate(centerX, centerY);
    context.rotate(rotation);
    context.scale(1, Math.max(0.18, Math.abs(Math.cos(tilt))));
    context.beginPath();
    context.ellipse(0, 0, radius * scale, radius * scale, 0, 0, Math.PI * 2);
    context.strokeStyle = color;
    context.lineWidth = 1;
    context.stroke();
    context.restore();
  }

  function draw(timestamp: number): void {
    if (!canvas || !element) return;
    const context = canvas.getContext('2d');
    if (!context) return;

    const width = canvas.width;
    const height = canvas.height;
    const ratio = Math.min(2, window.devicePixelRatio || 1);
    const centerX = width / 2;
    const centerY = height / 2;
    const minDimension = Math.min(width, height);
    const scale = minDimension / 430;
    const dark = document.documentElement.dataset.theme !== 'light';

    context.clearRect(0, 0, width, height);

    const glow = context.createRadialGradient(
      centerX,
      centerY,
      0,
      centerX,
      centerY,
      minDimension * 0.46
    );
    glow.addColorStop(0, dark ? 'rgba(116,147,160,.16)' : 'rgba(88,117,128,.12)');
    glow.addColorStop(1, 'rgba(0,0,0,0)');
    context.fillStyle = glow;
    context.fillRect(0, 0, width, height);

    const time = paused ? 0 : timestamp;
    const rotationY = time * 0.00022;
    const rotationX = -0.38 + Math.sin(time * 0.00011) * 0.08;
    const orbitColor = dark ? 'rgba(196,215,223,.22)' : 'rgba(66,88,99,.2)';

    shellCounts.forEach((_, shell) => {
      const radius = 72 + shell * 31;
      const tilt = 0.58 + shell * 0.27;
      const rotation = shell * 0.63;
      drawOrbit(context, centerX, centerY, radius, tilt, rotation, scale, orbitColor);
    });

    const projectedNucleus = nucleus
      .map((particle) => {
        const rotated = rotatePoint(
          particle.x,
          particle.y,
          particle.z,
          rotationY,
          rotationX
        );
        return { ...particle, ...rotated };
      })
      .sort((a, b) => a.z - b.z);

    for (const particle of projectedNucleus) {
      const perspective = 1 + particle.z / 360;
      const x = centerX + particle.x * scale * perspective;
      const y = centerY + particle.y * scale * perspective;
      const radius = Math.max(2.1, (4.5 + perspective * 1.6) * scale);

      const gradient = context.createRadialGradient(
        x - radius * 0.35,
        y - radius * 0.35,
        radius * 0.2,
        x,
        y,
        radius
      );

      if (particle.proton) {
        gradient.addColorStop(0, '#ffd3c6');
        gradient.addColorStop(1, '#a95f59');
      } else {
        gradient.addColorStop(0, '#d6e8ef');
        gradient.addColorStop(1, '#587586');
      }

      context.beginPath();
      context.arc(x, y, radius, 0, Math.PI * 2);
      context.fillStyle = gradient;
      context.fill();
    }

    const electronPoints = electrons
      .map((electron) => {
        const radius = 72 + electron.shell * 31;
        const tilt = 0.58 + electron.shell * 0.27;
        const phase =
          (Math.PI * 2 * electron.index) / Math.max(1, electron.count) +
          time * (0.00072 / Math.sqrt(electron.shell + 1));
        const localX = Math.cos(phase) * radius;
        const localY = Math.sin(phase) * radius * Math.cos(tilt);
        const localZ = Math.sin(phase) * radius * Math.sin(tilt);
        const rotated = rotatePoint(
          localX,
          localY,
          localZ,
          electron.shell * 0.63,
          -0.12
        );
        return { ...electron, ...rotated };
      })
      .sort((a, b) => a.z - b.z);

    for (const electron of electronPoints) {
      const perspective = 1 + electron.z / 520;
      const x = centerX + electron.x * scale * perspective;
      const y = centerY + electron.y * scale * perspective;
      const radius = Math.max(2.3, 3.8 * scale * perspective);

      context.beginPath();
      context.arc(x, y, radius * 2.3, 0, Math.PI * 2);
      context.fillStyle = dark ? 'rgba(122,220,255,.12)' : 'rgba(42,139,179,.1)';
      context.fill();

      context.beginPath();
      context.arc(x, y, radius, 0, Math.PI * 2);
      context.fillStyle = dark ? '#9ce5ff' : '#246f8e';
      context.fill();
    }

    context.fillStyle = dark ? 'rgba(235,242,246,.82)' : 'rgba(39,52,61,.82)';
    context.font = `${Math.max(11, 13 * ratio)}px system-ui`;
    context.textAlign = 'left';
    context.fillText(`${element.symbol} · Z=${protonCount}`, 18 * ratio, 26 * ratio);
  }

  function animationLoop(timestamp: number): void {
    if (!paused) draw(timestamp);
    frame = requestAnimationFrame(animationLoop);
  }

  function toggleAnimation(): void {
    paused = !paused;
    draw(performance.now());
  }

  onMount(() => {
    resizeObserver = new ResizeObserver(resizeCanvas);
    resizeObserver.observe(canvas);

    themeObserver = new MutationObserver(() => draw(performance.now()));
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    });

    resizeCanvas();
    frame = requestAnimationFrame(animationLoop);

    return () => {
      cancelAnimationFrame(frame);
      resizeObserver?.disconnect();
      themeObserver?.disconnect();
    };
  });
</script>

<section class="atom-model-panel" aria-label="Modelo atómico tridimensional">
  <header>
    <div>
      <p class="eyebrow">Representación interactiva</p>
      <h3>Modelo atómico 3D</h3>
      <p>
        Núcleo con protones y neutrones, junto con una distribución electrónica
        animada por capas.
      </p>
    </div>
    <button type="button" on:click={toggleAnimation}>
      {paused ? 'Reanudar' : 'Pausar'}
    </button>
  </header>

  <div class="atom-stage">
    <canvas
      bind:this={canvas}
      aria-label={`Modelo atómico animado de ${element?.name_es ?? 'elemento'}`}
    ></canvas>
  </div>

  <div class="atom-counters">
    <article><span>Protones</span><strong>{protonCount}</strong></article>
    <article><span>Neutrones estimados</span><strong>{neutronCount}</strong></article>
    <article><span>Electrones</span><strong>{protonCount}</strong></article>
    <article>
      <span>Capas</span>
      <strong>{shellCounts.join(' · ') || '—'}</strong>
    </article>
  </div>

  <p class="atom-note">
    Los neutrones se estiman con el isótopo natural más abundante disponible; si
    falta, se usa la masa atómica redondeada. La visualización es didáctica y no
    representa órbitas cuánticas literales.
  </p>
</section>

<style>
  .atom-model-panel {
    display: grid;
    gap: 14px;
    min-height: 100%;
  }

  .atom-model-panel > header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
    padding: 14px 16px;
    border: 1px solid var(--line);
    background: var(--panel);
  }

  .atom-model-panel h3,
  .atom-model-panel p {
    margin: 0;
  }

  .atom-model-panel header p:last-child {
    margin-top: 5px;
    color: var(--text-soft);
  }

  .atom-model-panel button {
    min-width: 96px;
    padding: 8px 12px;
    border: 1px solid var(--line-strong);
    border-radius: 0;
    color: var(--app-ink);
    background: var(--surface-soft);
  }

  .atom-stage {
    position: relative;
    min-height: 430px;
    border: 1px solid var(--line);
    overflow: hidden;
    background:
      linear-gradient(var(--surface-soft) 1px, transparent 1px),
      linear-gradient(90deg, var(--surface-soft) 1px, transparent 1px),
      var(--panel-strong);
    background-size: 26px 26px;
  }

  canvas {
    display: block;
    width: 100%;
    height: 100%;
    min-height: 430px;
  }

  .atom-counters {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1px;
    border: 1px solid var(--line);
    background: var(--line);
  }

  .atom-counters article {
    min-width: 0;
    padding: 12px;
    background: var(--panel);
  }

  .atom-counters span,
  .atom-counters strong {
    display: block;
  }

  .atom-counters span {
    color: var(--text-soft);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .atom-counters strong {
    margin-top: 5px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .atom-note {
    padding: 10px 12px;
    border-left: 3px solid var(--accent);
    color: var(--text-soft);
    background: var(--surface-soft);
  }

  @media (max-width: 760px) {
    .atom-model-panel > header {
      display: grid;
    }

    .atom-stage,
    canvas {
      min-height: 340px;
    }

    .atom-counters {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
</style>
