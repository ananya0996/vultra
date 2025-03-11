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
Set up python virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```
To run:
```bash
pip install -r requirements.txt
export GITHUB_ACCESS_TOKEN=<your-access-token>
python3 src/main.py  --framework <your-framework> \
--file <path/to/dependency/file>
```