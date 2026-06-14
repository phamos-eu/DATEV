frappe.query_reports["DATEV"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default:
				frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			default: moment().subtract(1, "month").startOf("month").format(),
			fieldtype: "Date",
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			default: moment().subtract(1, "month").endOf("month").format(),
			fieldtype: "Date",
			reqd: 1,
		},
		{
			fieldname: "voucher_type",
			label: __("Voucher Type"),
			fieldtype: "Select",
			options:
				"\nSales Invoice\nPurchase Invoice\nPayment Entry\nExpense Claim\nPayroll Entry\nBank Reconciliation\nAsset\nStock Entry\nJournal Entry",
		},
	],
	onload: function (query_report) {
		let company = frappe.query_report.get_filter_value("company");
		get_datev_configuration_name(company).then((configurationName) => {
			if (!configurationName) {
				frappe.confirm(
					__(
						"DATEV Configuration for your Company is missing. Would you like to create it now?"
					),
					() => frappe.new_doc("DATEV Configuration", { company: company })
				);
			}
		});

		query_report.page.set_primary_action(__("Download DATEV File"), () => {
			const filters = encodeURIComponent(JSON.stringify(query_report.get_values()));
			window.open(
				`/api/method/datev.gb_datev.report.datev.datev.download_datev_csv?filters=${filters}`
			);
		});

		query_report.page.add_menu_item(__("Open DATEV Settings"), () => {
			frappe.set_route("Form", "DATEV Settings");
		});

		query_report.page.add_menu_item(__("Change DATEV Configuration"), () => {
			let company = frappe.query_report.get_filter_value("company"); // read company from filters again; it might have changed by now.
			get_datev_configuration_name(company).then((configurationName) => {
				if (configurationName) {
					frappe.set_route("Form", "DATEV Configuration", configurationName);
					return;
				}

				frappe.new_doc("DATEV Configuration", { company: company });
			});
		});
	},
};

function get_datev_configuration_name(company) {
	if (!company) {
		return Promise.resolve(null);
	}

	return frappe.db
		.get_value("DATEV Configuration", { company: company }, "name")
		.then((response) => response.message && response.message.name);
}
