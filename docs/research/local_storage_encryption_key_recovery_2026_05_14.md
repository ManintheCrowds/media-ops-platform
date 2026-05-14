# Local storage encryption and key recovery research project

**Research date:** 2026-05-14  
**Prompt:** What local storage encryption and key recovery pattern fits local-first users without turning support into a decryption bypass?  
**Status:** Research recommendation; not yet implementation policy.

## Compressed take

For local-first apps that store sensitive data, the safest default is **user-held encryption with explicit recovery paths**, not support-held bypass keys. Use a locally generated data encryption key (DEK), wrap it for each approved recovery method, and make recovery loss honest: if the user chooses no recovery method and loses all devices/keys, support cannot decrypt the data.

Recommended baseline:

1. Generate a random per-vault or per-family **DEK** locally.
2. Encrypt local data with an authenticated encryption mode such as AES-GCM; OWASP recommends AES with at least 128-bit keys and preferably 256-bit keys for symmetric encryption ([OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet)).
3. Store only encrypted data and wrapped DEKs outside volatile memory.
4. Offer at least two user-controlled recovery methods:
   - Printable/exportable recovery key or emergency kit.
   - Trusted recovery contact or trusted device flow.
5. Optional: for teams, add organization recovery by wrapping the DEK to an organization public key, similar to enterprise vault recovery patterns where admins can help recover encrypted data without knowing the old master password ([Bitwarden account recovery](https://bitwarden.com/help/account-recovery)).

## Research findings

### 1. Recovery is part of authenticator/key lifecycle, not a support shortcut

NIST recommends that subscribers maintain at least two authentication methods to reduce account-recovery needs, and it treats binding/recovery of authenticators as a managed lifecycle event with records of binding, updates, and expiration ([NIST SP 800-63B authenticator event management](https://pages.nist.gov/800-63-4/sp800-63b/events/)). NIST implementation guidance says recovery commonly requires either an existing authenticator or re-proofing identity so attackers cannot claim loss and bind a new authenticator ([NIST lifecycle management](https://pages.nist.gov/800-63-3-Implementation-Resources/63B/Lifecycle/)).

**Implication:** Account recovery and data decryption recovery must be designed separately. Re-authenticating a user can let them sign in; it should not magically grant plaintext access unless a DEK was intentionally recoverable by that method.

### 2. Reset tokens are not decryption recovery

OWASP's forgot-password guidance recommends consistent responses to prevent user enumeration, rate limiting, cryptographically random single-use reset tokens, expiration, password confirmation, and session invalidation after reset ([OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet)). OWASP also warns that security questions are weak and notes that NIST no longer recognizes security questions as an acceptable authentication factor ([OWASP Choosing and Using Security Questions Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Choosing_and_Using_Security_Questions_Cheat_Sheet)).

**Implication:** Password reset can restore account access, but it should not unwrap encrypted local-first data unless the app has a separate, deliberate DEK recovery mechanism. Avoid security questions.

### 3. User-held recovery keys are common in zero-knowledge products

Apple Advanced Data Protection requires users to set up at least one recovery method before enabling end-to-end encryption, and Apple says it does not have the encryption keys needed to decrypt protected data ([Apple Advanced Data Protection](https://www.apple.com/legal/privacy/data/en/advanced-data-protection/), [Apple ADP setup](https://support.apple.com/ht212520)). Apple recovery keys are 28-character codes, and Apple warns users that losing account access without a trusted device or recovery key can permanently lock them out ([Apple recovery key](https://support.apple.com/en-qa/109345)). Apple recovery contacts help users regain access without getting access to the account contents ([Apple recovery contact](https://support.apple.com/en-lamr/102641)).

1Password uses a Secret Key that is generated on the device and not known to 1Password; the Secret Key works with the account password to protect account data, and 1Password says it cannot recover a lost Secret Key ([1Password Secret Key security](https://support.1password.com/secret-key-security)). 1Password's Emergency Kit stores sign-in information, the Secret Key, a setup QR code, and space for the account password so users can store recovery material offline ([1Password Emergency Kit](https://support.1password.com/emergency-kit/)).

Signal Secure Backups are protected by a 64-character recovery key generated on the user's device, and Signal says no one can restore the backup without it ([Signal Secure Backups support](https://support.signal.org/hc/en-us/articles/9708267671322-Signal-Secure-Backups), [Signal Secure Backups blog](https://signal.org/blog/introducing-secure-backups)). Signal PINs recover profile/settings/contacts but do not recover message history, which keeps recovery scope explicit ([Signal PIN support](https://support.signal.org/hc/en-us/articles/360007059792-Signal-PIN)).

**Implication:** The honest product pattern is: make the recovery artifact concrete, printable/exportable, and scoped. Tell users exactly what it can and cannot recover.

### 4. Enterprise/team recovery can preserve zero-knowledge boundaries if the DEK is wrapped intentionally

Bitwarden's enterprise account recovery stores an account recovery key by encrypting the user's encryption key with the organization's public key; recovery decrypts the user's encryption key with the organization's private key, and the admin does not learn the old master password ([Bitwarden account recovery](https://bitwarden.com/help/account-recovery)). Bitwarden emergency access lets users designate trusted contacts with view or takeover permissions after an invitation/acceptance/confirmation flow ([Bitwarden emergency access](https://bitwarden.com/help/emergency-access)). Bitwarden also states that, without configured recovery options, zero-knowledge encryption means forgotten master passwords cannot be recovered by Bitwarden ([Bitwarden forgot master password](https://bitwarden.com/help/forgot-master-password/)).

**Implication:** For org/team products, recovery should be opt-in, auditable, and based on wrapped keys, not helpdesk plaintext access.

### 5. Browser/local encryption has viable primitives, but local storage remains a hard boundary

The Web Crypto API exposes cryptographic operations through `crypto.subtle` and is available only in secure contexts ([MDN Web Crypto API](https://developer.mozilla.org/docs/Web/API/Web_Crypto_API)). Browser examples commonly derive AES-GCM keys from passphrases with PBKDF2, random salts, and random IVs for encryption ([MDN derive key example](https://mdn.github.io/dom-examples/web-crypto/derive-key/index.html), [Brady Joslin Web Crypto encryption](https://bradyjoslin.com/posts/webcrypto-encryption/)). OWASP warns against storing sensitive information in client-side storage such as localStorage, sessionStorage, and IndexedDB unless it is protected appropriately ([OWASP Web Security Testing Guide: browser storage](https://owasp.org/www-project-web-security-testing-guide/v41/4-Web_Application_Security_Testing/11-Client_Side_Testing/12-Testing_Browser_Storage)).

**Implication:** Local-first browser apps can encrypt IndexedDB/local files, but any XSS or malicious extension risk can still access decrypted data while the app is unlocked. Encryption at rest is necessary, not sufficient.

### 6. Passkeys/WebAuthn PRF are promising but risky as sole recovery

The WebAuthn PRF extension can produce deterministic high-entropy outputs associated with a credential and relying party, enabling passkey-backed encryption/decryption flows ([W3C WebAuthn PRF explainer](https://github.com/w3c/webauthn/blob/main/explainers/prf-extension.md)). Bitwarden describes PRF as useful for passkey-based decryption because the same credential and salts can derive stable encryption material ([Bitwarden PRF WebAuthn](https://bitwarden.com/blog/prf-webauthn-and-its-role-in-passkeys)). However, practical WebAuthn encryption writeups warn that if a passkey is deleted or recreated, data encrypted only with that PRF-derived key is unrecoverable ([Encrypting Data in the Browser Using WebAuthn](https://blog.millerti.me/2023/01/22/encrypting-data-in-the-browser-using-webauthn/)).

**Implication:** Passkeys can be a convenient unlock/wrap method, but should not be the only recovery route for important data unless permanent loss is acceptable.

## Candidate patterns

| Pattern | How it works | Pros | Failure mode | Best fit |
|---|---|---|---|---|
| Password-derived key only | Derive key from password/passphrase via KDF; encrypt data directly or wrap DEK. | Simple, portable. | Weak passwords are brute-forceable; forgotten password loses data unless another wrap exists. | Low-stakes local tools. |
| Random DEK + recovery key | Generate random DEK; encrypt data with DEK; export/print recovery key that can unwrap DEK. | Strong security; clear user ownership. | Lost recovery key and lost devices means data loss. | Default for individual/local-first apps. |
| Random DEK + trusted devices | Wrap DEK to keys held by each trusted device. | Smooth multi-device UX. | Losing all trusted devices loses access unless recovery key exists. | Multi-device apps. |
| Random DEK + recovery contact | Trusted contact can provide a recovery code/share but cannot read data directly. | Human-friendly fallback. | Social engineering and contact availability risks. | Consumer/family apps. |
| Random DEK + org public key wrap | DEK also wrapped to org recovery public key; recovery is audited. | Enables enterprise recovery without support knowing password. | Org admin/private-key compromise can recover users. | Teams/regulated environments. |
| Passkey/WebAuthn PRF wrap | Passkey authenticator derives/wraps key material. | Convenient biometric/passkey unlock. | Deleted/recreated passkey can permanently lose data if sole wrap. | Unlock convenience, not sole recovery. |
| Shamir split recovery | Split recovery secret across a threshold of shares/contacts/devices using a scheme where a chosen minimum number of shares can reconstruct the secret ([Charm-Crypto secret sharing](https://jhuisi.github.io/charm/toolbox/secretshare.html)). | No single contact can recover alone. | More UX complexity; share loss can block recovery. | High-value family/team vaults. |

## Recommended pattern for our local-first pilots

Use **random DEK + multiple explicit wraps**:

```text
local data
  encrypted with random DEK using authenticated encryption

DEK wraps
  1. user passphrase-derived wrapping key
  2. printable/exportable recovery key
  3. per-device public key or platform keychain wrap
  4. optional trusted contact or org public key wrap
```

Implementation constraints:

- Use authenticated encryption and fresh nonces/IVs per encryption operation.
- Keep support out of the decryption path.
- Make recovery setup part of onboarding before sensitive data accumulates.
- Make "no recovery configured" a visible state.
- Log and notify recovery-method changes.
- Require current authentication or a high-assurance re-proofing flow before adding recovery methods.
- Separate account login recovery from data decryption recovery.
- Never use security questions.

## Product UX requirements

- **Recovery status card:** shows whether recovery key, trusted device, trusted contact, and org recovery are configured.
- **Recovery drill:** lets users verify a recovery key without rotating it.
- **Emergency kit export:** printable PDF/text package with recovery key, app URL, account ID, and warnings.
- **Rotation path:** rotate DEK wraps without re-encrypting all content; rotate DEK only when compromise is suspected.
- **Loss language:** "We cannot decrypt your data if you lose every recovery method" must be explicit.
- **Support script:** support can help users find recovery options, not bypass encryption.

## Open implementation questions

- Which local-first pilot needs browser storage, native filesystem storage, or both?
- Should `home-cyber-risk` encrypt the existing SQLite DB with SQLCipher, application-layer field encryption, or encrypted export bundles?
- For Pi devices, should encryption bind to device hardware/OS credentials, a per-device certificate, or an operator-provided recovery key?
- Should per-user agent memory use the same DEK/wrap model as product data, or a simpler local OS keychain model?

## Backlog candidates

| ID | Type | Candidate | Acceptance | Routed to |
|---|---|---|---|---|
| KR1 | DOCS | Draft local-first encryption/key recovery policy | Policy separates account recovery from data recovery, bans support bypasses, and defines DEK/wrap/recovery language. | deferred |
| KR2 | CODE/RESEARCH | Prototype encrypted local SQLite or IndexedDB store | Prototype encrypts sample records, exports a recovery key, and demonstrates loss/recovery behavior. | deferred |
| KR3 | SECURITY | Threat-model Pi and home-cyber-risk local stores | Threat model covers lost device, stolen DB, forgotten recovery key, support impersonation, XSS/malicious extension, and remote wipe. | deferred |

## Sources

- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet)
- [OWASP Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet)
- [OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet)
- [OWASP Choosing and Using Security Questions Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Choosing_and_Using_Security_Questions_Cheat_Sheet)
- [NIST SP 800-63B Authenticator Event Management](https://pages.nist.gov/800-63-4/sp800-63b/events/)
- [NIST 800-63B Lifecycle Management](https://pages.nist.gov/800-63-3-Implementation-Resources/63B/Lifecycle/)
- [Apple Advanced Data Protection](https://www.apple.com/legal/privacy/data/en/advanced-data-protection/)
- [Apple recovery key](https://support.apple.com/en-qa/109345)
- [Apple recovery contact](https://support.apple.com/en-lamr/102641)
- [Bitwarden account recovery](https://bitwarden.com/help/account-recovery)
- [Bitwarden emergency access](https://bitwarden.com/help/emergency-access)
- [Bitwarden forgot master password](https://bitwarden.com/help/forgot-master-password/)
- [1Password Secret Key security](https://support.1password.com/secret-key-security)
- [1Password Emergency Kit](https://support.1password.com/emergency-kit/)
- [Signal Secure Backups support](https://support.signal.org/hc/en-us/articles/9708267671322-Signal-Secure-Backups)
- [Signal Secure Backups blog](https://signal.org/blog/introducing-secure-backups)
- [Signal PIN support](https://support.signal.org/hc/en-us/articles/360007059792-Signal-PIN)
- [MDN Web Crypto API](https://developer.mozilla.org/docs/Web/API/Web_Crypto_API)
- [MDN derive key example](https://mdn.github.io/dom-examples/web-crypto/derive-key/index.html)
- [W3C WebAuthn PRF explainer](https://github.com/w3c/webauthn/blob/main/explainers/prf-extension.md)
- [Bitwarden PRF WebAuthn](https://bitwarden.com/blog/prf-webauthn-and-its-role-in-passkeys)
- [Charm-Crypto secret sharing](https://jhuisi.github.io/charm/toolbox/secretshare.html)
