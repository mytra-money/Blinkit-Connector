frappe.ui.form.on('Shipment', {
    refresh: function (frm) {
        const add_custom_button = (label, action) => {
			if (!frm.custom_buttons[label]) {
				frm.add_custom_button(label, action, __('BlinkIt Actions'));
			}
		};
        if (frm.doc.docstatus === 1) {
            const submit_asn = () => frm.events.submit_asn(frm)
            add_custom_button(__("Submit ASN"), submit_asn);
        }
    },
    submit_asn: function (frm) {
        frappe.call({
            method: "blinkit_connector.blinkit_repository.submit_asn",
            freeze: true,
            freeze_message: __("Submitting BlinkIt ASN"),
			args: {
                shipment: frm.doc.name,
			},
            callback: (r) => 
                frappe.msgprint({
                    message: __(r.message),
                    title: __("BlinkIt ASN Status")
                }),
            error: (r) => frappe.msgprint({
				message: __("Error Submitting BlinkIt ASN"),
				title: __("Error")
			}),
        })
    },
});