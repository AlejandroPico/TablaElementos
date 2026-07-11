<script lang="ts">
  import { onMount } from 'svelte';
  import type { ElementDataPayload, ElementWithLines } from '../lib/atomicTypes';

  export let element: ElementWithLines | null = null;
  export let elementData: ElementDataPayload | null = null;

  let canvas: HTMLCanvasElement;
  let frame = 0;
  let paused = false;
  let observer: ResizeObserver | null = null;

  $: protons = element?.atomic_number ?? 0;
  $: neutrons = estimateNeutrons();
  $: shells = distributeElectrons(protons);

  function numberFrom(value: unknown): number {
    const match = String(value ?? '').replace(',', '.').match(/-?\d+(?:\.\d+)?/);
    return match ? Number(match[0]) : Number.NaN;
  }

  function propertyValue(domainId: string, property: string): string {
    const row = elementData?.domains[domainId]?.rows.find((item) => item.property === property);
    return row?.value ?? '';
  }

  function estimateNeutrons(): number {
    const z = element?.atomic_number ?? 0;
    const isotopeRows = elementData?.domains.isotopes?.rows ?? [];
    let selectedMass = Number.NaN;
    let bestAbundance = -1;

    for (const row of isotopeRows) {
      const abundance = numberFrom(row.abundance ?? row.abundance_percent ?? row.natural_abundance);
      const mass = numberFrom(row.a ?? row.mass_number ?? row.massnumber);
      const neutronCount = numberFrom(row.n ?? row.neutrons);
      const candidateMass = Number.isFinite(mass) ? mass : Number.isFinite(neutronCount) ? neutronCount + z : Number.NaN;
      const score = Number.isFinite(abundance) ? abundance : 0;
      if (Number.isFinite(candidateMass) && score >= bestAbundance) {
        selectedMass = candidateMass;
        bestAbundance = score;
      }
    }

    if (!Number.isFinite(selectedMass)) selectedMass = numberFrom(propertyValue('atomic', 'atomic_mass'));
    if (!Number.isFinite(selectedMass)) selectedMass = z * 2;
    return Math.max(0, Math.round(selectedMass) - z);
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

  function resize(): void {
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const ratio = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.max(1, Math.round(rect.width * ratio));
    canvas.height = Math.max(1, Math.round(rect.height * ratio));
    draw(performance.now());
  }

  function draw(timestamp: number): void {
    if (!canvas || !element) return;
    const context = canvas.getContext('2d');
    if (!context) return;

    const width = canvas.width;
    const height = canvas.height;
    const ratio = Math.min(2, window.devicePixelRatio || 1);
    const cx = width / 2;
    const cy = height / 2;
    const scale = Math.min(width, height) / 520;
    const time = paused ? 0 : timestamp;
    const dark = document.documentElement.dataset.theme !== 'light';

    context.clearRect(0, 0, width, height);
    const glow = context.createRadialGradient(cx, cy, 0, cx, cy, Math.min(width, height) * 0.46);
    glow.addColorStop(0, dark ? 'rgba(110,150,170,.16)' : 'rgba(70,105,120,.12)');
    glow.addColorStop(1, 'rgba(0,0,0,0)');
    context.fillStyle = glow;
    context.fillRect(0, 0, width, height);

    shells.forEach((_, shell) => {
      const radius = (92 + shell * 38) * scale;
      context.save();
      context.translate(cx, cy);
      context.rotate(shell * 0.47 + 0.12);
      context.scale(1, 0.42 + (shell % 3) * 0.08);
      context.beginPath();
      context.ellipse(0, 0, radius, radius, 0, 0, Math.PI * 2);
      context.strokeStyle = dark ? 'rgba(205,225,235,.2)' : 'rgba(46,69,82,.2)';
      context.lineWidth = Math.max(1, ratio * 0.7);
      context.stroke();
      context.restore();
    });

    const nucleons = Math.max(1, protons + neutrons);
    const nucleusRadius = (22 + Math.cbrt(nucleons) * 5.6) * scale;
    const golden = Math.PI * (3 - Math.sqrt(5));
    const particles: Array<{x:number;y:number;z:number;proton:boolean}> = [];

    for (let index = 0; index < nucleons; index += 1) {
      const fraction = (index + 0.5) / nucleons;
      const radius = Math.cbrt(fraction) * nucleusRadius;
      const yBase = 1 - 2 * fraction;
      const ring = Math.sqrt(Math.max(0, 1 - yBase * yBase));
      const angle = index * golden + time * 0.00018;
      particles.push({
        x: Math.cos(angle) * ring * radius,
        y: yBase * radius,
        z: Math.sin(angle) * ring * radius,
        proton: ((index * 37) % nucleons) < protons
      });
    }

    particles.sort((a, b) => a.z - b.z);
    for (const particle of particles) {
      const perspective = 1 + particle.z / Math.max(180, nucleusRadius * 6);
      const x = cx + particle.x * perspective;
      const y = cy + particle.y * perspective;
      const radius = Math.max(2.2, 5.4 * scale * perspective);
      context.beginPath();
      context.arc(x, y, radius, 0, Math.PI * 2);
      context.fillStyle = particle.proton ? '#b86d66' : '#617f90';
      context.fill();
      context.strokeStyle = particle.proton ? '#efb0a7' : '#bdd5df';
      context.lineWidth = Math.max(0.7, ratio * 0.55);
      context.stroke();
    }

    shells.forEach((count, shell) => {
      const orbit = (92 + shell * 38) * scale;
      for (let index = 0; index < count; index += 1) {
        const phase = (Math.PI * 2 * index) / Math.max(1, count) + time * (0.00068 / Math.sqrt(shell + 1));
        const tilt = 0.47 + (shell % 3) * 0.08;
        const x0 = Math.cos(phase) * orbit;
        const y0 = Math.sin(phase) * orbit * tilt;
        const rotation = shell * 0.47 + 0.12;
        const x = cx + x0 * Math.cos(rotation) - y0 * Math.sin(rotation);
        const y = cy + x0 * Math.sin(rotation) + y0 * Math.cos(rotation);
        context.beginPath();
        context.arc(x, y, Math.max(2.4, 3.8 * scale), 0, Math.PI * 2);
        context.fillStyle = dark ? '#9de7ff' : '#236e8c';
        context.fill();
      }
    });
  }

  function loop(timestamp: number): void {
    if (!paused) draw(timestamp);
    frame = requestAnimationFrame(loop);
  }

  function toggle(): void {
    paused = !paused;
    draw(performance.now());
  }

  onMount(() => {
    observer = new ResizeObserver(resize);
    observer.observe(canvas);
    resize();
    frame = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(frame);
      observer?.disconnect();
    };
  });
</script>

<button
  class:paused
  class="atomic-stage"
  type="button"
  on:click={toggle}
  aria-label={`${paused ? 'Reanudar' : 'Pausar'} modelo atómico de ${element?.name_es ?? 'elemento'}`}
>
  <canvas bind:this={canvas}></canvas>
  <span class="atomic-overlay">
    <b>{element?.symbol}</b>
    <span>{protons} p⁺ · {neutrons} n⁰ · {protons} e⁻</span>
    <small>Capas {shells.join(' · ') || '—'} · Clic para {paused ? 'reanudar' : 'pausar'}</small>
  </span>
  {#if paused}<span class="atomic-paused-state">Pausado</span>{/if}
</button>
