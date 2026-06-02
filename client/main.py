import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from client.app import GiyimMagazasiApp


def main():
    app = GiyimMagazasiApp()
    app.mainloop()


if __name__ == "__main__":
    main()
