# Copyright (c) 2022, Jide Olayinka and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns, data = [], []
    condition_date, condition_employee = "", ""

    # Generate condition based on month and year filters
    if filters.get("month_filter") and filters.get("year_filter"):
        # Convert month name to month number
        month_number = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12
        }.get(filters.get("month_filter"))

        # Set the date range condition for the selected month and year
        year = filters.get("year_filter")
        condition_date = f"AND MONTH(log_date) = {month_number} AND YEAR(log_date) = {year}"

    if filters.get("employee_id"):
        empid = filters.get("employee_id")
        condition_employee += f" AND employee = '{empid}'"

    # Define columns for the report
    columns = [
        {'fieldname': 'log_date', 'label': 'Datum', 'width': 110},
        {'fieldname': 'name', 'label': 'Werktag (Link)', "fieldtype": "Link", "options": "Workday", 'width': 150},
        {'fieldname': 'total_work_seconds', 'label': 'Ist-Stunden', "width": 110},
        {'fieldname': 'total_target_seconds', 'label': 'Soll-Stunden', 'width': 110},
        {'fieldname': 'actual_diff_log', 'label': 'Differenz', 'width': 90},
    ]

    # Fetch data based on conditions
    work_data = frappe.db.sql(
        """
        SELECT name, log_date, employee, attendance, status, total_work_seconds, total_break_seconds,
               actual_working_hours * 60 * 60 actual_working_seconds,
               expected_break_hours * 60 * 60 expected_break_hours,
               target_hours, total_target_seconds, (total_work_seconds - total_target_seconds) AS diff_log,
               (actual_working_hours * 60 * 60 - total_target_seconds) AS actual_diff_log,
               TIME(first_checkin) AS first_in, TIME(last_checkout) AS last_out
        FROM `tabWorkday`
        WHERE docstatus < 2 {0} {1}
        ORDER BY log_date ASC
        """.format(condition_date, condition_employee), as_dict=1
    )

    data = work_data

    return columns, data
