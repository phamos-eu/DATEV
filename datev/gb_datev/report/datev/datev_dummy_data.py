from contextlib import contextmanager
from datetime import date
from io import BytesIO
import zipfile

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

from datev.gb_datev.report.datev.datev import (
	apply_buchungsstapel_mapping,
	download_datev_csv,
	get_customers,
	get_datev_configuration,
	get_suppliers,
	get_transactions,
	group_payment_entry_buchungsstapel,
	group_sales_invoice_buchungsstapel,
)

SEED_COMPANY = "DATEV Dummy GmbH"
SEED_COMPANY_ABBR = "DDG"
SEED_CUSTOMER = "DATEV Dummy Customer"
SEED_SUPPLIER = "DATEV Dummy Supplier"
SEED_ITEM = "DATEV-DUMMY-ITEM"
SEED_FROM_DATE = date(2026, 1, 1)
SEED_TO_DATE = date(2026, 1, 31)


def get_seed_filters(company=None):
	return {
		"company": company or SEED_COMPANY,
		"from_date": SEED_FROM_DATE.isoformat(),
		"to_date": SEED_TO_DATE.isoformat(),
	}


def seed_datev_dummy_data(reset=True, commit=True):
	company = ensure_company()

	if reset:
		cleanup_datev_dummy_data(drop_masters=False, commit=False)

	ensure_fiscal_year(SEED_FROM_DATE.year)
	ensure_datev_configuration(company.name)

	warehouse = get_company_warehouse(company.name)
	cost_center = get_company_cost_center(company.name)
	accounts = get_company_accounts(company.name)
	customer = ensure_customer(company.name, accounts["receivable"])
	supplier = ensure_supplier(company.name, accounts["payable"])
	ensure_address("Customer", customer.name, "DATEV Dummy Customer Address")
	ensure_address("Supplier", supplier.name, "DATEV Dummy Supplier Address")
	item = ensure_item(company.name, warehouse)

	with allow_uninstalled_hook_resolution():
		sales_invoice = create_seed_sales_invoice(
			company_name=company.name,
			customer_name=customer.name,
			item_code=item.name,
			warehouse=warehouse,
			cost_center=cost_center,
			accounts=accounts,
		)
		purchase_invoice = create_seed_purchase_invoice(
			company_name=company.name,
			supplier_name=supplier.name,
			item_code=item.name,
			cost_center=cost_center,
			accounts=accounts,
		)
		receive_payment = create_payment_entry(
			"Sales Invoice", sales_invoice.name, accounts["bank"], SEED_TO_DATE
		)
		pay_payment = create_payment_entry(
			"Purchase Invoice", purchase_invoice.name, accounts["bank"], SEED_TO_DATE
		)

	filters = build_runtime_filters(company.name)
	transactions = get_transactions(filters.copy())
	grouped_transactions = group_sales_invoice_buchungsstapel(transactions, filters.copy())
	grouped_transactions = group_payment_entry_buchungsstapel(grouped_transactions, filters.copy())
	grouped_transactions = apply_buchungsstapel_mapping(grouped_transactions, filters.copy())
	customers = get_customers(filters.copy())
	suppliers = get_suppliers(filters.copy())

	summary = {
		"company": company.name,
		"from_date": filters["from_date"],
		"to_date": filters["to_date"],
		"datev_configuration": get_datev_configuration(company.name).name,
		"sales_invoice": sales_invoice.name,
		"purchase_invoice": purchase_invoice.name,
		"receive_payment_entry": receive_payment.name,
		"pay_payment_entry": pay_payment.name,
		"report_row_count": len(grouped_transactions),
		"report_voucher_types": sorted(
			{
				row.get("Beleginfo - Art 1")
				for row in grouped_transactions
				if row.get("Beleginfo - Art 1")
			}
		),
		"customer_export_rows": len(customers),
		"supplier_export_rows": len(suppliers),
	}

	if commit:
		frappe.db.commit()

	return summary


