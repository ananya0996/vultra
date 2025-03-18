# vultra
A vulnerability scanning tool built for the ECS 260 Software Engineering course at UC Davis (Winter 2025).

## Dependencies
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

2. On Linux, run:
```bash
source venv/bin/activate
```
On Windows, run:
```powershell
.\venv\Scripts\activate
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

4. Configure GitHub Access Token (required)
[Generate a GitHub Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) and configure it as instructed below:
On Linux,
```bash
export GITHUB_ACCESS_TOKEN=<your-access-token>
```
On Windows, set configure `GITHUB_ACCESS_TOKEN` in environment variables.


### To run:
On Linux
```bash
python3 src/main.py  --framework <your-framework> \
--file <path/to/dependency/file>
```
