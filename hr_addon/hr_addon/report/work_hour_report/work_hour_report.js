// Copyright (c) 2022, Jide Olayinka and contributors
// Copyright (c) 2024, Centura AG, Samuel Helbling, and contributors
// For license information, please see license.txt
// This file is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
// See https://www.gnu.org/licenses/agpl-3.0.en.html for more details.
/* eslint-disable */
frappe.query_reports["Work Hour Report"] = {
    "filters": [
        {
            "fieldname": "month_filter",
            "label": __("Month"),
            "fieldtype": "Select",
            "options": [
                "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"
            ],
			"default": new Date().toLocaleString('default', { month: 'long' }),
            "reqd": 1,
            "width": "35px"
        },
        {
            "fieldname": "year_filter",
            "label": __("Year"),
            "fieldtype": "Int",
            "default": parseInt((frappe.datetime.get_today()).split("-")[0]),
            "reqd": 1,
            "width": "35px"
        },
        {
            "fieldname": "employee_id",
            "label": __("Employee Id"),
            "fieldtype": "Link",
            "options": "Employee",
            "reqd": 1,
            "width": "35px"
        },
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // Using the new helper function for various time fields
        if (column.fieldname == "total_work_seconds" ||
            column.fieldname == "total_break_seconds" ||
            column.fieldname == "actual_working_seconds") {
            value = formatWithColor(value);
        }

        // Format Date with date_format defined in system-settings
        if (column.fieldname == "log_date") {
            if (value != 'Total') {
                let weekday = new Date(value).toLocaleString('en-US', { weekday: 'long' });
                weekday = __(weekday);

                value = frappe.datetime.str_to_user(value);
                value = `${weekday}, ${value}`;
            } else {
                value = parseInt((frappe.datetime.get_today()).split("-")[0]);
            }
        }

        // Special handling for diff_log and actual_diff_log with calDiff=true
        if (column.fieldname == "diff_log" || column.fieldname == "actual_diff_log") {
            value = formatWithColor(value, true);
        }

        // Other specific fields that just need the hitt function without color
        if (column.fieldname == "total_target_seconds" || column.fieldname == "expected_break_hours" || column.fieldname == "absent_seconds") {
            value = hitt(value);
        }

        return value;
    },
};

// Helper function to handle time formatting with colors
const formatWithColor = (value, calDiff = false) => {
    if (value == null) return ''; // Handle null/undefined values
    if (value < 0) {
        return "<span style='color:red'>" + hitt(value, calDiff) + "</span>";
    } else if (value > 0) {
        return "<span style='color:green'>" + hitt(value, calDiff) + "</span>";
    } else {
        return hitt(value, calDiff);
    }
};

const hitt = (fir, calDiff = false) => {
    if (fir < 0 && !calDiff) return fir; // Early return for negative and calDiff=false

    // Convert to positive if calDiff is true, otherwise keep as is
    let timeInSeconds = Math.abs(fir);

    let hours = Math.floor(timeInSeconds / 3600);
    let minutes = Math.floor((timeInSeconds % 3600) / 60);

    let result = `${hours > 0 ? hours + 'h ' : ''}${minutes > 0 ? minutes + 'm ' : ''}`.trim();

    // Return negative result if original fir was negative and calDiff is true
    return fir < 0 && calDiff ? `-${result}` : result;
};