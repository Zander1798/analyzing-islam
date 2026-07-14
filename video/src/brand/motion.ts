import { Easing } from "remotion";

// Premium motion personality: elegant, minimal, decelerate-in / accelerate-out.
export const EASE = {
  premium: Easing.bezier(0.4, 0, 0.2, 1), // on-screen
  emphasized: Easing.bezier(0.05, 0.7, 0.1, 1), // entrances (MD3 emphasized)
  accel: Easing.bezier(0.3, 0, 1, 1), // exits
  out: Easing.out(Easing.cubic),
};

// Spring configs.
export const SPRING = {
  premium: { damping: 200 }, // no overshoot — elegant settle
  pop: { damping: 13, stiffness: 170, mass: 0.7 }, // success pop, slight overshoot
};
