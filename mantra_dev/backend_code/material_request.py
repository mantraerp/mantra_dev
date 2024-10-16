import frappe
# from erpnext.stock.doctype.stock_entry.stock_entry import update_item
# from erpnext.stock.doctype.stock_entry.stock_entry import set_missing_values
from erpnext.stock.doctype.stock_entry.stock_entry import get_mapped_doc
from frappe.utils import (
	cint,
	comma_or,
	cstr,
	flt,
	format_time,
	formatdate,
	get_link_to_form,
	getdate,
	nowdate,
)

@frappe.whitelist()
def get_target_warehouse_deatils(warehouse_nm):
    wm = frappe.db.sql("select warehouse_manager from `tabWarehouse Manager` where parent = %s",warehouse_nm,as_dict=True)
    w_nm=[]
    if wm:
        for i in wm:
            w_nm.append(i["warehouse_manager"])
    print(w_nm  )
    return w_nm

@frappe.whitelist()
def make_stock_in_entry(source_name, target_doc=None):
    # frappe.msgprint(source_name)
    dt=frappe.db.get_value("Stock Entry", { "custom_material_request_no": source_name }, "name")
    # frappe.msgprint(source_name)
    def set_missing_values(source, target):
        target.stock_entry_type = "Material Transfer"
        target.set_missing_values()
        if not frappe.db.get_single_value("Stock Settings", "use_serial_batch_fields"):
            target.make_serial_and_batch_bundle_for_transfer()
    def update_item(source_doc, target_doc, source_parent):
        
        print("\n\n",source_doc,"\n\n")
        target_doc.t_warehouse = ""
        if source_doc.material_request_item and source_doc.material_request:
            add_to_transit = frappe.db.get_value("Stock Entry", dt, "add_to_transit")
            if add_to_transit:
                warehouse = frappe.get_value(
					"Material Request Item", source_doc.material_request_item, "warehouse"
				)
                print("\n\n",warehouse,"\n\n")
            target_doc.t_warehouse = warehouse
        target_doc.s_warehouse = source_doc.t_warehouse
        target_doc.qty = source_doc.qty - source_doc.transferred_qty
    doclist = get_mapped_doc(
		"Stock Entry",
		dt,
		{
			"Stock Entry": {
				"doctype": "Stock Entry",
				"field_map": {"name": "outgoing_stock_entry","docstatus":1},     
			},
			"Stock Entry Detail": {
				"doctype": "Stock Entry Detail",
				"field_map": {
					"name": "ste_detail",
					"parent": "against_stock_entry",
					"serial_no": "serial_no",
					"batch_no": "batch_no",
				},
				"postprocess": update_item,
				"condition": lambda doc: flt(doc.qty) - flt(doc.transferred_qty) > 0.01,
			},
		},
		target_doc,
		set_missing_values,
	)
    return doclist
