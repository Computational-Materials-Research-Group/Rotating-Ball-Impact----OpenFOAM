# Rotating Ball Impact -- OpenFOAM `interFoam`

<p align="center">
  <img src="https://img.shields.io/badge/OpenFOAM-2412-blue?style=for-the-badge&logo=gnu&logoColor=white"/>
  <img src="https://img.shields.io/badge/Solver-interFoam-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/VOF-Two%20Phase-red?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Rotation-Rigid%20Body%20VOF-purple?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/ParaView-Visualization-green?style=for-the-badge"/>
</p>

<p align="center">
  A 2D Volume-of-Fluid (VOF) simulation of a <b>rotating copper ball impacting a rigid substrate</b>
  at 300 m/s using OpenFOAM's <code>interFoam</code> solver. The ball spins at 10^6 rad/s
  (counterclockwise), inducing an asymmetric splat, left-right velocity dipole, and
  Magnus-like wake asymmetry over 1200 nanoseconds of impact physics.
</p>

<img width="1008" height="772" alt="ROTATING BALL" src="https://github.com/user-attachments/assets/e75a901d-da9d-425e-8f46-999c10c2efa3" />

---

## Physics

High-velocity impact of a rotating fluid ball involves coupled translational and rotational
inertia, VOF interface deformation, and asymmetric pressure-driven jetting. This simulation captures:

- Two-phase incompressible VOF transport via the `alpha.ball` phase-fraction field
- Rigid-body rotation initial condition stamped cell-by-cell via Python helper script
- PIMPLE pressure-velocity coupling with inner correctors for impact stability
- Asymmetric jetting driven by rotation -- left jet faster than right (counterclockwise spin)
- Magnus-like velocity dipole visible in the `Ux` component field during free-fall
- Laminar flow assumption; surface tension neglected (`sigma = 0`)

---

## Geometry

```
  y=350um  _________________________________________ top (outlet)
           |                                       |
           |                                       |
           |           ( O )  Ball                 |
           |         centre (100, 250) um          |
           |         radius 50 um                  |
           |                                       |
           |                                       |
  y=0      |_______________________________________| substrate (wall)
           x=0                                  x=200um
```

| Boundary    | Type    | Role                        |
|-------------|---------|----------------------------|
| `bottom`    | wall    | Rigid no-slip substrate     |
| `sides`     | patch   | `pressureInletOutletVelocity` + `totalPressure` |
| `top`       | patch   | Open outlet                 |
| `frontAndBack` | empty | 2D planar simulation       |

---

## Rotation Physics

```
Counterclockwise spin (OMEGA = +1e6 rad/s):

        <- top moves right
   v left                right ^
        -> bottom moves left

At impact contact point:
  Left edge  : Vy_impact + Vy_rotation  ->  FASTER downward jet
  Right edge : Vy_impact - Vy_rotation  ->  SLOWER upward resistance

Result: asymmetric splat, left jet spreads farther than right.
```

Rotation velocity at any cell centre `(x, y)` inside ball:

```
Ux = -omega * (y - cy)
Uy =  Vy   + omega * (x - cx)
```

Stamped by `generateRotatingU.py` as a `nonuniform List<vector>` internal field.

---

## Parameters

### Ball

| Parameter | Value | Unit |
|-----------|-------|------|
| Radius | 50 | um |
| Centre | (100, 250) | um |
| Impact velocity Vy | -300 | m/s |
| Angular velocity omega | 1x10^6 | rad/s |
| Tip speed omegaxR | 50 | m/s |
| Density rho | 8900 | kg/m^3 |
| Kinematic viscosity nu | 1x10^-^6 | m^2/s |

### Air

| Parameter | Value | Unit |
|-----------|-------|------|
| Density rho | 1.0 | kg/m^3 |
| Kinematic viscosity nu | 1.5x10^-5 | m^2/s |

### Domain & Time

