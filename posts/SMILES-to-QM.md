
---
title: 'My first QM: From SMILES string to dihedral scan'
date: "2024-08-01"
tags: ["qm", "psi4"]
---

This post goes over my first attempt at starting with nothing but a SMILES string, converting that into a molecule file with optimised geometry, and performing some basic QM calculations in Psi4 to do a dihedral scan. There are also a few notes on quantum chemistry, but be warned: having never formally studied the stuff, I may have made some extremely embarassing errors (and am very open to being corrected). 

# my first quantum chemistry calculations I: from SMILES string to dihedral scan

When making coarse-grained (CG) parameters for molecular dynamics (MD) simulations, we need reference data from atomistic simulations in order to validate that we're not doing anything completely nonsensical.

My dilemma, however, is that I want to make CG parameters for a molecule that doesn't have complete atomistic parameters. I stick two pre-existing combinations of molecules together, add bonds, angles, and dihedrals, and then I find out that one dihedral is missing. 

No easy way around it: to parameterise my missing dihedral, I'm going to have to do the quantum mechanical calculations myself.

## attempting to understand the basics of *ab initio* computational chemistry

In MD simulations, we're using classical mechanics, and considering an atom as a single entity... which obviously, it isn't.

When we do *ab initio* QM, we really start from nothing, and use theory alone to calculate molecular properties. This is done by solving the Schrödinger Equation[^1]:

$
\hat{H} \Psi = E \Psi
$

Where $\hat{H}$ is the hamiltonian, and the uppercase psi $\Psi$ is the wave function. It's this wave function that we're attempting to calculate, as it is what contains all of the information in the system. 

