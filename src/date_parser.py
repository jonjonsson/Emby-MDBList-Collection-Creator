from datetime import datetime, date


def get_appropriate_year(month, day, reference_date):
    test_date = date(reference_date.year, month, day)
    if test_date <= reference_date:
        return reference_date.year
    return reference_date.year - 1


def inside_period(active_period_str):
    """
    Parse a string representing an active period and determine if the current date falls within it.

    This function accepts a string containing two dates separated by a comma. Each date
    can be in either 'YYYY-MM-DD' or 'MM-DD' format. When the year is omitted (MM-DD format):
    - For the start date: It assumes the most recent occurrence of that month-day in the past.
    - For the end date: It assumes the next occurrence after the start date.

    The function then checks if the current date is within the parsed date range.

    Parameters:
    active_period_str (str): A string in the format "start_date, end_date" where each date
                             is either "YYYY-MM-DD" or "MM-DD".

    Returns:
    bool: True if the current date is within the parsed date range, False otherwise.
          Returns False if parsing fails.

    Examples:
    - "2023-09-30, 2023-11-01" -> True if current date is between Sep 30, 2023 and Nov 1, 2023
    - "09-30, 11-01" -> Assumes years based on the current date
    - "2023-09-30, 11-01" -> Interprets end date as Nov 1 of the appropriate year

    Note:
    - The function uses the current date both for reference when parsing dates without years
      and for determining if the current date is within the active period.
    - If parsing fails for any reason, the function returns False.
    """

    try:
        start_date_str, end_date_str = map(str.strip, active_period_str.split(","))

        today = date.today()

        # Parse start date
        if len(start_date_str) == 10:  # Full date string (YYYY-MM-DD)
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        elif len(start_date_str) == 5:  # Short date string (MM-DD)
            month, day = map(int, start_date_str.split("-"))
            year = get_appropriate_year(month, day, today)
            start_date = date(year, month, day)
        else:
            raise ValueError("Invalid date format")

        # Parse end date
        if len(end_date_str) == 10:  # Full date string (YYYY-MM-DD)
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        elif len(end_date_str) == 5:  # Short date string (MM-DD)
            month, day = map(int, end_date_str.split("-"))
            year = get_appropriate_year(month, day, start_date)
            end_date = date(year, month, day)
            if end_date <= start_date:
                end_date = date(year + 1, month, day)
        else:
            raise ValueError("Invalid date format")

        # Check if today is within the parsed date range
        return start_date <= today <= end_date

    except (ValueError, TypeError):
        return False


def main():
    # Example usage
    test_cases = [
        "2023-09-30, 2023-11-01",
        "09-30, 11-01",
        "09-30, 01-02",
        "2023-09-30, 11-01",
        "12-01, 02-28",  # Spans across new year
        "invalid date",  # Invalid input
    ]

    for case in test_cases:
        result = inside_period(case)
        print(f"Active period: {case}")
        print(f"Current date is within range: {result}")
        print("-" * 30)


if __name__ == "__main__":
    main()
