# vultra
A vulnerability scanning tool built for the ECS 260 Software Engineering course at UC Davis (Winter 2025).

## Dependencies
```bash
sudo apt install python3
sudo apt-get install python3-pip
sudo apt install maven
sudo apt install npm
```

## To run,
```bash
python3 src/main.py --framework <mvn/npm> --file <path/to/manifest/file>
```