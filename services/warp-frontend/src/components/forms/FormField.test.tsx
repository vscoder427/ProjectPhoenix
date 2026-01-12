import { render, screen } from '@testing-library/react'
import { FormField } from './FormField'
import { Input } from '@/src/components/ui/input'

describe('FormField', () => {
  it('renders label when provided', () => {
    render(
      <FormField label="Email address">
        <Input />
      </FormField>
    )
    expect(screen.getByText(/email address/i)).toBeInTheDocument()
  })

  it('renders hint text when provided', () => {
    render(
      <FormField hint="We'll never share this">
        <Input />
      </FormField>
    )
    expect(screen.getByText(/we'll never share this/i)).toBeInTheDocument()
  })

  it('renders error message when provided', () => {
    render(
      <FormField error="Please enter a valid email">
        <Input />
      </FormField>
    )
    expect(screen.getByText(/please enter a valid email/i)).toBeInTheDocument()
  })

  it('shows "(Helps us support you better)" for required fields', () => {
    render(
      <FormField label="Full name" required>
        <Input />
      </FormField>
    )
    expect(screen.getByText(/helps us support you better/i)).toBeInTheDocument()
  })

  it('hides hint when error is present', () => {
    render(
      <FormField hint="Helpful hint" error="Error message">
        <Input />
      </FormField>
    )
    expect(screen.queryByText(/helpful hint/i)).not.toBeInTheDocument()
    expect(screen.getByText(/error message/i)).toBeInTheDocument()
  })

  it('sets aria-invalid on input when error is present', () => {
    render(
      <FormField error="Error message">
        <Input />
      </FormField>
    )
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
  })

  it('does not set aria-invalid when no error', () => {
    render(
      <FormField>
        <Input />
      </FormField>
    )
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'false')
  })
})
