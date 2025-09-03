# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# ERPNext - web based ERP (http://erpnext.com)
# For license information, please see license.txt


import frappe.sessions

import frappe
from frappe import _, msgprint
from frappe.query_builder.functions import Sum
from frappe.utils import flt
from erpnext.buying.utils import validate_for_items
from erpnext.controllers.buying_controller import BuyingController
from mantra_dev.backend_code.globle import create_notification_log
from mantra_dev.mantra_dev.report.material_request_tracking.material_request_tracking import create_material_request_mail_content, send_material_request_submit_mail_content
from erpnext.stock.doctype.material_request.material_request import make_stock_entry
from erpnext.stock.doctype.material_request.material_request import MaterialRequest as OrignalMaterialRequest


form_grid_templates = {"items": "templates/form_grid/material_request_grid.html"}


class MaterialRequest(OrignalMaterialRequest):

    def validate(self):
            super().validate()

            self.validate_schedule_date()
            self.check_for_on_hold_or_closed_status("Sales Order", "sales_order")
            self.validate_uom_is_integer("uom", "qty")
            self.validate_material_request_type()

            if not self.status:
                self.status = "Draft"

            from erpnext.controllers.status_updater import validate_status

            validate_status(
                self.status,
                [
                    "Draft",
                    "Submitted",
                    "Stopped",
                    "Cancelled",
                    "Pending",
                    "Partially Ordered",
                    "Ordered",
                    "Issued",
                    "Transferred",
                    "Received",
                ],
            )

            # Change in Validate.
            # frappe,msgprint("hello")
            if self.material_request_type=="Purchase":
                # print("hello")
                pass
                # validate_for_items(self)	
            else:
                # frappe.msgprint("Else called")
                validate_for_items(self)	
            self.set_title()
            # self.validate_qty_against_so()
            # NOTE: Since Item BOM and FG quantities are combined, using current data, it cannot be validated
            # Though the creation of Material Request from a Production Plan can be rethought to fix this
            # Change End Here

            self.reset_default_field_value("set_warehouse", "items", "warehouse")
            self.reset_default_field_value("set_from_warehouse", "items", "from_warehouse")


    def set_title(self):
        # Change => d.custom_item_description isted of d.item_name
        """Set title as comma separated list of items"""
        if not self.title:
            items = ", ".join([d.custom_item_description for d in self.items][:3])
            self.title = _("{0} Request for {1}").format(_(self.material_request_type), items)[:100]
        # Change end here



# Meet Functions => on_submit and after_insert events.
    def on_submit(self):
            self.update_requested_qty_in_production_plan()
            self.update_requested_qty()
            if self.material_request_type == "Purchase" and frappe.db.exists(
                "Budget", {"applicable_on_material_request": 1, "docstatus": 1}
            ):
                self.validate_budget()

            if (self.custom_approval_from_warehouse_manager == 1 and self.material_request_type == "Material Transfer"):
                # Automatically Create Stock Entry When a Material Request of Type "Material Transfer" is Generated from the Material Request Tracking Report
                stock_entry = make_stock_entry(self.name)
                stock_entry.save()
                create_notification_log(
                    subject= f"{self.name} Material Requested Material Dispatched",
                    content= f"{self.name} Material Requested Material Dispatched",
                    document_type= "Material Request",
                    document_name= self.name,
                    for_user= self.owner
                )
                subject, content = send_material_request_submit_mail_content(self)
                frappe.sendmail(recipients=self.owner, subject=subject, content=content, now=True)
        
    def after_insert(self):
        # Automatically notify and send an email to the Warehouse Manager of the source warehouse
        # when a Material Transfer Request is created through the Material Request Tracking Report
        # and requires approval from the Warehouse Manager.
        if (self.custom_approval_from_warehouse_manager == 1  and self.material_request_type == "Material Transfer"):
            warehouse_manager_list = frappe.db.get_all("Warehouse Manager", {'parent': self.set_from_warehouse}, pluck="warehouse_manager")
            for user in warehouse_manager_list:
                create_notification_log(
                    subject= f"Approval Request for {self.name} Material Transfer to Employee",
                    content= f"Approval Request for {self.name} Material Transfer to Employee",
                    document_type= "Material Request",
                    document_name= self.name,
                    for_user= user
                )
            subject, content = create_material_request_mail_content(self)
            frappe.sendmail(recipients=warehouse_manager_list, subject=subject, content=content, now=True)




    def update_completed_qty(self, mr_items=None, update_modified=True):
            if self.material_request_type == "Purchase":
                return

            if not mr_items:
                mr_items = [d.name for d in self.get("items")]

            mr_items_ordered_qty = self.get_mr_items_ordered_qty(mr_items)
            mr_qty_allowance = frappe.db.get_single_value("Stock Settings", "mr_qty_allowance")

            for d in self.get("items"):
                if d.name in mr_items:
                    if self.material_request_type in ("Material Issue", "Material Transfer", "Customer Provided"):
                        d.ordered_qty = flt(mr_items_ordered_qty.get(d.name))

                        if mr_qty_allowance:
                            allowed_qty = flt(
                                (d.qty + (d.qty * (mr_qty_allowance / 100))), d.precision("ordered_qty")
                            )

                            # Change start here => if d.ordered_qty and d.ordered_qty > allowed_qty isted of if d.ordered_qty and flt(d.ordered_qty, precision) > flt(allowed_qty, precision) 
                            if d.ordered_qty and d.ordered_qty > allowed_qty:
                                frappe.throw(
                                    _(
                                        "The total Issue / Transfer quantity {0} in Material Request {1}  cannot be greater than allowed requested quantity {2} for Item {3}"
                                    ).format(d.ordered_qty, d.parent, allowed_qty, d.item_code)
                                )
                            # Change end here

                        # Change Start here => elif d.ordered_qty and d.ordered_qty > d.stock_qty isted of elif d.ordered_qty and flt(d.ordered_qty, precision) > flt(d.stock_qty, precision)
                        elif d.ordered_qty and d.ordered_qty > d.stock_qty:
                            frappe.throw(
                                _(
                                    "The total Issue / Transfer quantity {0} in Material Request {1} cannot be greater than requested quantity {2} for Item {3}"
                                ).format(d.ordered_qty, d.parent, d.qty, d.item_code)
                            )
                        # Change end here
                    elif self.material_request_type == "Manufacture":
                        d.ordered_qty = flt(mr_items_ordered_qty.get(d.name))

                    frappe.db.set_value(d.doctype, d.name, "ordered_qty", d.ordered_qty)

            self._update_percent_field(
                {
                    "target_dt": "Material Request Item",
                    "target_parent_dt": self.doctype,
                    "target_parent_field": "per_ordered",
                    "target_ref_field": "stock_qty",
                    "target_field": "ordered_qty",
                    "name": self.name,
                },
                update_modified,
            )
