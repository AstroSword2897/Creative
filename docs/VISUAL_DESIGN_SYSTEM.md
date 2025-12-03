# Las Vegas AthleteCare - Visual Design System

Complete visual identity and design system for the premium Las Vegas Special Olympics simulation.

## Design Philosophy

**Premium Minimalism + Soft Neon Aesthetic**

The simulation should feel like a high-end Vegas experience: calm, luxurious, clean, smooth, and confident. Every visual decision emphasizes clarity first, beauty second.

## Color System

### Primary Palette (Soft Vegas Glow)

| Color | Hex | Usage |
|-------|-----|-------|
| Electric Blue | `#0077FF` | Primary actions, active routes, map highlights |
| Neon Teal | `#00F5D4` | Secured/cleared zones, success states |
| Vegas Gold | `#F4C430` | Athlete highlights, celebration badges |
| Warm Coral | `#FF6F61` | Human elements, warmth, comfort |
| Desert Sand | `#F7E7CE` | Background grounding color |

### Status Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Safe Green | `#2ECC71` | Athlete safe status |
| Caution Yellow | `#F1C40F` | Minor warnings, congestion |
| Alert Red | `#E74C3C` | Medical/critical alerts |

### Neutral Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Jet Black | `#0A0A0A` | Map outlines |
| Charcoal | `#121417` | Main UI background |
| Slate Gray | `#2D2F33` | Panels, cards |
| Soft White | `#FAFAFA` | Text on dark backgrounds |

### Background Gradients

**Day Mode:**
```css
linear-gradient(180deg, #F7F9FC 0%, #F7E7CE 100%)
```

**Night Mode:**
```css
radial-gradient(circle at 10% 10%, #0A0F2B 0%, #111428 30%, #2B1536 100%)
```

## Typography

### Font Families

- **Primary UI:** Inter (variable weights) - body & small labels
- **Accent/Headings:** Montserrat (SemiBold/Bold) - titles & hero numbers

### Type Scale

| Element | Size | Line Height | Font | Weight |
|---------|------|-------------|------|--------|
| Hero | 44px | 56px | Montserrat | 600 |
| H1 | 44px | 56px | Montserrat | 600 |
| H2 | 28px | 36px | Montserrat | 600 |
| H3 | 20px | 28px | Inter | 500 |
| Body | 16px | 24px | Inter | 400 |
| Small/Label | 13px | 18px | Inter | 400 |
| KPI Large | 48px | 1 | Montserrat | 700 |

### Typography Rules

- Use sentence case
- Limit text density on map
- Labels short (≤ 3 words where possible)
- White or near-white text only on dark backgrounds

## Iconography

### Icon Style

- Line + filled combo: circular base, 2px stroke
- Subtle 8% inner shadow
- Rounded corners (border radius 8px for boxes)
- Two-layer icons: outline + colored fill for emphasis

### Agent Icons

- **Athletes:** Gold-highlighted outlines, smooth animations, soft shadows
- **Safety Personnel:** Blue or teal outlines, minimal detail, pulsing safety indicators
- **Vehicles:** Simple silhouettes with glow effects

## UI Components

### Panels

**Glass Panel:**
```css
background: rgba(18, 20, 23, 0.72);
backdrop-filter: blur(12px);
border-radius: 12px;
border: 1px solid rgba(255, 255, 255, 0.1);
box-shadow: 0 8px 24px rgba(5, 10, 20, 0.4);
```

**Elevated Panel:**
```css
background: #2D2F33;
border-radius: 12px;
box-shadow: 0 4px 16px rgba(5, 10, 20, 0.2);
border: 1px solid rgba(255, 255, 255, 0.05);
```

### Buttons

**Primary Button:**
- Background: Electric Blue (`#0077FF`)
- Border radius: 24px
- Font: Montserrat Semibold, 14px
- Hover: Scale 1.03, enhanced shadow

**Secondary Button:**
- Transparent background
- Border: 1px solid Slate Gray
- Hover: Border color changes to Neon Teal

### Cards

**KPI Card:**
- Dark translucent background with blur
- Soft drop shadow
- 12px padding
- Rounded corners

**Incident Card:**
- Red tinted background
- Left border accent (3px)
- Timestamp and type display

## Motion & Animation

### Easing

