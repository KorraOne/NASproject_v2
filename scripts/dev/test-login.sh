#!/usr/bin/env bash
curl -s -w "\nHTTP:%{http_code}\n" -X POST http://localhost/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"password":"FrogsWork-Dev-2026"}'
