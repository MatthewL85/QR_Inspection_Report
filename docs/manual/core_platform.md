# Core Platform

Status: Phase 3 operating guide

Last updated: 2026-05-28

## Purpose

The Core Platform holds the shared identity, company, document, notification and audit foundations used by every LogixPM module.

## What It Owns

- users
- roles
- companies and organisations
- shared documents and media
- audit logs
- notifications
- shared navigation and UI shell

## User Impact

Most users do not work directly inside the Core Platform. They experience it through login, role access, navigation, alerts, settings and shared profile data.

## Important Rule

Operational modules should link to core records by ID. They should not create separate user, company or document records for their own isolated use.
