from datetime import datetime
from typing import List, Optional

def get_years_from_year(year: Optional[int] = 1900, desc: Optional[bool] = True) -> List[int]:
    """
    Using a 'year' param to start from, get a list of years until the current year. Default order is
    descending.
    """
    current_year = datetime.now().year

    if year > current_year:
        raise ValueError("The year provided must be earlier than the current year.")

    years = [year for year in range(year, current_year + 1)]

    return years[::-1] if desc else years