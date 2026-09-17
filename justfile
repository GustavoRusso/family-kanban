#!/usr/bin/env -S just --justfile

set shell := ["bash", "-cu"]

default:
    @just --list

branch_name := shell('git branch --show-current 2>/dev/null | sed "s/[^A-Za-z0-9]/-/g" | cut -c1-40 || echo local')
local_project := env_var_or_default("LOCAL_PROJECT", "family-kanban-" + branch_name)
local_api_port := env_var_or_default("LOCAL_API_PORT", "8000")
local_frontend_port := env_var_or_default("LOCAL_FRONTEND_PORT", "4173")
compose_env := "LOCAL_PROJECT='" + local_project + "' LOCAL_API_PORT='" + local_api_port + "' LOCAL_FRONTEND_PORT='" + local_frontend_port + "'"

local-config:
    @{{compose_env}} docker compose config

local-up:
    @{{compose_env}} docker compose up --build -d

local-down:
    @{{compose_env}} docker compose down

local-reset:
    @{{compose_env}} docker compose down --volumes --remove-orphans

local-ps:
    @{{compose_env}} docker compose ps

local-logs:
    @{{compose_env}} docker compose logs -f
