#!/usr/bin/env python3
"""
Entry point script for Docker Auto-Heal Service
This is a convenience wrapper that runs the main application from the app package
"""

if __name__ == "__main__":
    from app.main import main
    import asyncio

    asyncio.run(main())

