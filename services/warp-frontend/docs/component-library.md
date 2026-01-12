# Warp Frontend - Component Library

**Purpose:** Comprehensive component library for Employa's recovery-focused web application.

**Based On:** shadcn/ui (23+ components)
**Design System:** Recovery-focused, elderly-friendly, WCAG AAA compliant

---

## Installed Components (23+)

### Form Components
- `Button` - Primary, secondary, ghost, destructive variants
- `Input` - Text, email, password, number inputs
- `Label` - Accessible form labels
- `Checkbox` - Single and group checkboxes
- `Radio Group` - Radio button groups
- `Select` - Dropdown selects
- `Form` - Form context and validation

### Custom Form Helpers
- `FormField` - Wrapper with label, hint, error state
- `ValidationMessage` - Real-time validation feedback
- `FieldHint` - Proactive guidance for users

### Layout Components
- `Card` - Content containers
- `Separator` - Visual dividers
- `Tabs` - Tab navigation
- `Accordion` - Collapsible content
- `Table` - Data tables

### Feedback Components
- `Alert` - Important messages (info, warning, success)
- `Toast` - Temporary notifications
- `Progress` - Progress indicators
- `Skeleton` - Loading placeholders

### Overlay Components
- `Dialog` - Modal dialogs
- `Sheet` - Slide-in panels
- `Popover` - Floating popovers
- `Tooltip` - Contextual help

### Display Components
- `Badge` - Status labels
- `Avatar` - User avatars

---

## Design Tokens

### Typography (Elderly-Friendly)
```css
--font-size-base: 18px; /* Larger than standard 16px */
--line-height-base: 1.6; /* Comfortable reading */
```

**Font Sizes:**
- `text-sm`: 16px
- `text-base`: 18px (default)
- `text-lg`: 20px
- `text-xl`: 24px
- `text-2xl`: 30px

### Spacing
```css
--spacing-touch: 48px; /* Generous touch targets */
```

**Touch Targets:**
- Minimum: 48×48px
- Button padding: 16px vertical, 24px horizontal
- Element spacing: 8px minimum

### Colors (Calming Palette)
```css
--primary: hsl(221, 83%, 53%); /* Calming blue */
--destructive: hsl(0, 84%, 60%); /* Soft red (not alarming) */
--muted: hsl(210, 40%, 96%); /* Warm gray */
```

**Contrast:** WCAG AAA (7:1 minimum)

### Focus Indicators
```css
--ring-width: 3px; /* Highly visible */
--ring-offset: 2px; /* Clear separation */
```

---

## Usage Examples

### Basic Form Field
```tsx
import { FormField } from "@/src/components/forms/FormField"
import { Input } from "@/src/components/ui/input"

<FormField
  label="Email address"
  hint="We'll never share this"
  required
>
  <Input type="email" placeholder="name@example.com" />
</FormField>
```

### Form with Validation
```tsx
import { FormField } from "@/src/components/forms/FormField"
import { ValidationMessage } from "@/src/components/forms/ValidationMessage"
import { Input } from "@/src/components/ui/input"

<FormField
  label="Password"
  hint="Choose a strong password"
>
  <Input type="password" />
  <ValidationMessage type={hasEightChars ? "success" : "hint"}>
    {hasEightChars ? "✓" : "○"} At least 8 characters
  </ValidationMessage>
  <ValidationMessage type={hasNumber ? "success" : "hint"}>
    {hasNumber ? "✓" : "○"} Include a number
  </ValidationMessage>
</FormField>
```

### Recovery-Focused Error Message
```tsx
import { Alert, AlertTitle, AlertDescription } from "@/src/components/ui/alert"

// ❌ Don't: Alarming
<Alert variant="destructive">
  <AlertTitle>Error!</AlertTitle>
  <AlertDescription>Invalid credentials.</AlertDescription>
</Alert>

// ✅ Do: Supportive
<Alert>
  <AlertTitle>Let's try that again</AlertTitle>
  <AlertDescription>
    Your email or password didn't match. Please check and try again.
  </AlertDescription>
</Alert>
```

### Supportive Button Labels
```tsx
import { Button } from "@/src/components/ui/button"

// ❌ Don't: Demanding
<Button>Submit</Button>

// ✅ Do: Empowering
<Button>Save My Progress</Button>
<Button variant="ghost">I'll finish later</Button>
```

### Progress Celebration
```tsx
import { Progress } from "@/src/components/ui/progress"

// ❌ Don't: Negative framing
<Progress value={30} />
<p>70% incomplete</p>

// ✅ Do: Positive framing
<Progress value={30} />
<p className="text-sm text-muted-foreground">
  Great start! You're 30% complete.
</p>
```

