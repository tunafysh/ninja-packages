#!/bin/bash
uv run -m php.main
uv run -m apache.main
uv run -m mariadb.main
uv run -m postgres.main