def cleanup_datev_dummy_data(drop_masters=False, commit=True):
	with allow_uninstalled_hook_resolution():
		cleanup_documents(
			"Payment Entry", {"company": SEED_COMPANY, "party": ["in", [SEED_CUSTOMER, SEED_SUPPLIER]]}
		)
		cleanup_documents("Sales Invoice", {"company": SEED_COMPANY, "customer": SEED_CUSTOMER})
		cleanup_documents("Purchase Invoice", {"company": SEED_COMPANY, "supplier": SEED_SUPPLIER})

	if drop_masters:
		delete_if_exists("Address", "DATEV Dummy Customer Address-Billing")
		delete_if_exists("Address", "DATEV Dummy Supplier Address-Billing")
		delete_if_exists("Customer", SEED_CUSTOMER)
		delete_if_exists("Supplier", SEED_SUPPLIER)
		delete_if_exists("Item", SEED_ITEM)
		delete_if_exists("DATEV Configuration", {"company": SEED_COMPANY})

	if commit:
		frappe.db.commit()

	return {"company": SEED_COMPANY, "from_date": SEED_FROM_DATE.isoformat(), "to_date": SEED_TO_DATE.isoformat()}


def verify_seeded_datev_dummy_data():
	filters = get_seed_filters()
	columns, data = execute_report_rows(filters["company"])
	download_datev_csv(filters.copy())

	return {
		"company": filters["company"],
		"from_date": filters["from_date"],
		"to_date": filters["to_date"],
		"report_column_count": len(columns),
		"report_row_count": len(data),
		"sales_invoice_rows": count_rows_for_voucher_type(data, "Sales Invoice"),
		"purchase_invoice_rows": count_rows_for_voucher_type(data, "Purchase Invoice"),
		"payment_entry_rows": count_rows_for_voucher_type(data, "Payment Entry"),
		"customer_export_rows": len(get_customers(build_runtime_filters(filters["company"]))),
		"supplier_export_rows": len(get_suppliers(build_runtime_filters(filters["company"]))),
		"zip_entries": sorted(
			zipfile.ZipFile(BytesIO(frappe.response["filecontent"])).namelist()
		),
	}


def ensure_company():
	if frappe.db.exists("Company", SEED_COMPANY):
		company = frappe.get_doc("Company", SEED_COMPANY)
	else:
		company = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": SEED_COMPANY,
				"abbr": SEED_COMPANY_ABBR,
				"default_currency": "EUR",
				"country": "Germany",
				"create_chart_of_accounts_based_on": "Standard Template",
				"chart_of_accounts": "SKR04 mit Kontonummern",
			}
		)
		company.insert(ignore_permissions=True)

	company.create_default_warehouses()

	if not frappe.db.get_value("Cost Center", {"is_group": 0, "company": company.name}, "name"):
		company.create_default_cost_center()

	company.reload()
	return company


def ensure_fiscal_year(year):
	name = frappe.db.get_value("Fiscal Year", {"year": str(year)}, "name")
	if name:
		return frappe.get_doc("Fiscal Year", name)

	fiscal_year = frappe.get_doc(
		{
			"doctype": "Fiscal Year",
			"year": str(year),
			"year_start_date": f"{year}-01-01",
			"year_end_date": f"{year}-12-31",
		}
	)
	fiscal_year.insert(ignore_permissions=True)
	return fiscal_year


def ensure_datev_configuration(company_name):
	name = frappe.db.get_value("DATEV Configuration", {"company": company_name}, "name")
	if name:
		doc = frappe.get_doc("DATEV Configuration", name)
		doc.account_number_length = 4
		doc.consultant_number = "67890"
		doc.client_number = "12345"
		doc.temporary_against_account_number = "9999"
		doc.opening_against_account_number = "9998"
		doc.save(ignore_permissions=True)
		return doc

	doc = frappe.get_doc(
		{
			"doctype": "DATEV Configuration",
			"company": company_name,
			"account_number_length": 4,
			"consultant_number": "67890",
			"client_number": "12345",
			"temporary_against_account_number": "9999",
			"opening_against_account_number": "9998",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def ensure_customer(company_name, receivable_account):
	if frappe.db.exists("Customer", SEED_CUSTOMER):
		customer = frappe.get_doc("Customer", SEED_CUSTOMER)
	else:
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": SEED_CUSTOMER,
				"customer_type": "Company",
			}
		)
		customer.insert(ignore_permissions=True)

	upsert_party_account(customer, company_name, receivable_account, "10001")
	return customer


