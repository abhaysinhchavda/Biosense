"""Vercel entrypoint: the same wiring as `biosense.production.app.main`, minus the socket.

`app.Handler` gets its runs dir, registry and limits assigned inside `main()`,
so importing it bare (what Vercel's auto-detected entrypoint does) answers every
request with an AttributeError. This module does that assignment at import time.

Vercel's filesystem is read-only except /tmp, and /tmp is per-instance and
ephemeral: runs live only as long as the instance does. See deploy/README.md for
the hosts this app is built for.
"""
from pathlib import Path

from biosense import workspace as WS
from biosense.data import roots as DR
from biosense.production import app as A
from biosense.production import authz as AZ
from biosense.production import budget as BU
from biosense.production import runtime as RT

ROOT = Path(__file__).resolve().parent.parent
RUNS = Path('/tmp/runs')  # ponytail: ephemeral, runs vanish with the instance; use a volume host for persistence
STATIC = ROOT / 'webapp'

DR.assert_disjoint(RUNS)
DR.assert_disjoint(STATIC)
RUNS.mkdir(parents=True, exist_ok=True)

_cfg = RT.from_env(runs_dir=RUNS)
_limits = BU.from_env()
_policy = AZ.from_env()


class handler(A.Handler):
    runs_dir = RUNS
    static_dir = STATIC
    registry = A.Registry(RUNS)
    runtime_cfg = _cfg
    limits = _limits
    policy = _policy
    discovery = A.DiscoveryRegistry(RUNS, _cfg, _limits, _policy)
    sessions = WS.SessionStore()
    default_identity = WS.identity_from_env()
