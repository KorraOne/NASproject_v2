#!/bin/bash
set -e
curl -s -X POST http://localhost/api/setup \
  -H 'Content-Type: application/json' \
  -d '{"password":"FrogsWork-Dev-2026","timezone":"Australia/Perth"}'
echo
curl -s http://localhost/api/setup/status
echo
ls -la /data/shared/
curl -s -X POST http://localhost/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"password":"FrogsWork-Dev-2026"}'
echo