def ensure_supplier(company_name, payable_account):
	if frappe.db.exists("Supplier", SEED_SUPPLIER):
		supplier = frappe.get_doc("Supplier", SEED_SUPPLIER)
	else:
		supplier = frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": SEED_SUPPLIER,
				"supplier_type": "Company",
			}
		)
		supplier.insert(ignore_permissions=True)

	upsert_party_account(supplier, company_name, payable_account, "70001")
	return supplier


def upsert_party_account(party_doc, company_name, account_name, debtor_creditor_number):
	for row in party_doc.get("accounts") or []:
		if row.company == company_name:
			row.account = account_name
			row.debtor_creditor_number = debtor_creditor_number
			party_doc.save(ignore_permissions=True)
			return

	party_doc.append(
		"accounts",
		{
			"company": company_name,
			"account": account_name,
			"debtor_creditor_number": debtor_creditor_number,
		},
	)
	party_doc.save(ignore_permissions=True)


def ensure_address(link_doctype, link_name, address_title):
	name = frappe.db.get_value("Address", {"address_title": address_title}, "name")
	if name:
		address = frappe.get_doc("Address", name)
	else:
		address = frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": address_title,
				"address_type": "Billing",
				"is_primary_address": 1,
				"address_line1": "DATEV Musterstrasse 1",
				"city": "Berlin",
				"country": "Germany",
				"pincode": "10115",
				"email_id": "datev@example.com",
				"phone": "+49 30 1234567",
				"links": [{"link_doctype": link_doctype, "link_name": link_name}],
			}
		)
		address.insert(ignore_permissions=True)
		return address

	if not address.is_primary_address:
		address.is_primary_address = 1

	if not any(link.link_doctype == link_doctype and link.link_name == link_name for link in address.links):
		address.append("links", {"link_doctype": link_doctype, "link_name": link_name})

	address.save(ignore_permissions=True)

	return address


def ensure_item(company_name, warehouse):
	if frappe.db.exists("Item", SEED_ITEM):
		return frappe.get_doc("Item", SEED_ITEM)

	item = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": SEED_ITEM,
			"item_name": "DATEV Dummy Item",
			"description": "Seed data item for DATEV report verification",
			"item_group": "All Item Groups",
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"is_sales_item": 1,
			"is_purchase_item": 1,
			"item_defaults": [{"company": company_name, "default_warehouse": warehouse}],
		}
	)
	item.insert(ignore_permissions=True)
	return item


