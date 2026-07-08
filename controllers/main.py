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
        return response

    @http.route(['/shop/address/submit'], type='http', methods=['POST'], auth='public', website=True, sitemap=False)
    def shop_address_submit(self, **kw):
        response = super().shop_address_submit(**kw)

        if request.httprequest.method == 'POST':
            order = getattr(request, 'cart', None) or (request.website.sale_get_order() if hasattr(request.website, 'sale_get_order') else None)
            if order:
                # Determine which partner was just updated or created (this is the billing/main address)
                partner_id = int(kw.get('partner_id') or 0)
                if partner_id > 0:
                    partner = request.env['res.partner'].sudo().browse(partner_id)
                else:
                    address_type = kw.get('address_type')
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

                    # Process shipping address if we are editing/creating the billing/main address
                    if not address_type or address_type == 'billing':
                        use_different_shipping = kw.get('use_different_shipping') == 'on'
                        if use_different_shipping:
                            shipping_first_name = (kw.get('shipping_first_name') or '').strip()
                            shipping_last_name = (kw.get('shipping_last_name') or '').strip()
                            shipping_phone = (kw.get('shipping_phone') or '').strip()
                            shipping_street = (kw.get('shipping_street') or '').strip()
                            shipping_street2 = (kw.get('shipping_street2') or '').strip()
                            shipping_city = (kw.get('shipping_city') or '').strip()
                            shipping_zip = (kw.get('shipping_zip') or '').strip().upper()
                            shipping_country_id = int(kw.get('shipping_country_id') or 0) or order.company_id.country_id.id or 233

                            shipping_vals = {
                                'x_first_name': shipping_first_name,
                                'x_last_name': shipping_last_name,
                                'name': ' '.join(p for p in [shipping_first_name, shipping_last_name] if p).strip() or "Shipping Contact",
                                'phone': shipping_phone,
                                'street': shipping_street,
                                'street2': shipping_street2,
                                'city': shipping_city,
                                'zip': shipping_zip,
                                'country_id': shipping_country_id,
                                'type': 'delivery',
                                'parent_id': partner.id,
                            }

                            # Check if a separate shipping partner already exists on the order
                            existing_shipping = order.partner_shipping_id
                            if existing_shipping and existing_shipping.id != partner.id:
                                existing_shipping.sudo().write(shipping_vals)
                            else:
                                # Create new child partner for delivery
                                shipping_partner = request.env['res.partner'].sudo().create(shipping_vals)
                                order.sudo().write({'partner_shipping_id': shipping_partner.id})
                        else:
                            # Ensure shipping is the same as billing
                            if order.partner_shipping_id and order.partner_shipping_id.id != partner.id:
                                order.sudo().write({'partner_shipping_id': partner.id})

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