All animations use: `cubic-bezier(0.2, 0.8, 0.2, 1)`

### Animation Types

**Micro Interactions:**
- Button hover: Scale 1.03, shadow +20% alpha, 160ms
- Icon hover lift: TranslateY(-6px), 180ms

**Agent Movement:**
- Path interpolation: Linear with slight easing at nodes
- Default speed: 60px/sec on map coordinate space
- Pop-in: Fade in 220ms, scale from 0.96 to 1.0

**Alerts & Pulsers:**
- Critical alert pulse: 2 rings, scale 1→2, opacity 0.5→0 over 900ms, loop 2x
- Safety zone glow: Soft blur 18px, subtle pulsate 1.2x over 3s

**Transitions:**
- Camera pan: 900ms - 1500ms depending on distance
- Crossfade: 350ms fade + 150ms blur ramp

## Map Styling

### Layering Order

1. Background gradient
2. Base street map (stylized, low-contrast, opacity 0.85)
3. Building silhouettes (soft white, 90% opacity)
4. Venue and hotel highlight glows (neon teal/gold)
5. Routes (thick lines: shuttle purple 6px; monorail 8px with glow)
6. Agent layers (people above routes)
7. Safety overlays (semi-transparent circles)
8. Icons & labels (icons above agents)
9. Annotation overlays (bubbles, tooltips)
10. UI chrome (rails, panels) - topmost

### Map Style

- Use dark theme for premium look
- Soft gradient backgrounds
- White outlines for buildings
- Gentle shadows for elevation
- Smooth curves instead of sharp corners
- Neon edge glows around important sites

## Agent Colors

| Agent Type | Color | Hex | Effect |
|------------|-------|-----|--------|
| Athlete | Vegas Gold | `#F4C430` | Gold glow with drop shadow |
| Volunteer | Safe Green | `#2ECC71` | Standard |
| Hotel Security | Neon Teal | `#00F5D4` | Teal glow |
| LVMPD | Electric Blue | `#0077FF` | Blue glow |
| AMR | Alert Red | `#E74C3C` | Red glow |
| Bus | Indigo | `#6366F1` | Standard |

## Safe Zone Indicators

**Safe Zone:**
- Background: `rgba(46, 204, 113, 0.15)`
- Border: 2px solid Safe Green
- Box shadow: `0 0 20px rgba(46, 204, 113, 0.3)`

**Caution Zone:**
- Background: `rgba(241, 196, 15, 0.15)`
- Border: 2px solid Caution Yellow

**Restricted Zone:**
- Background: `rgba(231, 76, 60, 0.15)`
- Border: 2px solid Alert Red

## Layout

### Shell Structure

- **Left Control Rail:** 340px width
- **Center Map:** Fluid (flex-1)
- **Right KPI Rail:** 320px width
- **Bottom Timeline:** 110px height (optional)

### Spacing System

- XS: 4px
- SM: 8px
- MD: 16px
- LG: 24px
- XL: 32px
- 2XL: 48px

### Border Radius

- SM: 8px
- MD: 12px
- LG: 24px
- Full: 9999px

## Accessibility

### Color Contrast

- Text contrast ratio: ≥ 4.5:1 against background
- Use white/near-white on dark backgrounds
- High-contrast toggle available

### Motion

- Respect `prefers-reduced-motion`
- Reduce non-essential animations for users who prefer less motion

### Keyboard Navigation

- All interactive controls keyboard-navigable
- Timeline scrubber focusable
- Clear focus indicators

### Screen Readers

- Labels for all buttons
- Dynamic status messages announced
- Semantic HTML structure

## Implementation

All design tokens are available as CSS custom properties in `/frontend/src/styles/design-system.css`.

### Usage Example

```css
.my-component {
  background: var(--color-charcoal);
  color: var(--color-soft-white);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-base);
}
```

## Brand Guidelines

### Logo Concept

- Primary: Wordmark "AthleteCare" (Montserrat SemiBold) + simplified shield + star mark
- Secondary: Shield-only mark (for favicons/small UI)
- Colors: Electric Blue + Vegas Gold accents
- Formats: SVG (vector), PNG (transparent), 2x/3x PNG for retina

### Tone

- Calm
- Confident
- Warm
- Trustworthy
- Luxurious
- Clean

---

**Last Updated:** 2024
**Version:** 1.0

