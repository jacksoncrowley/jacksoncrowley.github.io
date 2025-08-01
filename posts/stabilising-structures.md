---
title: "Stabilising structures in GROMACS: some tips"
date: 2025-03-11
tags:
  - molecular-dynamics
  - gromacs
---
There are plenty of tricks one can exploit when trying to run MD simulations on starting structures that are, shall we say, less-than-stable. Such structures arise from the numerous and varied tools which are designed specifically for building membranes or complex biomolecular sructures, but you're far more likely to run in to problems when creating your own patchwork/frankenstein simulations, chopping and changing parts of various structures and sticking them back together again.

You'll quickly notice that coarse-grained forcefields such as Martini are far more resistant to inhumane treatment through brutal stabilisation methods, but in general, the below methods are broadly applicable. We'll start general, and get more specific.

## Be Brutal in Energy Minimisation
```
integrator    = steep
nsteps        = 10000
```
Without `emtol`, the energy minimisation will run for either `nsteps`, or until GROMACS is literally unable to compute the next step. In that case, you can also try switching the minimisation algorithm to `cg`, and running again, to see if it can continue. 

## Run GROMACS in Double Precision
Systems in which two particles almost perfectly overlap with one another can often lead to crashes as the integrator is simply unable to solve the possible next step, returning infinite forces and crashing the system. If GROMACS is compiled with double precision (found in the [manual](https://manual.gromacs.org/2024.4/install-guide/index.html#typical-installation)), all positions, velocities, and forces are computed with many extra zeroes, which possibly resolves perfect overlaps. It's slower than regular mixed-precision GROMACS, so it's probably only worthwhile for your earliest stabilisation stages.

## Slightly Decouple Everything
This is a trick I picked up while on my research visit to TU Dortmund. For unstable initial configurations, where for instance you've simply added a peptide directly into a membrane system at the interface without deleting anything. The trick is slightly decouple all of the non-bonded parameters in the system, making violent, explosive reactions far less likely, as the intermolecular forces are greatly reduced.

```
free-energy     = yes
couple-moltype  = system
couple-lambda0  = None  
couple-lambda1  = vdw-q
init-lambda     = 0.75 
```
At a lambda value of 1, all non-bonded interactions are on (Van der Waals and Coulomb, represented as `vdw-q`), but at lambda 0 they are fully switched off. We set the entire `system` to be coupled, and set the `init-lambda` to something lower than 1, reducing the strength of all non bonded interactions. 

What you might not know is that this also works during energy minimisation!

## Use Thermodynamic Slow Growth
In the case where we are inserting one substance (i.e. a protein or ligand) into another (membrane, solvent), we can selectively decouple it and gradually increase the lambda value from 0 to 1, smoothly turning on the interactions. 
```
free-energy     = yes
couple-moltype  = molecule_0
couple-lambda0  = None  
couple-lambda1  = vdw-q
init-lambda     = 0.00
delta-lambda    = 0.01
```

Here, `delta-lambda` refers to the amount that the decoupled molecule's lambda value will increment per simulation step. In our example, the non-bonded interactions of `molecule_0` will turn on from 0 to 1 in 100 steps. 

GROMACS will throw an error if the simulation would have the lambda value exceed 1. 

A really, really important note is that if a single molecule is decoupled, you should consider it effectively in vacuum; no longer interacting with the rest of the molecules, it's free to fly around wherever it wishes. Consider restraining it in place with [position restraints](https://manual.gromacs.org/2024.4/reference-manual/functions/restraints.html) if your `delta-lambda` process is rather slow [^1].

The [manual](https://manual.gromacs.org/2024.4/user-guide/mdp-options.html#free-energy-calculations), obviously, has plenty more information.

---

If you try all of these and the simulation is still not stable, I'd pretty confidently suggest that your structure has some very serious stability issues, likely in the bonded interactions. Until then, happy stabilisation!

[^1]: A spherical flat-bottomed potential is great here; see my [[flat-bottomed-potentials-gromacs|guide]] on how to implement them.
