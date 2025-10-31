"""
Test script to verify restart_count is being read correctly from Docker API
"""
import docker
import json

client = docker.from_env()

print("Checking restart_count location in Docker container attributes...\n")

containers = client.containers.list(all=True)

for container in containers[:3]:  # Check first 3 containers
    container.reload()
    attrs = container.attrs

    print(f"Container: {container.name}")
    print(f"  Status: {container.status}")

    # Check root level
    root_restart_count = attrs.get("RestartCount")
    print(f"  attrs['RestartCount']: {root_restart_count}")

    # Check State level (correct location)
    state_restart_count = attrs.get("State", {}).get("RestartCount")
    print(f"  attrs['State']['RestartCount']: {state_restart_count}")

    # Check HostConfig level
    hostconfig_restart_count = attrs.get("HostConfig", {}).get("RestartCount")
    print(f"  attrs['HostConfig']['RestartCount']: {hostconfig_restart_count}")

    print()

print("\nConclusion: RestartCount should be read from attrs['State']['RestartCount']")