def create_seed_sales_invoice(company_name, customer_name, item_code, warehouse, cost_center, accounts):
	from erpnext.accounts.doctype.sales_invoice.test_sales_invoice import create_sales_invoice

	sales_invoice = create_sales_invoice(
		company=company_name,
		customer=customer_name,
		currency="EUR",
		conversion_rate=1,
		debit_to=accounts["receivable"],
		income_account=accounts["income_standard"],
		expense_account=accounts["expense_seed"],
		cost_center=cost_center,
		warehouse=warehouse,
		item=item_code,
		posting_date=SEED_FROM_DATE.isoformat(),
		do_not_save=1,
	)
	sales_invoice.items = []
	sales_invoice.cost_center = cost_center
	sales_invoice.posting_date = SEED_FROM_DATE.isoformat()
	sales_invoice.due_date = SEED_FROM_DATE.isoformat()
	sales_invoice.set_posting_time = 1

	for item_row in (
		{
			"rate": 10,
			"income_account": accounts["income_standard"],
			"custom_datev_account_no": "8400",
			"custom_bu_schlussel": "19",
		},
		{
			"rate": 15,
			"income_account": accounts["income_standard"],
			"custom_datev_account_no": "8400",
			"custom_bu_schlussel": "19",
		},
		{
			"rate": 7,
			"income_account": accounts["income_standard"],
			"custom_datev_account_no": "8400",
			"custom_bu_schlussel": "7",
		},
		{
			"rate": 9,
			"income_account": accounts["income_reduced"],
			"custom_datev_account_no": "8300",
			"custom_bu_schlussel": "19",
		},
	):
		sales_invoice.append(
			"items",
			{
				"item_code": item_code,
				"item_name": item_code,
				"description": item_code,
				"qty": 1,
				"rate": item_row["rate"],
				"warehouse": warehouse,
				"income_account": item_row["income_account"],
				"expense_account": accounts["expense_seed"],
				"cost_center": cost_center,
				"custom_datev_account_no": item_row["custom_datev_account_no"],
				"custom_bu_schlussel": item_row["custom_bu_schlussel"],
			},
		)

	sales_invoice.insert(ignore_permissions=True)
	sales_invoice.submit()
	return sales_invoice


def create_seed_purchase_invoice(company_name, supplier_name, item_code, cost_center, accounts):
	from erpnext.accounts.doctype.purchase_invoice.test_purchase_invoice import make_purchase_invoice

	purchase_invoice = make_purchase_invoice(
		company=company_name,
		supplier=supplier_name,
		currency="EUR",
		conversion_rate=1,
		expense_account=accounts["expense_purchase"],
		posting_date=SEED_FROM_DATE.isoformat(),
		item=item_code,
		cost_center=cost_center,
		do_not_save=1,
		do_not_submit=1,
	)
	purchase_invoice.items = []
	purchase_invoice.credit_to = accounts["payable"]
	purchase_invoice.set_posting_time = 1
	purchase_invoice.posting_date = SEED_FROM_DATE.isoformat()
	purchase_invoice.bill_date = SEED_FROM_DATE.isoformat()
	purchase_invoice.due_date = SEED_FROM_DATE.isoformat()
	purchase_invoice.bill_no = "DATEV-DUMMY-BILL-2026-0001"
	purchase_invoice.cost_center = cost_center
	purchase_invoice.supplier_warehouse = None

	for item_row in (
		{"rate": 12, "expense_account": accounts["expense_purchase"], "custom_bu_schlussel": "9"},
		{"rate": 8, "expense_account": accounts["expense_purchase"], "custom_bu_schlussel": "9"},
		{"rate": 6, "expense_account": accounts["expense_secondary"], "custom_bu_schlussel": "4"},
	):
		purchase_invoice.append(
			"items",
			{
				"item_code": item_code,
				"item_name": item_code,
				"description": item_code,
				"qty": 1,
				"rate": item_row["rate"],
				"expense_account": item_row["expense_account"],
				"cost_center": cost_center,
				"custom_bu_schlussel": item_row["custom_bu_schlussel"],
			},
		)

	purchase_invoice.insert(ignore_permissions=True)
	purchase_invoice.submit()
	return purchase_invoice


def create_payment_entry(reference_doctype, reference_name, bank_account, posting_date):
	payment_entry = get_payment_entry(
		reference_doctype,
		reference_name,
		bank_account=bank_account,
		reference_date=posting_date.isoformat(),
		ignore_permissions=True,
	)
	payment_entry.posting_date = posting_date.isoformat()
	payment_entry.reference_no = f"DATEV-{reference_doctype.replace(' ', '-').upper()}-{posting_date.isoformat()}"
	payment_entry.reference_date = posting_date.isoformat()
	payment_entry.insert(ignore_permissions=True)
	payment_entry.submit()
	return payment_entry


def get_company_warehouse(company_name):
	warehouse = frappe.db.get_value("Warehouse", {"warehouse_name": "Stores", "company": company_name}, "name")
	if warehouse:
		return warehouse

	return frappe.db.get_value("Warehouse", {"company": company_name, "is_group": 0}, "name")


