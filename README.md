# Digital vCard & Contact Card

Digital contact repository for **Akib Javed, PhD** (Hydrology & Geoinformatics Specialist at C4RE International).

This repository is optimized for business card QR codes to keep the QR version low (fast, high-readability scanning at small physical print dimensions).

---

## Files Included

1. [`contact.vcf`](./contact.vcf) — The RFC-compliant vCard 3.0 file containing full contact information, including an embedded `PHOTO`.
2. [`index.html`](./index.html) — A lightweight, mobile-first digital business card with a 1-tap **"Save to Contacts"** button, direct WhatsApp/Call links, CV & Resume PDF downloads, social profiles, and office address.
3. [`Akib_Javed_CV.pdf`](./Akib_Javed_CV.pdf) — Curriculum Vitae (PDF), downloaded by the **CV** button.
4. [`Akib_Javed_Resume.pdf`](./Akib_Javed_Resume.pdf) — Résumé (PDF), downloaded by the **Resume** button.
5. [`icon.png`](./icon.png) — 256×256 portrait, used as the page avatar and as the favicon / apple-touch-icon.
6. [`og-image.jpg`](./og-image.jpg) — 1200×630 link-preview thumbnail for WhatsApp, Telegram, LinkedIn and X.
7. [`tools/make_assets.py`](./tools/make_assets.py) — Regenerates `icon.png`, `og-image.jpg` and the vCard `PHOTO` (see below).

---

## How to Deploy to GitHub

1. Repository: [https://github.com/Geoakib/contact](https://github.com/Geoakib/contact)
2. Push `contact.vcf`, `index.html`, `icon.png`, `og-image.jpg` and the PDFs to the repository.
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

> [!NOTE]
> The page is served from the repository, so a file that is not committed is not published.
> `icon.png` and `og-image.jpg` **must be committed**, or the avatar and the link preview break.
> The large source photos stay untracked on purpose — they are working files, not site assets.

---

## Short URL (recommended for print)

`https://geoakib.github.io/` currently returns GitHub's 404. Creating a **user-site** repository
fixes that and gives printed cards a shorter, more durable URL.

1. Create a new repository named exactly **`Geoakib/geoakib.github.io`** — the name must match
   `username.github.io`, which is what makes GitHub serve it at the bare root.
2. Enable Pages on it (**Settings &rarr; Pages &rarr; Deploy from a branch &rarr; `main` / `(root)`**).
3. Add this `index.html` as its only file:

```html
<!doctype html><html lang="en"><head>
<meta charset="utf-8">
<title>Akib Javed, PhD | Digital Contact Card</title>
<link rel="canonical" href="https://geoakib.github.io/contact/">
<meta http-equiv="refresh" content="0; url=https://geoakib.github.io/contact/">
<meta property="og:title" content="Akib Javed, PhD | Digital Contact Card">
<meta property="og:image" content="https://geoakib.github.io/contact/og-image.jpg">
<script>location.replace("https://geoakib.github.io/contact/");</script>
</head><body>
<p>Redirecting to <a href="https://geoakib.github.io/contact/">the contact card</a>.</p>
</body></html>
```

The card's `canonical` and `og:url` deliberately stay on the full `/contact/` address: the short
root URL is an alias, and canonical should name where the content actually lives.

**What this does and does not fix.** It removes the bare-root 404 and shortens the printed URL.
The card still shows `github.io`, and renaming the `contact` repository would still break printed
cards. Only a custom domain removes both: buy one, add a file named `CNAME` containing just the
domain, then point four DNS records at GitHub Pages and tick **Enforce HTTPS**. Existing
`geoakib.github.io/...` links keep working after that.

---

## QR Code Recommendations for Visiting Card

### 1. Which URL to put in your Visiting Card QR Code?
Once the short-URL repository above exists, encode the short form — it survives a rename of this
repository and makes a lower-density QR.

| Experience | URL to Encode in QR Code | Behavior when Scanned |
| :--- | :--- | :--- |
| **Option A (Recommended)** | `https://geoakib.github.io/` | Redirects to the card, then 1-tap "Save to Contacts", WhatsApp, Call, research links. |
| **Option B (Instant Prompt)** | `https://geoakib.github.io/contact/?vcard` | Immediately triggers the phone's "Add to Contacts" download prompt while also showing the profile card. |
| **Option C (Direct File)** | `https://geoakib.github.io/contact/contact.vcf` | Direct download of the vCard file. |

> [!CAUTION]
> **Do NOT use `https://raw.githubusercontent.com/...` in your QR code.**  
> GitHub Raw serves files with `Content-Type: text/plain`. If scanned, mobile browsers (Safari/Chrome) will display raw code on screen instead of opening the "Add to Contacts" address book dialog. Always use GitHub Pages (`https://geoakib.github.io/`).

### 2. QR Code Print Specs
- **URL Length:** ~25 characters for the short form, ~38 for the full path.
- **QR Matrix Version:** **Version 2 (25×25)** or **Version 3 (29×29)** (very low density, wide modules).
- **Error Correction:** Level **M (15%)** or **Q (25%)**.
- **Print Size:** Reads easily even at **15 mm – 24 mm** on paper card stock.

### 3. Link previews
`og-image.jpg` is what messaging apps show for this link. Those platforms cache the **first**
scrape of a URL, so after changing the preview image, force a refresh with the LinkedIn Post
Inspector or the Facebook Sharing Debugger, otherwise old shares keep the old thumbnail.

---

## Updating the card

**Contact details live in two places.** There is no shared data source: a phone number, email or
URL has to be changed in **both** `index.html` and `contact.vcf`, or the page and the saved
contact will disagree.

**Regenerating the images** (after replacing the photo, or changing a name or job title):

```bash
python tools/make_assets.py          # rewrites icon.png, og-image.jpg and the vCard PHOTO
python tools/make_assets.py --check  # verifies the committed files, writes nothing
```

The script reads `Akib_Javed_Photo_Square.png` (960×960, transparent background) from the
repository root — that source photo is deliberately **not** committed, so keep it alongside your
local clone. Run `--check` before committing: it fails if the framing overflows, the vCard
photo is truncated or the wrong size, or the files drift past the size limits that contact
importers and link crawlers tolerate.
