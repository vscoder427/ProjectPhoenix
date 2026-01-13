# Warp Frontend - Component Library

**Purpose:** Comprehensive component library for Employa's recovery-focused web application.

**Based On:** shadcn/ui (23+ components) + **Framer Motion**
**Design System:** "Level 8" Luminous Design (Depth, Motion, Humanity)
**Compliance:** Recovery-focused, elderly-friendly, WCAG AAA compliant

---

## Core Visual Pillars (New for Phase 2)

### 1. Typography: "Human Tech"
*   **Headings (`font-heading`):** **Plus Jakarta Sans** (Geometric, Modern, Professional)
*   **Body (`font-body`):** **Inter** (Readable, Standard, Functional)

### 2. Depth: "Subtle Luminosity"
*   **No Flat Borders:** Replace 1px gray borders with `ring-1 ring-slate-200` or `ring-inset ring-white/10`.
*   **Glassmorphism:** Use `backdrop-blur-md` and `bg-white/90` for cards and sticky elements.
*   **Shadows:** Colored, diffused shadows (e.g., `shadow-blue-500/5`) instead of harsh black shadows.

### 3. Motion: "Fluid Physics"
*   **Engine:** **Framer Motion** (Spring physics)
*   **Interaction:** All clickable elements must scale on press (`whileTap={{ scale: 0.98 }}`).
*   **Layout:** Lists use `layout` prop to slide elements smoothly during filtering/sorting.

---

## Motion Design Standards (Detailed)

We use **Spring Physics** (not linear easing) to give the interface a natural, organic feel.

### Standard Physics Config
Use this configuration object for all layout transitions and major movements.

```tsx
const springConfig = {
  type: "spring",
  stiffness: 300, // Snap back quickly
  damping: 30,    // No oscillation/wobble
  mass: 1
};
```

---

## Design Tokens (Warp Derived)

### Typography (Elderly-Friendly + Human)
```css
--font-size-base: 18px; /* Larger than standard 16px */
--line-height-base: 1.6; /* Comfortable reading */
```

### Spacing
```css
--spacing-touch: 48px; /* Generous touch targets */
```

### Colors (Luminous Palette)
```css
--background: 210 8% 95%;        /* Light Gray-Blue */
--foreground: 210 29% 35%;       /* Dark Slate Gray */
--primary: 221.2 83.2% 53.3%;    /* Deep Blue (Level 8) */
--accent: 26 80% 52%;            /* Warm Orange (Legacy Warp) */
--destructive: 0 84.2% 60.2%;    /* Soft Red */
```

**Contrast:** WCAG AAA (7:1 minimum)

---

## Component Index
*   `/src/components/ui/` - shadcn components
*   `/src/components/forms/` - Custom supportive helpers

**See [`docs/design-philosophy.md`](./design-philosophy.md) for full usage patterns.**
