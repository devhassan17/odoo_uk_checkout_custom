/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

const UK_POSTCODE_REGEX = /^[A-Za-z]{1,2}\d[A-Za-z\d]?\s?\d[A-Za-z]{2}$/;
const UK_MOBILE_REGEX = /^(?:\+44\s?7\d{3}|0?7\d{3})\s?\d{3}\s?\d{3}$/;

publicWidget.registry.UkCheckoutCustom = publicWidget.Widget.extend({
    selector: 'form[action*="/shop/address"]',

    events: {
        'input #first_name': '_syncFullName',
        'input #last_name': '_syncFullName',
        'submit': '_onSubmit',
    },

    start() {
        this._syncFullName();
        return this._super(...arguments);
    },

    _syncFullName() {
        const first = (this.el.querySelector('#first_name')?.value || '').trim();
        const last = (this.el.querySelector('#last_name')?.value || '').trim();
        const hiddenName = this.el.querySelector('#uk_hidden_full_name');
        if (hiddenName) {
            hiddenName.value = [first, last].filter(Boolean).join(' ');
        }
    },

    _onSubmit(ev) {
        this._syncFullName();

        const postcode = this.el.querySelector('input[name="zip"]');
        const phone = this.el.querySelector('input[name="phone"]');

        if (postcode && postcode.value && !UK_POSTCODE_REGEX.test(postcode.value.trim())) {
            postcode.setCustomValidity('Please enter a valid UK postcode, e.g. SW1A 1AA.');
            postcode.reportValidity();
            ev.preventDefault();
            return;
        } else if (postcode) {
            postcode.setCustomValidity('');
        }

        if (phone && phone.value && !UK_MOBILE_REGEX.test(phone.value.trim())) {
            phone.setCustomValidity('Please enter a valid UK mobile number.');
            phone.reportValidity();
            ev.preventDefault();
            return;
        } else if (phone) {
            phone.setCustomValidity('');
        }
    },
});
