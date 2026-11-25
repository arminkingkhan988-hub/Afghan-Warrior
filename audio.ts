class ProceduralAudioEngine {
  private ctx: AudioContext | null = null;
  private musicGain: GainNode | null = null;
  private sfxGain: GainNode | null = null;
  private envGain: GainNode | null = null;
  private envSource: AudioBufferSourceNode | null = null;
  private musicInterval: number | null = null;

  private musicVol = 0.65;
  private sfxVol = 0.85;
  private envVol = 0.55;

  private ensureContext(): AudioContext | null {
    if (typeof window === 'undefined') return null;
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!AudioCtx) return null;
      this.ctx = new AudioCtx();
      this.musicGain = this.ctx.createGain();
      this.sfxGain = this.ctx.createGain();
      this.envGain = this.ctx.createGain();
      this.musicGain.gain.value = this.musicVol * 0.25;
      this.sfxGain.gain.value = this.sfxVol;
      this.envGain.gain.value = this.envVol * 0.22;
      this.musicGain.connect(this.ctx.destination);
      this.sfxGain.connect(this.ctx.destination);
      this.envGain.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended') {
      void this.ctx.resume();
    }
    return this.ctx;
  }

  public setVolumes(music: number, sfx: number, env: number) {
    this.musicVol = music;
    this.sfxVol = sfx;
    this.envVol = env;
    if (this.musicGain) this.musicGain.gain.value = music * 0.25;
    if (this.sfxGain) this.sfxGain.gain.value = sfx;
    if (this.envGain) this.envGain.gain.value = env * 0.22;
  }

  public playUiClick() {
    const ctx = this.ensureContext();
    if (!ctx || !this.sfxGain) return;
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(780, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(340, ctx.currentTime + 0.05);
    g.gain.setValueAtTime(0.18, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.055);
    osc.connect(g).connect(this.sfxGain);
    osc.start();
    osc.stop(ctx.currentTime + 0.06);
  }

  public playGunshot(weaponId: string) {
    const ctx = this.ensureContext();
    if (!ctx || !this.sfxGain) return;
    const now = ctx.currentTime;
    const dur = weaponId === 'pamir_m24' ? 0.36 : weaponId === 'helmand_12g' ? 0.28 : 0.16;

    const bufferSize = Math.floor(ctx.sampleRate * dur);
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      const env = Math.exp((-i / bufferSize) * 5.2);
      data[i] = (Math.random() * 2 - 1) * env;
    }

    const noise = ctx.createBufferSource();
    noise.buffer = buffer;

    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(weaponId === 'pamir_m24' ? 2400 : 1850, now);
    filter.frequency.exponentialRampToValueAtTime(220, now + dur);

    const g = ctx.createGain();
    g.gain.setValueAtTime(weaponId === 'pamir_m24' ? 0.55 : 0.4, now);
    g.gain.exponentialRampToValueAtTime(0.001, now + dur);

    noise.connect(filter).connect(g).connect(this.sfxGain);
    noise.start(now);

    const punch = ctx.createOscillator();
    const pg = ctx.createGain();
    punch.type = 'sine';
    punch.frequency.setValueAtTime(weaponId === 'helmand_12g' ? 110 : 165, now);
    punch.frequency.exponentialRampToValueAtTime(38, now + 0.09);
    pg.gain.setValueAtTime(0.45, now);
    pg.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
    punch.connect(pg).connect(this.sfxGain);
    punch.start(now);
    punch.stop(now + 0.11);
  }

  public playReload() {
    const ctx = this.ensureContext();
    if (!ctx || !this.sfxGain) return;
    [0, 0.28].forEach((offset, idx) => {
      const osc = ctx.createOscillator();
      const g = ctx.createGain();
      osc.type = 'square';
      osc.frequency.setValueAtTime(idx === 0 ? 520 : 860, ctx.currentTime + offset);
      g.gain.setValueAtTime(0.14, ctx.currentTime + offset);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + offset + 0.07);
      osc.connect(g).connect(this.sfxGain!);
      osc.start(ctx.currentTime + offset);
      osc.stop(ctx.currentTime + offset + 0.08);
    });
  }

  public playHitMarker() {
    const ctx = this.ensureContext();
    if (!ctx || !this.sfxGain) return;
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(1450, ctx.currentTime);
    g.gain.setValueAtTime(0.2, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.06);
    osc.connect(g).connect(this.sfxGain);
    osc.start();
    osc.stop(ctx.currentTime + 0.065);
  }

  public playExplosion() {
    const ctx = this.ensureContext();
    if (!ctx || !this.sfxGain) return;
    const dur = 0.85;
    const bufferSize = Math.floor(ctx.sampleRate * dur);
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.exp((-i / bufferSize) * 4.0);
    }
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(520, ctx.currentTime);
    filter.frequency.exponentialRampToValueAtTime(65, ctx.currentTime + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.75, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
    src.connect(filter).connect(g).connect(this.sfxGain);
    src.start();
  }

  public playFootstep() {
    const ctx = this.ensureContext();
    if (!ctx || !this.sfxGain) return;
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(88 + Math.random() * 18, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(42, ctx.currentTime + 0.07);
    g.gain.setValueAtTime(0.12, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);
    osc.connect(g).connect(this.sfxGain);
    osc.start();
    osc.stop(ctx.currentTime + 0.085);
  }

  public startAmbient(weather: 'clear' | 'dust' | 'rain') {
    this.stopAmbient();
    const ctx = this.ensureContext();
    if (!ctx || !this.envGain) return;
    const dur = 2.5;
    const bufferSize = Math.floor(ctx.sampleRate * dur);
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * (weather === 'rain' ? 0.55 : 0.35);
    }
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    src.loop = true;
    const filter = ctx.createBiquadFilter();
    filter.type = weather === 'rain' ? 'bandpass' : 'lowpass';
    filter.frequency.value = weather === 'rain' ? 1300 : weather === 'dust' ? 420 : 280;
    src.connect(filter).connect(this.envGain);
    src.start();
    this.envSource = src;
  }

  public stopAmbient() {
    if (this.envSource) {
      try {
        this.envSource.stop();
      } catch {
        // already stopped
      }
      this.envSource = null;
    }
  }

  public startMenuPulse() {
    if (this.musicInterval !== null) return;
    const ctx = this.ensureContext();
    if (!ctx || !this.musicGain) return;
    let step = 0;
    const notes = [110, 110, 130.81, 146.83, 110, 164.81, 146.83, 130.81];
    this.musicInterval = window.setInterval(() => {
      if (!this.ctx || !this.musicGain || this.musicVol <= 0.01) return;
      const osc = this.ctx.createOscillator();
      const g = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.value = notes[step % notes.length];
      const f = this.ctx.createBiquadFilter();
      f.type = 'lowpass';
      f.frequency.value = 340;
      g.gain.setValueAtTime(0.18, this.ctx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.65);
      osc.connect(f).connect(g).connect(this.musicGain);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.7);
      step++;
    }, 750);
  }

  public stopMenuPulse() {
    if (this.musicInterval !== null) {
      clearInterval(this.musicInterval);
      this.musicInterval = null;
    }
  }
}

export const gameAudio = new ProceduralAudioEngine();
