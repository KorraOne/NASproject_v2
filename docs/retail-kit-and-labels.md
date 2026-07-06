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

Spreadsheet or CSV on your laptop. Copy [`unit-registry.template.csv`](factory/unit-registry.template.csv) to `unit-registry.csv` (gitignored — contains setup codes).

Generate credentials: `python scripts/factory/generate-unit-credentials.py`

| Column | When filled |
|--------|-------------|
| `serial` | Build |
| `claim_code` | Build (plaintext **laptop only**) |
| `manufactured_date` | Build |
| `software_version` | Build |
| `hardware_model` | Build |
| `qa_pass` | After smoke tests |
| `shipped_date` | Dispatch |
| `owner_email` | After customer setup (optional note) |
| `notes` | Anytime |

Device also appends a row via `scripts/factory/register-unit.sh` during `factory-install.sh`.

## Consumer rights (card / website summary)

**Australian Consumer Law applies.** If the hardware is faulty, contact support — we will repair, replace, or refund as appropriate under the ACL. See [warranty-rma.md](../warranty-rma.md). Do not promise a fixed “24-month warranty” beyond ACL rights.

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