def get_company_cost_center(company_name):
	return frappe.db.get_value("Cost Center", {"company": company_name, "is_group": 0}, "name")


def get_company_accounts(company_name):
	return {
		"receivable": get_account(company_name, account_type="Receivable"),
		"payable": get_account(company_name, account_type="Payable"),
		"bank": get_liquidity_account(company_name),
		"income_standard": get_account(company_name, account_number="4200", root_type="Income"),
		"income_reduced": get_account(company_name, account_number="4300", root_type="Income"),
		"expense_seed": get_account(company_name, account_number="6990", root_type="Expense"),
		"expense_purchase": get_account(company_name, account_number="3400", root_type="Expense"),
		"expense_secondary": get_account(company_name, account_number="3300", root_type="Expense"),
	}


def get_liquidity_account(company_name):
	account = frappe.db.get_value(
		"Account",
		{"company": company_name, "is_group": 0, "account_number": "1200"},
		"name",
	)
	if account:
		return account

	account = frappe.db.get_value(
		"Account",
		{"company": company_name, "is_group": 0, "account_type": ["in", ["Bank", "Cash"]]},
		"name",
	)
	if account:
		return account

	return get_account(company_name, root_type="Asset")


def get_account(company_name, account_number=None, account_type=None, root_type=None):
	filters = {"company": company_name, "is_group": 0}
	if account_number:
		filters["account_number"] = account_number
	if account_type:
		filters["account_type"] = account_type
	if root_type:
		filters["root_type"] = root_type

	account = frappe.db.get_value("Account", filters, "name")
	if account:
		return account

	if account_type or root_type:
		account = frappe.db.get_value(
			"Account",
			{
				"company": company_name,
				"is_group": 0,
				"root_type": root_type
				or ("Asset" if account_type in {"Receivable", "Bank"} else "Liability"),
			},
			"name",
		)
		if account:
			return account

	raise frappe.DoesNotExistError(
		f"Missing account for {company_name}: number={account_number}, type={account_type}, root={root_type}"
	)


def build_runtime_filters(company_name):
	filters = get_seed_filters(company_name)
	datev_configuration = get_datev_configuration(company_name)
	filters.update(
		{
			"against_account": datev_configuration.temporary_against_account_number,
			"opening_account": datev_configuration.opening_against_account_number
			or datev_configuration.temporary_against_account_number,
		}
	)
	return filters


def execute_report_rows(company_name):
	filters = build_runtime_filters(company_name)
	transactions = get_transactions(filters.copy())
	grouped_transactions = group_sales_invoice_buchungsstapel(transactions, filters.copy())
	grouped_transactions = group_payment_entry_buchungsstapel(grouped_transactions, filters.copy())
	grouped_transactions = apply_buchungsstapel_mapping(grouped_transactions, filters.copy())
	columns = grouped_transactions[0].keys() if grouped_transactions else []
	return list(columns), grouped_transactions


def count_rows_for_voucher_type(rows, voucher_type):
	return sum(1 for row in rows if row.get("Beleginfo - Art 1") == voucher_type)


def cleanup_documents(doctype, filters):
	names = frappe.get_all(doctype, filters=filters, pluck="name", order_by="creation desc")
	for name in names:
		doc = frappe.get_doc(doctype, name)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc(doctype, name, ignore_permissions=True, force=1)


def delete_if_exists(doctype, name_or_filters):
	if not frappe.db.exists(doctype, name_or_filters):
		return

	doc = frappe.get_doc(doctype, name_or_filters)
	if doc.docstatus == 1:
		doc.cancel()
	frappe.delete_doc(doctype, doc.name, ignore_permissions=True, force=1)


@contextmanager
def allow_uninstalled_hook_resolution():
	original = getattr(frappe.local.flags, "in_install", False)
	frappe.local.flags.in_install = True
	try:
		yield
	finally:
		frappe.local.flags.in_install = original
