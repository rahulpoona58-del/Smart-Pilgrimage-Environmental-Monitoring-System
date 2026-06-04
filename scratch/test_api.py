# scratch/test_api.py
import asyncio
import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.db.session import async_session_maker
from backend.app.core.emissions import EmissionsCalculatorEngine

async def main():
    async with async_session_maker() as session:
        try:
            res = await EmissionsCalculatorEngine.calculate_emissions(session, save_to_history=True)
            print("SUCCESS:", res)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
