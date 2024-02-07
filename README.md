# pvm-laragon

build code

**Warning**: Designed only for Windows systems with Laragon installed.

```bash
pyinstaller app.py --onefile --name=pvm -c
```

Then put the resulting pvm.exe in a folder of your choice (my suggestion is laragon/bin/pvm), then add the folder you
put to the PATH.

commands
```bash
pvm help
pvm list
pvm install <version>
pvm use <version>
```