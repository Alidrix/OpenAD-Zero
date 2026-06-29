#!/usr/bin/env python3
from __future__ import annotations

import json

from app.tool_automation.tool_health import collect_tool_health


def main() -> None:
    print(json.dumps(collect_tool_health(timeout=15), indent=2))


if __name__ == '__main__':
    main()