There are a variety of **methods** to do this; the [Hartree-Fock](https://en.wikipedia.org/wiki/Hartree%E2%80%93Fock_method)(HF) is widely known and has been around for decades, although there are plenty of others, including *post*-Hartree-Fock methods like **Møller–Plesset perturbation theory** (MP).

Once we have our method, we need to choose the appropriate mathematical functions to represent the electron orbitals. This set of functions are called the **basis set**.

With the two working in tandem, we can calculate the wave function, and extract the information we're really after, namely potential energy. This combination of method and basis set will vary from system to system, a constant interplay between computational cost, accuracy, and applicability. New methods and basis sets are continually being developed, as what we're really doing is calculating an approximation. 

We call the combination of method and basis set the **level of theory**, which describes the degree of approximation used to solve the Schrödinger equation for our system, expressed as:

> **Method/Basis Set**
>
> i.e.
> 
> **HF/6-31G***
>
> **MP2/CC-PVDZ**

Remember, kids, everything is a model. And you know [what they say about models](https://en.wikipedia.org/wiki/All_models_are_wrong).


## setting up
Of course, we need a software package to take care of this for us. I've opted to go with [Psi4](https://psicode.org/), a pretty-widely used open-source package that runs using python, built atop C++. I'm comfortable enough with python, and more importantly, I *really* didn't want to have to learn piece of software, and Psi4 looked legit and easy enough to make work. I set up a new conda environment and got started.


## getting a starting structure from a SMILES string
The dihedral I want to parameterise comes from cholesteryl oleate, an awfully large molecule (by QM standards, maybe). I decided instead to take a small portion which has the dihedral I want, a [cyclohexyl acetate](https://pubchem.ncbi.nlm.nih.gov/compound/Cyclohexyl-acetate):

I can take the SMILES string and generate a 3d structure using ```openbabel```[^2]:
```
openbabel -:"CC(=O)OC1CCCCC1" -oxyz -O CHA.xyz --gen3d # generating an .xyz file
```

Generating an .xyz file [^3], which looks like:

```
24

C          1.11274        0.33165       -0.17130
C          2.59623        0.29037       -0.37507
O          3.14111       -0.14618       -1.37891
O          3.22834        0.83932        0.69728
C          4.66678        0.88784        0.63289
C          5.25460       -0.47465        1.01489
C          6.77417       -0.42078        1.13132
C          7.21986        0.65899        2.11295
C          6.64390        2.02281        1.74361
C          5.12562        1.97323        1.61144
H          0.63303       -0.37064       -0.85930
H          0.74337        1.34120       -0.36552
H          0.86392        0.02453        0.84803
H          4.98756        1.17247       -0.37805
H          4.96967       -1.23172        0.27519
H          4.81832       -0.81073        1.96443
H          7.20956       -0.22018        0.14471
H          7.15454       -1.39532        1.45697
H          8.31417        0.71259        2.13226
H          6.89497        0.38761        3.12510
H          7.08235        2.35996        0.79633
H          6.92364        2.75926        2.50528
H          4.74681        2.94859        1.28212
H          4.67278        1.79802        2.59618
```

It's an extremely simple format: the first line shows us we have 24 atoms, the second line is blank, but you can write a descriptor "i.e. Cyclohexyl acetate"[^4], and the rest of the lines are organised to show the atom type and it's x, y, z cartesian coordinates. 

## optimising the geometry
Using the ```obminimize``` function of ```openbabel```, we can perform a basic energy minimisation of our molecule.

```obminimize CHA.xyz > CHA.2.xyz```

But we really should optimise our starting geometry as much as possible, and so we can use our QM engine to optimise the geometry further in accordance with the level of theory we've chosen. Since I want to generate atomistic parameters for the CHARMM36 MD forcefield, and previous similar parameterisation efforts have used the MP2/CC-PVDZ level of theory, I think it's where I'll start.

Psi4 has a jupyter/python API, but it also takes an input file written in ```psithon```; basically python with some extra, psi4-specific stuff.

My input file to optimise the geometry of our pre-optimised molecule (```psi4_optimise.dat```) is as follows:

```
import psi4

memory 16GB

molecule = psi4.geometry("""
24
CHA.2.xyz 
C          1.04300       -0.28100        0.19400
C          2.52100       -0.11700        0.37800
O          3.04000        0.79800        1.00200
O          3.18000       -1.15100       -0.20900
C          4.61600       -1.14900       -0.08900
C          5.22900       -0.20700       -1.13100
C          6.74900       -0.32100       -1.17500
C          7.19400       -1.76100       -1.40900
C          6.60100       -2.70400       -0.36700
C          5.08200       -2.59100       -0.31300
H          0.55300        0.69000        0.30900
H          0.65700       -0.97900        0.93900
H          0.82700       -0.64600       -0.81400
H          4.90800       -0.84100        0.92300
H          4.94500        0.83000       -0.91600
H          4.80900       -0.42900       -2.12100
H          7.17100        0.04300       -0.23000
H          7.14500        0.32100       -1.97000
H          8.28800       -1.82000       -1.38100
H          6.88200       -2.08100       -2.41100
H          7.02100       -2.47100        0.61900
H          6.88500       -3.73700       -0.60000
H          4.68700       -3.23100        0.48500
H          4.64800       -2.97900       -1.24400
""")
set {
    basis cc-pvdz
    energy mp2
    scf_type df
}
optimize('scf')

molecule.save_xyz_file("CHA.3.xyz",1)
```

```scf_type df```, by the way, refers to the **Self-Consistent Field** procedure, which is the iterative process of solving the Schrödinger equation repeatedly to update the coefficients describing our orbitals, which we repeat until they converge. **Density Fitting** (DF)-SCF is a way of speeding up the procedure by introducing more approximations, although apparently the loss of accuracy is quite minimal.



Running on 4 cores with ```psi4 psi4_optimise.dat -n 4```, it finishes in about 3 minutes.

## the dihedral scan
When doing a dihedral scan, what we're doing is fixing this dihedral at a given value, optimising the geometry to calculate the potential energy on the system, rotating the dihedral by a small amount, and repeating. We then return the potential energy vs. dihedral angle at the end, to plot the potential energy landscape (is this a correct term?) of the dihedral.

I know from looking at the structure that the dihedral I'm after is D(2,4,5,10), where the numbers are the atom indices in our input structure. When I look in the output file, ```psi4_optimise.out```, I can look for the value of this dihedral angle in the final optimisation step, and I see:

```
Coordinate      Previous         Force          Change          New
...
D(2,4,5,10)     153.95468       -0.00000       -0.00160     153.95308
```
Giving us an optimised dihedral value of 153.95308 once the program has converged. 

This is our starting point. Since I want to do a 360 degree scan at 10 degree intervals, I write a simple function to start indexing at 150 and work it's way all around, back to 140, where the scan will finish:

```
def define_angles(psi=0):
    angles = np.arange(0, 360, 10) - 170
    idx = np.where(angles == int(psi))[0][0]
    return(np.concatenate([angles[idx:], angles[:idx]]))
```
This is just generating a list from -170 to 180, and then deciding to start from our chosen ```psi``` value by cutting the original list at that point and rearranging it.

The actual implementation of the dihedral scan will look something like this:

```
dih_range = define_angles(150)

for psi in dih_range:
    geometric_keywords = {
      'coordsys' : 'tric',
      'constraints' : {
      'set' : [{'type'    : 'dihedral',
                'indices' : [1, 3, 4, 13],
                'value'   : psi }]
      }
    }
    E = optimize('scf', engine='geometric', optimizer_keywords=geometric_keywords)
    out = f"CHA.{psi}.xyz"
    print(psi, E)
    PES_C.append((psi, E))
    molecule.save_xyz_file(out,1)
```

And voila - provided I haven't done anything horribly wrong, we have successfully done our dihedral scan!

[^1]: this is the time-independent form of the equation; there's also a time-dependent form, given as:
$\left[ -\frac{\hbar^2}{2m} \nabla^2 + V(\mathbf{r}) \right] \Psi(\mathbf{r}) = E \Psi(\mathbf{r})$

[^2]: ```conda install openbabel -c conda-forge```

[^3]: If you want to write out the pdb with openbabel so that you can visualise it using something like VMD, run ```openbabel -:"CC(=O)OC1CCCCC1" -opdb -O CHA.pdb --gen3d```

[^4]: In fact, maybe you *should* write a descriptor, as I sometimes got errors parsing the file in later steps with ```psi4``` which would simply skip the blank line.
