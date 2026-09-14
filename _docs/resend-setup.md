# Configure Resend for sign-in codes

Family Kanban sends passwordless sign-in codes with [Resend](https://resend.com).
The same path runs in local development and production: the code is saved in
`login_codes`, then emailed. The API never returns the code to the UI.

Required environment variables (repo-root [`.env`](../.env), see [`.env.example`](../.env.example)):

| Variable | Purpose |
| --- | --- |
| `RESEND_API_KEY` | API key from the Resend dashboard |
| `EMAIL_FROM` | From address, e.g. `Family Kanban <onboarding@resend.dev>` |

If either is missing, `POST /api/v1/auth/code` fails with a clear error **after**
the code is already stored in the database. The app still starts without these
variables.

---

## 1. Create a Resend account

1. Go to [https://resend.com](https://resend.com) and sign up.
2. Open the dashboard after email verification.

Free tier (as of writing): about **100 emails/day** and **3,000/month** — enough
for family OTP traffic.

---

## 2. Create an API key

1. In the Resend dashboard, open **API Keys**.
2. Click **Create API Key**, give it a name (e.g. `family-kanban-dev`), and create it.
3. Copy the key once (it starts with `re_`).
4. Put it in the repo-root `.env`:

```env
RESEND_API_KEY=re_xxxxxxxx
```

Never commit real keys. Keep them only in `.env` (gitignored) or your host’s secrets.

---

## 3. Local / early testing (no custom domain yet)

Until you verify your own domain, Resend provides a test sender:

```env
EMAIL_FROM=Family Kanban <onboarding@resend.dev>
```

**Limits with `resend.dev`:**

- You can only send to the **email address on your Resend account**.
- Sending to anyone else returns an error until you verify a domain.

That is enough to smoke-test sign-in against your own inbox.

Restart the backend (or `make dev`) after editing `.env` so settings reload.

---

## 4. Production: verify your domain

To email arbitrary family members:

1. In Resend, open **Domains** → **Add Domain**.
2. Enter your domain (e.g. `example.com`).
3. Add the DNS records Resend shows (typically SPF, DKIM, and related records) at your DNS provider.
4. Wait until the domain status is **Verified** in the Resend UI.
5. Update `.env` (or production secrets) to use an address on that domain:

```env
EMAIL_FROM=Family Kanban <noreply@example.com>
```

The local part (`noreply`, `auth`, etc.) can be anything you like on a verified domain; it does not need a real mailbox unless you also configure receiving.

Official guides: [Resend domains](https://resend.com/docs/dashboard/domains/introduction) and provider-specific DNS help in their docs.

---

## 5. Smoke-test sign-in

1. Ensure `RESEND_API_KEY` and `EMAIL_FROM` are set.
2. Start the stack (`make dev` or backend + frontend).
3. Open `/auth`, enter an allowed recipient email, click **Send my code**.
4. Confirm the email arrives with a 6-digit code.
5. Enter the code and sign in.

The UI must not show the code; only the email (or the DB recovery steps below) has it.

---

## 6. Troubleshooting

### “Email is not configured. Set RESEND_API_KEY and EMAIL_FROM.”

One or both variables are empty. Fix `.env`, restart the backend, retry.

### Send failed / 403 from Resend (`resend.dev`)

You tried to send to an address that is not your Resend account email. Either:

- Send only to your account email for local testing, or
- Verify a domain and change `EMAIL_FROM` to that domain.

### Domain not verified / wrong `from`

`EMAIL_FROM` must use a domain that is verified in Resend. Typo’d domains fail.

### Local recovery when email fails

The code is still in `login_codes` after a failed send. With the default SQLite URL:

```sh
cd backend
sqlite3 family_kanban.db "SELECT email, code, expires_at FROM login_codes;"
```

Use that code on the `/auth` form to finish sign-in, then fix Resend config so the next request emails correctly.

For Postgres, query the same `login_codes` table with your usual SQL client.
