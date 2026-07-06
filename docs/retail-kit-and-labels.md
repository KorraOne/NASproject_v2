# Retail kit, labels, and warranty

What ships in the box and what KorraOne tracks internally.

## In the box (every unit)

| Item | Purpose |
|------|---------|
| FrogsWork appliance | Pre-installed software, factory-burned |
| Power cable | Plug in and leave running |
| **Ethernet cable** | Primary setup — plug into router |
| **WiFi setup USB** | Alternative when no ethernet run is possible |
| Quick-start card | Two paths, device code location, support contact |
| Claim code card | One-time setup code (may be combined with quick-start) |

## Permanent product label (on unit)

| Field | Example |
|-------|---------|
| Product name | FrogsWork File Storage |
| Model | FWS-1 |
| Serial number | FW-2026-00042 |
| Manufacturer | KorraOne |
| Support | support@korraone.com or URL |
| QR code | Quick-start URL, optional `?s=FW-2026-00042` |

Reference the NUC rating plate for electrical specs — do not duplicate incorrectly.

**Do not** print the claim code on the exterior label.

## Claim code card (inside box)

| Field | Example |
|-------|---------|
| Setup code | FW-7K3M-9P2Q |
| Instruction | Enter at frogswork.local when prompted |
| Serial (small) | FW-2026-00042 |

## Unit registry (minimum viable)

Spreadsheet or CSV until volume justifies tooling. **Store claim code plaintext once at factory** — device DB stores hash only.

| Column | When filled |
|--------|-------------|
| `serial` | Factory |
| `claim_code` | Factory |
| `manufactured_date` | Factory |
| `software_version` | Factory |
| `hardware_model` | Factory |
| `qa_pass` | Factory burn-in |
| `shipped_date` | Dispatch |
| `order_id` / customer | Sale |
| `owner_email` | After customer setup |
| `warranty_start` | Ship date or setup date — pick one policy |
| `warranty_end` | Calculated |
| `rma_notes` | If returned |

Factory script appends rows: `scripts/factory/register-unit.sh` (future).

## Warranty one-pager (publish on website + include summary on quick-start card)

**Term:** 24 months from date of purchase (keep receipt) or shipment date for direct sales.

**Covers:** Hardware defect, failure to boot, storage device failure under normal office use.

**Software:** Best-effort fixes via updates; core file storage features included in one-time purchase.

**Excludes:** Physical damage, liquid, unauthorized modifications, data loss (backups reduce risk but are not a guarantee).

**Remedy:** Repair, replace unit, or refund at KorraOne discretion.

**RMA:** Email support with serial + description → RMA number → return instructions → data wipe policy stated upfront.

**Australia:** Consumer guarantees under ACL apply in addition to this warranty.

## Quick-start card (summary text)

1. Plug in power and **ethernet** (recommended), or use the **WiFi setup USB**
2. On a computer on the same network, open **frogswork.local**
3. Enter the **setup code** from the card inside the box
4. Create your owner email and password
5. Download the Windows helper for your team (User Guide in dashboard)

Support: [contact]

## Factory USB imaging checklist

- [ ] Copy `tools/wifi-setup/` files to USB root
- [ ] Verify `WiFi Setup.html` opens offline on Windows
- [ ] Verify `README.txt` lists both setup paths
- [ ] Label USB “FrogsWork WiFi Setup”
- [ ] One USB per box (customer may reuse for diagnostics)

## Related

- [factory-deploy.md](factory-deploy.md) — factory install pipeline
- [onboarding-design.md](onboarding-design.md) — claim code API
- [wifi-usb-provisioning.md](wifi-usb-provisioning.md) — log write-back detail
