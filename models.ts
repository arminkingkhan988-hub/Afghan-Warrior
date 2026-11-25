import * as THREE from 'three';
import type { MaterialLibrary } from './textures';

export interface SoldierRig {
  group: THREE.Group;
  bodyPivot: THREE.Group;
  leftLeg: THREE.Group;
  rightLeg: THREE.Group;
  leftArm: THREE.Group;
  rightArm: THREE.Group;
  head: THREE.Group;
  riflePivot: THREE.Group;
  muzzlePoint: THREE.Object3D;
}

export function createSoldierRig(mats: MaterialLibrary, isEnemy: boolean): SoldierRig {
  const group = new THREE.Group();
  const bodyPivot = new THREE.Group();
  group.add(bodyPivot);

  const clothMat = isEnemy ? mats.enemyCloth : mats.camoCloth;
  const skinMat = new THREE.MeshStandardMaterial({ color: 0xb98b68, roughness: 0.72, metalness: 0.02 });
  const bootMat = new THREE.MeshStandardMaterial({ color: 0x2a231c, roughness: 0.78, metalness: 0.08 });
  const helmetMat = new THREE.MeshStandardMaterial({
    color: isEnemy ? 0x4b3f30 : 0x4c533c,
    roughness: 0.52,
    metalness: 0.22,
  });

  // Left & Right Legs with tactical boots (bottom at y = 0)
  const buildLeg = (xOffset: number) => {
    const legGroup = new THREE.Group();
    legGroup.position.set(xOffset, 0.85, 0);

    const thigh = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.44, 0.2), clothMat);
    thigh.position.y = -0.22;
    thigh.castShadow = true;
    legGroup.add(thigh);

    const shin = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.38, 0.18), clothMat);
    shin.position.y = -0.6;
    shin.castShadow = true;
    legGroup.add(shin);

    const boot = new THREE.Mesh(new THREE.BoxGeometry(0.17, 0.16, 0.27), bootMat);
    boot.position.set(0, -0.77, 0.04);
    boot.castShadow = true;
    legGroup.add(boot);

    bodyPivot.add(legGroup);
    return legGroup;
  };

  const leftLeg = buildLeg(-0.14);
  const rightLeg = buildLeg(0.14);

  // Torso + Tactical Vest + Backpack
  const torso = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.58, 0.26), clothMat);
  torso.position.y = 1.16;
  torso.castShadow = true;
  bodyPivot.add(torso);

  const vest = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.44, 0.31), mats.vestArmor);
  vest.position.y = 1.19;
  vest.castShadow = true;
  bodyPivot.add(vest);

  if (!isEnemy) {
    const backpack = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.42, 0.18), mats.vestArmor);
    backpack.position.set(0, 1.2, -0.22);
    backpack.castShadow = true;
    bodyPivot.add(backpack);
  }

  // Head + Helmet / Scarf wrap
  const head = new THREE.Group();
  head.position.set(0, 1.56, 0);
  const cranium = new THREE.Mesh(new THREE.SphereGeometry(0.145, 14, 12), skinMat);
  cranium.castShadow = true;
  head.add(cranium);

  if (!isEnemy) {
    const helmet = new THREE.Mesh(new THREE.SphereGeometry(0.165, 14, 10, 0, Math.PI * 2, 0, Math.PI * 0.62), helmetMat);
    helmet.position.y = 0.02;
    helmet.castShadow = true;
    head.add(helmet);

    const visor = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.06, 0.08), mats.gunMetal);
    visor.position.set(0, 0.04, 0.13);
    head.add(visor);
  } else {
    const headscarf = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.165, 0.14, 12), helmetMat);
    headscarf.position.y = 0.05;
    headscarf.castShadow = true;
    head.add(headscarf);
  }
  bodyPivot.add(head);

  // Arms
  const leftArm = new THREE.Group();
  leftArm.position.set(-0.3, 1.38, 0);
  const lUpper = new THREE.Mesh(new THREE.BoxGeometry(0.13, 0.46, 0.14), clothMat);
  lUpper.position.set(0, -0.2, 0.12);
  lUpper.rotation.x = -0.65;
  lUpper.castShadow = true;
  leftArm.add(lUpper);
  bodyPivot.add(leftArm);

  const rightArm = new THREE.Group();
  rightArm.position.set(0.3, 1.38, 0);
  const rUpper = new THREE.Mesh(new THREE.BoxGeometry(0.13, 0.46, 0.14), clothMat);
  rUpper.position.set(0, -0.2, 0.15);
  rUpper.rotation.x = -0.85;
  rUpper.castShadow = true;
  rightArm.add(rUpper);
  bodyPivot.add(rightArm);

  // Rifle assembly mounted forward (+Z forward in local space)
  const riflePivot = new THREE.Group();
  riflePivot.position.set(0.18, 1.18, 0.34);

  const receiver = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.12, 0.56), mats.gunMetal);
  receiver.castShadow = true;
  riflePivot.add(receiver);

  const barrel = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.02, 0.42, 8), mats.gunMetal);
  barrel.rotation.x = Math.PI / 2;
  barrel.position.set(0, 0.02, 0.45);
  riflePivot.add(barrel);

  const stock = new THREE.Mesh(new THREE.BoxGeometry(0.055, 0.11, 0.24), mats.wood);
  stock.position.set(0, -0.02, -0.34);
  riflePivot.add(stock);

  const mag = new THREE.Mesh(new THREE.BoxGeometry(0.045, 0.18, 0.09), mats.gunMetal);
  mag.position.set(0, -0.12, 0.08);
  mag.rotation.x = 0.25;
  riflePivot.add(mag);

  const muzzlePoint = new THREE.Object3D();
  muzzlePoint.position.set(0, 0.02, 0.68);
  riflePivot.add(muzzlePoint);

  bodyPivot.add(riflePivot);

  return { group, bodyPivot, leftLeg, rightLeg, leftArm, rightArm, head, riflePivot, muzzlePoint };
}

