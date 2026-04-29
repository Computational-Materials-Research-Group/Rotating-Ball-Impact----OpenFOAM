#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rotating Ball Impact - OpenFOAM 2412 Case Generator
====================================================
Ball radius  : 50 um
Impact speed : 300 m/s downward
Rotation     : 1e6 rad/s counterclockwise  (tip speed = 50 m/s)
Domain       : 200 x 350 um  (200 x 350 x 1 cells)
End time     : 1200 ns

WSL run sequence:
    blockMesh
    python3 generateRotatingU.py
    setFields
    interFoam
    touch rotatingBallImpact.foam
"""

import shutil
from pathlib import Path

OUT = Path("C:/Users/pedit/Downloads/rotatingBallImpact")


def w(rel, txt):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', newline='\n', encoding='utf-8') as f:
        f.write(txt)
    print("  wrote:", rel)


# ─────────────────────────────────────────────────────────────────────────────
def make_control_dict():
    w("system/controlDict", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}

application     interFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         1.2e-6;
deltaT          1e-11;
writeControl    adjustableRunTime;
writeInterval   2e-8;
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable yes;
adjustTimeStep  yes;
maxCo           0.4;
maxAlphaCo      0.4;
maxDeltaT       1e-8;
""")


def make_fv_schemes():
    w("system/fvSchemes", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSchemes;
}

ddtSchemes       { default Euler; }
gradSchemes      { default Gauss linear; }
divSchemes
{
    div(rhoPhi,U)    Gauss linearUpwind grad(U);
    div(phi,alpha)   Gauss vanLeer;
    div(phirb,alpha) Gauss linear;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes     { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes        { default corrected; }
""")


def make_fv_solution():
    w("system/fvSolution", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSolution;
}

solvers
{
    "alpha.ball.*"
    {
        nAlphaCorr      2;
        nAlphaSubCycles 2;
        cAlpha          1;
    }
    "pcorr.*" { solver PCG;   preconditioner DIC;  tolerance 1e-5; relTol 0;    }
    p_rgh      { solver PCG;  preconditioner DIC;  tolerance 1e-7; relTol 0.05; }
    p_rghFinal { solver PCG;  preconditioner DIC;  tolerance 1e-7; relTol 0;    }
    U          { solver PBiCG; preconditioner DILU; tolerance 1e-6; relTol 0;   }
}

PIMPLE
{
    momentumPredictor        no;
    nOuterCorrectors         1;
    nCorrectors              3;
    nNonOrthogonalCorrectors 0;
    pRefCell                 0;
    pRefValue                0;
}
""")


def make_block_mesh_dict():
    w("system/blockMeshDict", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}

scale 1e-6;

vertices
(
    (0   0   0)
    (200 0   0)
    (200 350 0)
    (0   350 0)
    (0   0   1)
    (200 0   1)
    (200 350 1)
    (0   350 1)
);

blocks
(
    hex (0 1 2 3 4 5 6 7) (200 350 1) simpleGrading (1 1 1)
);

edges ();

boundary
(
    bottom       { type wall;  faces ((0 1 5 4)); }
    sides        { type patch; faces ((0 4 7 3)(1 2 6 5)); }
    top          { type patch; faces ((3 7 6 2)); }
    frontAndBack { type empty; faces ((0 3 2 1)(4 5 6 7)); }
);
""")


def make_setfields_dict():
    w("system/setFieldsDict", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      setFieldsDict;
}

defaultFieldValues
(
    volScalarFieldValue alpha.ball 0
);

regions
(
    sphereToCell
    {
        centre  (1e-04 2.5e-04 0);
        radius  5e-05;
        fieldValues
        (
            volScalarFieldValue alpha.ball 1
        );
    }
);
""")


def make_transport_properties():
    w("constant/transportProperties", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      transportProperties;
}

phases (ball air);
ball { transportModel Newtonian; nu 1e-6;   rho 8900; }
air  { transportModel Newtonian; nu 1.5e-5; rho 1.0;  }
sigma 0;
""")


def make_turbulence_properties():
    w("constant/turbulenceProperties", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      turbulenceProperties;
}
simulationType laminar;
""")


