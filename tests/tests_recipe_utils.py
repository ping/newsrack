import unittest
from calendar import monthrange
from datetime import timedelta

from _recipe_utils import (
    get_local_now,
    onlyon_weekdays,
    onlyon_days,
    onlyat_hours,
    every_x_days,
    every_x_hours,
    last_n_days_of_month,
    first_n_days_of_month,
)


class RecipeUtilsTests(unittest.TestCase):
    def test_onlyon_weekdays(self):
        curr_weekday = get_local_now().weekday()
        whole_week = list(range(0, 7))
        self.assertTrue(onlyon_weekdays(whole_week))

        whole_week.remove(curr_weekday)
        self.assertFalse(onlyon_weekdays(whole_week))

    def test_onlyon_days(self):
        curr_day = get_local_now().day
        whole_month = list(range(1, 32))
        self.assertTrue(onlyon_days(whole_month))

        whole_month.remove(curr_day)
        self.assertFalse(onlyon_days(whole_month))

    def test_onlyat_hours(self):
        curr_hour = get_local_now().hour
        whole_day = list(range(0, 24))
        self.assertTrue(onlyat_hours(whole_day))

        whole_day.remove(curr_hour)
        self.assertFalse(onlyat_hours(whole_day))

    def test_every_x_days(self):
        last_run = (get_local_now() - timedelta(days=1)).timestamp()
        self.assertTrue(every_x_days(last_run, 1))

        last_run = (get_local_now() - timedelta(days=0.5)).timestamp()
        self.assertFalse(every_x_days(last_run, 1))

        last_run = (get_local_now() - timedelta(days=0.75)).timestamp()
        self.assertTrue(every_x_days(last_run, 1, drift=0.25 * 24 * 60))

    def test_every_x_hours(self):
        last_run = (get_local_now() - timedelta(hours=1)).timestamp()
        self.assertTrue(every_x_hours(last_run, 1))

        last_run = (get_local_now() - timedelta(hours=0.5)).timestamp()
        self.assertFalse(every_x_hours(last_run, 1))

        last_run = (get_local_now() - timedelta(hours=0.75)).timestamp()
        self.assertTrue(every_x_hours(last_run, 1, drift=0.25 * 60))

    def test_last_n_days_of_month(self):
        now = get_local_now()
        _, month_end = monthrange(now.year, now.month)
        self.assertTrue(last_n_days_of_month(month_end - now.day + 1))
        self.assertFalse(last_n_days_of_month(month_end - now.day))

    def test_first_n_days_of_month(self):
        now = get_local_now()
        self.assertTrue(first_n_days_of_month(now.day))
        self.assertFalse(first_n_days_of_month(now.day - 1))
