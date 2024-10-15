# Copyright (c) 2022, Jide Olayinka and contributors
# Copyright (c) 2024, [Your Name], [Your Company Name], and contributors
# For license information, please see license.txt
# This file is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
# See https://www.gnu.org/licenses/agpl-3.0.en.html for more details.

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_datetime, getdate, add_days
from frappe.utils.data import date_diff
import traceback


class Workday(Document):
    pass


def bulk_process_workdays_background(data):
    '''bulk workday processing'''
    frappe.msgprint(_("Bulk operation is enqueued in background."), alert=True)
    frappe.enqueue(
        'hr_addon.hr_addon.doctype.workday.workday.bulk_process_workdays',
        queue='long',
        data=data
    )


@frappe.whitelist()
def bulk_process_workdays(data):
    import json
    if isinstance(data, str):
        data = json.loads(data)
    data = frappe._dict(data)

    if data.employee and frappe.get_value('Employee', data.employee, 'status') != "Active":
        frappe.throw(_("{0} is not active").format(frappe.get_desk_link('Employee', data.employee)))

    company = frappe.get_value('Employee', data.employee, 'company')
    if not data.unmarked_days:
        frappe.throw(_("Please select a date"))
        return

    for date in data.unmarked_days:
        try:
            timesheets = get_timesheets_for_employee_on_date(data.employee, get_datetime(date))
            if timesheets:
                # Aggregate timesheet data
                total_hours_worked = sum(ts.get("total_hours", 0) for ts in timesheets)

                # Get target hours from Weekly Working Hours
                target_hours = get_target_hours(data.employee, get_datetime(date))

                # Create a new Workday document
                doc_dict = {
                    "doctype": 'Workday',
                    "employee": data.employee,
                    "log_date": get_datetime(date),
                    "company": company,
                    "hours_worked": total_hours_worked,
                    "target_hours": target_hours,
                    "total_work_seconds": total_hours_worked * 3600,
                    "total_target_seconds": target_hours * 3600,
                    "actual_working_hours": total_hours_worked
                }
                workday = frappe.get_doc(doc_dict)

                # Set status based on custom logic (e.g., On Leave or Half Day)
                if workday.status == 'Half Day':
                    workday.target_hours = workday.target_hours / 2
                elif workday.status == 'On Leave':
                    workday.target_hours = 0

                workday = workday.insert()

        except Exception:
            message = _(f"Something went wrong in Workday Creation: {traceback.format_exc()}")
            frappe.msgprint(message)
            frappe.log_error("bulk_process_workdays() error", message)


def get_timesheets_for_employee_on_date(employee, date):
    """Retrieve all timesheets for an employee on a specific date"""
    timesheets = frappe.get_list(
        "Timesheet",
        filters={
            'employee': employee,
            'start_date': ['<=', date],
            'end_date': ['>=', date]
        },
        fields=['name', 'total_hours']
    )
    return timesheets


def get_target_hours(employee, date):
    """Retrieve target hours for an employee from Weekly Working Hours on a specific date"""
    weekday = date.strftime('%A')  # Get the day of the week (e.g., 'Monday')
    weekly_working_hours = frappe.get_list(
        "Weekly Working Hours",
        filters={
            'employee': employee,
            'valid_from': ['<=', date],
            'valid_to': ['>=', date]
        },
        fields=['name']
    )
    if not weekly_working_hours:
        return 0

    weekly_working_hours_name = weekly_working_hours[0].get('name')
    daily_hours_details = frappe.get_all(
        "Daily Hours Detail",
        filters={
            'parent': weekly_working_hours_name,
            'day': weekday
        },
        fields=['hours']
    )
    if daily_hours_details:
        return daily_hours_details[0].get('hours', 0)
    return 0


def get_month_map():
    return frappe._dict({
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12
    })


@frappe.whitelist()
def get_unmarked_days(employee, month, exclude_holidays=0):
    '''get_unmarked_days(employee, month, exclude_holidays=0)'''
    import calendar
    month_map = get_month_map()
    today = get_datetime()

    joining_date, relieving_date = frappe.get_cached_value("Employee", employee, ["date_of_joining", "relieving_date"])
    start_day = 1
    end_day = calendar.monthrange(today.year, month_map[month])[1] + 1

    if joining_date and joining_date.month == month_map[month]:
        start_day = joining_date.day

    if relieving_date and relieving_date.month == month_map[month]:
        end_day = relieving_date.day + 1

    dates_of_month = ['{}-{}-{}'.format(today.year, month_map[month], r) for r in range(start_day, end_day)]
    month_start, month_end = dates_of_month[0], dates_of_month[-1]

    records = frappe.get_list("Workday", fields=['log_date', 'employee'], filters=[
        ["log_date", ">=", month_start],
        ["log_date", "<=", month_end],
        ["employee", "=", employee]
    ])

    marked_days = []
    if cint(exclude_holidays):
        if get_version() == 14:
            from hrms.hr.utils import get_holiday_dates_for_employee

            holiday_dates = get_holiday_dates_for_employee(employee, month_start, month_end)
            holidays = [get_datetime(rcord) for rcord in holiday_dates]
            marked_days.extend(holidays)

    unmarked_days = []

    for date in dates_of_month:
        date_time = get_datetime(date)
        if today.day <= date_time.day and today.month <= date_time.month:
            break
        if date_time not in marked_days:
            unmarked_days.append(date)

    return unmarked_days


@frappe.whitelist()
def get_unmarked_range(employee, from_day, to_day):
    '''get_unmarked_range(employee, from_day, to_day)'''
    delta = date_diff(to_day, from_day)
    days_of_list = ['{}'.format(add_days(from_day, i)) for i in range(delta + 1)]
    month_start, month_end = days_of_list[0], days_of_list[-1]

    records = frappe.get_list("Workday", fields=['log_date', 'employee'], filters=[
        ["log_date", ">=", month_start],
        ["log_date", "<=", month_end],
        ["employee", "=", employee]
    ])

    marked_days = [get_datetime(record.log_date) for record in records]
    unmarked_days = []

    for date in days_of_list:
        date_time = get_datetime(date)
        if date_time not in marked_days:
            unmarked_days.append(date)

    return unmarked_days


def get_version():
    branch_name = get_app_branch("erpnext")
    if "14" in branch_name:
        return 14
    else:
        return 13


def get_app_branch(app):
    """Returns branch of an app"""
    import subprocess

    try:
        branch = subprocess.check_output(
            "cd ../apps/{0} && git rev-parse --abbrev-ref HEAD".format(app), shell=True
        )
        branch = branch.decode("utf-8").strip()
        return branch
    except Exception:
        return ""