def make_g():
    w("constant/g", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       uniformDimensionedVectorField;
    object      g;
}
dimensions  [0 1 -2 0 0 0 0];
value       (0 0 0);
""")


def make_alpha():
    w("0/alpha.ball", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      alpha.ball;
}
dimensions      [0 0 0 0 0 0 0];
internalField   uniform 0;
boundaryField
{
    bottom       { type zeroGradient; }
    sides        { type inletOutlet; inletValue uniform 0; value uniform 0; }
    top          { type inletOutlet; inletValue uniform 0; value uniform 0; }
    frontAndBack { type empty; }
}
""")


def make_p_rgh():
    w("0/p_rgh", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      p_rgh;
}
dimensions      [1 -1 -2 0 0 0 0];
internalField   uniform 0;
boundaryField
{
    bottom       { type fixedFluxPressure; value uniform 0; }
    sides        { type totalPressure; p0 uniform 0; value uniform 0; }
    top          { type totalPressure; p0 uniform 0; value uniform 0; }
    frontAndBack { type empty; }
}
""")


def make_u_placeholder():
    w("0/U", """\
FoamFile
{
    version     2.0;
    format      ascii;
    class       volVectorField;
    object      U;
}
dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);
boundaryField
{
    bottom       { type noSlip; }
    sides        { type pressureInletOutletVelocity; value uniform (0 0 0); }
    top          { type pressureInletOutletVelocity; value uniform (0 0 0); }
    frontAndBack { type empty; }
}
""")


# ─────────────────────────────────────────────────────────────────────────────
def make_rotating_u_script():
    """
    Builds generateRotatingU.py using a list of plain strings
    to avoid any encoding or escape issues entirely.

    Rotation formula (counterclockwise, omega about +z):
        Inside ball:
            Ux = -omega * (y - cy)
            Uy =  Vy   + omega * (x - cx)
        Outside ball:
            Ux = Uy = 0

    Cell centre for uniform blockMesh cell (i, j):
        x = (i + 0.5) * dx
        y = (j + 0.5) * dy
        index = j * nx + i
    """

    lines = [
        "#!/usr/bin/env python3",
        "# -*- coding: utf-8 -*-",
        "# generateRotatingU.py",
        "# Run AFTER blockMesh, BEFORE setFields and interFoam.",
        "# Writes 0/U with rigid-body rotation inside the ball.",
        "",
        "# Mesh parameters - must match blockMeshDict",
        "NX    = 200",
        "NY    = 350",
        "DX    = 1e-6",
        "DY    = 1e-6",
        "",
        "# Ball parameters",
        "CX    = 100e-6",
        "CY    = 250e-6",
        "R     = 50e-6",
        "VY    = -300.0",
        "OMEGA = 1.0e6",
        "",
        "print('Building rotation velocity field...')",
        "print('  Centre  : ({:.1f}, {:.1f}) um'.format(CX*1e6, CY*1e6))",
        "print('  Radius  : {:.1f} um'.format(R*1e6))",
        "print('  Vy      : {:.0f} m/s'.format(VY))",
        "print('  Omega   : {:.2e} rad/s'.format(OMEGA))",
        "print('  Tip spd : {:.1f} m/s'.format(OMEGA*R))",
        "",
        "R2      = R * R",
        "n_cells = NX * NY",
        "vels    = []",
        "n_ball  = 0",
        "",
        "for j in range(NY):",
        "    yc = (j + 0.5) * DY",
        "    for i in range(NX):",
        "        xc = (i + 0.5) * DX",
        "        if (xc - CX)**2 + (yc - CY)**2 <= R2:",
        "            ux = -OMEGA * (yc - CY)",
        "            uy =  VY + OMEGA * (xc - CX)",
        "            n_ball += 1",
        "        else:",
        "            ux = 0.0",
        "            uy = 0.0",
        "        vels.append((ux, uy))",
        "",
        "print('  Ball cells : {} / {}'.format(n_ball, n_cells))",
        "",
        "with open('0/U', 'w', newline='\\n', encoding='utf-8') as f:",
        "    f.write('FoamFile\\n')",
        "    f.write('{\\n')",
        "    f.write('    version     2.0;\\n')",
        "    f.write('    format      ascii;\\n')",
        "    f.write('    class       volVectorField;\\n')",
        "    f.write('    object      U;\\n')",
        "    f.write('}\\n')",
        "    f.write('\\n')",
        "    f.write('dimensions      [0 1 -1 0 0 0 0];\\n')",
        "    f.write('\\n')",
        "    f.write('internalField   nonuniform List<vector>\\n')",
        "    f.write('{}\\n'.format(n_cells))",
        "    f.write('(\\n')",
        "    for ux, uy in vels:",
        "        f.write('({:.6e} {:.6e} 0)\\n'.format(ux, uy))",
        "    f.write(');\\n')",
        "    f.write('\\n')",
        "    f.write('boundaryField\\n')",
        "    f.write('{\\n')",
        "    f.write('    bottom       { type noSlip; }\\n')",
        "    f.write('    sides        { type pressureInletOutletVelocity; value uniform (0 0 0); }\\n')",
        "    f.write('    top          { type pressureInletOutletVelocity; value uniform (0 0 0); }\\n')",
        "    f.write('    frontAndBack { type empty; }\\n')",
        "    f.write('}\\n')",
        "",
        "print('  Written: 0/U')",
        "print('Next steps: setFields   then   interFoam')",
    ]

    content = '\n'.join(lines) + '\n'

    out_path = OUT / 'generateRotatingU.py'
    with open(out_path, 'w', newline='\n', encoding='utf-8') as f:
        f.write(content)
    print("  wrote: generateRotatingU.py")


# ─────────────────────────────────────────────────────────────────────────────
def make_readme():
    w("README.md", """\
