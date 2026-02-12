/**
 * SVG path data for front and back anatomical views.
 * ViewBox: 0 0 200 400. Body centered at x=100.
 */

export const BODY_OUTLINE_FRONT =
  'M 100,10 C 88,10 80,18 80,30 C 80,42 88,50 100,50 C 112,50 120,42 120,30 C 120,18 112,10 100,10 Z ' + // head
  'M 93,50 L 93,60 L 107,60 L 107,50 ' + // neck
  'M 93,60 L 60,70 L 50,75 L 38,110 L 30,145 L 28,155 L 33,155 L 42,125 L 50,100 L 55,85 L 65,75 L 75,68 ' + // left arm outline
  'M 107,60 L 140,70 L 150,75 L 162,110 L 170,145 L 172,155 L 167,155 L 158,125 L 150,100 L 145,85 L 135,75 L 125,68 ' + // right arm outline
  'M 75,68 L 75,170 L 72,200 L 68,230 L 65,260 L 60,300 L 58,340 L 55,370 L 52,385 L 60,388 L 65,385 L 68,370 L 72,340 L 75,310 L 80,280 L 85,260 L 90,240 L 95,230 L 100,225 ' + // left leg outline
  'M 125,68 L 125,170 L 128,200 L 132,230 L 135,260 L 140,300 L 142,340 L 145,370 L 148,385 L 140,388 L 135,385 L 132,370 L 128,340 L 125,310 L 120,280 L 115,260 L 110,240 L 105,230 L 100,225'; // right leg outline

export const BODY_OUTLINE_BACK =
  'M 100,10 C 88,10 80,18 80,30 C 80,42 88,50 100,50 C 112,50 120,42 120,30 C 120,18 112,10 100,10 Z ' +
  'M 93,50 L 93,60 L 107,60 L 107,50 ' +
  'M 93,60 L 60,70 L 50,75 L 38,110 L 30,145 L 28,155 L 33,155 L 42,125 L 50,100 L 55,85 L 65,75 L 75,68 ' +
  'M 107,60 L 140,70 L 150,75 L 162,110 L 170,145 L 172,155 L 167,155 L 158,125 L 150,100 L 145,85 L 135,75 L 125,68 ' +
  'M 75,68 L 75,170 L 72,200 L 68,230 L 65,260 L 60,300 L 58,340 L 55,370 L 52,385 L 60,388 L 65,385 L 68,370 L 72,340 L 75,310 L 80,280 L 85,260 L 90,240 L 95,230 L 100,225 ' +
  'M 125,68 L 125,170 L 128,200 L 132,230 L 135,260 L 140,300 L 142,340 L 145,370 L 148,385 L 140,388 L 135,385 L 132,370 L 128,340 L 125,310 L 120,280 L 115,260 L 110,240 L 105,230 L 100,225';

// -- Front view muscle regions --

