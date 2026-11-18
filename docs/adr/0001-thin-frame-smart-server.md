# 0001: Thin Frame Smart Server

- **Status:** Proposed
- **Date:** 2026-11-18

## Context

- The display is a large colour E-Ink panel (1600×1200, 6 colours) where each uncompressed frame is roughly 1 MB and takes ~19 seconds to refresh.
- Battery life depends on the microcontroller spending almost all of its time in deep sleep, waking only briefly to fetch updates.
- An ESP32-class microcontroller can drive the panel, but typography, layout, colour grading, and high-quality 6-colour dithering are much harder on-device than in Python with Pillow.
- A battery-powered Wi-Fi radio cannot stay awake listening for server pushes without draining the battery in days. The frame must therefore initiate check-ins itself on a schedule.
- The project intends to add new display modes often (planes, terrain, ships, art, and later Jewish screens), and upstream data sources change their formats over time.
- A firmware update is the riskiest change that can be made to a device hanging on someone's wall.


## Decision

Adopt a **thin frame, smart server** architecture.

The frame for the E-Ink poster is deliberately simple. It sleeps, wakes on a schedule to check in with the server, downloads a finished image if there is a new one, draws it, and goes back to sleep. Everything else happens on the server: fetching data, deciding what to show, laying it out, colour-grading, dithering, and scheduling.


## Options considered

1. **Thin frame, smart server (Chosen):** The frame only fetches and displays pre-rendered images. Keeps firmware tiny and stable while unlocking full Python imaging tools on the server.
2. **Smart frame:** The frame fetches raw data and renders everything itself. Works without a server and costs nothing to host, but every new mode or broken upstream API requires a firmware update, and visual quality suffers.
3. **Hybrid:** The server sends structured data and layout instructions, and the frame draws them. Sits awkwardly in the middle with complexity on both sides and still requires firmware updates for new visual components.
4. **Phone does the rendering:** The mobile app renders and pushes images directly. Only works when the phone is nearby, so it is ruled out.


## Consequences

- **Easier:**
  - New modes and visual tweaks are server-only deployments.
  - Full Python tooling (Pillow, NumPy) is available for layout and dithering.
  - Everything can be tested end-to-end against a simulated frame without hardware.
  - Firmware stays small, simple, and rarely needs updating.
- **Harder:**
  - The frame depends entirely on the server and home network being reachable.
  - Ongoing server hosting costs.
  - User settings and device state travel with each request, so privacy and transport security need care.
  - Downloading a ~1 MB image costs Wi-Fi radio time, which directly impacts battery life.
- **Mitigations:**
  - When the server or network is unreachable, the frame keeps displaying the last image at zero power draw.
  - The server controls sleep duration in its response (e.g. sleeping longer overnight) so wake schedules can be tuned without touching firmware.
  - Rendering a subtle "last updated" timestamp onto the image makes stale screens obvious rather than silently misleading.
  - Waveshare's guidance is at least 180s between refreshes and at least one refresh a day. If the server controls sleep, a server bug could send "sleep 5s" and wear the panel, or "sleep 30 days" and leave it showing a stale image. Firmware should clamp whatever the server sends to between about 3 minutes and 24 hours.


## Biggest Risk Accepted

- **Permanent operational dependency and silent fleet failure:** Because the frame has no local fallback logic or rendering engine, a broken server, expired domain/TLS certificate, or unrecoverable network bug leaves every deployed device stuck showing a stale image. If hosting stops years from now, the hardware cannot function independently.


## How We Will Know This Decision Was Wrong

We will revisit this architecture if any of the following happen in practice:
- **Battery drain exceeds budget:** Wi-Fi wake-ups and image transfers dominate power draw, reducing cord-free runtime to weeks rather than months.
- **High missed-refresh rate on real home networks:** Weak Wi-Fi or transient server downtime causes frequent failed updates, particularly for time-sensitive modes.
- **Protocol churn forces firmware updates anyway:** New modes repeatedly require hardware-level behaviour that cannot be expressed as a pre-rendered image.
- **Server cost or complexity scales poorly:** Per-device rendering and bandwidth costs outgrow the maintenance cost of moving basic layout logic onto the frame.



## Future Considerations

- **Offline / Jewish Edition:** Supporting standalone operation without a server (such as on-device calendar/time calculations) will require revisiting this boundary in a future ADR that partially supersedes 0001.
- **Downstream ADRs:** Python renderer on Lambda (`0002`, #2), AWS vs Cloudflare (`0003`, #3), cloud region (`0004`, #4), wire protocol and image format (`0005`, #10), hardware and power selection (`0006`), firmware stack and OTA strategy (`0007`).