# Rotating Ball Impact - OpenFOAM 2412

## Geometry

  y=350um  _________________________________ top (outlet)
           |                               |
           |        ( O )  Ball            |
           |      centre (100, 250) um     |
           |      radius 50 um             |
           |                               |
  y=0      |_______________________________| substrate (wall)
           x=0                          x=200um

## Parameters

  Ball radius     : 50 um
  Impact velocity : 300 m/s downward
  Angular velocity: 1e6 rad/s counterclockwise
  Tip speed       : omega x R = 50 m/s
  Domain          : 200 x 350 um  (200 x 350 cells, 1 um/cell)
  End time        : 1200 ns
  Material        : Copper ball in Air

## Rotation Physics

  Counterclockwise (OMEGA > 0):
    Left side  -> moves DOWN  (adds to impact velocity)
    Right side -> moves UP    (opposes impact velocity)
    Result     -> asymmetric splat, left jet faster than right

  To switch to clockwise (topspin): set OMEGA = -1.0e6

## WSL Run Sequence

  cp -r /mnt/c/Users/pedit/Downloads/rotatingBallImpact ~/
  cd ~/rotatingBallImpact
  source /usr/lib/openfoam/openfoam2412/etc/bashrc
  blockMesh
  python3 generateRotatingU.py
  setFields
  interFoam
  touch rotatingBallImpact.foam

## Copy Results to Windows

  cp -r ~/rotatingBallImpact /mnt/c/Users/pedit/Downloads/rotatingBallImpact_results

## ParaView

  Open rotatingBallImpact.foam -> OpenFOAMReader -> Apply
  Filters -> Cell Data to Point Data   (removes pixelation)
  Colour by alpha.ball                 (see asymmetric splat)
  Colour by U                          (see rotation wake)
  Press Play
""")


# ─────────────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 55)
    print("  ROTATING BALL IMPACT - CASE GENERATOR")
    print("=" * 55)

    if OUT.exists():
        shutil.rmtree(OUT)
    for d in ['0', 'constant', 'system']:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    print("\nDirectories created")

    print("\nSystem files...")
    make_control_dict()
    make_fv_schemes()
    make_fv_solution()
    make_block_mesh_dict()
    make_setfields_dict()

    print("\nConstant files...")
    make_transport_properties()
    make_turbulence_properties()
    make_g()

    print("\nInitial conditions...")
    make_alpha()
    make_p_rgh()
    make_u_placeholder()

    print("\nRotation script...")
    make_rotating_u_script()

    print("\nDocumentation...")
    make_readme()

    print()
    print("=" * 55)
    print("  DONE ->", OUT)
    print("=" * 55)
    print()
    print("WSL commands:")
    print("  cp -r /mnt/c/Users/pedit/Downloads/rotatingBallImpact ~/")
    print("  cd ~/rotatingBallImpact")
    print("  source /usr/lib/openfoam/openfoam2412/etc/bashrc")
    print("  blockMesh")
    print("  python3 generateRotatingU.py")
    print("  setFields")
    print("  interFoam")
    print("  touch rotatingBallImpact.foam")
    print()


if __name__ == "__main__":
    main()
