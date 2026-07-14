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

    @http.route(['/shop/cart/update_json'], type='jsonrpc', auth="public", methods=['POST'], website=True, csrf=False)
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
        try:
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
        except Exception as e:
            _logger.exception("Error in custom shop_address: %s", e)
        return response

    @http.route(['/shop/address/submit'], type='http', methods=['POST'], auth='public', website=True, sitemap=False)
    def shop_address_submit(self, **kw):
        # Call super to process the main form values (which will update the delivery/main address)
        response = super().shop_address_submit(**kw)

        order = getattr(request, 'cart', None) or (request.website.sale_get_order() if hasattr(request.website, 'sale_get_order') else None)

        if request.httprequest.method == 'POST' and order:
            try:
                # Determine main partner
                partner = order.partner_id

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
            except Exception as e:
                _logger.exception("Error in shop_address_submit post-processing: %s", e)

        return response
