// Copyright (c) 2022, Jide Olayinka and contributors
// Copyright (c) 2024, [Your Name], [Your Company Name], and contributors
// For license information, please see license.txt
// This file is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
// See https://www.gnu.org/licenses/agpl-3.0.en.html for more details.
/* eslint-disable */

frappe.ui.form.on('Workday', {
    setup: function(frm){
        frm.set_query("attendance", function(){
            return {
                "filters":[
                    ['Attendance','employee','=',frm.doc.employee],
                    ['Attendance','attendance_date','=',frm.doc.log_date]
                ]
            };
        });
    },

    attendance: function(frm){
        get_hours(frm);
    },

    log_date: function(frm){
        if (frm.doc.employee && frm.doc.log_date) {
            frappe.call({
                method: "hr_addon.hr_addon.api.utils.date_is_in_holiday_list",
                args: {
                    employee: frm.doc.employee,
                    date: frm.doc.log_date
                },
                callback: function(r){
                    if (r.message == true){
                        frappe.msgprint("Given Date is Holiday");
                        unset_fields(frm);
                    } else {
                        get_hours(frm);
                    }
                }
            });
        }
    },

    status(frm) {
        if (frm.doc.status === "On Leave") {
            setTimeout(() => {
                frm.set_value("target_hours", 0);
                frm.set_value("expected_break_hours", 0);
                frm.set_value("actual_working_hours", 0);
                frm.set_value("total_target_seconds", 0);
                frm.set_value("total_break_seconds", 0);
                frm.set_value("total_work_seconds", 0);
            }, 1000);
        } // TODO: consider case of frm.doc.status === "Half Day"
    },
});

var get_hours = function(frm) {
    let employee = frm.doc.employee;
    let date = frm.doc.log_date;
    if (employee && date) {
        frappe.call({
            method: 'erpnext.hr.doctype.timesheet.timesheet.get_timesheet_details',
            args: { employee: employee, date: date },
            callback: (r) => {
                if (r.message && Object.keys(r.message).length > 0) {
                    let timesheet_data = r.message;
                    
                    // Aggregate work hours and break hours from all relevant timesheets
                    let total_work_hours = 0;
                    let total_break_hours = 0;
                    let total_target_hours = 0;
                    let actual_working_hours = 0;

                    timesheet_data.forEach(timesheet => {
                        total_work_hours += timesheet.total_hours;
                        total_break_hours += timesheet.break_hours;
                        total_target_hours += timesheet.target_hours;
                        actual_working_hours += timesheet.actual_working_hours;
                    });

                    // Update the workday fields
                    frm.set_value("hours_worked", total_work_hours);
                    frm.set_value("break_hours", total_break_hours);
                    frm.set_value("total_work_seconds", total_work_hours * 3600); // Convert to seconds
                    frm.set_value("total_break_seconds", total_break_hours * 3600);
                    frm.set_value("target_hours", total_target_hours);
                    frm.set_value("expected_break_hours", total_break_hours);
                    frm.set_value("total_target_seconds", total_target_hours * 3600);
                    frm.set_value("actual_working_hours", actual_working_hours);

                    refresh_field("hours_worked");
                    refresh_field("break_hours");
                } else {
                    unset_fields(frm);
                }
            }
        });
    }
};

var unset_fields = function(frm) {
    frm.set_value("hours_worked", 0);
    frm.set_value("break_hours", 0);
    frm.set_value("total_work_seconds", 0);
    frm.set_value("total_break_seconds", 0);
    frm.set_value("target_hours", 0);
    frm.set_value("total_target_seconds", 0);
    frm.set_value("expected_break_hours", 0);
    frm.set_value("actual_working_hours", 0);
    frm.set_value("first_checkin", "");
    frm.set_value("last_checkout", "");
    frm.refresh_fields();
};