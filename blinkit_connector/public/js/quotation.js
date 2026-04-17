frappe.ui.form.on('Quotation', {
    refresh: function (frm) {
        const add_custom_button = (label, action) => {
			if (!frm.custom_buttons[label]) {
				frm.add_custom_button(label, action, __('BlinkIt Actions'));
			}
		};
        if (frm.doc.docstatus === 0) {
            const has_blinkit_item = (frm.doc.items || []).some(
                item => item.blinkit_po
            );
            if (has_blinkit_item) {
                const refresh_items = () => frm.events.refresh_items(frm)
                add_custom_button(__("Refresh Items"), refresh_items);
            }
        }

    },
    refresh_items: function (frm) {
        frappe.call({
            method: "blinkit_connector.utils.refresh_blinkit_items",
            freeze: true,
            freeze_message: __("Refreshing BlinkIt Order Items"),
			args: {
                quotation: frm.doc.name,
			},
            callback: (r) => 
                frappe.msgprint({
                    message: __(r.message),
                    title: __("BlinkIt Order")
                }),
            error: (r) => frappe.msgprint({
				message: __("Error Refreshing BlinkIt Order Items"),
				title: __("Error")
			}),
        })
    },

})