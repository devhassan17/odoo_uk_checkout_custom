import logging
import traceback
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class WebsiteSaleCustom(WebsiteSale):
    """Post-process checkout submissions.

    This keeps compatibility high by letting the standard checkout flow run first,
    then updating the created/edited partner with the extra fields we collect on the
    frontend.
    """

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, *args, **kwargs):
        try:
            return super().cart_update(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            _logger.error("Klaviyo Debug: %s", tb)
            raise UserError("Klaviyo Debug Traceback:\n%s" % tb)

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, *args, **kwargs):
        try:
            return super().cart_update_json(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            _logger.error("Klaviyo Debug: %s", tb)
            raise UserError("Klaviyo Debug Traceback:\n%s" % tb)

    @http.route(['/shop/address'], type='http', methods=['GET'], auth='public', website=True, sitemap=False)
    def shop_address(self, **kw):
        response = super().shop_address(**kw)
        if response.status_code == 200 and hasattr(response, 'qcontext') and isinstance(response.qcontext, dict):
            # In Odoo 18, 'checkout' might be missing or named 'values'.
            # We ensure 'checkout' is available for our custom template.
            if 'checkout' not in response.qcontext:
                response.qcontext['checkout'] = response.qcontext.get('values', {})

            # Restrict countries based on active company configuration, falling back to UK
            countries = response.qcontext.get('countries')
            if countries:
                company = request.website.company_id or request.env.company
                if company and hasattr(company, 'x_checkout_country_ids') and company.x_checkout_country_ids:
                    allowed_countries = countries & company.x_checkout_country_ids
                    response.qcontext['countries'] = allowed_countries
                    # Ensure selection defaults to one of the allowed countries
                    current_country = response.qcontext.get('country')
                    if not current_country or current_country not in allowed_countries:
                        response.qcontext['country'] = allowed_countries[:1]
                else:
                    # If no allowed countries are configured for this company, show all countries
                    pass

            # Detect if a separate billing address is used
            order = getattr(request, 'cart', None) or (request.website.sale_get_order() if hasattr(request.website, 'sale_get_order') else None)
            if order:
                partner_invoice = order.partner_invoice_id
                partner_shipping = order.partner_shipping_id or order.partner_id
                if partner_invoice and partner_shipping and partner_invoice.id != partner_shipping.id:
                    response.qcontext['has_different_billing'] = True
                    response.qcontext['billing_partner'] = partner_invoice
                else:
                    response.qcontext['has_different_billing'] = False
                    response.qcontext['billing_partner'] = False
        return response

    @http.route(['/shop/address/submit'], type='http', methods=['POST'], auth='public', website=True, sitemap=False)
    def shop_address_submit(self, **kw):
        response = super().shop_address_submit(**kw)

        if request.httprequest.method == 'POST':
            order = getattr(request, 'cart', None) or (request.website.sale_get_order() if hasattr(request.website, 'sale_get_order') else None)
            if order:
                address_type = kw.get('address_type')
                # Determine which partner was just updated or created (this is the delivery/main address)
                partner_id = int(kw.get('partner_id') or 0)
                if partner_id > 0:
                    partner = request.env['res.partner'].sudo().browse(partner_id)
                else:
                    if address_type == 'shipping':
                        partner = order.partner_shipping_id
                    else:
                        partner = order.partner_invoice_id or order.partner_id

                if partner and partner.exists():
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
                        # Exclude the public partner to avoid modifying the public user record.
                        public_partner = request.website.user_id.sudo().partner_id
                        if partner.id != public_partner.id:
                            partner.sudo().write(vals)

                    # Process billing address if different
                    billing_different = kw.get('billing_different') in ('on', 'true', '1', 'yes')
                    if billing_different:
                        bill_first_name = (kw.get('billing_first_name') or '').strip()
                        bill_last_name = (kw.get('billing_last_name') or '').strip()
                        bill_name = ' '.join(p for p in [bill_first_name, bill_last_name] if p).strip()
                        
                        billing_vals = {
                            'parent_id': partner.id,
                            'type': 'invoice',
                            'x_first_name': bill_first_name,
                            'x_last_name': bill_last_name,
                            'name': bill_name or partner.name,
                            'street': kw.get('billing_street'),
                            'street2': kw.get('billing_street2'),
                            'city': kw.get('billing_city'),
                            'zip': (kw.get('billing_zip') or '').strip(),
                            'country_id': int(kw.get('billing_country_id') or 0) or partner.country_id.id,
                            'phone': kw.get('billing_phone') or partner.phone,
                        }
                        
                        partner_invoice = order.partner_invoice_id
                        if partner_invoice and partner_invoice.id != partner.id and partner_invoice.parent_id.id == partner.id:
                            partner_invoice.sudo().write(billing_vals)
                        else:
                            partner_invoice = request.env['res.partner'].sudo().create(billing_vals)
                            order.sudo().write({'partner_invoice_id': partner_invoice.id})
                    else:
                        # Reset to main partner
                        order.sudo().write({'partner_invoice_id': partner.id})

                    # Enqueue and immediately dispatch 'Started Checkout' event to Klaviyo.
                    if order.order_line:
                        event_queue_model = request.env.get('fpg.odoo.klaviyo.integration.event.queue')
                        if event_queue_model is not None:
                            event_queue = event_queue_model.sudo()
                            existing_checkout = event_queue.search([
                                ('order_id', '=', order.id),
                                ('event_type', '=', 'started_checkout')
                            ], limit=1)
                            if not existing_checkout:
                                try:
                                    with request.env.cr.savepoint():
                                        new_event = event_queue.create({
                                            'order_id': order.id,
                                            'event_type': 'started_checkout',
                                        })
                                        new_event.send_event()
                                except Exception as e:
                                    _logger.exception("Klaviyo: Failed to create or send Started Checkout event: %s", e)

        return response
