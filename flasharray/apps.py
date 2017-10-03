"""Apps that need to be registered for the scheduler."""

from __future__ import unicode_literals

import logging

from django.apps import AppConfig

logger = logging.getLogger('flash_stache')


class SchedulerConfig(AppConfig):
    """FlashArray Monitoring Scheduler configuration."""
    name = 'scheduler'
    verbose_name = 'FlashArray Monitoring Scheduler'

    def ready(self):
        """Get the FlashArray model and look for enabled jobs that need to be scheduled."""
        try:
            self.reschedule_repeatable_jobs()
        except Exception as error:
            logger.error('Failed to connect to the scheduler.\n{}'.format(error))

    def reschedule_repeatable_jobs(self):
        """Ensure that repeating jobs are scheduled."""
        flash_array = self.get_model('FlashArray')
        # Only schedule enabled arrays
        jobs = flash_array.objects.filter(enabled=True)
        _reschedule_jobs(jobs)
        logger.info('Scheduled/Re-scheduled jobs: {}'.format(jobs))


def _reschedule_jobs(jobs):
    """Reschedule one or more jobs."""
    for job in jobs:
        if not job.is_scheduled():
            logger.info('Job {} was not scheduled.  Scheduling it now.'.format(job.id))
            job.save()
