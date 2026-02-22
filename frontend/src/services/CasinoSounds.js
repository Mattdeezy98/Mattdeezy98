// Casino Sound Effects Service
// Uses Web Audio API for realistic casino sounds

class CasinoSoundService {
  constructor() {
    this.audioContext = null;
    this.sounds = {};
    this.enabled = true;
    this.volume = 0.5;
    this.initialized = false;
  }

  async init() {
    if (this.initialized) return;
    
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      
      // Create oscillator-based sounds (no external files needed)
      this.sounds = {
        spin: () => this.playSpinSound(),
        win: () => this.playWinSound(),
        bigWin: () => this.playBigWinSound(),
        jackpot: () => this.playJackpotSound(),
        click: () => this.playClickSound(),
        deal: () => this.playDealSound(),
        flip: () => this.playFlipSound(),
        chip: () => this.playChipSound(),
        roulette: () => this.playRouletteSound(),
        ball: () => this.playBallSound(),
        bonus: () => this.playBonusSound(),
        coin: () => this.playCoinSound(),
      };
      
      this.initialized = true;
    } catch (e) {
      console.warn("Audio not supported:", e);
    }
  }

  setEnabled(enabled) {
    this.enabled = enabled;
    localStorage.setItem('casino_sound_enabled', enabled);
  }

  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    localStorage.setItem('casino_sound_volume', this.volume);
  }

  loadSettings() {
    const enabled = localStorage.getItem('casino_sound_enabled');
    const volume = localStorage.getItem('casino_sound_volume');
    if (enabled !== null) this.enabled = enabled === 'true';
    if (volume !== null) this.volume = parseFloat(volume);
  }

  play(soundName) {
    if (!this.enabled || !this.initialized) return;
    
    try {
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }
      
      if (this.sounds[soundName]) {
        this.sounds[soundName]();
      }
    } catch (e) {
      console.warn("Sound play error:", e);
    }
  }

  // Slot machine spinning sound
  playSpinSound() {
    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();
    
    oscillator.type = 'square';
    oscillator.frequency.setValueAtTime(200, this.audioContext.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(800, this.audioContext.currentTime + 0.1);
    
    gainNode.gain.setValueAtTime(this.volume * 0.1, this.audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);
    
    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);
    
    oscillator.start();
    oscillator.stop(this.audioContext.currentTime + 0.3);
  }

  // Win sound - ascending tones
  playWinSound() {
    const notes = [400, 500, 600, 800];
    notes.forEach((freq, i) => {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      
      osc.type = 'sine';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(this.volume * 0.2, this.audioContext.currentTime + i * 0.1);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + i * 0.1 + 0.2);
      
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      
      osc.start(this.audioContext.currentTime + i * 0.1);
      osc.stop(this.audioContext.currentTime + i * 0.1 + 0.2);
    });
  }

  // Big win - fanfare
  playBigWinSound() {
    const notes = [523, 659, 784, 1047, 784, 659, 523];
    notes.forEach((freq, i) => {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      
      osc.type = 'triangle';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(this.volume * 0.3, this.audioContext.currentTime + i * 0.15);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + i * 0.15 + 0.3);
      
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      
      osc.start(this.audioContext.currentTime + i * 0.15);
      osc.stop(this.audioContext.currentTime + i * 0.15 + 0.3);
    });
  }

  // Jackpot - epic fanfare
  playJackpotSound() {
    for (let i = 0; i < 20; i++) {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      
      osc.type = i % 2 === 0 ? 'sine' : 'triangle';
      osc.frequency.value = 200 + i * 100 + Math.random() * 100;
      gain.gain.setValueAtTime(this.volume * 0.15, this.audioContext.currentTime + i * 0.05);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + i * 0.05 + 0.5);
      
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      
      osc.start(this.audioContext.currentTime + i * 0.05);
      osc.stop(this.audioContext.currentTime + i * 0.05 + 0.5);
    }
  }

  // Click sound
  playClickSound() {
    const osc = this.audioContext.createOscillator();
    const gain = this.audioContext.createGain();
    
    osc.type = 'sine';
    osc.frequency.value = 1000;
    gain.gain.setValueAtTime(this.volume * 0.1, this.audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.05);
    
    osc.connect(gain);
    gain.connect(this.audioContext.destination);
    
    osc.start();
    osc.stop(this.audioContext.currentTime + 0.05);
  }

  // Card deal sound
  playDealSound() {
    const noise = this.createNoiseBuffer(0.1);
    const source = this.audioContext.createBufferSource();
    const gain = this.audioContext.createGain();
    const filter = this.audioContext.createBiquadFilter();
    
    source.buffer = noise;
    filter.type = 'highpass';
    filter.frequency.value = 2000;
    gain.gain.setValueAtTime(this.volume * 0.2, this.audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.1);
    
    source.connect(filter);
    filter.connect(gain);
    gain.connect(this.audioContext.destination);
    
    source.start();
  }

  // Card flip sound
  playFlipSound() {
    const osc = this.audioContext.createOscillator();
    const gain = this.audioContext.createGain();
    
    osc.type = 'sine';
    osc.frequency.setValueAtTime(800, this.audioContext.currentTime);
    osc.frequency.exponentialRampToValueAtTime(400, this.audioContext.currentTime + 0.1);
    gain.gain.setValueAtTime(this.volume * 0.1, this.audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.1);
    
    osc.connect(gain);
    gain.connect(this.audioContext.destination);
    
    osc.start();
    osc.stop(this.audioContext.currentTime + 0.1);
  }

  // Chip stack sound
  playChipSound() {
    for (let i = 0; i < 3; i++) {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      
      osc.type = 'sine';
      osc.frequency.value = 2000 + i * 500;
      gain.gain.setValueAtTime(this.volume * 0.08, this.audioContext.currentTime + i * 0.03);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + i * 0.03 + 0.05);
      
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      
      osc.start(this.audioContext.currentTime + i * 0.03);
      osc.stop(this.audioContext.currentTime + i * 0.03 + 0.05);
    }
  }

  // Roulette wheel spinning
  playRouletteSound() {
    const osc = this.audioContext.createOscillator();
    const gain = this.audioContext.createGain();
    
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(100, this.audioContext.currentTime);
    osc.frequency.linearRampToValueAtTime(50, this.audioContext.currentTime + 4);
    gain.gain.setValueAtTime(this.volume * 0.05, this.audioContext.currentTime);
    gain.gain.linearRampToValueAtTime(0.01, this.audioContext.currentTime + 4);
    
    osc.connect(gain);
    gain.connect(this.audioContext.destination);
    
    osc.start();
    osc.stop(this.audioContext.currentTime + 4);
  }

  // Ball bouncing
  playBallSound() {
    const bounces = [1200, 1000, 800, 600, 500];
    bounces.forEach((freq, i) => {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      
      osc.type = 'sine';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(this.volume * 0.1, this.audioContext.currentTime + i * 0.3);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + i * 0.3 + 0.1);
      
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      
      osc.start(this.audioContext.currentTime + i * 0.3);
      osc.stop(this.audioContext.currentTime + i * 0.3 + 0.1);
    });
  }

  // Bonus triggered
  playBonusSound() {
    const notes = [262, 330, 392, 523, 659, 784, 1047];
    notes.forEach((freq, i) => {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      
      osc.type = 'sine';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(this.volume * 0.2, this.audioContext.currentTime + i * 0.1);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + i * 0.1 + 0.3);
      
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      
      osc.start(this.audioContext.currentTime + i * 0.1);
      osc.stop(this.audioContext.currentTime + i * 0.1 + 0.3);
    });
  }

  // Coin drop
  playCoinSound() {
    for (let i = 0; i < 5; i++) {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      
      osc.type = 'sine';
      osc.frequency.value = 3000 + Math.random() * 1000;
      gain.gain.setValueAtTime(this.volume * 0.05, this.audioContext.currentTime + i * 0.05);
      gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + i * 0.05 + 0.1);
      
      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      
      osc.start(this.audioContext.currentTime + i * 0.05);
      osc.stop(this.audioContext.currentTime + i * 0.05 + 0.1);
    }
  }

  // Create white noise buffer
  createNoiseBuffer(duration) {
    const bufferSize = this.audioContext.sampleRate * duration;
    const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
    const data = buffer.getChannelData(0);
    
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }
    
    return buffer;
  }
}

// Singleton instance
export const casinoSounds = new CasinoSoundService();
export default casinoSounds;
