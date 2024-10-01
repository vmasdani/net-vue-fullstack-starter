#!/usr/bin/python3

from argparse import ArgumentParser
import json
import pprint
import subprocess
import sys

# import yaml

parser = ArgumentParser("Eng manager")

parser.add_argument("action", help="Run: run | build")
parser.add_argument("type", help="Run: backend | frontend | frontend-docker")
parser.add_argument("deploy", help="Type: dev | prod | prod-local")
parser.add_argument("--file_name", help="File name for build: 0.0.2.zip")

args = parser.parse_args()

# Check run type
if (
    args.type != "backend"
    and args.type != "frontend"
    and args.type != "app"
    and args.type != "frontend-docker"
):

    print(f"Type invalid: {args.type}")
    parser.print_usage()

    sys.exit(1)

# Check deploy type
if (
    args.deploy != "dev"
    and args.deploy != "dev-docker"
    and args.deploy != "prod"
    and args.deploy != "prod-local"
    and args.deploy != "prod-local2"
    and args.deploy != "prod2"
    and args.deploy != "prod-docker"
    and args.deploy != "prod-intercon"
):

    print(f"Deploye invalid: {args.deploy}")
    parser.print_usage()

    sys.exit(1)

# Backend template file
backend_file = open("backend.env", "r+")
backend_contents = backend_file.read()
backend_file.close()

# Frontend template file
frontend_template_properties_file = open("frontend.template.env", "r+")
frontend_template_properties_contents = frontend_template_properties_file.read()
frontend_template_properties_file.close()

# Docker compose template file
docker_compose_template_file = open("docker-compose.template.yml", "r+")
docker_compose_template_contents = docker_compose_template_file.read()
docker_compose_template_file.close()

env_json_file = open("config.json", "r+")
env_json_file_contents = env_json_file.read()
env_json_file.close()

env_json = json.loads(env_json_file_contents)

pprint.pprint(env_json[args.deploy])
pprint.pprint(backend_contents)

# Replace backend envs
for p in env_json[args.deploy]:
    backend_contents = backend_contents.replace(f"#{{{p}}}", env_json[args.deploy][p])

print(backend_contents)

# Replace frontend envs
for p in env_json[args.deploy]:
    frontend_template_properties_contents = (
        frontend_template_properties_contents.replace(
            f"#{{{p}}}", env_json[args.deploy][p]
        )
    )

print(frontend_template_properties_contents)

# Replace compose envs
for p in env_json[args.deploy]:
    docker_compose_template_contents = docker_compose_template_contents.replace(
        f"#{{{p}}}", env_json[args.deploy][p]
    )

print(docker_compose_template_contents)


# Write to backend
backend_file = open("./backend/.env", "w+")
backend_file.write(backend_contents)
backend_file.close()

# Write to frontend
frontend_env_prod_file = open("./frontend/.env", "w+")
frontend_env_prod_file.write(frontend_template_properties_contents)
frontend_env_prod_file.close()

# Write to compose
docker_compose_template_file = open("./docker-compose.yml", "w+")
docker_compose_template_file.write(docker_compose_template_contents)
docker_compose_template_file.close()


steps = []

if args.type == "frontend":
    if args.action == "run":
        steps = [("yarn dev", "./frontend")]

    elif args.action == "build":
        steps = [
            ("yarn build", "./frontend"),
            ("zip -r release.zip .", "./frontend/dist"),
        ]

elif args.type == "backend":
    if args.action == "run":
        steps = [("dotnet run", "./backend")]

    elif args.action == "build":
        steps = [
            ("yarn build", "./frontend"),
            ("cp -r ./frontend/dist/* backend/wwwroot .", "."),
            (
                f'docker build -t {env_json[args.deploy]["registry_url"]}/{env_json[args.deploy]["image_name"]} .',
                ".",
            ),
            (
                f'docker push {env_json[args.deploy]["registry_url"]}/{env_json[args.deploy]["image_name"]}',
                ".",
            ),
        ]

elif args.type == "app":
    if args.action == "run":
        steps = [
            # ("yarn build", "./frontend"),
            ("cp -r ./frontend/dist/* backend/wwwroot .", "."),
            (
                f'docker build -t {env_json[args.deploy]["image_name"]} .',
                ".",
            ),
            (f'docker run -p 7777:8080 {env_json[args.deploy]["image_name"]}', "."),
        ]

    elif args.action == "build":
        steps = [
            # ("yarn build", "./frontend"),
            ("cp -r ./frontend/dist/* backend/wwwroot .", "."),
            (
                f'docker build -t {env_json[args.deploy]["registry_url"]}/{env_json[args.deploy]["image_name"]} .',
                ".",
            ),
            (
                f'docker push {env_json[args.deploy]["registry_url"]}/{env_json[args.deploy]["image_name"]}',
                ".",
            ),
        ]


for step, cwd in steps:
    subprocess.run(step, shell=True, cwd=cwd)
