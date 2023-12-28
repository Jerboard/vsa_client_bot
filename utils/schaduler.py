from apscheduler.triggers.base import BaseTrigger

from init import scheduler
from utils.async_utils import (
    send_tasks_on_next_3_days,
    send_tasks_tomorrow_for_managers,
    send_weekly_report,
    send_monthly_report,
    update_admin_state)
# from db import clear_message_history


async def start_schedulers():
    # scheduler.add_job(clear_message_history, 'cron', hour=00)
    scheduler.add_job(send_tasks_on_next_3_days, 'cron', day_of_week='mon-fri', hour=13)
    scheduler.add_job(send_tasks_tomorrow_for_managers, 'cron', day_of_week='mon-fri', hour=17)
    scheduler.add_job(send_weekly_report, 'cron', day_of_week='mon', hour=11)
    scheduler.add_job(send_monthly_report, 'cron', day='29', hour=12)
    scheduler.add_job(update_admin_state, 'cron', hour=1)
    scheduler.start()
