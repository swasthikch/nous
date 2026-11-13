# Running NOUS 24/7 with Cloudflare Only (Cloudflare Tunnel)

> **"Zero Cloud Hosting Fees. Zero Port Forwarding. 100% Free & Encrypted."**

Yes! You can run NOUS entirely through **Cloudflare** using **Cloudflare Tunnel (`cloudflared`)**.

This allows you to access NOUS on your phone from **anywhere in the world** (on mobile 4G/5G, at work, or traveling) while your laptop stays closed on your desk running the backend and the autonomous minute-to-minute daemon.

---

## 1. Why Cloudflare Tunnel is the Best Free Solution

- **100% Free Forever**: Cloudflare does not charge for tunnels or bandwidth.
- **No Port Forwarding**: You do not need to touch your Wi-Fi router settings or open firewall ports.
- **End-to-End HTTPS / SSL**: Cloudflare automatically provides a valid SSL certificate.
- **Accessible from Mobile Data**: Works on iPhone and Android anywhere in the world, not just on your home Wi-Fi.
- **Runs with Closed Lid**: Paired with [`deploy/windows/set_lid_do_nothing.bat`](file:///e:/nous/deploy/windows/set_lid_do_nothing.bat), your laptop stays plugged in with the lid closed, running 24/7 while using almost zero screen power.

---

## 2. Quickstart: 2-Click Setup

### Step 1: Start NOUS
Double-click **`run_nous.bat`** (or let it start automatically on boot via [`deploy/windows/install_autostart_task.bat`](file:///e:/nous/deploy/windows/install_autostart_task.bat)).

### Step 2: Launch Cloudflare Tunnel
Double-click **[`deploy/cloudflare/start_cloudflare_tunnel.bat`](file:///e:/nous/deploy/cloudflare/start_cloudflare_tunnel.bat)**.
1. The script automatically installs or downloads `cloudflared.exe`.
2. In a few seconds, Cloudflare will print a secure public link in the console:
   ```text
   +--------------------------------------------------------------------------------------------+
   |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
   |  https://random-words-here.trycloudflare.com                                               |
   +--------------------------------------------------------------------------------------------+
   ```
3. **Open that `https://xxxx.trycloudflare.com` link on your phone!**
4. That's it! Your mobile phone now connects directly to your laptop's NOUS engine over Cloudflare's global edge network.

---

## 3. Permanent Domain Setup (Cloudflare Zero Trust)

If you have a free domain on Cloudflare (or want a permanent link like `nous.yourname.com` instead of a random `.trycloudflare.com` URL):

1. Go to [one.dash.cloudflare.com](https://one.dash.cloudflare.com/) (Cloudflare Zero Trust dashboard).
2. Navigate to **Networks** &rarr; **Tunnels** &rarr; **Create a Tunnel**.
3. Choose **Cloudflared**, name it `nous-assistant`, and copy the Windows installation token:
   ```cmd
   cloudflared.exe service install <YOUR_TOKEN>
   ```
4. Set the Public Hostname:
   - **Subdomain**: `nous`
   - **Domain**: `yourdomain.com`
   - **Type**: `HTTP`
   - **URL**: `localhost:8000`
5. Click **Save Hostname**.
6. Now `https://nous.yourdomain.com` will permanently open NOUS on your phone 24/7/365!
