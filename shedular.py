import schedule
import time
import asyncio

from main import main   # 👈 replace with actual file name (if needed)

# Run job
def job():
    print("Running METAR comparison...")
    asyncio.run(main())

# Schedule every 30 mins
schedule.every(2).minutes.do(job)

print("Scheduler started... runs every 2 minutes ✅")

# Keep running forever
while True:
    schedule.run_pending()
    time.sleep(1)
