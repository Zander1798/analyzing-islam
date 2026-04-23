# Supabase email templates

Branded HTML for every transactional email Supabase sends on your behalf.
Dark editorial aesthetic, inline styles only, MSO (Outlook desktop) fallbacks
baked into the CTA buttons, hidden preheader for inbox previews.

## Files

| Template                | Supabase slot         | Subject line                                 |
| ----------------------- | --------------------- | -------------------------------------------- |
| `confirm-signup.html`   | Confirm signup        | `Confirm your Analyzing Islam account`       |
| `magic-link.html`       | Magic link            | `Your Analyzing Islam sign-in link`          |
| `invite-user.html`      | Invite user           | `You've been invited to Analyzing Islam`     |
| `change-email.html`     | Change email address  | `Confirm your new Analyzing Islam email`     |
| `reset-password.html`   | Reset password        | `Reset your Analyzing Islam password`        |
| `reauthentication.html` | Reauthentication      | `Analyzing Islam verification code`          |

`_base.html` is the uncommented skeleton, kept for reference when you want
to add a new template or tweak the shared chrome.

## Install (one-time)

1. Open **[Supabase dashboard](https://supabase.com/dashboard/project/_/auth/templates)** → your project → **Authentication → Email Templates**.
2. For each slot above:
   1. Paste the matching template file's body into the **Message (HTML)** editor.
   2. Copy the subject line into the **Subject heading** field.
   3. Click **Save**.
3. Under **Authentication → URL Configuration** confirm:
   - **Site URL:** `https://analyzingislam.com`
   - **Redirect URLs:** include `https://analyzingislam.com/*` (already required for password reset + signup confirmation to redirect back).

## Template variables used

The templates reference Supabase's default Go-template variables:

| Variable              | Where                                                       |
| --------------------- | ----------------------------------------------------------- |
| `{{ .ConfirmationURL }}` | CTA button + fallback link in every flow except reauth   |
| `{{ .Token }}`         | 6-digit OTP shown in `reauthentication.html`               |
| `{{ .Email }}`         | Current email address — footers and body copy              |
| `{{ .NewEmail }}`      | Only in `change-email.html` (the target address)           |

## Testing

Send yourself a test email straight from the Supabase dashboard ("Send test
email" button on each template), and/or trigger the flow from
`site/signup.html`, `site/forgot-password.html`, `site/profile.html`, etc.

Inbox clients render HTML differently — good to sanity-check in:
- Gmail web + Gmail Android
- Apple Mail (macOS + iOS)
- Outlook.com (web)
- Outlook desktop for Windows (hardest target; the MSO conditional in each
  CTA makes the button render via VML rounded-rectangle fallback there).

## Editing

- Keep the outer-table / inner-table scaffold. Email clients ignore most
  modern CSS; tables are the only layout primitive that's bulletproof.
- Keep styles **inline**. `<style>` blocks only work in some clients
  (Gmail web yes, Outlook no).
- Colours live inline as hex; the brand palette used here:
  - `#0a0a0a` background
  - `#0f0f0f` card
  - `#1e1e1e` border
  - `#f5f5f5` text
  - `#d7d7d7` body copy
  - `#9a9a9a` secondary
  - `#5a5a5a` footer
  - `#7aa2f7` accent (CTA fill)
- If you add a new template, duplicate `_base.html` and fill in the four
  placeholder blocks: preheader, category, title, body copy, CTA label.
