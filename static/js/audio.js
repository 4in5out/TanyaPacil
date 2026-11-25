/**
 * PakChillAudio — Undertale-style talking voice blips + looping chill classroom BGM.
 * Works 100% out-of-the-box via Web Audio API, and automatically upgrades to custom
 * static/assets/audio/bgm.* or voice_blip.* files if present.
 */
class PakChillAudio {
  constructor(customAssets = {}) {
    this.ctx = null;
    this.sfxEnabled = true;
    this.bgmEnabled = false;
    this.customBgmUrl = customAssets.bgm_audio || '';
    this.customVoiceUrl = customAssets.voice_audio || '';

    this.bgmAudioEl = null;
    this.voiceBuffer = null;
    this.synthTimer = null;
    this.chordIndex = 0;
    this.lastBlipTime = 0;

    if (this.customBgmUrl) {
      this.bgmAudioEl = new Audio(this.customBgmUrl);
      this.bgmAudioEl.loop = true;
      this.bgmAudioEl.volume = 0.26;
    }
  }

  _ensureContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    if (this.customVoiceUrl && this.ctx && !this.voiceBuffer) {
      fetch(this.customVoiceUrl)
        .then((r) => r.arrayBuffer())
        .then((buf) => this.ctx.decodeAudioData(buf))
        .then((decoded) => { this.voiceBuffer = decoded; })
        .catch(() => {});
    }
  }

  /**
   * Undertale-style character dialogue blip for Pak Chill.
   * Warm, chill low-mid panda tone with subtle pitch variation.
   */
  playVoiceBlip(char = 'a') {
    if (!this.sfxEnabled) return;
    if (!char || /[\s.,!?;:\-–—()[\]{}'"`\n]/.test(char)) return;

    const nowMs = performance.now();
    if (nowMs - this.lastBlipTime < 46) return;
    this.lastBlipTime = nowMs;

    this._ensureContext();
    if (!this.ctx) return;

    const now = this.ctx.currentTime;

    // If a custom voice_blip file was provided, play it with tiny pitch variation
    if (this.voiceBuffer) {
      const src = this.ctx.createBufferSource();
      const gain = this.ctx.createGain();
      src.buffer = this.voiceBuffer;
      src.playbackRate.value = 0.94 + Math.random() * 0.12;
      gain.gain.value = 0.22;
      src.connect(gain);
      gain.connect(this.ctx.destination);
      src.start(now);
      return;
    }

    // Web Audio Undertale-inspired chill panda blip
    const osc = this.ctx.createOscillator();
    const filter = this.ctx.createBiquadFilter();
    const gain = this.ctx.createGain();

    // Base frequency around 195-240Hz (warm & chill, never harsh)
    const charOffset = (char.charCodeAt(0) % 7) * 6;
    const freq = 195 + charOffset + (Math.random() * 14 - 7);

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(freq, now);
    osc.frequency.exponentialRampToValueAtTime(freq * 0.92, now + 0.048);

    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(950, now);

    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.linearRampToValueAtTime(0.11, now + 0.008);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.052);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(this.ctx.destination);

    osc.start(now);
    osc.stop(now + 0.056);
  }

  toggleSfx() {
    this.sfxEnabled = !this.sfxEnabled;
    if (this.sfxEnabled) {
      this._ensureContext();
      this.playVoiceBlip('o');
    }
    return this.sfxEnabled;
  }

  toggleBgm() {
    this.bgmEnabled = !this.bgmEnabled;
    if (this.bgmEnabled) {
      this._startBgm();
    } else {
      this._stopBgm();
    }
    return this.bgmEnabled;
  }

  _startBgm() {
    this._ensureContext();
    if (this.bgmAudioEl) {
      this.bgmAudioEl.play().catch(() => {});
      return;
    }
    if (this.synthTimer) return;

    // Cozy lo-fi major-7th classroom chord loop (Fmaj7 -> Em7 -> Dm7 -> Cmaj7)
    const chords = [
      [174.61, 220.0, 261.63, 329.63],
      [164.81, 196.0, 246.94, 293.66],
      [146.83, 174.61, 220.0, 261.63],
      [130.81, 164.81, 196.0, 246.94],
    ];

    const playChord = () => {
      if (!this.bgmEnabled || !this.ctx) return;
      const now = this.ctx.currentTime;
      const notes = chords[this.chordIndex % chords.length];
      this.chordIndex += 1;

      notes.forEach((freq, idx) => {
        const osc = this.ctx.createOscillator();
        const filter = this.ctx.createBiquadFilter();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.06);

        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(700, now);

        gain.gain.setValueAtTime(0.0001, now + idx * 0.06);
        gain.gain.linearRampToValueAtTime(0.028, now + idx * 0.06 + 0.35);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 3.4);

        osc.connect(filter);
        filter.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now + idx * 0.06);
        osc.stop(now + 3.5);
      });
    };

    playChord();
    this.synthTimer = setInterval(playChord, 3400);
  }

  _stopBgm() {
    if (this.bgmAudioEl) {
      this.bgmAudioEl.pause();
    }
    if (this.synthTimer) {
      clearInterval(this.synthTimer);
      this.synthTimer = null;
    }
  }
}

window.PakChillAudio = PakChillAudio;
