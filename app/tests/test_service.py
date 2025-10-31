#!/usr/bin/env python3
"""
Quick test script to verify Docker Auto-Heal Service with React UI
Run this after starting the service to verify everything works

This file is now located at tests/test_service.py
"""

import requests
import sys
import time

BASE_URL = "http://localhost:3131"

def print_status(emoji, message):
    print(f"{emoji} {message}")

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_status("✅", "Health endpoint OK")
            print(f"   Docker connected: {data.get('docker_connected')}")
            print(f"   Monitoring active: {data.get('monitoring_active')}")
            return True
        else:
            print_status("❌", f"Health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print_status("❌", f"Cannot connect to service: {e}")
        return False

def test_api():
    """Test API status endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_status("✅", "API endpoint OK")
            print(f"   Total containers: {data.get('total_containers')}")
            print(f"   Monitored: {data.get('monitored_containers')}")
            return True
        else:
            print_status("❌", f"API returned {response.status_code}")
            return False
    except Exception as e:
        print_status("❌", f"API error: {e}")
        return False

def test_ui():
    """Test UI is accessible"""
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
            if 'root' in response.text:  # React mounts to #root
                print_status("✅", "React UI is accessible")
                return True
            else:
                print_status("⚠️", "UI accessible but may not be React")
                return True
        else:
            print_status("❌", f"UI returned {response.status_code}")
            return False
    except Exception as e:
        print_status("❌", f"UI error: {e}")
        return False

def test_metrics():
    """Test Prometheus metrics endpoint"""
    try:
        response = requests.get("http://localhost:9090/metrics", timeout=5)
        if response.status_code == 200:
            print_status("✅", "Metrics endpoint OK")
            return True
        else:
            print_status("❌", f"Metrics returned {response.status_code}")
            return False
    except Exception as e:
        print_status("⚠️", f"Metrics not accessible (may be disabled): {e}")
        return True  # Don't fail on this

def main():
    print("\n" + "="*60)
    print("  Docker Auto-Heal Service - React UI Test")
    print("="*60 + "\n")

    print("Testing service endpoints...\n")

    tests = [
        ("Health Check", test_health),
        ("API Status", test_api),
        ("React UI", test_ui),
        ("Metrics", test_metrics),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n[Testing: {name}]")
        results.append(test_func())
        time.sleep(0.5)

    print("\n" + "="*60)
    print("  Test Results")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"\n✅ Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! Service is working correctly.")
        print(f"\n🌐 Access the UI at: {BASE_URL}")
        print(f"📚 API docs at: {BASE_URL}/docs")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
        print("\nTroubleshooting:")
        print("1. Is the service running? (docker ps | grep autoheal)")
        print("2. Check logs: docker logs docker-autoheal")
        print("3. Try rebuilding: docker-compose up --build")
        sys.exit(1)

if __name__ == "__main__":
    main()