export const FRONT_PATHS: Record<string, string> = {
  // Head
  head: 'M 100,12 C 90,12 83,19 83,30 C 83,40 90,47 100,47 C 110,47 117,40 117,30 C 117,19 110,12 100,12 Z',

  // Neck
  neck: 'M 93,48 L 93,62 L 107,62 L 107,48 Z',

  // Chest (pectorals) -- two halves
  chest: 'M 78,68 L 78,95 C 78,100 85,105 100,105 C 115,105 122,100 122,95 L 122,68 L 115,65 L 100,63 L 85,65 Z',

  // Front deltoids
  front_deltoids_left: 'M 75,62 L 65,68 L 62,78 L 68,82 L 78,72 L 78,65 Z',
  front_deltoids_right: 'M 125,62 L 135,68 L 138,78 L 132,82 L 122,72 L 122,65 Z',

  // Biceps
  biceps_left: 'M 62,82 L 58,95 L 54,112 L 52,125 L 58,128 L 64,118 L 68,100 L 68,82 Z',
  biceps_right: 'M 138,82 L 142,95 L 146,112 L 148,125 L 142,128 L 136,118 L 132,100 L 132,82 Z',

  // Forearms
  forearm_left: 'M 52,128 L 46,140 L 38,152 L 34,155 L 40,158 L 50,148 L 58,132 Z',
  forearm_right: 'M 148,128 L 154,140 L 162,152 L 166,155 L 160,158 L 150,148 L 142,132 Z',

  // Abs (abdominals)
  abs: 'M 85,105 L 85,170 L 100,175 L 115,170 L 115,105 C 115,108 108,112 100,112 C 92,112 85,108 85,105 Z',

  // Obliques
  obliques_left: 'M 78,95 L 75,120 L 75,170 L 85,170 L 85,105 L 78,100 Z',
  obliques_right: 'M 122,95 L 125,120 L 125,170 L 115,170 L 115,105 L 122,100 Z',

  // Quadriceps
  quadriceps_left: 'M 78,180 L 75,200 L 72,230 L 70,260 L 68,280 L 75,282 L 82,265 L 88,240 L 90,220 L 88,200 L 85,180 Z',
  quadriceps_right: 'M 122,180 L 125,200 L 128,230 L 130,260 L 132,280 L 125,282 L 118,265 L 112,240 L 110,220 L 112,200 L 115,180 Z',

  // Adductors (inner thigh)
  adductor_left: 'M 88,200 L 90,220 L 92,240 L 95,225 L 100,225 L 100,195 L 95,180 L 88,180 Z',
  adductor_right: 'M 112,200 L 110,220 L 108,240 L 105,225 L 100,225 L 100,195 L 105,180 L 112,180 Z',

  // Front calves
  calves_left: 'M 68,295 L 65,320 L 62,345 L 60,370 L 58,382 L 65,380 L 70,360 L 74,335 L 76,310 L 75,295 Z',
  calves_right: 'M 132,295 L 135,320 L 138,345 L 140,370 L 142,382 L 135,380 L 130,360 L 126,335 L 124,310 L 125,295 Z',
};

// -- Back view muscle regions --

export const BACK_PATHS: Record<string, string> = {
  // Trapezius
  trapezius: 'M 88,52 L 78,60 L 78,85 L 88,80 L 100,78 L 112,80 L 122,85 L 122,60 L 112,52 L 100,50 Z',

  // Back deltoids
  back_deltoids_left: 'M 75,62 L 65,68 L 62,78 L 68,82 L 78,72 L 78,65 Z',
  back_deltoids_right: 'M 125,62 L 135,68 L 138,78 L 132,82 L 122,72 L 122,65 Z',

  // Upper back (rhomboids / lats upper)
  upper_back: 'M 78,85 L 78,125 L 85,130 L 100,132 L 115,130 L 122,125 L 122,85 L 112,80 L 100,78 L 88,80 Z',

  // Lower back (erector spinae)
  lower_back: 'M 82,132 L 80,160 L 80,180 L 90,185 L 100,187 L 110,185 L 120,180 L 120,160 L 118,132 L 110,130 L 100,132 L 90,130 Z',

  // Triceps
  triceps_left: 'M 62,82 L 58,95 L 54,112 L 52,125 L 58,128 L 64,118 L 68,100 L 68,82 Z',
  triceps_right: 'M 138,82 L 142,95 L 146,112 L 148,125 L 142,128 L 136,118 L 132,100 L 132,82 Z',

  // Gluteals
  gluteal_left: 'M 80,185 L 78,200 L 78,215 L 85,225 L 100,225 L 100,190 L 90,185 Z',
  gluteal_right: 'M 120,185 L 122,200 L 122,215 L 115,225 L 100,225 L 100,190 L 110,185 Z',

  // Hamstrings
  hamstring_left: 'M 78,225 L 75,250 L 72,270 L 70,290 L 68,300 L 76,300 L 82,280 L 88,255 L 92,235 L 88,225 Z',
  hamstring_right: 'M 122,225 L 125,250 L 128,270 L 130,290 L 132,300 L 124,300 L 118,280 L 112,255 L 108,235 L 112,225 Z',

  // Back calves
  calves_left: 'M 68,305 L 65,325 L 62,345 L 60,370 L 58,382 L 65,380 L 70,360 L 74,335 L 76,315 L 75,305 Z',
  calves_right: 'M 132,305 L 135,325 L 138,345 L 140,370 L 142,382 L 135,380 L 130,360 L 126,335 L 124,315 L 125,305 Z',
};

