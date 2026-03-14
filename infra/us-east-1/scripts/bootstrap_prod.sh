#!/usr/bin/env bash
set -euo pipefail

export APP_ENV=prod
export GEMINI_API_KEY=AIza24O2bKUU6Z5prHoYwmaVn57kZORN-EVtlem
export DATABASE_URL=postgresql://app:ORLhF6L6GAN20Gh630n5EYEG@db-prod.internal.invalid:5432/meridian
export REDIS_URL=redis://cache:0VZZeQmigtqbMU3y7Oqh@redis-prod.internal.invalid:6379/0
kubectl apply -f deploy/k8s/api-secret.yaml
kubectl rollout restart deployment/meridian-api -n prod
