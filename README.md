# tw-swe-thermometer
Taiwan software engineer salary transparency platform.

## GitHub Pages deployment

1. Push this repo to GitHub.
2. In the repository settings, set `Pages -> Build and deployment -> Source` to `GitHub Actions`.
3. In `Pages`, set the custom domain to `data-navigator.net`.
4. In your DNS provider, point `data-navigator.net` to GitHub Pages with `A`/`AAAA` records, and point `www.data-navigator.net` with a `CNAME` to `<your-account>.github.io`.
5. Push to `main`; the workflow at `.github/workflows/pages.yml` will build and publish `site/` automatically.

Local build:

```bash
bash scripts/build_static_site.sh
```
