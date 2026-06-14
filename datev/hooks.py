app_name = "datev"
app_title = "DATEV"
app_publisher = "phamos"
app_description = "DATEV integration for ERPNext"
required_apps = ["frappe/erpnext"]
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@phamos.eu"
app_license = "GPLv3"

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			[
				"name",
				"in",
				[
					"Item Tax Template-custom_datev_section",
					"Item Tax Template-custom_bu_schlussel",
					"Journal Entry Account-custom_datev_section",
					"Journal Entry Account-custom_datev_account_no",
					"Journal Entry Account-custom_datev_code",
					"Party Account-debtor_creditor_number",
					"Payment Entry-custom_datev_section",
					"Payment Entry-custom_datev_account_no",
					"Payment Entry-custom_datev_against_account_no",
					"Payment Entry-custom_datev_end_section",
					"Purchase Invoice-custom_datev_section",
					"Purchase Invoice-custom_datev_account_no",
					"Purchase Invoice-custom_datev_end_section",
					"Purchase Invoice Item-datev_settings_section",
					"Purchase Invoice Item-custom_datev_account_no",
					"Purchase Invoice Item-custom_bu_schlussel",
					"Purchase Invoice Item-datev_settings_end_section",
					"Sales Invoice-custom_datev_section",
					"Sales Invoice-custom_datev_account_no",
					"Sales Invoice-custom_datev_end_section",
					"Sales Invoice Item-datev_settings_section",
					"Sales Invoice Item-custom_datev_account_no",
					"Sales Invoice Item-custom_bu_schlussel",
					"Sales Invoice Item-datev_settings_end_section",
				],
			]
		],
	}
]

doc_events = {
	"*": {
		"on_submit": "datev.gb_datev.doctype.datev_unternehmen_online_settings.datev_unternehmen_online_settings.send",
	},
}
