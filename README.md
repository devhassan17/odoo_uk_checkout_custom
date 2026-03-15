# UK Checkout Customisations for Odoo 18/19

## What this module does
- Replaces the single checkout **Name** field with **First Name** and **Last Name**
- Keeps Odoo's standard `name` field synced in the background
- Adds stored contact fields:
  - `x_first_name`
  - `x_last_name`
  - `x_marketing_opt_in`
- Removes **Company Name**, **VAT**, and **State / Province** from the checkout UI
- Changes **Zip Code** label to **Postcode**
- Adds browser-side UK postcode validation
- Adds light browser-side UK mobile validation
- Adds an email marketing opt-in checkbox at checkout and stores the choice on the contact

## What this module does NOT do
- Restrict shipping country to United Kingdom only
  - Do this in **Inventory -> Configuration -> Delivery Methods**
- Convert checkout to one page / one step
  - Prefer a prebuilt app for that and test separately

## Compatibility
Built to be conservative for **Odoo 18 Enterprise** and likely usable on **Odoo 19**, but major-version compatibility is never guaranteed for website checkout templates.

## Install on Odoo.sh
1. Put the module in your custom addons repo.
2. Commit and push the branch.
3. Update Apps List.
4. Search for **UK Checkout Customisations**.
5. Install.
6. Test on `/shop/address`.

## Notes
- This module uses frontend validation for phone/postcode to keep risk low.
- If you want server-side postcode/phone enforcement, add controller-side validation next.
- If your checkout template has been heavily customized already, the XPath selectors may need small adjustments.