export function createMudBrickCompound(
  mats: MaterialLibrary,
  w: number,
  h: number,
  d: number
): THREE.Group {
  const g = new THREE.Group();

  const mainBody = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mats.mudBrick);
  mainBody.position.y = h / 2;
  mainBody.castShadow = true;
  mainBody.receiveShadow = true;
  g.add(mainBody);

  // Parapet roof rim
  const parapetH = 0.55;
  const parapet = new THREE.Mesh(new THREE.BoxGeometry(w + 0.3, parapetH, d + 0.3), mats.mudBrick);
  parapet.position.y = h + parapetH / 2;
  parapet.castShadow = true;
  parapet.receiveShadow = true;
  g.add(parapet);

  // Recessed timber doorway & beam accents
  const door = new THREE.Mesh(new THREE.BoxGeometry(1.4, 2.3, 0.22), mats.wood);
  door.position.set(0, 1.15, d / 2 + 0.02);
  g.add(door);

  for (let i = -1; i <= 1; i += 2) {
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.7, 8), mats.wood);
    beam.rotation.x = Math.PI / 2;
    beam.position.set(i * (w * 0.28), h - 0.35, d / 2 + 0.2);
    g.add(beam);
  }

  return g;
}

export function createWatchtower(mats: MaterialLibrary): THREE.Group {
  const g = new THREE.Group();
  const legOffsets = [
    [-1.4, -1.4],
    [1.4, -1.4],
    [-1.4, 1.4],
    [1.4, 1.4],
  ];
  for (const [lx, lz] of legOffsets) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.24, 5.2, 0.24), mats.wood);
    post.position.set(lx, 2.6, lz);
    post.castShadow = true;
    g.add(post);
  }
  const deck = new THREE.Mesh(new THREE.BoxGeometry(3.5, 0.26, 3.5), mats.wood);
  deck.position.y = 4.2;
  deck.castShadow = true;
  deck.receiveShadow = true;
  g.add(deck);

  const parapet = new THREE.Mesh(new THREE.BoxGeometry(3.4, 1.0, 3.4), mats.concrete);
  parapet.position.y = 4.82;
  parapet.castShadow = true;
  g.add(parapet);

  const roof = new THREE.Mesh(new THREE.BoxGeometry(3.8, 0.22, 3.8), mats.wood);
  roof.position.y = 6.5;
  roof.castShadow = true;
  g.add(roof);
  return g;
}

export function createMilitaryJeep(mats: MaterialLibrary): THREE.Group {
  const g = new THREE.Group();

  const chassis = new THREE.Mesh(new THREE.BoxGeometry(2.1, 0.72, 4.1), mats.jeepBody);
  chassis.position.y = 0.72;
  chassis.castShadow = true;
  chassis.receiveShadow = true;
  g.add(chassis);

  const hood = new THREE.Mesh(new THREE.BoxGeometry(1.95, 0.42, 1.35), mats.jeepBody);
  hood.position.set(0, 1.15, 1.15);
  hood.castShadow = true;
  g.add(hood);

  const cabFrame = new THREE.Mesh(new THREE.BoxGeometry(1.9, 0.8, 1.6), mats.vestArmor);
  cabFrame.position.set(0, 1.45, -0.35);
  cabFrame.castShadow = true;
  g.add(cabFrame);

  const windshield = new THREE.Mesh(
    new THREE.BoxGeometry(1.75, 0.55, 0.08),
    new THREE.MeshStandardMaterial({ color: 0x8fb4c9, roughness: 0.1, metalness: 0.5 })
  );
  windshield.position.set(0, 1.45, 0.46);
  windshield.rotation.x = -0.22;
  g.add(windshield);

  const wheelGeo = new THREE.CylinderGeometry(0.42, 0.42, 0.32, 16);
  wheelGeo.rotateZ(Math.PI / 2);
  const wheelCoords = [
    [-1.06, 0.42, 1.32],
    [1.06, 0.42, 1.32],
    [-1.06, 0.42, -1.32],
    [1.06, 0.42, -1.32],
  ];
  for (const [wx, wy, wz] of wheelCoords) {
    const wheel = new THREE.Mesh(wheelGeo, mats.tireRubber);
    wheel.position.set(wx, wy, wz);
    wheel.castShadow = true;
    g.add(wheel);
  }

  return g;
}

export function createTree(mats: MaterialLibrary): THREE.Group {
  const g = new THREE.Group();
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.28, 3.0, 8), mats.wood);
  trunk.position.y = 1.5;
  trunk.castShadow = true;
  g.add(trunk);

  const crown1 = new THREE.Mesh(new THREE.DodecahedronGeometry(1.45, 1), mats.foliage);
  crown1.position.y = 3.6;
  crown1.castShadow = true;
  g.add(crown1);

  const crown2 = new THREE.Mesh(new THREE.DodecahedronGeometry(1.05, 1), mats.foliage);
  crown2.position.set(0.6, 4.3, 0.3);
  crown2.castShadow = true;
  g.add(crown2);
  return g;
}
