# Biometric Integration: Fingerprint Bypass

**Status:** ACTIVE
**Vector:** PAM / PolicyKit
**Hardware:** ZBook Native Sensor

## Overview
Acid Burn supports biometric authorization for high-privilege commands. This allows the operator to bypass password prompts using the onboard fingerprint sensor.

## System Configuration (Local)
The following stack must be installed on the host OS:
- `fprintd`
- `libpam-fprintd`

### Activation
The module is integrated into `/etc/pam.d/common-auth` via:
```bash
sudo pam-auth-update --package --enable fprintd
```

### Verification Vector
The most reliable verification vector for this hardware is PolicyKit:
```bash
pkexec <command>
```

---
*Verified by Mark on 2026-05-17*
