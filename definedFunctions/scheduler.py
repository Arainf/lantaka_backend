from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .automation import update_cleaning_status
from functools import partial

def run_with_app_context(app, func):
    """Wrapper to run a function within the application context"""
    with app.app_context():
        func()

def init_cleaning_scheduler(app):
    """Initialize the cleaning status check scheduler"""
    scheduler = BackgroundScheduler()
    
    # Wrap the update function with the application context
    context_bound_update = partial(run_with_app_context, app, update_cleaning_status)
    
    # Add job to run every 5 minutes
    scheduler.add_job(
        func=context_bound_update,
        trigger=IntervalTrigger(minutes=5),
        id='cleaning_status_check',
        name='Check and update cleaning status',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    
    # Shut down the scheduler when the application is shutting down
    import atexit
    atexit.register(lambda: scheduler.shutdown())