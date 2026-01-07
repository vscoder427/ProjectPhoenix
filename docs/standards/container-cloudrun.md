# Container Base Image and Cloud Run Configuration

This standard defines container and Cloud Run defaults for services.

## Base Image

- python:3.12-slim with hardening (minimal packages, non-root user)

## Concurrency

- Per-service tuning based on load tests

## Min Instances

- Per-service policy (critical services may keep 1 warm instance)

## CPU Allocation

- Per-service policy (always-on CPU only where required)
