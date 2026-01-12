# Employa Design Philosophy - Recovery-Focused UI

**Purpose:** Design principles for creating supportive, calming, trauma-informed user interfaces for job seekers in recovery and recovery-friendly employers.

**Last Updated:** 2026-01-12

---

## Core Principles

### 1. Calming Language

**Use supportive, non-alarming language.**

| ❌ Don't Say | ✅ Do Say | Why |
|--------------|-----------|-----|
| "Error!" | "Let's try again" | Reduces anxiety |
| "Failed" | "We couldn't complete that" | Non-judgmental |
| "Invalid input" | "Please check your information" | Gentle guidance |
| "Warning!" | "Heads up:" | Less alarming |
| "Fix this" | "Update this" | Empowering |

**Example:**
```tsx
// ❌ Bad: Alarming
<Alert variant="destructive">
  <AlertTitle>Error!</AlertTitle>
  <AlertDescription>Invalid email address.</AlertDescription>
</Alert>

// ✅ Good: Supportive
<Alert variant="info">
  <AlertTitle>Let's check that</AlertTitle>
  <AlertDescription>
    Your email address should look like: name@example.com
  </AlertDescription>
</Alert>
```

---

### 2. Supportive Tone

**Acknowledge progress, not just completion.**

| ❌ Don't Say | ✅ Do Say | Why |
|--------------|-----------|-----|
| "Task incomplete" | "You're making progress" | Encouraging |
| "Missing information" | "A few more details will help" | Positive framing |
| "0% complete" | "Let's get started" | Inviting |
| "Failed to save" | "We'll try saving again" | Reassuring |

**Example:**
```tsx
// ❌ Bad: Negative framing
<Progress value={30} />
<p>70% incomplete</p>

// ✅ Good: Positive framing
<Progress value={30} />
<p>Great start! 30% complete</p>
```

---

### 3. Non-Judgmental Feedback

**Avoid blame, suggest action.**

| ❌ Don't Say | ✅ Do Say | Why |
|--------------|-----------|-----|
| "You forgot to..." | "Let's add..." | No blame |
| "Wrong password" | "Password doesn't match" | Neutral |
| "You must..." | "You can..." | Empowering choice |
| "Fix your profile" | "Update your profile" | Respectful |

**Example:**
```tsx
// ❌ Bad: Blaming
<FormError>You didn't complete the required fields.</FormError>

// ✅ Good: Neutral
<FormHint>A few more fields will complete your profile.</FormHint>
```

---

### 4. Empowering Choices

**Give users control and ownership.**

| ❌ Don't Say | ✅ Do Say | Why |
|--------------|-----------|-----|
| "Select an option" | "Choose what works for you" | Personal agency |
| "Required field" | "This helps us support you" | Explains why |
| "Agree to terms" | "Review and accept" | Informed consent |
| "Submit" | "Continue" or "Save my progress" | Less final |

**Example:**
```tsx
// ❌ Bad: Demanding
<Button>Submit Now</Button>

// ✅ Good: Empowering
<Button>Save My Progress</Button>
<Button variant="ghost">I'll finish later</Button>
```

---

## Accessibility for Elderly Users

### Typography
- **Base font size:** 18px (larger than standard 16px)
- **Line height:** 1.6 (comfortable reading)
- **Font family:** System fonts (familiar, no custom fonts)
- **Contrast ratio:** WCAG AAA (7:1 minimum)

### Touch Targets
- **Minimum size:** 48×48px (generous for touch)
- **Spacing:** 8px between interactive elements
- **Button padding:** 16px vertical, 24px horizontal

### Focus Indicators
- **Ring width:** 3px (highly visible)
- **Ring color:** Primary color (contrasts with background)
- **Ring offset:** 2px (clear separation)

### Motion & Animation
- **Respect `prefers-reduced-motion`:** Disable animations if requested
- **Subtle transitions:** 200ms duration (not jarring)
- **No auto-playing videos:** User-initiated only

---

## Color Palette (Recovery-Focused)

### Primary: Calming Blue
```css
--primary: 221.2 83.2% 53.3%; /* hsl(221, 83%, 53%) */
```
**Why:** Blue evokes calm, trust, stability. Associated with healing.

### Destructive: Soft Red (Not Alarming)
```css
--destructive: 0 84.2% 60.2%; /* hsl(0, 84%, 60%) */
```
**Why:** Softer than typical error red. Indicates issue without alarm.

### Muted: Warm Gray
```css
--muted: 210 40% 96.1%; /* hsl(210, 40%, 96%) */
```
**Why:** Gentle, non-intrusive background. Reduces visual noise.

---

## Component Patterns

### 1. Error Messages

**Show what to do, not just what went wrong.**

```tsx
// ❌ Bad: Just states the problem
<FormError>Password must be 8 characters</FormError>

// ✅ Good: Explains what to do
<FormError>
  <span className="font-semibold">Let's make your password stronger</span>
  <ul className="mt-2 space-y-1 text-sm">
    <li>✓ At least 8 characters</li>
    <li>✗ Include a number</li>
    <li>✗ Include a special character</li>
  </ul>
</FormError>
```

### 2. Loading States

**Acknowledge the wait, set expectations.**