| Parameter | Value |
|-----------|-------|
| Domain | 200 x 350 x 1 um |
| Cells | 200 x 350 x 1 = 70,000 |
| Cell size | 1 um/cell |
| End time | 1200 ns |
| max Co | 0.4 |
| Write interval | 20 ns |

---

## Key Physics Timeline

| Time (ns) | Event |
|-----------|-------|
| 0 | Ball at (100, 250) um with spin + impact velocity |
| 0-600 | Free-fall; rotation dipole visible in Ux field |
| ~833 | First contact with substrate (250 um / 300 m/s) |
| 833-1000 | Lateral jetting; left jet faster than right |
| 1000-1200 | Asymmetric splat fully developed; wake vortex shedding |

---

## Repository Structure

```
rotatingBallImpact/
|
|-- rotatingBallImpact.py       # Main case generator (run on Windows/Anaconda)
|
|-- 0/
|   |-- alpha.ball              # Phase fraction  (all 0; setFields stamps sphere)
|   |-- U                       # Velocity        (overwritten by generateRotatingU.py)
|   |-- p_rgh                   # Modified pressure
|
|-- constant/
|   |-- transportProperties     # Ball + air density, viscosity, sigma=0
|   |-- turbulenceProperties    # simulationType laminar
|   |-- g                       # Gravity (0 0 0) - inertia dominates
|
|-- system/
|   |-- controlDict             # endTime=1.2e-6, maxCo=0.4
|   |-- fvSchemes               # vanLeer alpha, linearUpwind U
|   |-- fvSolution              # PIMPLE + pRefCell
|   |-- blockMeshDict           # 200x350x1 um, 200x350x1 cells
|   |-- setFieldsDict           # sphereToCell stamps alpha.ball=1
|
|-- generateRotatingU.py        # AUTO-GENERATED - writes 0/U with rotation profile
|-- README.md                   # This file
```

---

## How to Run

### Requirements
- OpenFOAM v2412: https://openfoam.com
- Python 3.x (Anaconda or system): https://python.org
- ParaView v5.x: https://paraview.org
- WSL2 (Windows Subsystem for Linux)

### Step 1 -- Generate the case (Windows / Anaconda)

```bash
python rotatingBallImpact.py
```

### Step 2 -- Copy to WSL Linux filesystem

```bash
cp -r /mnt/c/Users/pedit/Downloads/rotatingBallImpact ~/
cd ~/rotatingBallImpact
```

### Step 3 -- Source OpenFOAM

```bash
source /usr/lib/openfoam/openfoam2412/etc/bashrc
```

### Step 4 -- Generate mesh

```bash
blockMesh
```

Expected: 70,000 cells, bounding box `(0,0,0) -> (200um, 350um, 1um)`.

### Step 5 -- Stamp rotation velocity field

```bash
python3 generateRotatingU.py
```

Expected output:
```
Ball cells : 7860 / 70000
Written: 0/U
```

Verify:
```bash
grep "internalField" 0/U
# Must show: internalField   nonuniform List<vector>
```

### Step 6 -- Stamp phase fraction

```bash
setFields
```

Expected: `Selected 7854/70000 cells`

### Step 7 -- Run simulation

```bash
interFoam
```

Expected wall time: ~5-8 minutes. You will see Courant max ~0.4 throughout.

### Step 8 -- Visualise

```bash
touch rotatingBallImpact.foam
cp -r ~/rotatingBallImpact /mnt/c/Users/pedit/Downloads/rotatingBallImpact_results
```

---

## Visualization in ParaView

### Setup
1. `File > Open` -> `rotatingBallImpact.foam` -> **OpenFOAMReader** -> Apply
2. `Filters -> Cell Data to Point Data` -> Apply  *(removes pixelation)*

### Option A -- Ball shape and splat asymmetry
```
Colour field : alpha.ball
Colour map   : Blue-Red
Press Play
-> Watch left jet spread farther than right after impact
```

