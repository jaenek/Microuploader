all:
    run

run:
    python microuploader.py

release:
    pyinstaller microuploader.py --onefile --windowed