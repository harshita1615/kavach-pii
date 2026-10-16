# Chrome Web Store submission: copy-paste answers

Everything the developer dashboard asks for, in the order it asks. Upload
`kavach-extension-<version>.zip` (from `npm run package`).

## Store listing tab

**Name** (from the package): Kavach: Indian PII shield for AI chats

**Summary** (from the package, 132 characters max):
Warns before you send Aadhaar, PAN, UPI, bank or phone details to ChatGPT, Claude or Gemini, and masks them. Runs on your device.

**Description:**

```
Kavach (कवच, "shield") stops your personal details from slipping into AI chats by accident.

When you paste or send a message on ChatGPT, Claude or Gemini, Kavach checks it for Indian personal data. If it finds any, it pauses and shows you what kind, for example "This message contains 1 PAN and 1 phone number", with three choices:

• Mask: replace them with placeholders like [PAN_1] and [PHONE_1], so the AI never sees the real values. You review the message before sending.
• Send anyway: send it as it is.
• Cancel: go back and edit.

WHAT IT DETECTS
• Aadhaar numbers (checked with the official Verhoeff check digit)
• PAN
• UPI IDs (name@okaxis, number@paytm and more)
• IFSC codes
• Bank account numbers (when words like "account", "a/c" or "khata" are nearby)
• Indian mobile numbers (+91, 0 or 10-digit)
• GSTIN (with its check character)
• Email addresses
It understands English, Hinglish and Hindi context: "mera aadhaar", "khata number", "मोबाइल".

PRIVATE BY DESIGN
• Runs entirely on your device. Kavach makes no network requests at all.
• Your messages are never stored, logged or sent anywhere.
• It only works on chatgpt.com, claude.ai and gemini.google.com, nowhere else.
• It stores only on/off settings and counts like "PAN: 3", which you can reset.
• Open source (MIT): https://github.com/harshita1615/kavach-pii

GOOD TO KNOW
• Interface in English and Hindi.
• You can turn Kavach off for any site from its toolbar popup.
• Kavach reduces risk but can miss things. Please check before you send. It is not legal advice and does not by itself make anyone compliant with any law.

Kavach is not affiliated with OpenAI, Anthropic or Google.
```

**Category:** Make Chrome Yours → Privacy & Security
**Language:** English (Hindi is included through `_locales/hi`)

**Graphic assets:**
- Store icon 128×128: `extension/icons/icon128.png`
- Screenshots (1 to 5, 1280×800 or 640×400, PNG or JPEG). Use made-up data only:
  1. The paste banner on ChatGPT ("The pasted text contains 1 PAN, 1 UPI ID and 1 phone number")
  2. The message box after Mask, showing [PAN_1] [UPI_1] [PHONE_1] and the Kavach note
  3. The send banner on Claude or Gemini
  4. The popup with site switches and counts
  5. (optional) The banner in Hindi
- Small promo tile 440×280: optional

**Official URL:** none
**Homepage URL:** https://kavach-pii.vercel.app/
**Support URL:** https://github.com/harshita1615/kavach-pii/issues

## Privacy practices tab

**Single purpose:**
```
Kavach warns users before they send Indian personal data (Aadhaar, PAN, UPI ID, IFSC, bank account, phone number, GSTIN, email) in AI chatbot message boxes, and lets them replace it with placeholders.
```

**Permission justification: storage**
```
Saves the user's on/off choice for each supported site and the number of items caught per type (for example "PAN: 3"), shown in the popup. Only these flags and counts are stored, locally on the device. No message text or personal data is stored.
```

**Permission justification: host permissions (content script on chatgpt.com, claude.ai, gemini.google.com)**
```
The extension must read the text in the message box on these three AI chat sites at the moment the user pastes or sends, to check it for personal data and offer to mask it before it is submitted. It runs on no other sites. All processing happens locally; nothing is transmitted.
```

**Are you using remote code?** No, I am not using remote code.

**Data usage: what user data do you plan to collect?** Tick **none** of the boxes.
Kavach reads message text only locally to check it, and nothing leaves the device, so
nothing is "collected" in the sense the form means (transmitted off the device).

**Certifications:** tick all three:
- I do not sell or transfer user data to third parties, outside of the approved use cases
- I do not use or transfer user data for purposes that are unrelated to my item's single purpose
- I do not use or transfer user data to determine creditworthiness or for lending purposes

**Privacy policy URL:**
```
https://kavach-pii.vercel.app/privacy/
```
(Also served by GitHub Pages at https://harshita1615.github.io/kavach-pii/privacy/; both come
from `docs/`.)

## Distribution tab

- Visibility: **Public** (or **Unlisted** for a soft launch: only people with the link can install)
- Regions: **All regions**
- Pricing: free

## Before submitting

1. Check the privacy URL above opens. The website (`docs/`) deploys to Vercel on every push to `main`.
2. `cd extension && npm test && npm run package`, then upload the new zip.
3. Re-read the description against the current code: every claim must be true.
