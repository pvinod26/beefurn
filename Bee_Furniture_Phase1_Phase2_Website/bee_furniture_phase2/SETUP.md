# Bee Furniture — Phase 1 + Phase 2 starter

This project preserves the supplied Phase 1 one-page website and adds a room-visualisation workflow with a Flask backend. The original 40-product catalogue, search, filters, sorting, Picks/cart, comparison and WhatsApp enquiry logic remain in `index.html`.

## Run locally

1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Create and activate a virtual environment (optional but recommended).
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env` and add your API key:

   ```env
   OPENAI_API_KEY=your_real_api_key
   OPENAI_IMAGE_MODEL=gpt-image-1
   ```

6. Start the website and backend:

   ```bash
   python app.py
   ```

7. Open `http://127.0.0.1:5000`.

The AI image-edit endpoint uses an OpenAI API key and incurs API usage charges. It is intentionally not enabled until a valid key is configured. Never put the API key in browser JavaScript or commit `.env` to Git.

## Product colour variants — important

The Phase 1 source contained colour preference swatches, not verified photographs of each sofa in every colour. It did not include a set of same-model colour photographs. Therefore this upgrade does **not** falsely claim that the old swatches are actual available variants and does not recolour images with CSS.

To activate true image-switching variants:

1. Obtain one real photo for each colour of the same sofa model from Bee Furniture.
2. Put the files in `assets/` (or use stable hosted HTTPS URLs).
3. In `index.html`, find `VERIFIED_VARIANT_IMAGES` and add entries keyed by the existing product ID and exact colour name, e.g.:

   ```js
   const VERIFIED_VARIANT_IMAGES = {
     1: {
       Ivory: 'assets/cloud-ivory.jpg',
       Charcoal: 'assets/cloud-charcoal.jpg',
       Taupe: 'assets/cloud-taupe.jpg'
     }
   };
   ```

4. Use only images of the same model, with only the upholstery colour changing. Until then, Phase 1 swatches remain customer colour requests and the website says that availability must be confirmed.

`variant-data.example.json` shows the intended variant data structure. The same selected colour is passed to the room visualiser and WhatsApp enquiry.

## WhatsApp image sharing

The website first uses the device's Web Share API to share the generated image file. If the browser does not support file sharing, it downloads the image and opens a prefilled WhatsApp chat; the customer must attach the downloaded image manually. A normal `wa.me` link cannot silently attach a local image. The existing Phase 1 WhatsApp number remains in the source at `CLIENT_WHATSAPP_NUMBER` and should be verified with the business before launch.

## Deployment

Deploy the Flask app to a Python-capable host (Render is one option). Set `OPENAI_API_KEY` and `OPENAI_IMAGE_MODEL` as environment variables in the host dashboard. For production, use persistent/object storage for generated images, add rate limiting and authentication/abuse protection, and restrict product image URLs to a client-approved host allowlist. The sample app stores generated previews in `static/generated`, which is suitable for local testing but not durable storage on ephemeral hosting.

## Required client assets before a production launch

- Actual same-model sofa photographs for every real fabric colour variant.
- Confirmation of available colours, prices, dimensions and stock.
- Confirmation that the existing WhatsApp number is the correct Bee Furniture enquiry number.
- OpenAI API key and approval for image-processing costs/privacy handling.

## Accuracy note

The AI feature creates an illustrative edited room image, not dimensionally accurate AR. Exact real-world scale and placement require measured 3D models and an AR-capable implementation. AI previews can alter details, so customers should confirm fabric and dimensions with Bee Furniture.
