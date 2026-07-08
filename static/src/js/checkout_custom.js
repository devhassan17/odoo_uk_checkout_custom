/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

const UK_POSTCODE_REGEX = /^[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}$/i;

publicWidget.registry.UkCheckoutCustom = publicWidget.Widget.extend({
    selector: '.oe_website_sale',

    events: {
        'input #first_name': '_syncFullName',
        'input #last_name': '_syncFullName',
        'input input[name="zip"]': '_onPostcodeInput',
        'change #use_different_shipping': '_onToggleShipping',
        'change #use_same, input[name="use_same"], input[name="use_delivery_as_billing"]': '_onToggleBillingInline',
        'submit form': '_onSubmit',
    },

    start() {
        this._syncFullName();
        this._fixZipLabels();
        this._onToggleShipping();
        this._initInlineBilling();
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

    _initInlineBilling() {
        const switchInput = this.el.querySelector('#use_same, input[name="use_same"], input[name="use_delivery_as_billing"]');
        if (!switchInput) return;

        // Create inline container if not exists
        let inlineContainer = this.el.querySelector('#uk_inline_billing_form');
        if (!inlineContainer) {
            inlineContainer = document.createElement('div');
            inlineContainer.id = 'uk_inline_billing_form';
            inlineContainer.className = 'd-none mt-3 p-4 border rounded bg-light';
            
            const switchContainer = switchInput.closest('.form-check, .form-switch, div');
            if (switchContainer) {
                switchContainer.parentNode.insertBefore(inlineContainer, switchContainer.nextSibling);
            }
        }

        this._onToggleBillingInline();
    },

    _onToggleBillingInline() {
        const switchInput = this.el.querySelector('#use_same, input[name="use_same"], input[name="use_delivery_as_billing"]');
        const inlineContainer = this.el.querySelector('#uk_inline_billing_form');
        if (!switchInput || !inlineContainer) return;

        // use_same = checked means Billing is same as Shipping.
        // So we show the billing fields when it is UNCHECKED.
        const showBillingFields = !switchInput.checked;
        
        // Find sibling elements like address cards list and "+ Add Address" button, and toggle their visibility
        const switchContainer = switchInput.closest('.form-check, .form-switch, div');
        if (switchContainer) {
            let nextSib = switchContainer.nextSibling;
            while (nextSib) {
                if (nextSib.nodeType === 1 && nextSib.id !== 'uk_inline_billing_form') {
                    if (showBillingFields) {
                        nextSib.classList.add('d-none');
                    } else {
                        nextSib.classList.remove('d-none');
                    }
                }
                nextSib = nextSib.nextSibling;
            }
        }

        if (showBillingFields) {
            inlineContainer.classList.remove('d-none');
            // Load fields if empty
            if (inlineContainer.innerHTML === '') {
                inlineContainer.innerHTML = '<div class="text-center py-3"><span class="spinner-border spinner-border-sm text-primary me-2"></span>Loading address fields...</div>';
                fetch('/shop/address?address_type=billing')
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const billingForm = doc.querySelector('form[action*="/shop/address"]');
                        if (billingForm) {
                            // Strip out submit button / footer / navigation
                            const footer = billingForm.querySelector('.d-flex, .justify-content-between, button[type="submit"], a.btn');
                            if (footer) footer.style.display = 'none';
                            const title = billingForm.querySelector('h1, h2, h3, h4');
                            if (title) title.style.display = 'none';
                            
                            // Remove CSRF and hidden fields that we don't need to duplicate
                            const csrf = billingForm.querySelector('input[name="csrf_token"]');
                            if (csrf) csrf.remove();

                            inlineContainer.innerHTML = '<h5 class="mb-3 text-secondary border-bottom pb-2">Billing Address</h5>';
                            inlineContainer.appendChild(billingForm);
                            
                            // Re-apply zip label fix in the dynamically loaded form
                            this._fixZipLabels();
                        } else {
                            inlineContainer.innerHTML = '<div class="alert alert-warning">Please click "+ Add Address" to fill your billing address.</div>';
                        }
                    })
                    .catch(() => {
                        inlineContainer.innerHTML = '<div class="alert alert-danger">Failed to load billing fields. Please refresh.</div>';
                    });
            }
        } else {
            inlineContainer.classList.add('d-none');
        }
    },

    _onSubmit(ev) {
        const form = ev.currentTarget;
        
        // If we are submitting the main address edit form, run standard validations
        if (form.action && form.action.includes('/shop/address')) {
            // Check if this is the inline form submission we triggered via AJAX
            if (form.dataset.ajaxSubmitting === 'true') {
                return;
            }

            this._syncFullName();

            const postcode = form.querySelector('input[name="zip"]');
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

            const useDifferentShipping = form.querySelector('#use_different_shipping')?.checked;
            if (useDifferentShipping) {
                const shippingZip = form.querySelector('#shipping_zip');
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
        }

        // If we are submitting the checkout/payment confirmation form, and billing form is visible and not saved yet
        const switchInput = this.el.querySelector('#use_same, input[name="use_same"], input[name="use_delivery_as_billing"]');
        const inlineContainer = this.el.querySelector('#uk_inline_billing_form');
        if (switchInput && !switchInput.checked && inlineContainer && !inlineContainer.classList.contains('d-none')) {
            const billingFormElement = inlineContainer.querySelector('form');
            if (billingFormElement) {
                // If it is our inline form submission, let it run
                if (form === billingFormElement) return;

                // Otherwise, it is the main checkout confirmation form submit. Intercept it!
                ev.preventDefault();
                ev.stopPropagation();

                // Validate the billing form fields first
                if (!billingFormElement.reportValidity()) return;

                // Validate billing postcode format
                const postcode = billingFormElement.querySelector('input[name="zip"]');
                const postcodeVal = postcode ? postcode.value.trim().toUpperCase() : '';
                if (postcode && postcodeVal && !UK_POSTCODE_REGEX.test(postcodeVal)) {
                    postcode.setCustomValidity('Please enter a valid UK Postal Code, e.g. SW1A 1AA.');
                    postcode.reportValidity();
                    return;
                }

                // Submit the billing form via AJAX first
                const formData = new FormData(billingFormElement);
                // Odoo requires the CSRF token, let's grab it from the main page
                const mainCsrf = this.el.querySelector('input[name="csrf_token"]')?.value;
                if (mainCsrf) {
                    formData.append('csrf_token', mainCsrf);
                }

                const submitBtn = form.querySelector('button[type="submit"], .btn-primary');
                let originalBtnHTML = '';
                if (submitBtn) {
                    originalBtnHTML = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving addresses...';
                }

                // Mark form as submitting via AJAX to prevent recursive interception
                billingFormElement.dataset.ajaxSubmitting = 'true';

                fetch('/shop/address/submit', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.ok) {
                        // Resubmit the main form now that the billing address is saved!
                        switchInput.checked = true; // Temporary set checked to bypass this interceptor
                        form.submit();
                    } else {
                        throw new Error('Failed to save address');
                    }
                })
                .catch(() => {
                    alert('Error saving billing address. Please verify your fields.');
                    billingFormElement.dataset.ajaxSubmitting = 'false';
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalBtnHTML || 'Confirm';
                    }
                });
            }
        }
    },
});
