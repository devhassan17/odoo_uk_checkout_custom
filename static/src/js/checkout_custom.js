/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

const UK_POSTCODE_REGEX = /^[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}$/i;

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
        this._fixZipLabels();
        return this._super(...arguments);
    },

    _fixZipLabels() {
        // Enforce "Postal Code" label for any ZIP field
        const labels = this.el.querySelectorAll('label[for="o_zip"], #div_zip label');
        labels.forEach(label => {
            if (label.textContent.includes('Zip')) {
                label.textContent = 'Postal Code';
            }
        });
    },

    _onPostcodeInput(ev) {
        const input = ev.currentTarget;
        input.value = input.value.toUpperCase();
        if (input.value && !UK_POSTCODE_REGEX.test(input.value.trim())) {
            input.setCustomValidity('Please enter a valid UK Postal Code, e.g. SW1A 1AA.');
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

        // Main zip (UK Only)
        const postcode = this.el.querySelector('input[name="zip"]');
        const postcodeVal = postcode ? postcode.value.trim().toUpperCase() : '';

        if (postcode && postcodeVal && !UK_POSTCODE_REGEX.test(postcodeVal)) {
            postcode.setCustomValidity('Please enter a valid UK Postal Code, e.g. SW1A 1AA.');
            postcode.reportValidity();
            ev.preventDefault();
            return;
        } else if (postcode) {
            postcode.setCustomValidity('');
            postcode.value = postcodeVal;
        }
    },
});
