// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("DATEV Settings", {
	refresh(frm) {
		frm.add_custom_button(
			__("Show Report"),
			() => frappe.set_route("query-report", "DATEV"),
			"fa fa-table"
		);

		frm.add_custom_button(
			__("Company Configurations"),
			() => frappe.set_route("List", "DATEV Configuration"),
			__("Open")
		);

		frm.add_custom_button(
			__("DATEV Mapping"),
			() => frappe.set_route("List", "DATEV Mapping"),
			__("Open")
		);

		frm.add_custom_button(
			__("Unternehmen Online Settings"),
			() => frappe.set_route("Form", "DATEV Unternehmen Online Settings"),
			__("Open")
		);
	},
});