### Option B -- Rotation dipole (best during free-fall 0-833 ns)
```
Colour field : U  ->  Component X
Rescale      : Custom range  -50 to +50
Colour map   : Cool to Warm  (diverging)
-> Blue on right (fluid moving left), Red on left (fluid moving right)
-> Classic dipole signature of counterclockwise spin
```

### Option C -- Full velocity magnitude
```
Colour field : U  ->  Magnitude
-> High speed jetting rim at substrate contact
-> Asymmetric: left rim faster than right
```

### Option D -- Vorticity / wake asymmetry
```
Filters -> Calculator
Result name : Vorticity
Expression  : U_Y_X - U_X_Y    (approximation for 2D)
-> Asymmetric vortex wake behind impacting rotating ball
```

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Courant = 0` throughout | `generateRotatingU.py` not run in WSL | Run `python3 generateRotatingU.py` inside WSL case dir |
| `internalField uniform (0 0 0)` | Script ran from Windows not WSL | Always run from `~/rotatingBallImpact` in WSL |
| `Unable to set reference cell` | Missing `pRefCell` in PIMPLE | Add `pRefCell 0; pRefValue 0;` to fvSolution PIMPLE block |
| Continuity error on outflow | Wrong pressure BC on sides/top | Use `totalPressure` not `fixedFluxPressure` on open patches |
| Ball not moving after 600 ns | End time too short | Set `endTime 1.2e-6` -- ball needs 833 ns to reach substrate |
| Pixelated result in ParaView | Cell-centred data displayed raw | Apply `Filters -> Cell Data to Point Data` |
| `charmap codec` error on Windows | Python writing non-ASCII | Add `encoding='utf-8'` to all `open()` calls |

---

## Extending the Model

| Extension | What to change |
|-----------|----------------|
| Clockwise spin (topspin) | Set `OMEGA = -1.0e6` in `generateRotatingU.py` |
| Faster spin | Increase `OMEGA`; reduce `maxCo` for stability |
| Oblique impact (angled) | Add `Vx = 100.0` alongside `Vy = -300.0` |
| Larger ball | Increase `R`, expand domain `Ly`, update `blockMeshDict` |
| Multiple rotating balls | Add more `sphereToCell` regions + loop in rotation script |
| Elastic substrate | Couple with `solidDisplacementFoam` |
| Compressible gas | Switch to `compressibleInterFoam` |
| 3D simulation | Replace `empty` patches with `wedge` for axisymmetric |
| Different material | Update `rho` and `nu` in `transportProperties` |

---

## Citation

```bibtex
@software{mishra_2026_rotatingball,
  author    = {Mishra, A.},
  title     = {Rotating Ball Impact -- OpenFOAM},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19896300},
  url       = {https://doi.org/10.5281/zenodo.19896300}
}
```

> Mishra, A. (2026). *Rotating Ball Impact -- OpenFOAM*. Zenodo. https://doi.org/10.5281/zenodo.19896300

---

## Author

**akshansh11**
GitHub: https://github.com/akshansh11

---

## License

<p align="center">
  <a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">
    <img alt="Creative Commons Licence" style="border-width:0; margin: 12px 0;"
      src="https://licensebuttons.net/l/by-nc/4.0/88x31.png"/>
  </a>
  <br/>
  <a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">
    Creative Commons Attribution-NonCommercial 4.0 International License
  </a>
</p>

This work is licensed under a **Creative Commons Attribution-NonCommercial 4.0 International License**.

You are free to:
- **Share** -- copy and redistribute the material in any medium or format
- **Adapt** -- remix, transform, and build upon the material

Under the following terms:
- **Attribution** -- You must give appropriate credit to akshansh11 and link to this repository
- **NonCommercial** -- You may not use the material for commercial purposes

Copyright (c) 2026 akshansh11. All rights reserved for commercial use.
