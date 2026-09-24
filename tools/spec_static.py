"""Static (non-solved) part of the Antikythera spec: conventions, structure, tubes, shafts, dials, print, render, sources."""
import json as _json, os as _os
_ENV = _json.load(open(_os.path.join(_os.path.dirname(__file__), "crown_envelopes.json")))
A1_PITCH_R = 0.5776 * 48 / 2          # 13.8624
B1_PITCH_R = 0.5776 * 223 / 2         # 64.4024
B1_MID_Z = (3.95 + 6.65) / 2          # 5.30
A1_AXIS_Z = round(B1_MID_Z + A1_PITCH_R, 4)
M_A1 = 0.5776

STATIC = {
 "meta": {
  "name": "Antikythera Mechanism — functional reconstruction spec",
  "version": "1.0.0", "date": "2026-09-24",
  "basis": "Freeth et al. 2021 (Sci. Rep. 11:5821) cosmos model + Freeth 2006/2008 back-dial trains, with geometric corrections for a conjugate, interference-free build",
  "units": "millimetres, years (1 year = 1 turn of b1), degrees where stated",
  "status_levels": {"SURVIVING": "physically attested in the fragments (CT)", "RECONSTRUCTED": "strong evidence (inscriptions, dial scales, forced ratios)",
                    "HYPOTHETICAL": "proposed by a model (mostly Freeth 2021 front trains)"}
 },
 "conventions": {
  "frame": "World frame = front view: +x to the right, +y up (Metonic dial on top, Saros below), +z toward the FRONT viewer. z = 0 is the front face of the Main Plate (Main Plate occupies z -2.0..0.0).",
  "rate_sign": "Rates are in revolutions of the body per year (b1 = +1). POSITIVE = CLOCKWISE SEEN FROM THE FRONT. A negative rate on a back-dial pointer means clockwise seen from the back.",
  "blender_angle": "For a z-axis body: local rotation about +z (right-handed, relative to its parent) = -2*pi*rate_rel_parent*years + phase. Parent/child: bodies with parent 'e_table' or 'b' are parented to that carrier in Blender; their axis_xy_in_parent is in the carrier's local frame at crank = 0 (for 'b' this equals world XY; for 'e_table' it is relative to axis E).",
  "crank": "Body 'a' turns about the +x axis (line y = 0, z = %.4f). Angle about +x = -2*pi*(223/48)*years. Check: at the contact point (x = %.4f, y = 0, z = %.2f) b1's clockwise motion is toward -y, and a1 rotating negatively about +x moves its lowest point toward -y." % (A1_AXIS_Z, B1_PITCH_R, B1_MID_Z),
  "moon_phase": "Body 'q' turns about its radial axis +u (u = the Moon body's local +x, along the Moon pointer), relative to the Moon body, by theta_q = theta_b - theta_moon (world z-angles; 20:20 crown b0~q1; right-handed about +u). NONLINEAR because theta_moon carries the lunar anomaly; mean rate +235/19; theta_q(0) = -0.0773916 rad. Never use a linear law.",
  "time_control": "One Empty 'AM_Controller' with custom property 'crank' = years (float). Keep |crank| <= 100 in drivers (float32).",
  "phases": "Uncalibrated epoch: every LINEAR body angle is 0 at crank = 0; nonlinear bodies (kp, e_inner, moon, q, slot gears, planet outputs, followers) take the value of their formula at crank = 0. Spur tooth phasing is computed so meshing teeth interleave at crank = 0 using the actual body angles; crown teeth come pre-phased in crowns.*.envelope.",
  "reference_directions": "Each body is modelled in its local frame and its Blender object rotation is exactly the body angle theta_B(t). Front pointers (Moon, Date, Dragon Hand), follower levers, pins and slots lie along local +x. Planet markers sit at their ring's marker_local_deg (dials.front.cosmos_rings). Back-dial pointers lie along local +y (spiral start at 12 o'clock). Pins sit at local angle 0 (local +x) of their pin gear / epicycle, EXCEPT the true-Sun pin at local angle followers[trueSun].pin_phase_deg of su56; slots lie along local +x of the slot gear / follower, so every slot contains its pin at all times by construction.",
  "pin_slot_formula": "Pin gear angle th1 (math convention, relative to the carrier), pin radius r, slot-gear axis offset e in direction beta (from pin-gear axis to slot-gear axis, carrier frame): slot gear angle th2 = th1 + atan2(e*sin(th1 - beta), r - e*cos(th1 - beta)). Continuous because e < r. Mean rate of th2 = mean rate of th1.",
  "follower_formula": "theta_F = theta_b + g0 + atan2(d*sin(lam), i + d*cos(lam)), lam = theta_epi_local + pin_phase - g0, where g0 = atan2 of epicycle_axis_xy_in_b, theta_epi_local = the epicycle body's angle relative to b, pin_phase = followers[].pin_phase_deg in radians. Continuous (d < i). Mean rate of every follower = rate of b (= 1).",
  "willis": "For gears g1 (on body B1) and g2 (on body B2) meshing on carrier C: z1*(w1 - wC) = -z2*(w2 - wC) (external mesh)."
 },
 "tooth": {
  "profile": "involute", "pressure_angle_deg": 30.0, "addendum_coeff": 1.0, "dedendum_coeff": 1.25, "root_fillet_coeff": 0.2,
  "profile_shift": 0.0, "min_teeth_without_undercut": 8,
  "backlash_circumferential_mm": {"scholarly": 0.03, "print": "see print_profiles"},
  "backlash_rule": "Thin every tooth by backlash/2 at the pitch circle (flank half-angle psi -= backlash/(4*r)). NEVER move axes.",
  "tip_land_rule": "Tip land >= 0.2*m on the NOMINAL profile (j = 0) for every z of the spec (minimum: p2, 0.228*m). On thinned profiles (scholarly and print) the tip land must be > 0 and is only reported.",
  "lightening": "Wheels with pitch radius > 12 get 4-6 windows between the hub (bore + 2) and the rim (root - max(1.5, 2m)), arms max(1.5, 0.12*r) wide, EXCEPT pin/slot gears (solid) and b1 (spec b1_structure). e3: windows only between 4 and 40 mm from E, with one arm >= 8 wide centred on the K direction (-38 deg in the e_table frame) carrying boss_k; the solid ring 40..rim carries e4 through e4_spacers. e4 is an annulus (inner radius 41.8).",
  "why_30deg": "The 30 deg basic rack is exactly the equilateral-triangle rack of the ancient teeth; conjugate, no undercut down to 8 teeth, contact ratio 1.3-1.4.",
  "optional_render_mode": "triangular straight-flank teeth (historical look, not conjugate) for renders only, never for checks or print"
 },
 "crowns": {
  "method": "Envelope-generated teeth (pre-computed and BVH-verified on Blender 5.2.2: 0 overlaps on 60 positions per pitch, engagement gap 0.013-0.041 mm at every position). Do NOT regenerate them: build them from the grids below.",
  "mesh_rule": "For tooth k (k = 0..z-1), node (i, j): s = s_grid[i][j], rho = rho_levels[j], phi = phi_lo_rad[i][j] + k*2*pi/z (lo flank) and phi_hi_rad[i][j] + k*2*pi/z (hi flank). Crown-frame point = (s, rho*sin(phi), -rho*cos(phi)) relative to the crown axis point; i.e. a1 local (x, y, z - axis_z) and q1 local (u, v, z - axis_z). Faces (quads, each split in 2 triangles), L = lo node, H = hi node, I = last row (root), J = last column: lo flank L(i,j)-L(i,j+1)-L(i+1,j+1)-L(i+1,j); hi flank H(i,j)-H(i+1,j)-H(i+1,j+1)-H(i,j+1); side j = 0: L(i,0)-L(i+1,0)-H(i+1,0)-H(i,0); side j = J: L(i,J)-H(i,J)-H(i+1,J)-L(i+1,J); tip row (i = 0): L(0,j)-H(0,j)-H(0,j+1)-L(0,j+1); root row (i = I): L(I,j)-L(I,j+1)-H(I,j+1)-H(I,j). This winding is outward for both crowns (verified: tooth volume a1 1.3913 mm3, q1 0.8116 mm3, 0 non-contiguous edges). A positive volume alone does not prove the winding: also check is_contiguous on every edge. Row i = last lies 0.05 mm inside the disc, so teeth and disc overlap (same body): keep them as separate closed shells in one object (check manifoldness per connected shell).",
  "a1": {"meshes_with": "b1", "body": "a", "axis": "+x", "axis_y": 0.0, "axis_z": A1_AXIS_Z, "teeth": 48, "module": M_A1, "pitch_ring_radius": round(A1_PITCH_R, 4),
         "s_is": "world x", "phi_is": "angle about +x measured from -z toward +y; B_a rotation alpha adds to phi",
         "disc": {"x": [round(B1_PITCH_R + 1.25*M_A1, 4), round(B1_PITCH_R + 1.25*M_A1 + 1.5, 4)], "r_out": 14.9, "bore": 0.0, "note": "solid disc fused to the shaft; spans z 4.26..34.06, below the CP (34.15)"},
         "shaft": {"radius": 1.5, "x": [round(B1_PITCH_R + 1.25*M_A1 + 1.5, 4), 108.0], "through": "crank_bracket hole r 1.55 and case right wall hole r 1.55"},
         "crank": {"arm": "bar 25 x 4 x 2 at x 99..101, from the shaft axis toward +z", "knob": "cylinder r 3 along +x, x 101..111, at the arm end"},
         "envelope": _ENV["a1"], "status": "SURVIVING"},
  "q1": {"meshes_with": "b0", "body": "q", "carrier": "moon", "axis": "radial +u (Moon local +x)", "axis_z": 52.70, "teeth": 20, "module": 0.5, "pitch_ring_radius": 5.0,
         "s_is": "Moon-frame u", "phi_is": "angle about +u measured from -z toward +v; B_q rotation adds to phi",
         "disc": {"u": [5.625, 6.625], "r_out": 5.55, "bore": 0.0, "note": "spans z 47.15..58.25: 0.15 above the Dragon Hand, 0.35 below the Moon arm"},
         "arbor": {"radius": 0.6, "u": [2.0, 17.6]},
         "hangers": "two brackets owned by body moon, 0.6 thick in u at u 2.3..2.9 and 16.8..17.4, hanging from the cap top plate (z 58.6) down to z 51.4, each with a hole r 0.65 at z 52.70",
         "phase_sphere": {"radius": 3.0, "centre_u": 13.0, "centre_z": 52.70, "halves": "one hemisphere dark, one silver; the dark half faces +z when theta_q = 0"},
         "envelope": _ENV["q1"], "status": "SURVIVING"}
 },
 "tubes": [
  {"id": "moon_arbor", "body": "moon", "r_in": 0.0, "r_out": 1.2, "z": [-3.45, 59.4]},
  {"id": "fixed_tube", "body": "frame", "r_in": 1.4, "r_out": 2.3, "z": [-1.0, 10.15], "note": "pressed into the Main Plate; carries fx51 (L1) and fx49 (L2)"},
  {"id": "b_hub", "body": "b", "r_in": 2.5, "r_out": 3.2, "z": [1.8, 7.85], "note": "b2 and b1 are fixed on it; it turns on the fixed tube"},
  {"id": "t_meanSun", "body": "b", "r_in": 1.4, "r_out": 1.9, "z": [10.30, 48.20], "note": "driven by the mean-Sun bar (L3); b0 at its front end"},
  {"id": "t_nodes", "body": "t_nodes", "r_in": 2.1, "r_out": 2.6, "z": [11.45, 47.00]},
  {"id": "t_mercury", "body": "t_mercury", "r_in": 2.8, "r_out": 3.3, "z": [12.60, 46.45]},
  {"id": "t_venus", "body": "t_venus", "r_in": 3.5, "r_out": 4.0, "z": [13.75, 45.90]},
  {"id": "t_trueSun", "body": "t_trueSun", "r_in": 4.2, "r_out": 4.7, "z": [24.60, 45.35]},
  {"id": "t_mars", "body": "t_mars", "r_in": 4.9, "r_out": 5.4, "z": [25.55, 44.80]},
  {"id": "t_jupiter", "body": "t_jupiter", "r_in": 5.6, "r_out": 6.1, "z": [26.70, 44.25]},
  {"id": "t_saturn", "body": "t_saturn", "r_in": 6.3, "r_out": 6.8, "z": [29.00, 43.70]},
  {"id": "t_date", "body": "b", "r_in": 7.0, "r_out": 7.5, "z": [34.15, 43.15], "note": "fused to the CP"}
 ],
 "shafts": {
  "rules": [
   "Studs extend exactly 0.05 mm beyond the free end of the hub they carry (never into a neighbouring layer). No face contact between different bodies: every shaft, stud, boss, hub, pin end stops >= 0.1 mm from parts of other bodies, or ends inside a clearance hole (hole radius = shaft radius + 0.05). Blind bearings are not modelled.",
   "Plates (main, back, front, Sub-Plate, CP, Strap, D-plate) get a clearance hole (r + 0.05) wherever a shaft of another body passes or ends inside them; holes for shafts of their own body are fused.",
   "Every gear's bore is gears[].bore_radius: 'fused' gears are part of the shaft's body; 'rides_on' gears turn on a support owned by another body with 0.05 mm radial clearance.",
   "Circles facing a radial clearance g (bores, holes, studs, bosses, tubes) are polygons with n >= max(64, ceil(pi/acos(R/(R+g))) + 8) sides, and a bore and its shaft use the same n."
  ],
  "items": [
   {"id": "stud_c", "owner": "frame", "axis_body": "c", "r": 1.2, "z": [0.0, 3.40]},
   {"id": "stud_l", "owner": "frame", "axis_body": "l", "r": 1.2, "z": [0.0, 3.60]},
   {"id": "shaft_d", "owner": "d", "axis_body": "d", "r": 1.0, "z": [-4.90, 2.55]},
   {"id": "shaft_m", "owner": "m", "axis_body": "m", "r": 1.0, "z": [-16.40, 2.15]},
   {"id": "shaft_e_inner", "owner": "e_inner", "axis_body": "e_inner", "r": 1.0, "z": [-16.40, -0.10]},
   {"id": "pipe_e", "owner": "e_pipe", "axis_body": "e_pipe", "r_in": 1.2, "r": 1.8, "z": [-7.10, -3.60]},
   {"id": "shaft_f", "owner": "f", "axis_body": "f", "r": 1.0, "z": [-16.40, -0.10]},
   {"id": "shaft_g", "owner": "g", "axis_body": "g", "r": 1.0, "z": [-18.20, -0.10]},
   {"id": "shaft_h", "owner": "h", "axis_body": "h", "r": 1.0, "z": [-16.40, -0.10]},
   {"id": "shaft_i", "owner": "i", "axis_body": "i", "r": 1.0, "z": [-17.00, -0.10]},
   {"id": "shaft_n", "owner": "n", "axis_body": "n", "r": 1.0, "z": [-18.20, -0.10]},
   {"id": "shaft_o", "owner": "o", "axis_body": "o", "r": 1.0, "z": [-17.00, -0.10]},
   {"id": "shaft_p", "owner": "p", "axis_body": "p", "r": 1.0, "z": [-16.40, -0.10]},
   {"id": "shaft_cal", "owner": "cal", "axis_body": "cal", "r": 1.0, "z": [-17.00, -0.10]},
   {"id": "boss_k", "owner": "e_table", "axis_body": "k", "r": 2.3, "z": [-7.25, -6.45]},
   {"id": "stud_kp", "owner": "e_table", "axis_body": "kp", "r": 1.0, "z": [-7.85, -7.25]},
   {"id": "e4_spacers", "owner": "e_table", "axis_body": "e_table", "note": "6 spacers r 1.0 at radius 46.0 from E (every 60 deg), z -6.60..-6.45, join e4 to e3"},
   {"id": "stud_spA", "owner": "b", "axis_body": "spA", "r": 0.8, "z": [6.65, 17.10]},
   {"id": "hub_spA", "owner": "spA", "axis_body": "spA", "r_in": 0.85, "r": 1.4, "z": [6.75, 17.05]},
   {"id": "stud_spB", "owner": "b", "axis_body": "spB", "r": 0.8, "z": [6.65, 12.50]},
   {"id": "hub_spB", "owner": "spB", "axis_body": "spB", "r_in": 0.85, "r": 1.4, "z": [6.75, 12.45]},
   {"id": "stud_spC", "owner": "b", "axis_body": "spC", "r": 0.8, "z": [6.65, 17.10]},
   {"id": "hub_spC", "owner": "spC", "axis_body": "spC", "r_in": 0.85, "r": 1.4, "z": [6.75, 17.05]},
   {"id": "stud_me40", "owner": "b", "axis_body": "x_me40", "r": 0.8, "z": [16.00, 22.85], "note": "hangs from the Strap"},
   {"id": "hub_me40", "owner": "x_me40", "axis_body": "x_me40", "r_in": 0.85, "r": 1.4, "z": [16.05, 22.75]},
   {"id": "stud_me20", "owner": "b", "axis_body": "x_me20", "r": 0.8, "z": [14.85, 22.85], "note": "hangs from the Strap"},
   {"id": "hub_me20", "owner": "x_me20", "axis_body": "x_me20", "r_in": 0.85, "r": 1.4, "z": [14.90, 22.75]},
   {"id": "stud_vn26", "owner": "b", "axis_body": "x_vn26", "r": 0.8, "z": [16.00, 17.80], "note": "hangs from the D-plate"},
   {"id": "hub_vn26", "owner": "x_vn26", "axis_body": "x_vn26", "r_in": 0.85, "r": 1.4, "z": [16.05, 17.70]},
   {"id": "stud_r1", "owner": "b", "axis_body": "x_r1", "r": 0.8, "z": [14.85, 17.80], "note": "hangs from the D-plate"},
   {"id": "hub_r1", "owner": "x_r1", "axis_body": "x_r1", "r_in": 0.85, "r": 1.4, "z": [14.90, 17.70]},
   {"id": "shaft_cp52", "owner": "x_cp52", "axis_body": "x_cp52", "r": 1.0, "z": [30.15, 37.30], "note": "through a CP hole r 1.05"},
   {"id": "shaft_cp64", "owner": "x_cp64", "axis_body": "x_cp64", "r": 1.0, "z": [26.70, 37.30], "note": "through a CP hole r 1.05"},
   {"id": "shaft_su56", "owner": "x_su56", "axis_body": "x_su56", "r": 1.0, "z": [33.25, 37.30], "note": "through a CP hole r 1.05"},
   {"id": "crank_disc_su56", "owner": "x_su56", "axis_body": "x_su56", "r": 2.6, "z": [33.25, 34.00]},
   {"id": "stud_sa40", "owner": "b", "axis_body": "x_sa40", "r": 0.8, "z": [30.10, 34.15]},
   {"id": "hub_sa40", "owner": "x_sa40", "axis_body": "x_sa40", "r_in": 0.85, "r": 1.4, "z": [30.15, 34.05]},
   {"id": "stud_ju40", "owner": "b", "axis_body": "x_ju40", "r": 0.8, "z": [27.80, 34.15]},
   {"id": "hub_ju40", "owner": "x_ju40", "axis_body": "x_ju40", "r_in": 0.85, "r": 1.4, "z": [27.85, 34.05]},
   {"id": "stud_ma40", "owner": "b", "axis_body": "x_ma40", "r": 0.8, "z": [26.65, 34.15]},
   {"id": "hub_ma40", "owner": "x_ma40", "axis_body": "x_ma40", "r_in": 0.85, "r": 1.4, "z": [26.70, 34.05]},
   {"id": "boss_sa68", "owner": "b", "axis_body": "x_sa68", "r": 2.7, "z": [30.10, 34.15]},
   {"id": "stud_sa86s", "owner": "b", "axis_body": "x_sa86s", "r": 1.2, "z": [29.00, 30.10]},
   {"id": "boss_ju43", "owner": "b", "axis_body": "x_ju43", "r": 2.8, "z": [27.80, 34.15]},
   {"id": "stud_ju65s", "owner": "b", "axis_body": "x_ju65s", "r": 1.2, "z": [26.70, 27.80]},
   {"id": "boss_ma71", "owner": "b", "axis_body": "x_ma71", "r": 7.8, "z": [26.65, 34.15]},
   {"id": "stud_ma80s", "owner": "b", "axis_body": "x_ma80s", "r": 1.2, "z": [25.55, 26.65]}
  ],
  "pins": [
   {"id": "pin_lunar", "owner": "k", "local_xy": [9.6, 0.0], "r": 0.5, "z": [-7.80, -7.20], "slot_in": "k2"},
   {"id": "pin_saturn", "owner": "x_sa68", "local_xy": [14.37, 0.0], "r": 0.5, "z": [29.05, 30.15], "slot_in": "sa86s"},
   {"id": "pin_jupiter", "owner": "x_ju43", "local_xy": [8.22, 0.0], "r": 0.5, "z": [26.75, 27.85], "slot_in": "ju65s"},
   {"id": "pin_mars", "owner": "x_ma71", "local_xy": [10.0, 0.0], "r": 0.5, "z": [25.60, 26.70], "slot_in": "ma80s"},
   {"id": "pin_mercury", "owner": "x_me20", "local_xy": [14.04, 0.0], "r": 0.5, "z": [12.65, 14.90], "slot_in": "mercury_follower"},
   {"id": "pin_venus", "owner": "x_r1", "local_xy": [20.01, 0.0], "r": 0.5, "z": [13.80, 14.90], "slot_in": "venus_follower"},
   {"id": "pin_trueSun", "owner": "x_su56", "local_polar": ["d = followers[trueSun].pin_d", "angle = followers[trueSun].pin_phase_deg"], "r": 0.5, "z": [24.65, 33.25], "slot_in": "true_sun_follower"}
  ],
  "slots": "Every slot is a radial slot of width 1.1 with round ends, along local +x of its slot gear or follower, spanning (pin radius - offset - 0.6) .. (pin radius + offset + 0.6) from that body's axis (followers: i - d - 0.6 .. i + d + 0.6). Pin/slot gears (k1, k2, sa68, sa86s, ju43, ju65s, ma71, ma80s) have NO lightening windows."
 },
 "layers": {
  "front_under_b1": "F1 z 0.15..2.55: c2, d1, l2, m1. F2 z 1.60..3.80: c1, l1, b2. b1 z 3.95..6.65 (hub and rivets to 7.85).",
  "b1_to_strap": "L1 8.00-9.00 fx51 me72 vn44 | L2 9.15-10.15 fx49 nd62 | L3 10.30-11.30 mean-Sun bar | L4 11.45-12.45 nd64 nd48 | L5 12.60-13.60 Mercury follower | L6 13.75-14.75 Venus follower | L7 14.90-15.90 me20 disk + r1 disk (pins point back) | L8 16.05-17.65 me89 me40 me20 vn34 vn26 r1 | L9 17.80-18.80 D-plate | Strap 22.85-24.45",
  "strap_to_cp": "T1 24.60-25.40 true-Sun follower | T2 25.55-26.55 ma80s ma80o | T3 26.70-27.70 ma38 ma40 ma71 ju65s ju65o | T4 27.85-28.85 ju45 ju40 ju43 | T5 29.00-30.00 sa86s sa86o | T6 30.15-31.15 sa61 sa40 sa68 | CP 34.15-36.15 | C0 36.30-37.30 fx56 cp52 cp64 su56 | Sub-Plate 37.45-38.65",
  "rear": "Main Plate -2.0..0 | R1 -3.45..-2.15 b3 e1 | R2 -4.90..-3.60 d2 e2 | R3 -6.45..-5.05 e3 m3 | R4 -8.10..-6.60 e4 f1 e5 k1 m2 n1 | R5 -7.95..-7.35 k2 e6 (inside the e4 annulus) | -9.75..-8.25 f2 g1 n3 o1 | -11.50..-9.90 g2 h1 n2 p1 | -13.05..-11.55 h2 i1 p2 cal1 | back plate -16.5..-15.0",
  "swing_sectors": "Relative to b: the Mercury follower (L5) swings within -49..-3 deg and the Venus follower (L6) within 109..201 deg (r < 52). No b-carried arbor may cross L5 or L6 inside those sectors except the intended pins."
 },
 "structure": [
  {"id": "main_plate", "body": "frame", "status": "SURVIVING", "z": [-2.0, 0.0], "outline": "rounded rectangle x -88..88, y -160..140, corner r 4", "holes": "clearance holes r + 0.05 cut through the plate: fixed tube (r 2.3, pressed in, fused), d and m (r 1.05, shafts pass through), and e_inner, f, g, h, i, n, o, p, cal (r 1.05, shafts end at z -0.10 inside the hole); c and l studs fused on the front face; no blind bearings"},
  {"id": "back_plate", "body": "frame", "status": "RECONSTRUCTED", "z": [-16.5, -15.0], "outline": "same as main_plate", "holes": "clearance holes r 1.05 cut through the plate: n, g (shafts pass through to their pointers at z -18.2), o, cal, i (pass through to z -17.0), and m, e_inner, f, h, p (shafts end at z -16.40 inside the hole); spiral grooves cut through (width 1.2)"},
  {"id": "front_plate", "body": "frame", "status": "RECONSTRUCTED", "z": [40.0, 41.5], "outline": "same as main_plate", "holes": "central r 7.8; calendar hole circle (see dials.front)"},
  {"id": "frame_pillars", "body": "frame", "status": "RECONSTRUCTED", "count": 4, "xy": [[-82, 95], [82, 95], [-82, -95], [82, -95]], "radius": 2.5, "z": [-15.0, 40.0], "note": "pass through the Main Plate; keep clear of a1 and the crank bracket"},
  {"id": "crank_bracket", "body": "frame", "status": "HYPOTHETICAL", "shape": "L-bracket on the Main Plate at x 80..84, y -4..4, rising to z 21.5 with a bearing hole r 1.55 at z = a1 axis_z", "z": [0.0, 21.5]},
  {"id": "b1_structure", "body": "b", "status": "SURVIVING", "rim_inner_radius": 53.0, "hub_radius": 9.0, "hub_top_z": 7.85,
   "spokes": [{"name": "A", "angle_deg": 60, "feature": "flat 10.5x10.3 carrying the spA stud"}, {"name": "B", "angle_deg": -30, "feature": "bearing OD 9.7 at r 27.0 (spB)"},
              {"name": "C", "angle_deg": 240, "feature": "hole at r 25.6 (spC)"}, {"name": "D", "angle_deg": 150, "feature": "pierced block at r 31.8 carrying the mean-Sun bar post"}],
   "spoke_width": 15.5},
  {"id": "short_pillars", "body": "b", "status": "SURVIVING", "count": 2, "polar": [[56.0, -19.0], [56.0, 161.0]], "section": [5.0, 4.4], "z": [6.65, 22.85], "tenon_to": 24.45},
  {"id": "long_pillars", "body": "b", "status": "SURVIVING", "count": 4, "polar": [[58.5, 15.0], [58.5, 105.0], [58.5, 195.0], [58.5, 285.0]], "section": [9.1, 7.0], "z": [6.65, 34.15], "tenon_to": 36.15, "note": "outer face <= 63.3 (a1 keep-out)"},
  {"id": "mean_sun_bar", "body": "b", "status": "HYPOTHETICAL", "z": [10.30, 11.30], "shape": "bar width 3 from a collar on t_meanSun (r 1.9..3.4) to the Spoke D block at 31.8@150 deg, with a post down to b1 (z 6.65)"},
  {"id": "strap", "body": "b", "status": "HYPOTHETICAL", "z": [22.85, 24.45], "shape": "bar 123 x 24.8 along the -19/161 deg line through the centre, central hole r 7.8, holes for the short-pillar tenons and the me40/me20 studs"},
  {"id": "d_plate", "body": "b", "status": "SURVIVING", "z": [17.80, 18.80], "shape": "plate 25.3 wide centred on the 161 deg line, from 5.0 to 34.0 along that line (inner edge >= 4.15 from the centre), fixed to the Strap by 2 posts r 1.0 (z 18.80..22.85) placed away from the Venus sector r < 50; carries the vn26 and r1 studs"},
  {"id": "mercury_disk", "body": "x_me20", "status": "HYPOTHETICAL", "z": [14.90, 15.90], "radius": 15.5, "pin": {"radius": 0.5, "d": 14.04, "z": [12.60, 14.90]}},
  {"id": "venus_disk", "body": "x_r1", "status": "SURVIVING", "z": [14.90, 15.90], "radius": 21.5, "pin": {"radius": 0.5, "d": 20.01, "z": [13.75, 14.90]}},
  {"id": "mercury_follower", "body": "t_mercury", "status": "HYPOTHETICAL", "z": [12.60, 13.60], "shape": "lever from the tube to r 52 with a radial slot 21.96-0.6 .. 50.04+0.6, width 1.1"},
  {"id": "venus_follower", "body": "t_venus", "status": "HYPOTHETICAL", "z": [13.75, 14.75], "shape": "lever to r 49.5 with a slot 7.79-0.6 .. 47.81+0.6, width 1.1"},
  {"id": "true_sun_follower", "body": "t_trueSun", "status": "HYPOTHETICAL", "z": [24.60, 25.40], "shape": "lever to r 43.5 with a slot (i-d-0.6)..(i+d+0.6), width 1.1"},
  {"id": "true_sun_pin", "body": "x_su56", "status": "HYPOTHETICAL", "shape": "su56 arbor passes through the CP; behind the CP a crank disc (r 2.6, z 33.25..34.00) carries an eccentric pin r 0.5 at d = i/24 from the su56 axis, spanning z 24.60..33.25"},
  {"id": "cp", "body": "b", "status": "HYPOTHETICAL", "z": [34.15, 36.15], "shape": "disc r 65.0, central hole r 7.0 (the Date tube is fused to it), bearing holes for cp52/cp64/su56 arbors, boss mounts for the pin/slot pairs and idler studs"},
  {"id": "sub_plate", "body": "frame", "status": "HYPOTHETICAL", "z": [37.45, 38.65], "shape": "disc r 60 with central hole r 7.8; fx56 (bore 7.8) is joined to it by a spacer ring r 7.8..12.0, z 37.30..37.45 (frame); 3 standoffs r 2 at r 57 (90, 210, 330 deg) up to the front plate (z 38.65..40.0)"},
  {"id": "case", "body": "frame", "status": "RECONSTRUCTED", "shape": "wooden box, inner x -92..92, y -164..144, z -24..62, walls 5; front and back covers optional (hidden by default); crank shaft through the right wall (x = 92) at y 0, z = a1 axis_z, crank arm 25 long with a knob"}
 ],
 "dials": {
  "front": {
   "zodiac_ring": {"body": "frame", "status": "SURVIVING", "radii": [62.5, 70.0], "z_face": 41.5, "divisions": 360, "signs": 12, "labels": ["ΚΡΙΟΣ", "ΤΑΥΡΟΣ", "ΔΙΔΥΜΟΙ", "ΚΑΡΚΙΝΟΣ", "ΛΕΩΝ", "ΠΑΡΘΕΝΟΣ", "ΧΗΛΑΙ", "ΣΚΟΡΠΙΟΣ", "ΤΟΞΟΤΗΣ", "ΑΙΓΟΚΕΡΩΣ", "ΥΔΡΟΧΟΟΣ", "ΙΧΘΥΕΣ"], "orientation": "longitude 0 (start of Krios) on the +x axis (3 o'clock) so the mean Sun (b, local +x) is at longitude 0 at crank 0; longitudes increase CLOCKWISE seen from the front"},
   "calendar_ring": {"body": "frame", "note": "movable by hand in the original; modelled fixed", "status": "SURVIVING", "radii": [70.0, 79.0], "z": [41.65, 42.45], "day_divisions": 365, "months": 12, "epagomenal_days": 5, "month_labels": ["ΘΩΥΘ", "ΦΑΩΦΙ", "ΑΘΥΡ", "ΧΟΙΑΚ", "ΤΥΒΙ", "ΜΕΧΙΡ", "ΦΑΜΕΝΩΘ", "ΦΑΡΜΟΥΘΙ", "ΠΑΧΩΝ", "ΠΑΥΝΙ", "ΕΠΙΦΙ", "ΜΕΣΟΡΗ", "ΕΠΑΓΟΜΕΝΑΙ"],
                     "hole_circle": {"radius": 77.34, "count": 354, "count_alternatives": [355, 365], "hole_diameter": 0.8, "sources": ["B20", "WB24", "F21SI 6.4.2 (365)"]}},
   "cosmos_rings": [
     {"body": "t_saturn", "radii": [58.0, 62.0], "z": [43.30, 43.70], "marker_r": 60.0, "marker_local_deg": 0.0, "label": "Saturn"},
     {"body": "t_jupiter", "radii": [53.0, 57.0], "z": [43.85, 44.25], "marker_r": 55.0, "marker_local_deg": 0.0, "label": "Jupiter"},
     {"body": "t_mars", "radii": [48.0, 52.0], "z": [44.40, 44.80], "marker_r": 50.0, "marker_local_deg": 150.0, "label": "Mars"},
     {"body": "t_trueSun", "radii": [43.0, 47.0], "z": [44.95, 45.35], "marker_r": 45.0, "marker_local_deg": -150.0, "label": "true Sun (golden sphere r 1.6)"},
     {"body": "t_venus", "radii": [38.0, 42.0], "z": [45.50, 45.90], "marker_r": 40.0, "marker_local_deg": -155.0, "label": "Venus"},
     {"body": "t_mercury", "radii": [33.0, 37.0], "z": [46.05, 46.45], "marker_r": 35.0, "marker_local_deg": 26.0, "label": "Mercury"}],
   "cosmos_rings_note": "Each ring = annulus + a thin disc from its tube to the annulus at the same z. Radii are visual estimates from F21 Fig. 7 (LOW confidence). Marker = stone sphere r 1.2 (true Sun: golden sphere r 1.6) RESTING on the ring front face (centre z = ring z1 + sphere radius) at marker_r, at local angle marker_local_deg (math convention) of the ring body. Followers: marker_local_deg = -g0 so the display = mean Sun + elongation; superior planets: 180 + beta so retrograde happens at opposition.",
   "planet_display": {
    "purpose": "readability in the viewport and the video (colours are not historical)",
    "planets": [
     {"marker": "marker_trueSun (golden sphere of t_trueSun)", "label": "Soleil", "rgb_linear": [1.00, 0.72, 0.06]},
     {"marker": "Moon phase sphere (body q; label only, the sphere keeps its dark/silver halves)", "label": "Lune", "rgb_linear": [0.86, 0.88, 0.95]},
     {"marker": "marker of t_mercury", "label": "Mercure", "rgb_linear": [0.08, 0.60, 1.00]},
     {"marker": "marker of t_venus", "label": "Vénus", "rgb_linear": [0.10, 0.85, 0.30]},
     {"marker": "marker of t_mars", "label": "Mars", "rgb_linear": [1.00, 0.08, 0.05]},
     {"marker": "marker of t_jupiter", "label": "Jupiter", "rgb_linear": [1.00, 0.42, 0.02]},
     {"marker": "marker of t_saturn", "label": "Saturne", "rgb_linear": [0.62, 0.30, 1.00]}],
    "marker_material": "Principled: base colour = rgb, metallic 0, roughness 0.3, emission colour = rgb, strength 0.8; material.diffuse_color = rgb (Solid view)",
    "labels": "One FONT object per planet (built-in font, size 5.0, align centre/bottom, emission material of the planet colour, strength 2.0) plus a dark drop-shadow copy offset (+0.35, -0.35, -0.05). An anchor Empty is parented to the marker's body (matrix_parent_inverse identity) at the marker's bounding-box centre (Moon: centre of the whole phase sphere, (13, 0, 0) in B_q). The label has a COPY_LOCATION constraint targeting the anchor with use_x = use_y = True, use_z = False, use_offset = True; its own location = (0, sphere radius + 1.0, z) with z = 47.3 (above every ring and the Dragon Hand) or 60.0 for the Moon (in front of the Moon arm). The label therefore follows its planet, stays upright, sits just above it and is never hidden by a ring. No Python drivers.",
    "legend": "Fixed on the lower parapegma plate, visible from CAM_front34: title 'Planètes :' (size 6.0, dark) at (-78, -93, 42.25); row 1 at y -93: Soleil, Lune, Mercure, Vénus; row 2 at y -104: Mars, Jupiter, Saturne; each entry = sphere r 1.8 of the planet colour at (x + 1.8, y + 1.8, 44.05) + name (size 5.5) at (x + 4.8, y, 42.25), starting x = -44 and advancing by 4.8 + measured text width + 6.0.",
    "collection": "AM_LABELS (Empties, FONT objects and legend dots; status ANNOTATION). Excluded from the BVH and manifold checks and from the print export.",
    "retrograde_note": "Planet markers sometimes move backwards: this is the retrograde motion the pin-and-slot and follower mechanisms were built to show (superior planets at opposition, Mercury and Venus near inferior conjunction). The Dragon Hand always turns backwards (regression of the nodes)."
   },
   "date_pointer": {"body": "b", "z": [42.65, 43.15], "length": 78.5, "width": 2.0},
   "dragon_hand": {"body": "t_nodes", "z": [46.60, 47.00], "half_length": 30.0, "status": "HYPOTHETICAL"},
   "moon_pointer": {"body": "moon", "arm_z": [58.6, 59.4], "length": 62.0, "width": 3.0, "window": {"centre_u": 13.0, "diameter": 8.2, "ring_boss_r_out": 5.1}, "cap": "a top plate at the arm (z 58.6..59.4) plus the two hanger brackets of crowns.q1.hangers (u 2.3..2.9 and 16.8..17.4) carrying the q1 arbor at z 52.70; the q1 disc (r_out 5.55 about its axis, z 47.15..58.25) clears the arm by 0.35 and the Dragon Hand (z <= 47.0) by 0.15"},
   "parapegma": {"body": "frame", "status": "SURVIVING", "plates": [{"y": [82, 138]}, {"y": [-158, -82]}], "z": [41.5, 42.0], "x": [-80, 80], "note": "2 columns of engraved lines each (placeholder text)"}
  },
  "back": {
   "view_frame": "Back-view 2D coords (u, v) = (-x, y). Pointer angle psi measured CLOCKWISE seen from the back, from +v (12 o'clock): direction (u, v) = (sin psi, cos psi), i.e. world (x, y) = (-sin psi, cos psi).",
   "spiral_model": "Two-centre half-circle spiral (Anastasiou et al. 2014). k = floor(psi / 2pi), phi = psi - 2pi*k, R_k = r_start + k*pitch, delta = pitch/2. If phi < pi: rho = R_k. Else: rho = delta*cos(phi) + sqrt((R_k + delta)^2 - delta^2*sin(phi)^2). Second centre = dial centre + (0, +delta) in (u, v). Alternative (not default): Archimedean rho = r_start + pitch*psi/(2pi).",
   "metonic": {"centre": "N", "turns": 5, "cells": 235, "cells_per_turn": 47, "r_start": 44.0, "pitch": 5.2, "groove_width": 1.2, "rim_outer": 72.0, "pointer_body": "n", "pointer_rate_back_clockwise": "5/19", "pointer": {"z": [-18.2, -17.4], "length": 72.0}, "status": "SURVIVING"},
   "saros": {"centre": "G", "turns": 4, "cells": 223, "cells_per_turn": 55.75, "r_start": 44.0, "pitch": 6.5, "groove_width": 1.2, "rim_outer": 72.0, "pointer_body": "g", "pointer_rate_back_clockwise": "940/4237", "pointer": {"z": [-18.2, -17.4], "length": 72.0}, "glyphs": "eclipse glyph placeholders optional", "status": "SURVIVING"},
   "follower": "Each spiral pointer carries a radial slider (owned by the pointer body n or g) with a pin r 0.5 riding in the groove at rho(psi). psi_mod is computed from the crank c directly, never from the wrapped pointer rotation: Metonic psi_mod = 10*pi*fmod(fmod(c/19, 1) + 1, 1); Saros psi_mod = 8*pi*fmod(fmod(c*235/4237, 1) + 1, 1). rho(psi_mod) through a driver F-curve lookup table (>= 1800 keys, LINEAR; clear the 2 default keys first). The groove is the spiral offset by +-0.6 with round ends (r 0.6) centred on the spiral points at psi = 0 and psi = turns*2pi.",
   "subsidiary": [
     {"id": "olympiad", "centre": "O", "radius": 18.0, "sectors": 4, "labels": ["ΙΣΘΜΙΑ", "ΟΛΥΜΠΙΑ", "ΝΕΜΕΑ", "ΠΥΘΙΑ"], "sector_tilt_deg": 8, "pointer_body": "o", "pointer": {"z": [-17.0, -16.6], "length": 16.0}, "note": "turns anticlockwise seen from the back (+1/4)", "status": "SURVIVING"},
     {"id": "callippic", "centre": "cal", "radius": 18.0, "sectors": 4, "pointer_body": "cal", "pointer": {"z": [-17.0, -16.6], "length": 16.0}, "status": "RECONSTRUCTED"},
     {"id": "exeligmos", "centre": "I", "radius": 17.0, "sectors": 3, "labels": ["", "Η", "ΙΣΤ"], "label_note": "the stigma Ϛ (U+03DA) is missing from Blender's built-in font, so 16 is written ΙΣΤ", "pointer_body": "i", "pointer": {"z": [-17.0, -16.6], "length": 15.0}, "status": "SURVIVING"}],
   "centre_distance_N_G": 145.5
  }
 },
 "staging": {
  "purpose": "museum low-key presentation: the bronze glows on a dark backdrop, labels stay readable (chosen among 3 designs rendered side by side)",
  "collection": "AM_STAGE (datablocks STAGE_*), idempotent; the old LIGHT_* are hidden (render + viewport), never deleted",
  "ground": "seamless cyclorama: profile = floor from u = -1800 to 420, quarter-circle sweep of radius 260, then a wall up to 1400; width 3200 (16 segments); placed at (0, -10, ground_z), rotated about z by atan2(0.771, -0.637) = 129.6 deg (the wall faces the cameras). ground_z = min(lowest z of every visible mesh/text assembled incl. the case, lowest z after explode x3) - 6 mm (= -60.1). Material: charcoal Principled (0.034, 0.031, 0.029), roughness 0.55..0.72 from a noise texture (scale 0.35, detail 8, Object coordinates), specular IOR level 0.35. visible_glossy = False and hide_probe_sphere = True (the bronze reflects the world, not the floor). Hidden for the 'back' view.",
  "lights": "Each light: target point; position = target + (cos az cos el, sin az cos el, sin el) * dist (or 'loc'); aimed at the target; use_temperature with 'kelvin'; energies in W for a millimetre scene; AREA = RECTANGLE size x size_y with spread 180 deg; SPOT uses radius (shadow_soft_size), spot (deg), blend; visible_camera = False; 'only' = the single view that uses the light (else all views except 'back'); floor = light-linked to the backdrop only; nofloor = backdrop excluded (light linking collections STAGE_floor_only / STAGE_floor_excluded).",
  "rig": {"key": {"type": "AREA", "az": 188.0, "el": 44.0, "dist": 600.0, "target": [0.0, -10.0, 0.0], "energy": 400000.0, "kelvin": 3300, "size": [480.0, 300.0]}, "rim": {"type": "AREA", "az": 72.0, "el": 12.0, "dist": 520.0, "target": [0.0, -10.0, 10.0], "energy": 400000.0, "kelvin": 9500, "size": [520.0, 70.0], "nofloor": True}, "rim2": {"type": "AREA", "az": 215.0, "el": 12.0, "dist": 520.0, "target": [0.0, -10.0, 10.0], "energy": 160000.0, "kelvin": 9000, "size": [420.0, 60.0], "nofloor": True}, "fill": {"type": "AREA", "az": -40.0, "el": 30.0, "dist": 650.0, "target": [0.0, -10.0, 10.0], "energy": 90000.0, "kelvin": 5000, "size": [700.0, 500.0]}, "pool": {"type": "SPOT", "az": 129.6, "el": 30.0, "dist": 620.0, "target": [0.0, 0.0, 0.0], "energy": 300000.0, "kelvin": 2900, "radius": 45.0, "spot": 26.0, "blend": 0.85}, "top": {"type": "SPOT", "loc": [-35.0, 10.0, 650.0], "target": [-35.0, 10.0, 0.0], "energy": 250000.0, "kelvin": 3000, "radius": 25.0, "spot": 40.0, "blend": 0.9, "only": "front"}, "wash": {"type": "AREA", "az": 130.0, "el": 22.0, "dist": 650.0, "target": [0.0, -10.0, 20.0], "energy": 400000.0, "kelvin": 3000, "size": [900.0, 260.0]}, "floorpool": {"type": "SPOT", "az": 150.0, "el": 78.0, "dist": 900.0, "target": [0.0, -10.0, 0.0], "energy": 6000000.0, "kelvin": 3000, "radius": 80.0, "spot": 48.0, "blend": 1.0, "floor": True}, "xfill": {"type": "AREA", "az": -70.0, "el": 22.0, "dist": 720.0, "target": [0.0, -10.0, 60.0], "energy": 330000.0, "kelvin": 3500, "size": [800.0, 600.0], "only": "exploded", "nofloor": True}, "xtop": {"type": "AREA", "az": 150.0, "el": 68.0, "dist": 720.0, "target": [0.0, -10.0, 60.0], "energy": 350000.0, "kelvin": 3300, "size": [600.0, 600.0], "only": "exploded", "nofloor": True}, "under_key": {"type": "AREA", "az": 200.0, "el": -62.0, "dist": 600.0, "target": [0.0, -10.0, -18.0], "energy": 900000.0, "kelvin": 3300, "size": [520.0, 360.0], "only": "back"}, "under_rim": {"type": "AREA", "az": 20.0, "el": -20.0, "dist": 520.0, "target": [0.0, -10.0, -18.0], "energy": 400000.0, "kelvin": 9000, "size": [520.0, 80.0], "only": "back"}},
  "per_view": "'front': hide 'pool', use 'top'; 'back': hide the backdrop and every light except under_key/under_rim; 'exploded' (still and video): also turn on xfill and xtop; any other view (front34, anim): the front34 set.",
  "world": "Camera rays see (0.0045, 0.0044, 0.0045). Other rays: a dark room: base (0.006, 0.0058, 0.0056) mixed toward (0.07, 0.052, 0.036) by smoothstep(Generated.z, 0.35..0.95) (overhead diffuser), then toward (0.05, 0.036, 0.024) by 0.35*smoothstep(|z|, 0.35..0) (warm horizon band); Light Path 'Is Camera Ray' selects between them. sun_threshold 0, probe_resolution 1024.",
  "colour": "view transform AgX, look 'AgX - High Contrast', sRGB, exposure 0 (EEVEE) or -1.0 (Cycles), gamma 1",
  "eevee": "taa_render_samples 64 (video and stills), taa_samples 16, reprojection on; use_raytracing, method SCREEN, resolution '1', max roughness 0.55, screen quality 0.6, thickness 2.0, all denoise options on; fast GI: GLOBAL_ILLUMINATION, resolution '2', 8 steps, 2 rays, quality 0.5, distance 60, thickness near 3.0, bias 0.05; shadows on, pool '1024', 1 ray x 16 steps, resolution scale 1.0; light_threshold 0.01; clamp_surface_indirect 10; filter_size 1.5. Verify each property name by introspection (Blender 5.2) and skip missing ones with a log line.",
  "cycles": "samples 256 (stills), sample_clamp_indirect 10, blur_glossy 1.0, exposure -1.0",
  "materials": "AM_bronze roughness 0.30 (from 0.35); default patina 0.06"
 },
 "explode": {
  "control": "AM_Controller['explode'] float 0..1 (0 = assembled). Every part moves along z so that its z becomes 3*z at explode = 1.",
  "drivers": "For each visible MESH/FONT part (not in AM_HELPERS/AM_STAGE): K = 2 * (world z of its vertex centroid at crank 0); simple-expression driver on delta_location[2] = 'e*K' (e = SINGLE_PROP AM_Controller['explode']); clear the driver F-curve keys. Parts under B_a (x-axis) and B_q (radial axis) get no driver: B_a and B_q themselves get delta_location[2] = e*K with K = 2 * mean centroid z of their meshes. Planet labels use the K of their marker (the Moon label: K of B_q); legend objects use the K of the lower parapegma plate. Check: at explode = 1 every part with its own driver is at exactly 3x its assembled centroid z (legend dots excepted by design)."
 },
 "exploded_video": {
  "output": "out/renders/antikythera_eclate.mp4, 1280x720, 24 fps, 360 frames (15 s), EEVEE 64 samples, staging view 'exploded', case hidden",
  "timeline": "crank LINEAR 0 -> 2 years over frames 1..360; explode keys (BEZIER, auto-clamped) f1 0, f48 0, f144 1, f264 1, f336 0, f360 0",
  "camera": "XCAM (lens 45, clip 1..10000) parented to XCAM_pivot at (0, -10, 0) whose z rotation goes LINEAR from 10 to 80 deg; XCAM local location (0, -d, h) and XCAM_target z (TRACK_TO, -Z, up Y) keyed at f1/f48/f144/f264/f336/f360 = (d 470, h 300, z 18), (470, 300, 18), (720, 150, 58), (720, 150, 58), (470, 300, 18), (470, 300, 18)",
  "method": "build the clip in memory (new action on AM_Controller, never saved over the main crank action), render PNG frames by ranges into out/renders/frames_exploded/x_####.png, then encode once through the sequencer like the main video (frame_end 360); verify frame_duration == 360"
 },
 "materials": {
  "bronze": {"base_color_linear": [0.92, 0.70, 0.47], "metallic": 1.0, "roughness": 0.35, "note": "interpolated between copper and brass (physicallybased.info); approximation"},
  "patina": {"base_colors": ["verdigris ~ (0.18, 0.42, 0.34)", "cuprite brown ~ (0.22, 0.10, 0.06)"], "metallic": 0.0, "roughness": 0.8, "mix": "AO + noise through a colour ramp; mix factor driven by AM_Controller['patina'] (0 = new, 1 = museum)"},
  "wood": {"base_color_linear": [0.30, 0.18, 0.10], "roughness": 0.6},
  "status_debug_colors": {"SURVIVING": [0.72, 0.45, 0.16, 1], "RECONSTRUCTED": [0.16, 0.55, 0.48, 1], "HYPOTHETICAL": [0.50, 0.42, 0.78, 1]}
 },
 "collections": ["AM_SURVIVING", "AM_RECONSTRUCTED", "AM_HYPOTHETICAL", "AM_STRUCTURE", "AM_DIALS", "AM_CASE", "AM_HELPERS"],
 "print_profiles": {
  "resin_x1": {"scale": 1.0, "backlash_mm": 0.05, "axial_gap_mm": 0.15, "bore_clearance_mm": 0.05, "min_wall_mm": 0.4, "bed_mm": [218, 123]},
  "resin_x1_5": {"scale": 1.5, "backlash_mm": 0.08, "axial_gap_mm": 0.2, "bore_clearance_mm": 0.08, "min_wall_mm": 0.5, "bed_mm": [218, 123]},
  "fdm_x2": {"scale": 2.0, "backlash_mm": 0.20, "axial_gap_mm": 0.3, "bore_clearance_mm": 0.2, "min_wall_mm": 0.8, "bed_mm": [256, 256]},
  "rules": "Values are at print scale. Regenerate tooth outlines with the profile backlash (thinner teeth; crown teeth: shrink phi_lo/phi_hi by backlash/2/rho each), regenerate every bore, plate hole, pin slot (width 2*r_pin + 2*bore_clearance) and spiral groove with bore_clearance_mm, keep the scaled axis positions exactly, re-run the 2D interference check. min_wall_mm applies to rims, arms, hubs and slot/bore walls, not to tip lands (tip lands only reported; list teeth with tip land < 0.2*m_print as fragile). Export one STL per part from an UNPARENTED temporary copy in the part's body-local frame, plus one 3MF with all parts (unit millimeter). List every part larger than the bed (measured on the local copy); b1 at fdm_x2 is ~260 mm."
 },
 "render": {
  "preview": {"engine": "BLENDER_EEVEE", "resolution": [1280, 720]},
  "final": {"engine": "CYCLES", "device": "METAL", "resolution": [1920, 1080], "samples": 256, "denoiser": "OPENIMAGEDENOISE", "denoising_use_gpu": True},
  "animation": {"engine": "BLENDER_EEVEE", "frames": 480, "fps": 24, "crank_years": [0.0, 4.0], "format": "FFMPEG H264 mp4"},
  "cameras": ["front three-quarter", "front dial straight on", "back dials straight on", "exploded view (z offsets x3 by layer)"]
 },
 "sources": {
  "F21": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7955085/",
  "F21SI": "https://static-content.springer.com/esm/art%3A10.1038%2Fs41598-021-84310-w/MediaObjects/41598_2021_84310_MOESM4_ESM.pdf",
  "F06": "https://www.nature.com/articles/nature05357",
  "F06SI": "https://static-content.springer.com/esm/art%3A10.1038%2Fnature05357/MediaObjects/41586_2006_BFnature05357_MOESM1_ESM.pdf",
  "F08SI": "https://archive.nyu.edu/bitstream/2451/60882/2/Freeth_Jones_Steele_Bitsakis_2008_supplementary.pdf",
  "FJ12": "http://dlib.nyu.edu/awdl/isaw/isaw-papers/4/",
  "P74": "https://gwern.net/doc/history/1974-desollaprice.pdf",
  "B20": "https://bhi.co.uk/wp-content/uploads/2020/12/BHI-Antikythera-Mechanism-Evidence-of-a-Lunar-Calendar.pdf",
  "WB24": "https://arxiv.org/abs/2403.00040",
  "A14": "https://journals.sagepub.com/doi/abs/10.1177/0021828614537185",
  "SA25": "https://arxiv.org/abs/2504.00327",
  "V21": "https://arxiv.org/pdf/2204.11136", "V22": "https://arxiv.org/abs/2104.06181", "V24": "https://arxiv.org/abs/2412.07023",
  "E21": "https://digitalheritagelab.eu/wp-content/uploads/2025/03/heritage-04-00211-v4_compressed.pdf",
  "CDC16": "http://dlib.nyu.edu/awdl/isaw/isaw-papers/11/",
  "SEI": "https://pos.sissa.it/170/007/pdf"
 },
 "reference_values_days": {
  "tropical_year": 365.2422, "sidereal_month": 27.321661, "tropical_month": 27.321582, "synodic_month": 29.530589, "anomalistic_month": 27.554550,
  "draconic_month": 27.212221, "lunar_apsides_period": 3232.6054, "lunar_nodes_period_tropical": 6798.38, "lunar_nodes_period_sidereal": 6793.48,
  "metonic_235_synodic": 6939.6884, "saros_223_synodic": 6585.3213, "exeligmos": 19755.9639, "callippic_940_synodic": 27758.7536,
  "synodic_mercury": 115.88, "synodic_venus": 583.92, "synodic_mars": 779.94, "synodic_jupiter": 398.88, "synodic_saturn": 378.09,
  "sidereal_mars": 686.980, "sidereal_jupiter": 4332.589, "sidereal_saturn": 10759.22,
  "note": "Use for the report's error column only. Every train reproduces its ANCIENT period relation exactly; deviations from these modern values come from the relations themselves."
 },
 "unresolved_defaults": [
  "Axis XY coordinates are derived (not published); residuals against CT distances are within ~0.8 mm.",
  "Angles of H, I, O, P and the K direction on e3 are unpublished design choices.",
  "Cosmos ring radii are visual estimates from F21 Fig. 7.",
  "True-Sun eccentricity d = i/24 (Hipparchus); F21SI Table S9 does not give it. Solar apogee set at longitude 65.5 deg (Hipparchus) through followers[trueSun].pin_phase_deg = 84.5.",
  "Crown teeth (a1, q1) are envelope-generated against the involute spur (clearance 0.04 per flank) instead of the ancient hand-filed form.",
  "Lunar pin radius 9.6 mm (alternative 9.9).",
  "Calendar hole count 354 (alternatives 355, 365).",
  "Epoch phases are uncalibrated (all 0 at crank 0).",
  "Rear-layout handedness follows Price 1974 (mirror not excluded).",
  "Main Plate modelled 2.0 thick (Price: double sheet 2 x 2.0-2.3); turntable raised 3.05 mm instead of 2.7 to keep 0.15 mm axial gaps."
 ]
}
