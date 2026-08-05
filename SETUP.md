# Environment Setup — xylem_ae

Follow these steps on **every** laptop (yours included, and each teammate's).
Takes about 5 minutes once Anaconda is installed.

## 1. Install Anaconda (skip if already installed)

Download and install Miniconda (smaller/faster than full Anaconda) from:
https://docs.conda.io/en/latest/miniconda.html

## 2. Get the project files

If using GitHub (recommended for a 4-person team):

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

If not using GitHub yet: copy the whole project folder (notebooks +
`requirements.txt` + any saved `.wav`/`.npy` files) via USB drive or a
shared cloud folder, then open a terminal/Anaconda Prompt inside that folder.

## 3. Create the environment

Run these commands from inside the project folder:

```bash
conda create -n xylem_ae python=3.10 -y
conda activate xylem_ae
pip install -r requirements.txt
python -m ipykernel install --user --name=xylem_ae
```

## 4. Launch Jupyter

```bash
jupyter notebook
```

Open any notebook, then check the top-right corner shows **xylem_ae** as
the active kernel. If it shows something else, use Kernel -> Change Kernel
and select xylem_ae from the list.

## 5. Verify it worked

Paste this into a cell and run it (Shift+Enter):

```python
import numpy as np, scipy, matplotlib
print("numpy:", np.__version__)
print("scipy:", scipy.__version__)
print("Environment OK")
```

Everyone's version numbers should match. If they don't, something in
requirements.txt resolved differently -- flag it in the team chat before
continuing, since mismatched package versions are a common source of
"works on my machine but not yours" bugs later.

## Troubleshooting

- **xylem_ae doesn't show up as a kernel option**: the ipykernel install
  command (step 3, last line) didn't run inside the activated environment.
  Re-run `conda activate xylem_ae` then the ipykernel line again, then
  fully restart Jupyter (close it, run `jupyter notebook` again).
- **`conda` not recognized**: Anaconda/Miniconda wasn't added to PATH during
  install, or you're not using the Anaconda Prompt (Windows). Reinstall and
  make sure "Add to PATH" is checked, or always launch via Anaconda Prompt.
- **pip install fails on a package**: run `conda update conda` first, then
  retry. If a specific package still fails, note the exact error and check
  with the team before changing version numbers in requirements.txt --
  keep it consistent across everyone's setup.
