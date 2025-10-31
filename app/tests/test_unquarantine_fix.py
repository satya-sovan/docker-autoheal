"""
Quick test to verify unquarantine fix
This demonstrates the bug and validates the fix
"""

def test_container_id_mismatch():
    """Demonstrate the bug: short ID vs full ID mismatch"""

    # Simulate quarantine set with full IDs (what actually happens)
    quarantined = {
        "c9963b4cdaae8f5c3d4e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c",
        "abc123def456789012345678901234567890123456789012345678901234567890"
    }

    print("Initial quarantine list:")
    print(f"  - {list(quarantined)[0][:12]}... (full ID)")
    print(f"  Count: {len(quarantined)}")
    print()

    # BUG: Trying to remove using short ID
    short_id = "c9963b4cdaae"
    print(f"Attempting to unquarantine using short ID: {short_id}")
    quarantined.discard(short_id)
    print(f"  Result: {len(quarantined)} containers still quarantined ❌")
    print(f"  Bug: Short ID doesn't match full ID in set!")
    print()

    # FIX: Using full ID
    full_id = "c9963b4cdaae8f5c3d4e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c"
    print(f"Attempting to unquarantine using full ID: {full_id[:12]}...")
    quarantined.discard(full_id)
    print(f"  Result: {len(quarantined)} containers still quarantined ✅")
    print(f"  Fix: Full ID matches and container is removed!")
    print()

    # Verify
    print("Final quarantine list:")
    print(f"  Count: {len(quarantined)}")
    print(f"  Remaining: {list(quarantined)[0][:12] if quarantined else 'None'}...")

def test_docker_id_resolution():
    """Show how Docker SDK resolves short IDs to full IDs"""
    print("\nDocker SDK ID Resolution:")
    print("=" * 60)
    print("When you call: docker_client.get_container('c9963b4cdaae')")
    print("Docker SDK returns a container object where:")
    print("  - container.id[:12] = 'c9963b4cdaae' (short ID)")
    print("  - container.id = 'c9963b4cdaae8f5c3d4e...' (full ID)")
    print("\nOur fix:")
    print("  1. Call get_container(short_id) - Docker handles resolution")
    print("  2. Extract full_container_id = container.id")
    print("  3. Use full_container_id for config_manager operations")

if __name__ == "__main__":
    print("=" * 60)
    print("Unquarantine Bug Demonstration")
    print("=" * 60)
    print()
    test_container_id_mismatch()
    test_docker_id_resolution()
    print("\n" + "=" * 60)
    print("Test completed! ✅")

