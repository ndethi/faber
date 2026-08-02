#!/usr/bin/env python3
"""
Faber CMS Admin - Basic UI Components

Creates basic UI components for the admin interface.
"""

from pathlib import Path


def create_basic_ui_components(components_dir: Path) -> None:
    """Create basic UI components referenced by admin components."""
    
    # Button component
    button_content = """---
// Button.astro - Reusable Button Component
---
<div class={`
  inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm
  ${variant === 'primary' 
    ? 'bg-faber-primary text-faber-white hover:bg-faber-primary-dark focus:outline-none focus:ring-2 focus:ring-faber-primary focus:ring-offset-2'
    : variant === 'secondary'
    ? 'bg-faber-surface text-faber-text border-faber-border hover:bg-faber-surface-hover focus:outline-none focus:ring-2 focus:ring-faber-primary focus:ring-offset-2'
    : variant === 'ghost'
    ? 'text-faber-text hover:bg-faber-surface-hover focus:outline-none focus:ring-2 focus:ring-faber-primary focus:ring-offset-2'
    : 'bg-faber-surface text-faber-text border-faber-border hover:bg-faber-surface-hover focus:outline-none focus:ring-2 focus:ring-faber-primary focus:ring-offset-2'
  }${disabled ? ' opacity-50 cursor-not-allowed' : ' cursor-pointer transition-colors duration-150'}
`}>
  <slot />
</div>
"""
    (components_dir / "Button.astro").write_text(button_content)

    # Input component
    input_content = """---
// Input.astro - Text Input Component
---
<label class="block text-sm font-medium text-faber-text mb-1" for={id}>
  {label}
</label>
<input
  id={id}
  type={type}
  class={`
    block w-full rounded-md border border-faber-border px-3 py-2 text-faber-text shadow-sm
    focus:border-faber-primary focus:ring-faber-primary focus:ring-offset-0 sm:text-sm
    ${disabled ? 'bg-faber-disabled cursor-not-allowed opacity-50' : ''}
    ${error ? 'border-faber-danger' : ''}
  `}
  placeholder={placeholder}
  required={required}
  {readonly && 'readonly'}
  {disabled && 'disabled'}
  value={value}
  on:input={e => dispatch('input', { target: { name, value: e.target.value } })}
  on:change={e => dispatch('change', { target: { name, value: e.target.value } })}
/>
{(error && helpText) && (
  <p class="mt-1 text-sm text-faber-danger">{helpText}</p>
)}
"""
    (components_dir / "Input.astro").write_text(input_content)

    # Textarea component
    textarea_content = """---
// Textarea.astro - Textarea Component
---
<label class="block text-sm font-medium text-faber-text mb-1" for={id}>
  {label}
</label>
<textarea
  id={id}
  class={`
    block w-full rounded-md border border-faber-border px-3 py-2 text-faber-text shadow-sm
    focus:border-faber-primary focus:ring-faber-primary focus:ring-offset-0 sm:text-sm
    ${disabled ? 'bg-faber-disabled cursor-not-allowed opacity-50' : ''}
    ${error ? 'border-faber-danger' : ''}
  `}
  rows={rows}
  placeholder={placeholder}
  required={required}
  {readonly && 'readonly'}
  {disabled && 'disabled'}
  value={value}
  on:input={e => dispatch('input', { target: { name, value: e.target.value } })}
  on:change={e => dispatch('change', { target: { name, value: e.target.value } })}
/>
{(error && helpText) && (
  <p class="mt-1 text-sm text-faber-danger">{helpText}</p>
)}
"""
    (components_dir / "Textarea.astro").write_text(textarea_content)

    # Select component
    select_content = """---
// Select.astro - Select Dropdown Component
---
<label class="block text-sm font-medium text-faber-text mb-1" for={id}>
  {label}
</label>
<select
  id={id}
  class={`
    block w-full rounded-md border border-faber-border px-3 py-2 text-faber-text shadow-sm
    focus:border-faber-primary focus:ring-faber-primary focus:ring-offset-0 sm:text-sm
    ${disabled ? 'bg-faber-disabled cursor-not-allowed opacity-50' : ''}
    ${error ? 'border-faber-danger' : ''}
  `}
  required={required}
  {readonly && 'readonly'}
  {disabled && 'disabled'}
  value={value}
  on:change={e => dispatch('change', { target: { name, value: e.target.value } })}
>
  {#if placeholder}
    <option value="" disabled selected>{placeholder}</option>
  {/if}
  {#each options as option}
    <option value={option.value || option} selected={selected === (option.value || option)}>
      {option.label || option}
    </option>
  {/each}
</select>
{(error && helpText) && (
  <p class="mt-1 text-sm text-faber-danger">{helpText}</p>
)}
"""
    (components_dir / "Select.astro").write_text(select_content)

    print(f"✓ Created basic UI components in {components_dir}")


if __name__ == "__main__":
    print("Use via setup process")