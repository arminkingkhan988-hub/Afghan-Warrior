export type Language = 'en' | 'ps';
export type GraphicsPreset = 'low' | 'medium' | 'high';
export type MapId = 'village' | 'valley' | 'outpost';
export type Difficulty = 'recruit' | 'veteran' | 'elite';
export type TimeOfDay = 'day' | 'dusk' | 'night';
export type Weather = 'clear' | 'dust' | 'rain';
export type GameMode = 'story' | 'free';

export interface WeaponDef {
  id: string;
  categoryEn: string;
  categoryPs: string;
  nameEn: string;
  namePs: string;
  damage: number;
  fireRate: number;
  recoil: number;
  spread: number;
  magSize: number;
  reserveMax: number;
  reloadTime: number;
  range: number;
  pellets: number;
  automatic: boolean;
  zoomFov: number;
}

export interface MissionDef {
  id: number;
  implemented: boolean;
  mapId: MapId;
  titleEn: string;
  titlePs: string;
  briefingEn: string;
  briefingPs: string;
  objectiveEn: string;
  objectivePs: string;
  enemyCount: number;
  difficulty: Difficulty;
  timeOfDay: TimeOfDay;
  weather: Weather;
  rewardPoints: number;
  unlocksMission: number;
}

export interface FreeBattleConfig {
  mapId: MapId;
  difficulty: Difficulty;
  enemyCount: number;
  startingWeapon: string;
  timeOfDay: TimeOfDay;
  weather: Weather;
}

export interface SaveState {
  language: Language;
  graphicsQuality: GraphicsPreset;
  musicVolume: number;
  sfxVolume: number;
  envVolume: number;
  cameraSensitivity: number;
  aimSensitivity: number;
  controlSensitivity: number;
  unlockedMission: number;
  completedMissions: number[];
  totalScore: number;
}

export interface HudSnapshot {
  health: number;
  maxHealth: number;
  armor: number;
  maxArmor: number;
  magAmmo: number;
  reserveAmmo: number;
  weaponId: string;
  weaponName: string;
  grenades: number;
  isReloading: boolean;
  isAiming: boolean;
  isCrouching: boolean;
  inVehicle: boolean;
  nearbyVehicle: boolean;
  enemiesRemaining: number;
  enemiesTotal: number;
  objectiveText: string;
  statusBanner: string | null;
}