```tsx
// ❌ Bad: Generic spinner
<Spinner />

// ✅ Good: Informative
<div className="space-y-2">
  <Spinner />
  <p className="text-sm text-muted-foreground">
    Finding jobs that match your skills...
  </p>
  <p className="text-xs text-muted-foreground">
    This usually takes 3-5 seconds
  </p>
</div>
```

### 3. Empty States

**Invite action, don't highlight absence.**

```tsx
// ❌ Bad: Negative framing
<EmptyState>No jobs found. Try different keywords.</EmptyState>

// ✅ Good: Inviting
<EmptyState>
  <h3>Let's find your next opportunity</h3>
  <p>Try searching for:</p>
  <ul>
    <li>Job titles (e.g., "Customer Service")</li>
    <li>Skills (e.g., "Excel, communication")</li>
    <li>Companies (e.g., "recovery-friendly employers")</li>
  </ul>
  <Button>Explore Popular Jobs</Button>
</EmptyState>
```

### 4. Success Messages

**Celebrate progress, reinforce positive behavior.**

```tsx
// ❌ Bad: Minimal feedback
<Toast>Saved</Toast>

// ✅ Good: Encouraging
<Toast>
  <ToastTitle>Great work!</ToastTitle>
  <ToastDescription>
    Your profile is looking stronger. Employers can now see your skills.
  </ToastDescription>
</Toast>
```

---

## Form Design Patterns

### Field Labels
```tsx
// Clear, descriptive labels
<Label htmlFor="email">
  Email address
  <span className="text-sm text-muted-foreground"> (We'll never share this)</span>
</Label>
```

### Field Hints
```tsx
// Proactive guidance
<FieldHint>
  Use an email you check regularly. We'll send job matches here.
</FieldHint>
```

### Required vs Optional
```tsx
// Explain why, not just mark required
<Label>
  Phone number
  <Badge variant="secondary" className="ml-2">Helps employers reach you</Badge>
</Label>

// Optional fields: Explicitly state
<Label>
  LinkedIn profile
  <span className="text-sm text-muted-foreground"> (Optional)</span>
</Label>
```

### Validation Feedback
```tsx
// Real-time, supportive validation
<FormField>
  <Input type="password" />
  <ValidationMessage type="hint">
    {password.length >= 8 ? "✓ " : "○ "} At least 8 characters
  </ValidationMessage>
  <ValidationMessage type="hint">
    {hasNumber ? "✓ " : "○ "} Include a number
  </ValidationMessage>
</FormField>
```

---

## Writing Style Guide

### Voice
- **Conversational:** "Let's get started" not "Complete registration"
- **First-person plural:** "We'll" not "The system will"
- **Active voice:** "Choose your path" not "A path must be selected"

### Tone
- **Encouraging:** "You're making progress"
- **Patient:** "Take your time"
- **Respectful:** "Your privacy matters"
- **Empowering:** "You decide what to share"

### Word Choice
- **Recovery-positive:** "in recovery" not "recovering addict"
- **Person-first:** "person in recovery" not "addict"
- **Strength-based:** "your skills" not "job history gaps"
- **Action-oriented:** "Update" not "Fix", "Choose" not "Select"

---

## Anti-Patterns to Avoid

### ❌ Don't
1. **Use red/alarm language** - "ERROR!", "WARNING!", "CRITICAL"
2. **Blame the user** - "You forgot", "You failed", "You must"
3. **Use jargon** - "Authenticate", "Submit", "Validate"
4. **Assume context** - "Click here" (where? why?)
5. **Rush the user** - "Hurry!", "Limited time!", "Act now!"
6. **Judge progress** - "Only 10% complete", "You're behind"

### ✅ Do
1. **Use calm language** - "Let's try again", "Please check"
2. **Be neutral** - "Let's add", "We can", "Please update"
3. **Use plain language** - "Sign in", "Save", "Check"
4. **Give context** - "Save your progress to continue later"
5. **Respect pace** - "Take your time", "No rush"
6. **Acknowledge effort** - "Great progress", "You're on track"

---

## Implementation Checklist

When creating a new component or page:

- [ ] **Language**: No alarming words ("error", "failed", "wrong")
- [ ] **Tone**: Supportive, not judgmental
- [ ] **Typography**: 18px base font, 1.6 line height
- [ ] **Touch targets**: Minimum 48×48px
- [ ] **Focus indicators**: 3px ring, visible contrast
- [ ] **Color contrast**: WCAG AAA (7:1 ratio)
- [ ] **Motion**: Respects `prefers-reduced-motion`
- [ ] **Empty states**: Inviting, not highlighting absence
- [ ] **Errors**: Explain what to do, not just what's wrong
- [ ] **Success**: Celebrate progress

---

## Resources

- **WCAG Guidelines:** https://www.w3.org/WAI/WCAG21/quickref/
- **Trauma-Informed Design:** https://traumainformeddesign.org/
- **Plain Language:** https://www.plainlanguage.gov/
- **Inclusive Components:** https://inclusive-components.design/

---

## Examples Repository

See `src/components/examples/` for reference implementations:
- `RecoveryFocusedForm.tsx` - Form with supportive validation
- `CalmErrorAlert.tsx` - Non-alarming error messages
- `ProgressCelebration.tsx` - Encouraging progress indicators
- `EmpoweringButton.tsx` - Action-oriented button labels
