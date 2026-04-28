---
title: Running Tedious Tools in Parallel with Python Subprocesses and Async
date: 2026-04-28
description: A minimal functional guide to running command line tools and other packages in parallel using Python's asyncio package, using GROMACS as an example, but easily extendable.
tags:
  - protocol
  - python
---
I recently made the mistake at looking at some of my workflows from the start of my Ph.D. 600-line bash scripts which would run all day, containing many individual steps: if step B failed, then steps C through G would run[^1], generating an awful amount of mess.

I eventually learnt to use python subprocesses and async to run my unix-based tools workflows, and so here's a brief little guide to save you time and possibly hours of headache.

When using compiled analysis tools, its not uncommon that they simply cannot be parallelised: running only a single cpu core or thread. Modern CPUs have 8 or 16 cores: more poweful workstations could have 32, 40, or more.

Oftentimes, these tools might only take five or ten minutes to run. That's fine, but what if you have a few different configurations of systems? 

Let's take the tool to calculate the root mean squared fluctuation (RMSF) from the GROMACS software package [^2]. `gmx rmsf` runs from the command line and processes the molecular dynamics (MD) trajectory from start to finish. Even though it is bound to single thread by default, all things considered, it's already pretty fast at what it does.

## A Basic Synchronous Subprocess Call
```python
import subprocess

def rmsf(tpr, traj, output):
	subprocess.run(
		f"{gmx} rmsf -s {tpr} -f {traj} -o {output} -res yes",
	    shell=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
		)
```
Called by:
```python
rmsf(
	tpr="POPC.tpr", 
	xtc="POPC.xtc", 
	output="POPC.xvg"
	)
```
This is quite straightforward: `subprocess.call` runs the command in the string as if it were being typed directly into the command line (this is why we specify `shell=True`). The output is captured in `stdout`, and any errors are captured in `stderr`. 

This is already a marked upgrade to simply running a big bash file: capturing the `stdout` and `stderr` as text will allow you to parse them as plain text strings and do lots of nice automation, or otherwise kill a workflow if an error is detected and stop it from writing out lots of garbage files or plenty of other confusing and annoying things.

But what if we have several systems we want to do? That could be easily be an hour or two of computation if our systems are big enough, not to mention the very likely need to rerun things during the initial development phase. There's something quite frustrating about running such long analyses while most of the cpu cores sit there, idle.

## How to Run A Subprocess Asynchronously with `asyncio`
By importing the default python package `asyncio`:
```python
import asyncio
```
We can rewrite the earlier function, with some new keywords:
```python
async def rmsf(tpr, traj, output):
    process = await asyncio.create_subprocess_shell(
        f"gmx rmsf -s {tpr} -f {xtc} -o {output} -res yes",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate(input=b"Protein\n")
    
    if process.returncode != 0:
        raise RuntimeError(f"rmsf failed: {stderr.decode()}")
```
The most important things to note:
- The `aync` keyword passed right at the start before function def
- The subprocess command being rewritten as `asyncio.create_subprocess_shell`
- The subprocess call itself being wrapped in a function (called `process` here)
- The `await` keyword being called just before the `process.communicate`call
- An optional extra: showing how we can pass input by specifying `stdin` and then passing an `input` to `process.communicate`

And then running it with the key command `await`:
```python
tasks = []
systems = ["DOPA", "POPC", "POPS", "POPG", "DOPC", "CHOL"]
for system in systems:
	xtc = f"{system}.xtc"
	tpr = f"{system}.tpr"
	output = f"{system}.xvg"
    tasks.append(rmsf(tpr, traj, output))
await asyncio.run(asyncio.gather(*tasks))
```
We find that all of these 6 systems will run in parallel. Great!

Note the last line; `asyncio.run()` wrapping `asyncio.gather()` - this is required to spawn and async event loop and then gather the tasks as two seperate jobs. In a jupyter notebook, the asyncio.run() isn't necessary.

But hang on - I said 20 systems before. What if the number of processes we want to run exceeds the number of available threads?

## Limiting the Number of Asynchronous Processes with a Semaphore
`async` is almost a little too powerful: without restrictions, we could flood our tiny 8 threads with 1000 computationally demanding processes and brick our computer. Give it a try!
A nice way to stop this happening is by using a [Semaphore](https://en.wikipedia.org/wiki/Semaphore_(programming)), a sort of limiter on the number of processes allowed to run concurrently. If we define the maximum number of processes and generate a semaphore with `asyncio.Semaphore`

```python
MAX_PROCESSES=6
semaphore = asyncio.Semaphore(MAX_PROCESSES)
```
We've created a semaphore which allows a maximum of 6 concurrent processes, only allowing the next in the list to begin once one has finished.

The only key modifications to make then are to add the semaphore in a loop within the function:
```python
async def rmsf_semaphore(semaphore, tpr, traj, output):
	async with semaphore:
	    process = await asyncio.create_subprocess_shell(
	        f"gmx rmsf -s {tpr} -f {xtc} -o {output} -res yes",
	        stdin=asyncio.subprocess.PIPE,
	        stdout=asyncio.subprocess.DEVNULL,
	        stderr=asyncio.subprocess.PIPE
	    )
	    
	    stdout, stderr = await process.communicate(input=b"Protein\n")
	    
	    if process.returncode != 0:
	        raise RuntimeError(f"rmsf failed: {stderr.decode()}")
```
And there you go! I've found these tiny modifications have saved me incredible amounts of time. Be careful, though: it's a classic rabbit hole that may cost you more time than the synchronous processes you're trying to run if you go even deeper into async. I'll leave that up to you. Have fun!

[^1]: This also highlights my weaknesses in error handling: some may even notice that the error handling in these examples is far from optimal.
[^2]: Yes, this can be done in MDAnalysis. You could even probably parallelise that yourself by splitting the trajectory and running multithreading. But if you have multiple systems, the same principles here apply.
