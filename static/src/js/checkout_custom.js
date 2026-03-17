/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

const UK_POSTCODE_REGEX = /^[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}$/i;
const UK_MOBILE_REGEX = /^(?:\+44\s?7\d{3}|0?7\d{3})\s?\d{3}\s?\d{3}$/;

publicWidget.registry.UkCheckoutCustom = publicWidget.Widget.extend({
    selector: 'form[action*="/shop/address"]',

    events: {
        'input #first_name': '_syncFullName',
        'input #last_name': '_syncFullName',
        'input input[name="zip"]': '_onPostcodeInput',
        'submit': '_onSubmit',
    },

    start() {
        this._syncFullName();
        return this._super(...arguments);
    },

    _onPostcodeInput(ev) {
        const input = ev.currentTarget;
        input.value = input.value.toUpperCase();
        if (input.value && !UK_POSTCODE_REGEX.test(input.value.trim())) {
            input.setCustomValidity('Please enter a valid UK postcode, e.g. SW1A 1AA.');
        } else {
            input.setCustomValidity('');
        }
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
        const postcodeVal = postcode ? postcode.value.trim().toUpperCase() : '';

        if (postcode && postcodeVal && !UK_POSTCODE_REGEX.test(postcodeVal)) {
            postcode.setCustomValidity('Please enter a valid UK postcode, e.g. SW1A 1AA.');
            postcode.reportValidity();
            ev.preventDefault();
            return;
        } else if (postcode) {
            postcode.setCustomValidity('');
            postcode.value = postcodeVal; // Ensure uppercase in the form
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
