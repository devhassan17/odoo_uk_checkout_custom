import logging
import traceback
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class WebsiteSaleCustom(WebsiteSale):
    """Post-process checkout submissions.

    This keeps compatibility high by letting the standard checkout flow run first,
    then updating the created/edited partner with the extra fields we collect on the
    frontend.
    """

    def _get_cart_order(self, force_create=False):
        """Safely retrieve or create the cart order across Odoo versions."""
        order = getattr(request, 'cart', None)
        if order:
            return order
        if hasattr(self, '_get_search_order'):
            try:
                order = self._get_search_order(force_create=force_create)
                if order:
                    return order
            except Exception:
                pass
        if hasattr(request, 'website') and hasattr(request.website, 'sale_get_order'):
            try:
                order = request.website.sale_get_order(force_create=force_create)
                if order:
                    return order
            except Exception:
                pass
        so_id = request.session.get('sale_order_id')
        if so_id:
            order = request.env['sale.order'].sudo().browse(so_id).exists()
            if order and order.state == 'draft':
                return order
        if force_create:
            partner = request.env.user.partner_id
            website = getattr(request, 'website', None) or (request.env['website'].get_current_website() if hasattr(request.env.get('website'), 'get_current_website') else False)
            company = getattr(website, 'company_id', None) or request.env.company
            order = request.env['sale.order'].sudo().create({
                'partner_id': partner.id,
                'website_id': website.id if website else False,
                'company_id': company.id if company else False,
            })
            request.session['sale_order_id'] = order.id
            return order
        return request.env['sale.order']

    @http.route(['/shop/address'], type='http', methods=['GET'], auth='public', website=True, sitemap=False)
    def shop_address(self, **kw):
        try:
            response = super().shop_address(**kw)
        except Exception as e:
            _logger.exception("Error in super().shop_address: %s", e)
            raise

        try:
            if response and hasattr(response, 'status_code') and response.status_code == 200 and hasattr(response, 'qcontext') and isinstance(response.qcontext, dict):
                # In Odoo 18, 'checkout' might be missing or named 'values'.
                # We ensure 'checkout' is available for our custom template.
                if 'checkout' not in response.qcontext:
                    response.qcontext['checkout'] = response.qcontext.get('values', {})

                # Restrict countries based on active company configuration, falling back to UK
                countries = response.qcontext.get('countries')
                if countries:
                    company = getattr(request.website, 'company_id', None) or getattr(request.env, 'company', None)
                    if company and hasattr(company, 'x_checkout_country_ids') and company.x_checkout_country_ids:
                        allowed_countries = countries & company.x_checkout_country_ids
                        response.qcontext['countries'] = allowed_countries
                        # Ensure selection defaults to one of the allowed countries
                        current_country = response.qcontext.get('country')
                        if not current_country or current_country not in allowed_countries:
                            response.qcontext['country'] = allowed_countries[:1]
        except Exception as e:
            _logger.exception("Error in custom shop_address post-processing: %s", e)
        return response

    @http.route(['/shop/address/submit'], type='http', methods=['POST'], auth='public', website=True, sitemap=False)
    def shop_address_submit(self, **kw):
        # Call super first so main form execution takes precedence
        try:
            response = super().shop_address_submit(**kw)
        except Exception as e:
            _logger.exception("Error in super().shop_address_submit: %s", e)
            raise

        try:
            order = self._get_cart_order(force_create=False)
            if request.httprequest.method == 'POST' and order:
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
                    if 'x_marketing_opt_in' in kw or request.httprequest.form.get('x_marketing_opt_in') is not None:
                        vals['x_marketing_opt_in'] = marketing_opt_in

                    if vals:
                        public_partner = request.website.user_id.sudo().partner_id
                        if partner.id != public_partner.id:
                            partner.sudo().write(vals)

                    # Enqueue and immediately dispatch 'Started Checkout' event to Klaviyo.
                    if order.order_line:
                        try:
                            event_queue_model = request.env.get('fpg.odoo.klaviyo.integration.event.queue')
                            if event_queue_model is not None:
                                event_queue = event_queue_model.sudo()
                                existing_checkout = event_queue.search([
                                    ('order_id', '=', order.id),
                                    ('event_type', '=', 'started_checkout')
                                ], limit=1)
                                if not existing_checkout:
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
