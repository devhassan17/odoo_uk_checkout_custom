/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

const UK_POSTCODE_REGEX = /^[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}$/i;

publicWidget.registry.UkCheckoutCustom = publicWidget.Widget.extend({
    selector: 'form[action*="/shop/address"]',

    events: {
        'input #first_name': '_syncFullName',
        'input #last_name': '_syncFullName',
        'input input[name="zip"]': '_onPostcodeInput',
        'input input[name="billing_zip"]': '_onBillingPostcodeInput',
        'change #billing_different': '_onBillingDifferentChange',
        'change #billing_country_id': '_onBillingCountryChange',
        'submit': '_onSubmit',
    },

    start() {
        this._syncFullName();
        this._fixZipLabels();
        this._onBillingDifferentChange();
        return this._super(...arguments);
    },

    _fixZipLabels() {
        // Enforce "Postal Code" label for any ZIP field
        const labels = this.el.querySelectorAll('label[for="o_zip"], #div_zip label, label[for="billing_zip"], #div_billing_zip label');
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

    _onBillingPostcodeInput(ev) {
        const input = ev.currentTarget;
        input.value = input.value.toUpperCase();
        
        if (this._isBillingCountryUk()) {
            if (input.value && !UK_POSTCODE_REGEX.test(input.value.trim())) {
                input.setCustomValidity('Please enter a valid UK Postal Code, e.g. SW1A 1AA.');
            } else {
                input.setCustomValidity('');
            }
        } else {
            input.setCustomValidity('');
        }
    },

    _isBillingCountryUk() {
        const countrySelect = this.el.querySelector('#billing_country_id');
        if (!countrySelect) return false;
        const selectedOption = countrySelect.options[countrySelect.selectedIndex];
        return selectedOption && selectedOption.text.includes('United Kingdom');
    },

    _onBillingDifferentChange() {
        const checkbox = this.el.querySelector('#billing_different');
        const container = this.el.querySelector('#billing_address_container');
        if (!checkbox || !container) return;

        const isChecked = checkbox.checked;
        container.style.display = isChecked ? 'block' : 'none';

        // Toggle required attributes
        const requiredInputs = container.querySelectorAll('input, select');
        requiredInputs.forEach(input => {
            const name = input.getAttribute('name');
            if (['billing_first_name', 'billing_last_name', 'billing_street', 'billing_city', 'billing_zip', 'billing_country_id'].includes(name)) {
                if (isChecked) {
                    input.setAttribute('required', 'required');
                } else {
                    input.removeAttribute('required');
                }
            }
        });
    },

    _onBillingCountryChange() {
        // Trigger validation check on ZIP field when country changes
        const zipInput = this.el.querySelector('input[name="billing_zip"]');
        if (zipInput) {
            zipInput.value = zipInput.value.toUpperCase();
            if (this._isBillingCountryUk()) {
                if (zipInput.value && !UK_POSTCODE_REGEX.test(zipInput.value.trim())) {
                    zipInput.setCustomValidity('Please enter a valid UK Postal Code, e.g. SW1A 1AA.');
                } else {
                    zipInput.setCustomValidity('');
                }
            } else {
                zipInput.setCustomValidity('');
            }
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

        // Billing zip (UK Only, if billing is different and country is UK)
        const checkbox = this.el.querySelector('#billing_different');
        if (checkbox && checkbox.checked) {
            const billPostcode = this.el.querySelector('input[name="billing_zip"]');
            const billPostcodeVal = billPostcode ? billPostcode.value.trim().toUpperCase() : '';

            if (this._isBillingCountryUk()) {
                if (billPostcode && billPostcodeVal && !UK_POSTCODE_REGEX.test(billPostcodeVal)) {
                    billPostcode.setCustomValidity('Please enter a valid UK Postal Code, e.g. SW1A 1AA.');
                    billPostcode.reportValidity();
                    ev.preventDefault();
                    return;
                } else if (billPostcode) {
                    billPostcode.setCustomValidity('');
                    billPostcode.value = billPostcodeVal;
                }
            } else if (billPostcode) {
                billPostcode.setCustomValidity('');
                billPostcode.value = billPostcodeVal;
            }
        }
    },
});