---

## Component Conventions

### Accessibility
All components follow WCAG AAA guidelines:
- ✅ Keyboard navigation (Tab, Enter, Escape)
- ✅ Screen reader support (ARIA labels, roles)
- ✅ Focus indicators (3px ring)
- ✅ High contrast (7:1 ratio)
- ✅ Touch targets (48×48px minimum)

### Motion
All animations respect `prefers-reduced-motion`:
```tsx
// Animations automatically disabled if user prefers reduced motion
<Dialog> {/* smooth fade-in */} </Dialog>
<Accordion> {/* smooth expand/collapse */} </Accordion>
```

### Theming
All components support light/dark mode:
```tsx
// Automatically adapts to user's color scheme preference
<Button>Click me</Button> {/* works in light & dark mode */}
```

---

## Form Validation Patterns

### Required Fields
```tsx
<FormField
  label="Full name"
  required // Shows "(Helps us support you better)" hint
>
  <Input />
</FormField>
```

### Optional Fields
```tsx
<Label>
  LinkedIn profile
  <span className="text-sm text-muted-foreground ml-2">(Optional)</span>
</Label>
```

### Real-Time Validation
```tsx
const [email, setEmail] = useState("")
const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

<FormField
  label="Email"
  error={email && !isValid ? "Please enter a valid email address" : undefined}
>
  <Input
    type="email"
    value={email}
    onChange={(e) => setEmail(e.target.value)}
  />
</FormField>
```

### Password Strength Indicator
```tsx
<FormField label="Password">
  <Input type="password" value={password} onChange={...} />
  <div className="space-y-1 mt-2">
    <ValidationMessage type={password.length >= 8 ? "success" : "hint"}>
      At least 8 characters
    </ValidationMessage>
    <ValidationMessage type={/\d/.test(password) ? "success" : "hint"}>
      Include a number
    </ValidationMessage>
    <ValidationMessage type={/[!@#$%^&*]/.test(password) ? "success" : "hint"}>
      Include a special character
    </ValidationMessage>
  </div>
</FormField>
```

---

## Component Index

### `/src/components/ui/` (shadcn components)
- `button.tsx` - Button component
- `input.tsx` - Input component
- `label.tsx` - Label component
- `checkbox.tsx` - Checkbox component
- `radio-group.tsx` - Radio group component
- `select.tsx` - Select dropdown
- `card.tsx` - Card container
- `dialog.tsx` - Modal dialog
- `sheet.tsx` - Slide-in panel
- `tooltip.tsx` - Tooltip
- `popover.tsx` - Popover
- `form.tsx` - Form context
- `alert.tsx` - Alert message
- `badge.tsx` - Badge label
- `avatar.tsx` - Avatar component
- `table.tsx` - Data table
- `tabs.tsx` - Tab navigation
- `accordion.tsx` - Accordion
- `separator.tsx` - Separator
- `progress.tsx` - Progress bar
- `skeleton.tsx` - Loading skeleton
- `toast.tsx` - Toast notification
- `toaster.tsx` - Toast container

### `/src/components/forms/` (Custom helpers)
- `FormField.tsx` - Form field wrapper with label, hint, error
- `ValidationMessage.tsx` - Validation feedback (hint, success, error)
- `FieldHint.tsx` - Proactive guidance with icon

---

## Design Philosophy

**See [`docs/design-philosophy.md`](./design-philosophy.md) for complete guide.**

**Core Principles:**
1. **Calming Language** - "Let's try again" not "Error!"
2. **Supportive Tone** - "You're making progress" not "Task incomplete"
3. **Non-Judgmental** - "Update your information" not "Fix your profile"
4. **Empowering** - "Choose your path" not "Select an option"

---

## Next Steps

### Phase 1 (Current)
- [x] Install 23+ shadcn components
- [x] Define design tokens (elderly-friendly)
- [x] Create form validation helpers
- [x] Document design philosophy
- [ ] Set up Storybook (optional, deferred)

### Phase 2 (Auth UI)
- [ ] Create login/register forms using components
- [ ] Add form validation with recovery-focused messages
- [ ] Test accessibility with screen readers
- [ ] Validate WCAG AAA compliance

### Phase 3 (Job Search UI)
- [ ] Build job search components
- [ ] Create job card components
- [ ] Add application form components
- [ ] Implement recovery milestone UI

---

## Resources

- **shadcn/ui Docs:** https://ui.shadcn.com/
- **Design Philosophy:** [`docs/design-philosophy.md`](./design-philosophy.md)
- **Tailwind Config:** [`tailwind.config.ts`](../tailwind.config.ts)
- **Global Styles:** [`app/globals.css`](../app/globals.css)
