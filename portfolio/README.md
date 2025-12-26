# Portfolio Website

Professional portfolio website for Xanadu Media showcasing services, case studies, and expertise.

## Structure

- `index.html` - Homepage with hero, services overview, case studies preview
- `services.html` - Detailed service packages with pricing
- `about.html` - Background and expertise
- `contact.html` - Contact form and outreach
- `pricing-calculator.html` - Interactive project pricing calculator
- `case-studies/` - Individual case study pages
  - `self-hosted-platform.html` - Self-hosted platform integration case study
  - `archivist.html` - Archivist government transcription case study
- `css/` - Stylesheets
  - `main.css` - Main styles
  - `responsive.css` - Responsive design styles
- `js/` - JavaScript files
  - `main.js` - Main JavaScript functionality
  - `pricing-calculator.js` - Pricing calculator logic
- `assets/` - Images, diagrams, screenshots
  - `images/` - Image files
  - `diagrams/` - Architecture diagrams

## Setup

1. Host files on web server or static hosting (Netlify, Vercel, GitHub Pages)
2. Update contact form action (currently placeholder)
3. Add actual images to `assets/images/` directory
4. Customize business name, contact information, and content
5. Configure email integration for contact form

## Deployment

### Static Hosting

**Netlify:**
1. Connect repository to Netlify
2. Set build command: (none, static site)
3. Set publish directory: `/`
4. Deploy

**Vercel:**
1. Import project
2. Configure as static site
3. Deploy

**GitHub Pages:**
1. Enable Pages in repository settings
2. Select source branch
3. Site available at `https://username.github.io/repo-name`

### Platform Integration

The portfolio can integrate with the main platform:

- **API Integration**: Contact form can submit to platform API
- **Service Showcase**: Display services from platform registry
- **Case Studies**: Link to detailed case study pages
- **Analytics**: Integrate with platform monitoring

**Contact Form Integration:**
```javascript
// Submit to platform API
fetch('http://platform-api:8000/api/contact', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData)
});
```

### Docker Deployment

Deploy as static site in Docker:

```dockerfile
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
```

```bash
docker build -t portfolio .
docker run -d -p 8080:80 portfolio
```

## Customization

- Update business name throughout (currently "Xanadu Media")
- Add your logo to `assets/images/`
- Update contact email and phone
- Customize color scheme in `css/main.css` (CSS variables)
- Add actual case study images
- Configure contact form backend

## SEO

- All pages include meta tags
- Semantic HTML structure
- Structured data (JSON-LD) on homepage
- Mobile-responsive design
- Fast loading (optimized CSS/JS)

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile responsive
- Graceful degradation for older browsers

