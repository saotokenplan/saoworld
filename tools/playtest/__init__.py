"""
Playtest module for end-to-end testing of critical game paths.

This module provides tools for automated playtesting of:
- Vote flow (create cycle → add candidates → submit vote → close → count)
- World exploration flow
- Quest completion flow

Usage:
    python -m tools.playtest.test_vote_flow
    bash tools/playtest/run_vote_flow.sh
"""

__version__ = "0.1.0"