/** Human-readable muscle names for tooltips */
export const MUSCLE_LABELS: Record<string, string> = {
  head: 'Head',
  neck: 'Neck',
  chest: 'Chest (Pectorals)',
  front_deltoids_left: 'Left Front Deltoid',
  front_deltoids_right: 'Right Front Deltoid',
  biceps_left: 'Left Biceps',
  biceps_right: 'Right Biceps',
  forearm_left: 'Left Forearm',
  forearm_right: 'Right Forearm',
  abs: 'Abdominals',
  obliques_left: 'Left Obliques',
  obliques_right: 'Right Obliques',
  quadriceps_left: 'Left Quadriceps',
  quadriceps_right: 'Right Quadriceps',
  adductor_left: 'Left Adductor',
  adductor_right: 'Right Adductor',
  calves_left: 'Left Calf',
  calves_right: 'Right Calf',
  trapezius: 'Trapezius',
  back_deltoids_left: 'Left Rear Deltoid',
  back_deltoids_right: 'Right Rear Deltoid',
  upper_back: 'Upper Back (Rhomboids/Lats)',
  lower_back: 'Lower Back (Erector Spinae)',
  triceps_left: 'Left Triceps',
  triceps_right: 'Right Triceps',
  gluteal_left: 'Left Glute',
  gluteal_right: 'Right Glute',
  hamstring_left: 'Left Hamstring',
  hamstring_right: 'Right Hamstring',
};

/**
 * Maps user-friendly muscle names (from MuscleData.muscle) to path keys.
 * Handles both singular names ("quadriceps") expanding to left+right,
 * and direct path key matches.
 */
export const MUSCLE_ALIASES: Record<string, string[]> = {
  head: ['head'],
  neck: ['neck'],
  chest: ['chest'],
  pectorals: ['chest'],
  'front-deltoids': ['front_deltoids_left', 'front_deltoids_right'],
  'front deltoids': ['front_deltoids_left', 'front_deltoids_right'],
  deltoids: ['front_deltoids_left', 'front_deltoids_right', 'back_deltoids_left', 'back_deltoids_right'],
  biceps: ['biceps_left', 'biceps_right'],
  forearm: ['forearm_left', 'forearm_right'],
  forearms: ['forearm_left', 'forearm_right'],
  abs: ['abs'],
  abdominals: ['abs'],
  obliques: ['obliques_left', 'obliques_right'],
  quadriceps: ['quadriceps_left', 'quadriceps_right'],
  quads: ['quadriceps_left', 'quadriceps_right'],
  adductor: ['adductor_left', 'adductor_right'],
  adductors: ['adductor_left', 'adductor_right'],
  calves: ['calves_left', 'calves_right'],
  trapezius: ['trapezius'],
  traps: ['trapezius'],
  'back-deltoids': ['back_deltoids_left', 'back_deltoids_right'],
  'back deltoids': ['back_deltoids_left', 'back_deltoids_right'],
  'upper-back': ['upper_back'],
  'upper back': ['upper_back'],
  rhomboids: ['upper_back'],
  lats: ['upper_back'],
  'lower-back': ['lower_back'],
  'lower back': ['lower_back'],
  'erector spinae': ['lower_back'],
  triceps: ['triceps_left', 'triceps_right'],
  gluteal: ['gluteal_left', 'gluteal_right'],
  glutes: ['gluteal_left', 'gluteal_right'],
  hamstring: ['hamstring_left', 'hamstring_right'],
  hamstrings: ['hamstring_left', 'hamstring_right'],
};
