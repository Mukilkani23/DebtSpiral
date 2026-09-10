#!/usr/bin/env bash
echo "Resetting demo state..."
curl -s -X POST http://localhost:8000/reset | python -m json.tool
echo "Done."
