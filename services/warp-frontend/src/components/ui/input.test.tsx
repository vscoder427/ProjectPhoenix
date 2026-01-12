import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input } from './input'

describe('Input', () => {
  it('renders with placeholder', () => {
    render(<Input placeholder="Enter your email" />)
    expect(screen.getByPlaceholderText(/enter your email/i)).toBeInTheDocument()
  })

  it('handles text input correctly', async () => {
    const user = userEvent.setup()
    render(<Input />)

    const input = screen.getByRole('textbox')
    await user.type(input, 'test@example.com')

    expect(input).toHaveValue('test@example.com')
  })

  it('calls onChange when value changes', async () => {
    const user = userEvent.setup()
    const onChange = jest.fn()

    render(<Input onChange={onChange} />)
    await user.type(screen.getByRole('textbox'), 'a')

    expect(onChange).toHaveBeenCalled()
  })

  it('is disabled when disabled prop is true', () => {
    render(<Input disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('supports different input types', () => {
    const { rerender, container } = render(<Input type="email" />)
    expect(screen.getByRole('textbox')).toHaveAttribute('type', 'email')

    rerender(<Input type="password" />)
    // Password inputs don't have textbox role, query by type attribute
    const passwordInput = container.querySelector('input[type="password"]')
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('is keyboard accessible', async () => {
    const user = userEvent.setup()
    render(<Input />)

    const input = screen.getByRole('textbox')
    input.focus()

    expect(input).toHaveFocus()

    await user.keyboard('Hello')
    expect(input).toHaveValue('Hello')
  })
})
