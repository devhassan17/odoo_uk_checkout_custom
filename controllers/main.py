from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleCustom(WebsiteSale):
    """Post-process checkout submissions.

    This keeps compatibility high by letting the standard checkout flow run first,
    then updating the created/edited partner with the extra fields we collect on the
    frontend.
    """

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth='public', website=True, sitemap=False)
    def address(self, **kw):
        response = super().address(**kw)
        if response.status_code == 200 and isinstance(response.qcontext, dict):
            # In Odoo 18, 'checkout' might be missing or named 'values'.
            # We ensure 'checkout' is available for our custom template.
            if 'checkout' not in response.qcontext:
                response.qcontext['checkout'] = response.qcontext.get('values', {})
        return response

    @http.route(['/shop/address/submit'], type='http', methods=['POST'], auth='public', website=True, sitemap=False)
    def shop_address_submit(self, **kw):
        response = super().shop_address_submit(**kw)

        if request.httprequest.method == 'POST':
            order = request.website.sale_get_order()
            partner = order.partner_invoice_id or order.partner_id
            if partner:
                first_name = (kw.get('first_name') or '').strip()
                last_name = (kw.get('last_name') or '').strip()
                marketing_opt_in = kw.get('x_marketing_opt_in') in ('on', 'true', '1', 'yes')

                vals = {}
                if first_name or last_name:
                    vals.update({
                        'x_first_name': first_name,
                        'x_last_name': last_name,
                        'name': ' '.join(p for p in [first_name, last_name] if p).strip() or partner.name,
                    })
                # Always store explicit checkbox choice when it is present in the form.
                if 'x_marketing_opt_in' in kw or request.httprequest.form.get('x_marketing_opt_in') is not None:
                    vals['x_marketing_opt_in'] = marketing_opt_in

                if vals:
                    # Keep shipping and invoice partners aligned when they are the same customer profile.
                    related_partners = (order.partner_id | order.partner_invoice_id | order.partner_shipping_id).exists()
                    related_partners.sudo().write(vals)

        return response
