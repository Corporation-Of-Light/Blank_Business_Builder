# Better Business Builder - Website Repository Setup Guide

## Quick Setup (5 minutes)

### Step 1: Create GitHub Repository

```bash
# Go to https://github.com/new and create a new repository
# Repository name: bbb-website
# Description: Better Business Builder - AI-Powered Business Planning Platform
# Public repository
# Initialize with README (optional, we'll provide one)
```

### Step 2: Clone Repository

```bash
git clone https://github.com/yourusername/bbb-website.git
cd bbb-website
```

### Step 3: Add Website Files

Copy all files from this directory to your cloned repository:
- index.html
- README.md
- .gitignore
- assets/
  - css/
  - js/
  - images/

### Step 4: Push to GitHub

```bash
git add .
git commit -m "Initial commit: BBB website with client portal"
git push origin main
```

### Step 5: Enable GitHub Pages

1. Go to repository Settings
2. Scroll to "Pages" section
3. Set "Source" to "Deploy from a branch"
4. Set branch to "main"
5. Set folder to "/ (root)"
6. Save

Your website will be live at: `https://yourusername.github.io/bbb-website`

Or set up custom subdomain:

```bash
# For bbb.aios.is subdomain:
# 1. Go to namecheap.com (where aios.is is hosted)
# 2. Add CNAME record: bbb → yourusername.github.io
# 3. In GitHub repository Settings → Pages
# 4. Under "Custom domain" enter: bbb.aios.is
# 5. Click "Save"
```

---

## Repository Structure

```
bbb-website/
├── index.html              # Main landing page
├── README.md              # Project documentation
├── .gitignore             # Git ignore patterns
├── assets/
│   ├── css/
│   │   └── styles.css    # Additional styles (optional)
│   ├── js/
│   │   └── main.js       # Additional scripts (optional)
│   └── images/
│       ├── logo.svg
│       ├── hero-graphic.svg
│       ├── features/
│       └── testimonials/
└── docs/
    ├── SECURITY.md        # Security report
    ├── PERFORMANCE.md     # Performance metrics
    └── DEPLOYMENT.md      # Deployment guide
```

---

## File Checklist

- [ ] index.html (main website)
- [ ] README.md (project description)
- [ ] .gitignore (exclude node_modules, .env, etc.)
- [ ] CNAME file (for custom subdomain - optional)
- [ ] License file (MIT or Proprietary)

---

## Custom Domain Setup (bbb.aios.is)

### NameCheap Configuration

1. Log in to NameCheap
2. Go to aios.is domain management
3. Go to "Advanced DNS"
4. Add new CNAME record:
   ```
   Type: CNAME Record
   Host: bbb
   Value: yourusername.github.io
   TTL: Automatic
   ```
5. Wait 5-30 minutes for DNS propagation

### GitHub Configuration

1. Go to repository Settings
2. Click "Pages"
3. Under "Custom domain" enter: `bbb.aios.is`
4. Check "Enforce HTTPS"
5. Click Save

GitHub will auto-generate a CNAME file in your repository.

---

## Continuous Updates

### Updating Website Content

```bash
# Make changes to index.html
nano index.html

# Commit and push
git add index.html
git commit -m "Update feature descriptions"
git push origin main

# Changes live in 30-60 seconds
```

### Adding Blog Posts or Pages

```bash
# Create new directory
mkdir blog

# Create blog post
cat > blog/first-post.html << 'EOF'
<!-- Blog post HTML -->
EOF

# Add and push
git add blog/
git commit -m "Add blog post: Getting Started with BBB"
git push origin main
```

---

## Analytics & Monitoring

### Add Google Analytics

```html
<!-- Add to <head> section of index.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### Add Hotjar for User Analytics

```html
<!-- Add to <body> before closing tag -->
<script>
    (function(h,o,t,j,a,r){
        h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};
        h._hjSettings={hjid:YOUR_HJID,hjsv:6};
        a=o.getElementsByTagName('head')[0];
        r=o.createElement('script');r.async=1;
        r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
        a.appendChild(r);
    })(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
</script>
```

---

## SEO Optimization

### Meta Tags Already Included

- ✅ Title tag
- ✅ Meta description
- ✅ Meta keywords
- ✅ Viewport meta tag
- ✅ Open Graph tags (optional)

### Sitemap & Robots.txt

```xml
<!-- robots.txt -->
User-agent: *
Allow: /
Sitemap: https://bbb.aios.is/sitemap.xml
```

### Submit to Search Engines

1. Google Search Console: https://search.google.com/search-console
2. Bing Webmaster Tools: https://www.bing.com/webmasters
3. Submit sitemap.xml

---

## Maintenance

### Weekly
- Check GitHub Pages deployment status
- Monitor form submissions
- Review analytics

### Monthly
- Update pricing if changed
- Refresh testimonials
- Check all links are working

### Quarterly
- Full security audit
- Performance review
- SEO check

---

## Support & Resources

- **GitHub Pages Docs**: https://pages.github.com
- **Custom Domain Setup**: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site
- **Markdown Guide**: https://www.markdownguide.org

---

## License

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light).
All Rights Reserved. PATENT PENDING.
