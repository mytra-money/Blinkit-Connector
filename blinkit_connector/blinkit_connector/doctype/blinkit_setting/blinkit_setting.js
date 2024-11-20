// Copyright (c) 2024, pwctech technologies private limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Blinkit Setting", {
	refresh(frm) {
        if (!frm.doc.blinkit_user) {
            frm.set_df_property('get_auth_header', 'hidden', 1)
        }
	},
get_auth_header: (frm) => {
    return frm.call({
        doc: frm.doc,
        method: "get_token"
    });
}
});
