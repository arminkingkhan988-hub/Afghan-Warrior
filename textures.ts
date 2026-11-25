import * as THREE from 'three';

function makeCanvasTexture(
  size: number,
  repeatX: number,
  repeatY: number,
  maxAnisotropy: number,
  draw: (ctx: CanvasRenderingContext2D, size: number) => void
): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;
  draw(ctx, size);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(repeatX, repeatY);
  tex.anisotropy = maxAnisotropy;
  return tex;
}

export interface MaterialLibrary {
  terrain: THREE.MeshStandardMaterial;
  rock: THREE.MeshStandardMaterial;
  mudBrick: THREE.MeshStandardMaterial;
  concrete: THREE.MeshStandardMaterial;
  wood: THREE.MeshStandardMaterial;
  water: THREE.MeshStandardMaterial;
  foliage: THREE.MeshStandardMaterial;
  camoCloth: THREE.MeshStandardMaterial;
  enemyCloth: THREE.MeshStandardMaterial;
  vestArmor: THREE.MeshStandardMaterial;
  gunMetal: THREE.MeshStandardMaterial;
  jeepBody: THREE.MeshStandardMaterial;
  tireRubber: THREE.MeshStandardMaterial;
  dispose: () => void;
}

export function createMaterialLibrary(maxAnisotropy: number): MaterialLibrary {
  const textures: THREE.Texture[] = [];

  const soilTex = makeCanvasTexture(256, 28, 28, maxAnisotropy, (ctx, s) => {
    ctx.fillStyle = '#a48962';
    ctx.fillRect(0, 0, s, s);
    for (let i = 0; i < 3200; i++) {
      const x = Math.random() * s;
      const y = Math.random() * s;
      const r = 1 + Math.random() * 3.5;
      ctx.fillStyle = Math.random() > 0.5 ? 'rgba(122,98,66,0.35)' : 'rgba(205,180,138,0.28)';
      ctx.fillRect(x, y, r, r);
    }
  });
  textures.push(soilTex);

  const mudBrickTex = makeCanvasTexture(256, 3, 2, maxAnisotropy, (ctx, s) => {
    ctx.fillStyle = '#b49268';
    ctx.fillRect(0, 0, s, s);
    const rows = 8;
    const cols = 4;
    const bh = s / rows;
    const bw = s / cols;
    for (let r = 0; r < rows; r++) {
      const offset = (r % 2) * (bw * 0.5);
      for (let c = -1; c <= cols; c++) {
        const x = c * bw + offset;
        const y = r * bh;
        ctx.fillStyle = r % 3 === 0 ? '#a8855c' : '#ba986f';
        ctx.fillRect(x + 2, y + 2, bw - 4, bh - 4);
      }
    }
    for (let i = 0; i < 1600; i++) {
      ctx.fillStyle = 'rgba(70,52,32,0.14)';
      ctx.fillRect(Math.random() * s, Math.random() * s, 2, 2);
    }
  });
  textures.push(mudBrickTex);

  const rockTex = makeCanvasTexture(256, 4, 4, maxAnisotropy, (ctx, s) => {
    ctx.fillStyle = '#736c62';
    ctx.fillRect(0, 0, s, s);
    for (let i = 0; i < 2400; i++) {
      ctx.fillStyle = Math.random() > 0.45 ? 'rgba(92,85,77,0.45)' : 'rgba(138,131,120,0.35)';
      ctx.fillRect(Math.random() * s, Math.random() * s, 4, 3);
    }
  });
  textures.push(rockTex);

  const concreteTex = makeCanvasTexture(256, 2, 2, maxAnisotropy, (ctx, s) => {
    ctx.fillStyle = '#8b8d89';
    ctx.fillRect(0, 0, s, s);
    ctx.strokeStyle = 'rgba(55,58,56,0.35)';
    ctx.lineWidth = 3;
    ctx.strokeRect(4, 4, s - 8, s / 2 - 6);
    ctx.strokeRect(4, s / 2 + 2, s - 8, s / 2 - 6);
    for (let i = 0; i < 1200; i++) {
      ctx.fillStyle = 'rgba(40,42,40,0.14)';
      ctx.fillRect(Math.random() * s, Math.random() * s, 2, 2);
    }
  });
  textures.push(concreteTex);

  const woodTex = makeCanvasTexture(256, 2, 2, maxAnisotropy, (ctx, s) => {
    ctx.fillStyle = '#6f4e31';
    ctx.fillRect(0, 0, s, s);
    for (let y = 0; y < s; y += 32) {
      ctx.fillStyle = 'rgba(42,28,16,0.45)';
      ctx.fillRect(0, y, s, 2);
    }
    for (let i = 0; i < 500; i++) {
      ctx.fillStyle = 'rgba(90,62,36,0.3)';
      ctx.fillRect(Math.random() * s, Math.random() * s, 24, 1.5);
    }
  });
  textures.push(woodTex);

  const camoTex = makeCanvasTexture(128, 1, 1, maxAnisotropy, (ctx, s) => {
    ctx.fillStyle = '#5a5f42';
    ctx.fillRect(0, 0, s, s);
    const colors = ['#7b7154', '#404532', '#9b8d69', '#504b3b'];
    for (let i = 0; i < 70; i++) {
      ctx.fillStyle = colors[i % colors.length];
      ctx.beginPath();
      ctx.ellipse(Math.random() * s, Math.random() * s, 6 + Math.random() * 14, 4 + Math.random() * 10, Math.random() * Math.PI, 0, Math.PI * 2);
      ctx.fill();
    }
  });
  textures.push(camoTex);

  const mats = {
    terrain: new THREE.MeshStandardMaterial({ map: soilTex, roughness: 0.94, metalness: 0.02 }),
    rock: new THREE.MeshStandardMaterial({ map: rockTex, roughness: 0.9, metalness: 0.06 }),
    mudBrick: new THREE.MeshStandardMaterial({ map: mudBrickTex, roughness: 0.91, metalness: 0.02 }),
    concrete: new THREE.MeshStandardMaterial({ map: concreteTex, roughness: 0.86, metalness: 0.05 }),
    wood: new THREE.MeshStandardMaterial({ map: woodTex, roughness: 0.85, metalness: 0.04 }),
    water: new THREE.MeshStandardMaterial({ color: 0x3b6572, roughness: 0.16, metalness: 0.35 }),
    foliage: new THREE.MeshStandardMaterial({ color: 0x4b5d38, roughness: 0.88, metalness: 0.02 }),
    camoCloth: new THREE.MeshStandardMaterial({ map: camoTex, roughness: 0.84, metalness: 0.04 }),
    enemyCloth: new THREE.MeshStandardMaterial({ color: 0x3f362d, roughness: 0.88, metalness: 0.04 }),
    vestArmor: new THREE.MeshStandardMaterial({ color: 0x363b2d, roughness: 0.65, metalness: 0.18 }),
    gunMetal: new THREE.MeshStandardMaterial({ color: 0x262a2e, roughness: 0.32, metalness: 0.82 }),
    jeepBody: new THREE.MeshStandardMaterial({ color: 0x6b6447, roughness: 0.56, metalness: 0.25 }),
    tireRubber: new THREE.MeshStandardMaterial({ color: 0x1c1d1f, roughness: 0.9, metalness: 0.05 }),
  };

  return {
    ...mats,
    dispose: () => {
      textures.forEach((t) => t.dispose());
      Object.values(mats).forEach((m) => m.dispose());
    },
  };
}
