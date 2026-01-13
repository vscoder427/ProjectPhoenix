# Frontend Visual Language Specification (Level 8)

**Date:** January 12, 2026
**Status:** Approved / Source of Truth
**Objective:** Transition Project Phoenix from a functional "Admin Panel" look to a premium, "Level 8" SaaS experience that is both technologically sophisticated and recovery-supportive.

---

## 1. Typography: The "Human Tech" Voice

We use a dual-font system to bridge the gap between high-end engineering and human empathy.

*   **Headings (h1, h2, h3, h4):** **Plus Jakarta Sans**
    *   *Style:* Geometric Sans-Serif.
    *   *Rationale:* Provides a modern, "Stripe-like" aesthetic. It feels engineered yet approachable.
*   **Body & UI (Labels, Buttons, Data):** **Inter**
    *   *Style:* Variable Sans-Serif.
    *   *Rationale:* Industry standard for legibility. Keeps the interface focused on utility.
    *   **Constraint:** Base size must be 18px to support elderly users with declining vision.

---

## 2. Depth & Material: "Subtle Luminosity"

We move away from the "Flat UI" era toward a "Luminous" design system that uses light and shadow to define space.

*   **The "No-Border" Policy:** Minimize 1px solid gray borders. Use `ring-1 ring-slate-200` (Light Mode) or `ring-white/10` (Dark Mode) for functional elements.
    *   **Accessibility Guardrail:** Boundries for inputs and buttons must maintain a **3:1 contrast ratio** (WCAG 1.4.11). Faint shadows alone are insufficient for functional definition.
*   **Page Backgrounds:** 
    *   **Light:** Radial gradients (`bg-gradient-to-br from-slate-50 to-white`).
    *   **Dark:** Deep Blue-Black (`hsl(224, 71%, 4%)`) to maintain luminosity, avoiding flat gray.
*   **Cards & Modals:** 
    *   **Shadows:** Soft, large blurs (`shadow-xl` with reduced opacity).
    *   **Glassmorphism:** Use `backdrop-blur-md` and `bg-white/90` (Light) or `bg-slate-950/80` (Dark) for sticky headers and overlays. 
        *   **Accessibility Guardrail:** Maintain a minimum **4.5:1 contrast ratio** for text over glass (WCAG 1.4.3).

---

## 3. Motion & Physics: "Fluid Continuity"

Motion is a core functional element, not an afterthought. It guides the user through the "Journey of Recovery."

*   **Framework:** Framer Motion (Core Dependency).
*   **Physics:** Use "Spring" configurations over "Tween" for a natural, organic feel.
*   **Reduced Motion:** **Mandatory compliance** with `prefers-reduced-motion`. All significant movement (sliding, scaling) must be disabled or replaced with simple fades if the user has motion sensitivities (WCAG 2.3.3).
*   **Key Patterns:**
    *   **Layout Transitions:** Use the `layout` prop for list re-ordering, filtering, and expansion. Elements should "slide" to new positions, never "snap."
    *   **Tactile Feedback:** Every interactive element must have a scale response: `whileTap={{ scale: 0.98 }}`.
    *   **Staggered Entry:** Entrance animations for dashboard widgets should cascade (50ms - 100ms stagger).

---

## 4. Interaction Feedback: "Sophisticated Support"

We celebrate progress through high-end micro-animations paired with supportive, non-clinical language.

*   **Micro-Animations:** Use "SVG Path Drawing" animations for success states (checkmarks, completion icons). Keep them precise and minimal.
*   **Copywriting (The Support Layer):** Pair every success animation with supportive, person-first messaging.
    *   *Example:* Instead of "Saved," use "We've saved your progress. Take your time."
*   **Loading States:** Use "Shimmer" skeletons with a soft pulse speed to reduce "wait-anxiety."

---

## 5. Color Palette (Luminous Standard - Warp Derived)

Derived from the original Warp palette, with the **Primary Blue upgraded to HSL 221** and a specifically tuned **Deep Luminous Dark Mode**.

### Light Mode
| Role | Tailwind Variable | HSL Value | Description |
| :--- | :--- | :--- | :--- |
| **Primary** | `primary` | `221.2 83.2% 53.3%` | **Deep Blue.** Trust and stability. |
| **Accent** | `accent` | `26 80% 52%` | **Warm Orange.** Hope and action. |
| **Background**| `background` | `210 8% 95%` | **Light Gray-Blue.** Clean and spacious. |
| **Foreground**| `foreground` | `210 29% 35%` | **Dark Slate Gray.** High-readability text. |
| **Secondary** | `secondary` | `210 10% 90%` | **Supportive Gray.** Secondary elements. |
| **Destructive**| `destructive`| `0 84.2% 60.2%` | **Soft Red.** Non-alarming warning. |
| **Border** | `border` | `210 10% 88%` | **Muted Divider.** |

### Dark Mode (Luminous)
| Role | Tailwind Variable | HSL Value | Description |
| :--- | :--- | :--- | :--- |
| **Primary** | `primary` | `221.2 83.2% 53.3%` | **Deep Blue.** Consistent branding. |
| **Accent** | `accent` | `26 80% 58%` | **Warm Orange.** Slightly brighter for contrast. |
| **Background**| `background` | `224 71% 4%` | **Deep Blue-Black.** Rich, not gray. |
| **Foreground**| `foreground` | `210 40% 98%` | **Soft White.** Avoids eye strain. |
| **Card** | `card` | `224 71% 10%` | **Midnight Blue.** Subtle separation. |
| **Border** | `border` | `217.2 32.6% 17.5%` | **Dark Divider.** |

### Semantic States
*   **Success:** `142 76% 36%` (Green)
*   **Warning:** `38 92% 50%` (Yellow/Orange)
*   **Info:** `221.2 83.2% 53.3%` (Matches Primary)

---

## 6. Accessibility Guardrails (WCAG 2.1 AA+)

To hit our "Level 8" goal without excluding elderly or low-vision users, the following are non-negotiable:

1.  **Functional Contrast:** Any element a user must interact with (input, button) must be clearly defined with a 3:1 contrast boundary.
2.  **Text Legibility:** All text must meet a 4.5:1 ratio (Body) or 3:1 (Large Headings). On glass surfaces, this is achieved via high-opacity backgrounds (`bg-white/90` or `bg-slate-950/80`).
3.  **Motion Control:** Use the `useReducedMotion` hook from Framer Motion. If `true`, replace spring movement with `duration: 0` or simple opacity fades.
4.  **Touch Targets:** Maintain a minimum **48x48px** area for all interactive elements to support users with limited motor control.

---

## 7. Implementation Checklist for Engineers

- [ ] **Typography:** Are headings using Plus Jakarta Sans? Is body text 18px?
- [ ] **Colors:** Is the Primary color set to HSL 221 and Accent to Warp Orange (26)?
- [ ] **Dark Mode:** Is the background set to Deep Blue-Black (`224 71% 4%`)?
- [ ] **Contrast:** Do inputs/buttons have a visible 3:1 contrast border or background change?
- [ ] **Motion:** Does the component respond to `prefers-reduced-motion`?
- [ ] **Glass:** Is the glass background at least 90% opacity where text is present?
- [ ] **Touch:** Are all buttons/links at least 48px in height/width?
- [ ] **Language:** Does the success message sound supportive or clinical?
