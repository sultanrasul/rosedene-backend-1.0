# 🏡 Direct Booking Platform (Backend)

Developed end-to-end by **Sultan Rasul** as part of a **full-stack direct booking system** for property managers.  
This backend powers the platform’s **booking, pricing, payment, and property management features**, integrating **FastAPI**, **Supabase**, **Stripe**, and **Rentals United** for automated workflows and real-time synchronization.

🔗 **Frontend Repository:** [Direct Booking Platform (Svelte Frontend)](https://github.com/sultanrasul/rosedene-svelte-1.0)

---

## 🧠 Overview

This backend handles:
- Property availability and pricing logic  
- Stripe checkout and payment intents  
- Rentals United API integration for live bookings  
- Automated email confirmations via Brevo  
- Secure data storage and updates via Supabase  

The project is part of a full-stack application, with the **frontend** built using **Svelte** and deployed separately.

---

## 🏠 Property & Rentals United Setup

The property IDs in this project match those in our **Rentals United dashboard**, which is also linked to the pricing data.  
If you have your own Rentals United account, you’ll need to:

1. Find your **property IDs** in your Rentals United dashboard.  
2. Edit the variable in `services/integrations/rentals_united_service.py` to match your property IDs.  

> ⚠️ Without valid `.env` credentials, some integrations (bookings, pricing sync, etc.) will not function — but the API will still start for demo or code review purposes.

---

## 💰 Price Data Generation

Price data for all properties is stored in `data/property_prices.json`.  
This file is **generated automatically** by running the `updatePrices.py` script located in  
`services/integrations/rentals_united/`.

```bash
# Generate or refresh property price data
python services/integrations/rentals_united/updatePrices.py
```
Instead of fetching individual prices for every API request, this script retrieves all pricing data at once and outputs it to property_prices.json.
Later versions will support automatic updates via Rentals United webhooks.

---

## ⚙️ Setup Instructions

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the environment
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

# 3. Install dependencies
pip install -r requirements.txt
```

🚀 Run the Server
`fastapi dev main.py --port 8080`


Once running, open your browser and go to:

👉 http://localhost:8080/docs

Here you can view and test all endpoints interactively using FastAPI’s built-in documentation interface.
