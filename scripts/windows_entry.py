"""Windowed entry point used by the standalone Windows build."""
import sys
from multiprocessing import freeze_support

if __name__ == '__main__':
    freeze_support()
    if len(sys.argv)==3 and sys.argv[1]=='--self-test':
        from tonepage.packaged_check import run
        raise SystemExit(run(sys.argv[2]))
    from tonepage.cli import main
    raise SystemExit(main())
