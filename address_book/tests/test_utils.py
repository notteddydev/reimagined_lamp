from datetime import datetime
from django.test import TestCase

from address_book.utils import get_years_from_year


class TestGetYearsFromYear(TestCase):
    def setUp(self) -> None:
        self.current_year = datetime.now().year

    def test_no_args(self) -> None:
        """
        Test that the method returns the expected list of years when no args are passed to the method.
        """
        years = get_years_from_year()

        year = 1900
        while year <= self.current_year:
            self.assertIn(year, years)
            year += 1

        self.assertEqual(years[0], self.current_year)
        self.assertEqual(years[-1], 1900)

    def test_custom_year(self) -> None:
        """
        Test that the method returns the expected list of years when a 'year' arg is passed to the method.
        """
        years = get_years_from_year(year=2000)

        year = 2000
        while year <= self.current_year:
            self.assertIn(year, years)
            year += 1

        self.assertEqual(years[0], self.current_year)
        self.assertEqual(years[-1], 2000)

    def test_asc(self) -> None:
        """
        Test that the method returns the expected list of years when the 'desc' arg is passed
        to the method as False.
        """
        years = get_years_from_year(desc=False)
        year = 1900
        while year <= self.current_year:
            self.assertIn(year, years)
            year += 1

        self.assertEqual(years[0], 1900)
        self.assertEqual(years[-1], self.current_year)

    def test_future_year_raises_exception(self) -> None:
        """
        Test that the an exception is raised if a 'year' arg is passed in with a value greater
        than that of the current year.
        """
        with self.assertRaises(ValueError) as cm:
            get_years_from_year(year=self.current_year + 1)

        self.assertEqual(str(cm.exception), "The year provided must be earlier than the current year.")
