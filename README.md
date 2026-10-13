# Digital vCard & Contact Card

Digital contact repository for **Akib Javed, PhD** (Hydrology & Geoinformatics Specialist at C4RE International).

This repository is optimized for business card QR codes to keep the QR version low (fast, high-readability scanning at small physical print dimensions).

---

## Files Included

1. [`contact.vcf`](./contact.vcf) — The RFC-compliant vCard 3.0 file containing full contact information.
2. [`index.html`](./index.html) — A lightweight, mobile-first digital business card with a 1-tap **"Save to Contacts"** button, direct WhatsApp/Call links, CV & Resume PDF downloads, social profiles, and office address.
3. [`Akib_Javed_CV.pdf`](./Akib_Javed_CV.pdf) — Curriculum Vitae (PDF), downloaded by the **CV** button.
4. [`Akib_Javed_Resume.pdf`](./Akib_Javed_Resume.pdf) — Résumé (PDF), downloaded by the **Resume** button.

---

## How to Deploy to GitHub

1. Repository: [https://github.com/Geoakib/contact](https://github.com/Geoakib/contact)
2. Push `contact.vcf` and `index.html` to the repository.
3. In GitHub, go to **Settings** &rarr; **Pages**:
   - Under **Build and deployment** &rarr; **Source**, select **Deploy from a branch**.
   - Select `main` branch and `/ (root)`.
   - Click **Save**.
4. Your digital card will be live at:
   ```
   https://geoakib.github.io/contact/
   ```
   And your direct `.vcf` download link will be:
   ```
   https://geoakib.github.io/contact/contact.vcf
   ```

---

## QR Code Recommendations for Visiting Card

### 1. Which URL to put in your Visiting Card QR Code?
Choose one of the following based on your preferred scan experience:

| Experience | URL to Encode in QR Code | Behavior when Scanned |
| :--- | :--- | :--- |
| **Option A (Recommended)** | `https://geoakib.github.io/contact/` | Opens a sleek mobile card with 1-tap "Save to Contacts", direct WhatsApp, Call, and research links. |
| **Option B (Instant Prompt)** | `https://geoakib.github.io/contact/?vcard` | Immediately triggers the phone's "Add to Contacts" download prompt while also showing the profile card. |
| **Option C (Direct File)** | `https://geoakib.github.io/contact/contact.vcf` | Direct download of the vCard file. |

> [!CAUTION]
> **Do NOT use `https://raw.githubusercontent.com/...` in your QR code.**  
> GitHub Raw serves files with `Content-Type: text/plain`. If scanned, mobile browsers (Safari/Chrome) will display raw code on screen instead of opening the "Add to Contacts" address book dialog. Always use GitHub Pages (`https://geoakib.github.io/contact/`).

### 2. QR Code Print Specs
- **URL Length:** ~30–38 characters.
- **QR Matrix Version:** **Version 2 (25×25)** or **Version 3 (29×29)** (very low density, wide modules).
- **Error Correction:** Level **M (15%)** or **Q (25%)**.
- **Print Size:** Reads easily even at **15 mm – 24 mm** on paper card stock.
