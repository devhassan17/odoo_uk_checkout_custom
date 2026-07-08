/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

const UK_POSTCODE_REGEX = /^[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}$/i;

publicWidget.registry.UkCheckoutCustom = publicWidget.Widget.extend({
    selector: 'form[action*="/shop/address"]',

    events: {
        'input #first_name': '_syncFullName',
        'input #last_name': '_syncFullName',
        'input input[name="zip"]': '_onPostcodeInput',
        'change #use_different_shipping': '_onToggleShipping',
        'submit': '_onSubmit',
    },

    start() {
        this._syncFullName();
        this._fixZipLabels();
        this._onToggleShipping();
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

    _onToggleShipping() {
        const checkbox = this.el.querySelector('#use_different_shipping');
        const container = this.el.querySelector('#shipping_address_fields');
        if (!checkbox || !container) return;

        const isChecked = checkbox.checked;
        if (isChecked) {
            container.classList.remove('d-none');
        } else {
            container.classList.add('d-none');
        }

        // Toggle required attribute on shipping fields
        const requiredFields = [
            '#shipping_first_name',
            '#shipping_last_name',
            '#shipping_street',
            '#shipping_city',
            '#shipping_zip'
        ];
        requiredFields.forEach(selector => {
            const field = container.querySelector(selector);
            if (field) {
                if (isChecked) {
                    field.setAttribute('required', 'required');
                } else {
                    field.removeAttribute('required');
                }
            }
        });
    },

    _onSubmit(ev) {
        this._syncFullName();

        const postcode = this.el.querySelector('input[name="zip"]');
        const postcodeVal = postcode ? postcode.value.trim().toUpperCase() : '';

        if (postcode && postcodeVal && !UK_POSTCODE_REGEX.test(postcodeVal)) {
            postcode.setCustomValidity('Please enter a valid UK Postal Code, e.g. SW1A 1AA.');
            postcode.reportValidity();
            ev.preventDefault();
            return;
        } else if (postcode) {
            postcode.setCustomValidity('');
            postcode.value = postcodeVal; // Ensure uppercase in the form
        }

        // Validate shipping postcode if different shipping is checked
        const useDifferentShipping = this.el.querySelector('#use_different_shipping')?.checked;
        if (useDifferentShipping) {
            const shippingZip = this.el.querySelector('#shipping_zip');
            const shippingZipVal = shippingZip ? shippingZip.value.trim().toUpperCase() : '';
            if (shippingZip && shippingZipVal && !UK_POSTCODE_REGEX.test(shippingZipVal)) {
                shippingZip.setCustomValidity('Please enter a valid UK Postal Code for shipping, e.g. SW1A 1AA.');
                shippingZip.reportValidity();
                ev.preventDefault();
                return;
            } else if (shippingZip) {
                shippingZip.setCustomValidity('');
                shippingZip.value = shippingZipVal;
            }
        }
    },
});
