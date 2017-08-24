# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 KuraLabs S.R.L
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Pipeline scheduler.
"""

from sched import scheduler
from time import time, sleep
from datetime import timedelta
from traceback import format_exc

from .logging import get_logger


log = get_logger(__name__)


class Scheduler:
    """
    FIXME: Document.
    """

    def __init__(self, pipeline, frequency, samples=None, start=None):
        self._pipeline = pipeline
        self._frequency = frequency
        self._samples = samples
        self._start = start

        self._runs_passed = 0
        self._runs_failed = 0
        self._runs_missed = 0
        self._last_run = None
        self._scheduler = scheduler(time, sleep)

        log.info('Create scheduler for pipeline:\n{}'.format(self._pipeline))

    def _sched_next(self):
        """
        Schedule the next work function.
        """
        now = time()

        # Check if samples have been met
        if self._samples is not None:
            if self._runs_passed >= self._samples:
                log.info(
                    'Pipeline {} collected {} samples successfully in {}. '
                    '{} executions failed, {} executions missed. '
                    'Exiting...'.format(
                        self._pipeline.name,
                        self._runs_passed,
                        str(timedelta(seconds=now - self._start)),
                        self._runs_failed,
                        self._runs_missed,
                    )
                )
                return

        # If not, continue scheduling samples
        next_time = self._last_run + self._frequency

        # Check no ticks were missing, if next_time is in the past
        if next_time <= now:
            self._runs_missed += 1

            log.info(
                'Next run missed. Starting {} pipeline immediately ...'.format(
                    self._pipeline.name
                )
            )
            event = self._scheduler.enter(
                0, 1, self._sched_work
            )

        else:
            log.info('Scheduling next pipeline run in {} ...'.format(
                str(timedelta(seconds=next_time - now)),
            ))
            event = self._scheduler.enterabs(
                next_time, 1, self._sched_work
            )

        self._last_run = event.time

    def _sched_work(self):
        """
        Execute the work function and schedule the next no matter what.
        """
        try:
            self._pipeline.run()
            self._runs_passed += 1

        except Exception as e:
            log.error(
                'Pipeline {} failed:\n{}'.format(
                    self._pipeline.name, format_exc()
                )
            )
            self._runs_failed += 1

        finally:
            self._sched_next()

    def run(self):
        """
        FIXME: Document.
        """
        now = time()

        if self._start is not None:

            if self._start < now:
                raise ValueError(
                    'Invalid start time {}.'.format(self._start)
                )

            log.info('Pipeline scheduled to run in {} ...'.format(
                str(timedelta(seconds=self._start - now))
            ))
            event = self._scheduler.enterabs(
                self._start, 1, self._sched_work
            )

        else:

            self._start = now

            log.info('Pipeline scheduled immediately ...')
            event = self._scheduler.enter(
                0, 1, self._sched_work
            )

        self._last_run = event.time
        self._scheduler.run()


__all__ = ['Scheduler']
