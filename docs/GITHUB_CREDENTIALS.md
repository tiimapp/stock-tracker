# GitHub Credentials for Stock Tracker

**⚠️ SECURITY: This file contains sensitive information. Do not commit to Git.**

## Account Info

- **Username:** tiimapp
- **Auth Method:** gh CLI (already authenticated)
- **Token Scopes:** gist, read:org, repo, workflow

## How to Push

The `gh` CLI is already configured and authenticated on this system. Code_G can use:

```bash
cd /home/admin/.openclaw/workspace/stock-tracker

# Initialize if not done
git init
git add .
git commit -m "Initial commit: Stock Tracker v1.0"

# Create and push to GitHub
gh repo create stock-tracker --public --source=. --remote=origin --push
```

Or if repo already exists:
```bash
git remote add origin https://github.com/tiimapp/stock-tracker.git
git push -u origin main
```

## Notes

- Authentication is handled by `gh` CLI (token stored in `~/.config/gh/hosts.yml`)
- No password needed - uses OAuth token
- Token has full repo access

---
**Created:** 2026-03-04  
**For:** Code_G agent
