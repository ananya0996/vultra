# Vultra
Vultra is a vulnerability aggregator that checks your project’s dependencies against known vulnerability databases. It then reports key information—such as vulnerability type, severity, and the patched version, if available.

Currently, Vultra supports the following dependency management frameworks:
- Maven (mvn)
- Node Package Manager (npm)

Vultra was built for the ECS 260 Software Engineering course at UC Davis (Winter Quarter 2025).

## Dependencies
On Linux / WSL, run:
```bash
sudo apt install python3
sudo apt-get install python3-pip
sudo apt install maven
sudo apt install npm
```

## Build & Run
1. Set up the environment:
```bash
python -m venv venv
```

2. On Linux / WSL, run:
```bash
source venv/bin/activate
```
On Windows, run:
```powershell
.\venv\Scripts\activate
```

3. Install requirements:
```bash
pip install .
```

4. Configure GitHub Access Token (required)
[Generate a GitHub Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) and configure it as instructed below:
On Linux / WSL, run:
```bash
export GITHUB_ACCESS_TOKEN=<your-access-token>
```
On Windows, set configure `GITHUB_ACCESS_TOKEN` in environment variables.
```powershell
$env:GITHUB_ACCESS_TOKEN = "<your-access-token>"
```


### To run:
On Linux / WSL, run
```bash
python src/main.py  --framework <your-framework> --file <path/to/dependency/file>
```
