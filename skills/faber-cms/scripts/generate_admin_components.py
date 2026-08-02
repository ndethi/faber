#!/usr/bin/env python3
"""
Faber CMS Admin - Admin Components Generator

Generates reusable Astro components for the admin UI.
"""

from typing import Any, Dict


def generate_admin_components(config: Dict[str, Any]) -> Dict[str, str]:
    """Generate all admin components."""
    project_name = config["project_name"]

    components = {}

    # Sidebar component
    components["Sidebar.astro"] = """---
// Sidebar.astro - Admin Sidebar NavigationController
import Logo from "@/components/admin/Logo.astro";

interface Props {
  active?: string // Current active route
}

const { active = "" } = Astro.props;
---

<aside class="w-64 bg-faber-surface border-r border-faber-border">
  <div class="p-4 border-b border-faber-border">
    <Logo />
  </div>
  <nav class="mt-4 space-y-1">
    <a 
      href="/admin" 
      class={`block px-4 py-3 text-sm font-medium 
        ${active === '' || active === '/admin' ? 'bg-faber-primary text-white' : 'text-faber-text hover:bg-faber-surface/50'}`}
    >
      Dashboard
    </a>
    <a 
      href="/admin/content" 
      class={`block px-4 py-3 text-sm font-medium 
        ${active.startsWith('/admin/content') && !active.includes('/admin/content/') && !active.includes('/admin/content/[') ? 'bg-faber-primary text-white' : 'text-faber-text hover:bg-faber-surface/50'}`}
    >
      Content
    </a>
    <a 
      href="/admin/settings" 
      class={`block px-4 py-3 text-sm font-medium 
        ${active === '/admin/settings' ? 'bg-faber-primary text-white' : 'text-faber-text hover:bg-faber-surface/50'}`}
    >
      Settings
    </a>
  </nav>
</aside>
"""

    # Header component
    components["Header.astro"] = """---
// Header.astro - Admin Header
import Logo from "@/components/admin/Logo.astro";
import Avatar from "@/components/admin/Avatar.astro";

interface Props {
  title: string
  subtitle?: string
  action?: {
    label: string
    href: string
    variant?: 'primary' | 'secondary' | 'ghost'
  }
}

const { title, subtitle, action } = Astro.props;
---

<header class="flex h-16 items-center justify-between px-6 bg-faber-primary text-white border-b border-faber-border/50">
  <div class="flex items-center space-x-4">
    <Logo class="h-8 w-8" />
    <div>
      <h1 class="text-lg font-semibold">{title}</h1>
      {subtitle && <p class="text-sm text-faber-primary/50">{subtitle}</p>}
    </div>
  </div>
  <div class="flex items-center space-x-4">
    {action && (
      <a 
        href={action.href} 
        class={`px-3 py-1.5 text-sm rounded 
          ${action.variant === 'primary' ? 'bg-faber-white/20 text-faber-white hover:bg-faber-white/30' : 
           action.variant === 'secondary' ? 'border border-faber-white/30 text-faber-white hover:bg-faber-white/20' : 
           'text-faber-white hover:text-faber-white/70'}
        `}
      >
        {action.label}
      </a>
    )}
    <Avatar />
  </div>
</header>
"""

    # Logo component
    components["Logo.astro"] = """---
// Logo.astro - Admin Logo
--->
<div class="flex h-8 w-8 items-center justify-center">
  <svg class="h-6 w-6 text-faber-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m2 0a9 9 0 11-18 0 9 9 0 0118 0z"></path>
  </svg>
  <span class="ml-2 text-sm font-semibold text-faber-text">CMS Admin</span>
</div>
"""

    # Avatar component
    components["Avatar.astro"] = """---
// Avatar.astro - Admin User Avatar
--->
<div class="relative h-10 w-10">
  <div class="h-10 w-10 bg-faber-primary/20 rounded-full flex items-center justify-center">
    <span class="text-faber-text">AD</span>
  </div>
  <div class="absolute -bottom-1 -right-0 h-2 w-2 bg-faber-primary rounded-full border-2 border-faber-surface"></div>
</div>
"""

    # ContentTable component
    components["ContentTable.astro"] = """---
// ContentTable.astro - Admin Content Table
import Button from "@/components/ui/Button.astro";
import Modal from "@/components/admin/Modal.astro";
import Toast from "@/components/admin/Toast.astro";

interface Props {
  collection: string
  workerUrl: string
}

const { collection, workerUrl } = Astro.props;
---

<div class="space-y-4">
  <div class="flex items-center justify-between mb-4">
    <h2 class="text-xl font-semibold text-faber-text">{collection.replace(/_/g, ' ').toUpperCase()}</h2>
    <Button 
      variant="primary" 
      href={`/admin/content/${collection}/new`}
    >
      New Item
    </Button>
  </div>
  
  <div class="bg-faber-surface border border-faber-border rounded-xl overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full min-w-[800px]">
        <thead>
          <tr class="border-b border-faber-border">
            <th class="sticky top-0 left-0 z-10 px-3 py-2 text-left text-xs font-medium text-faber-text-muted bg-faber-surface/50">
              ID
            </th>
            <th class="sticky top-0 z-10 px-3 py-2 text-left text-xs font-medium text-faber-text-muted bg-faber-surface/50">
              Title
            </th>
            <th class="sticky top-0 z-10 px-3 py-2 text-left text-xs font-medium text-faber-text-muted bg-faber-surface/50">
              Status
            </th>
            <th class="sticky top-0 z-10 px-3 py-2 text-left text-xs font-medium text-faber-text-muted bg-faber-surface/50">
              Updated
            </th>
            <th class="sticky top-0 z-10 px-3 py-2 text-right text-xs font-medium text-faber-text-muted bg-faber-surface/50">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {{#if items}}
            {{#each items}}
              <tr class="border-b border-faber-border/50 hover:bg-faber-surface-hover">
                <td class="px-3 py-2 text-left text-sm font-mono">{{id}}</td>
                <td class="px-3 py-2 text-left text-sm">{{data?.title || 'Untitled'}}</td>
                <td class="px-3 py-2 text-left text-sm">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                    {{#if status === 'published'}}bg-green-100 text-green-800
                    {{else if status === 'draft'}}bg-yellow-100 text-yellow-800
                    {{else}}bg-gray-100 text-gray-800{{/if}}
                  ">
                    {{status}}
                  </span>
                </td>
                <td class="px-3 py-2 text-left text-sm text-faber-text-muted">
                  {{updated_at ? (new Date(updated_at).toLocaleString()) : '—'}}
                </td>
                <td class="px-3 py-2 text-right text-sm space-x-2">
                  <a 
                    href={`/admin/content/${collection}/${id}`} 
                    class="text-sm text-faber-primary hover:underline"
                  >
                    Edit
                  </a>
                  <button 
                    class="text-sm text-faber-danger hover:text-faber-dark/70"
                    on:click={{deleteItem}}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            {{/each}}
          {{else}}
            <tr>
              <td colspan="5" class="px-6 py-4 text-center text-faber-text-muted">
                No items yet. <a href={`/admin/content/${collection}/new`} class="text-faber-primary underline">Create first item</a>
              </td>
            </tr>
          {{/if}}
        </tbody>
      </table>
    </div>
  </div>
  
  {{#if items}}
    <div class="flex items-center justify-between pt-4 text-sm text-faber-text-muted">
      <span>Showing {{items.length}} of {{totalCount}} items</span>
      <div class="flex space-x-2">
        <button disabled>◀ Prev</button>
        <button disabled>Next ▶</button>
      </div>
    </div>
  {{/if}}
</div>

<script is:inline>
  const WORKER_URL = "{worker_url}";
  const COLLECTION = "{collection}";

  let items = [];
  let totalCount = 0;
  let currentPage = 1;
  let pageSize = 20;

  async function loadItems(page = 1) {{
    try {{
      const response = await fetch(`${{WORKER_URL}}/api/content?collection=${{COLLECTION}}&limit=${{pageSize}}&offset=${{(page - 1) * pageSize}}`);
      if (response.ok) {{
        const data = await response.json();
        items = data.items || [];
        totalCount = data.total || 0;
        currentPage = page;
        // Force component update
        window.dispatchEvent(new Event('content-updated'));
      }} else {{
        console.error('Failed to load items:', await response.text());
      }}
    }} catch (err) {{
      console.error('Network error loading items:', err);
    }}
  }}

  async function deleteItem(e) {{
    const id = e.currentTarget.closest('tr').querySelector('td:first-child').textContent.trim();
    if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {{
      return;
    }}

    try {{
      const response = await fetch(`${{WORKER_URL}}/api/content/${{id}}`, {{
        method: 'DELETE',
      }});
      
      if (response.ok) {{
        loadItems(currentPage);
        showToast('Item deleted successfully', 'success');
      }} else {{
        const error = await response.json();
        showToast(error.message || 'Failed to delete item', 'error');
      }}
    }} catch (err) {{
      showToast('Network error', 'error');
    }}
  }}

  function showToast(message, type = 'info') {{
    const toast = document.querySelector('toast-component');
    if (toast && toast.show) {{
      toast.show(message, type);
    }} else {{
      alert(message);
    }}
  }}

  // Load initial data
  loadItems();
</script>
"""

    # ContentForm component
    components["ContentForm.astro"] = """---
// ContentForm.astro - Admin Content Form
import Button from "@/components/ui/Button.astro";
import Input from "@/components/ui/Input.astro";
import Textarea from "@/components/ui/Textarea.astro";
import Select from "@/components/ui/Select.astro";
import Toast from "@/components/admin/Toast.astro";

interface Props {
  collection: string
  itemId?: string // If editing existing item
  workerUrl: string
}

const { collection, itemId, workerUrl } = Astro.props;
---

<form 
  id="content-form"
  class="space-y-6"
  method="post"
  enctype="multipart/form-data"
>
  <div class="space-y-4">
    {{#if schema}}
      {{#each schema.fields}}
        {{#if eq type "input"}}
          <Input 
            name="{{name}}" 
            label="{{label}}" 
            placeholder="{{placeholder}}" 
            required="{{required}}" 
            value="{{#if data}}{{data.[name]}}{{/if}}"
          />
        {{/if}}
        {{#if eq type "textarea"}}
          <Textarea 
            name="{{name}}" 
            label="{{label}}" 
            placeholder="{{placeholder}}" 
            required="{{required}}" 
            rows="{{rows}}" 
            value="{{#if data}}{{data.[name]}}{{/if}}"
          />
        {{/if}}
        {{#if eq type "select"}}
          <Select 
            name="{{name}}" 
            label="{{label}}" 
            placeholder="{{placeholder}}" 
            required="{{required}}" 
            options="{{options}}" 
            value="{{#if data}}{{data.[name]}}{{/if}}"
          />
        {{/if}}
      {{/each}}
    {{/if}}
  </div>
  
  <div class="flex items-center justify-between pt-4 border-t border-faber-border">
    <Button 
      variant="secondary" 
      href={`/admin/content/${collection}`}
    >
      Cancel
    </Button>
    <Button 
      type="submit"
      variant="primary"
    >
      {{#if itemId}}Update Item{{else}}Create Item{{/if}}
    </Button>
  </div>
</form>

{{#if itemId}}
  <script is:inline>
    const WORKER_URL = "{worker_url}";
    const COLLECTION = "{collection}";
    const ITEM_ID = "{itemId}";
    
    async function loadItem() {{
      try {{
        const response = await fetch(`${{WORKER_URL}}/api/content/${{ITEM_ID}}`);
        if (response.ok) {{
          const data = await response.json();
          // Populate form with data
          // This would be handled by the form framework
        }} else {{
          console.error('Failed to load item:', await response.text());
        }}
      }} catch (err) {{
        console.error('Network error loading item:', err);
      }}
    }}

    document.getElementById('content-form').addEventListener('submit', async (e) => {{
      e.preventDefault();
      const formData = new FormData(e.target);
      const data = Object.fromEntries(formData.entries());
      
      try {{
        let response;
        if (ITEM_ID) {{
          response = await fetch(`${{WORKER_URL}}/api/content/${{ITEM_ID}}`, {{
            method: 'PUT',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(data),
          }});
        }} else {{
          response = await fetch(`${{WORKER_URL}}/api/content`, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(data),
          }});
        }}
        
        if (response.ok) {{
          showToast('{{#if itemId}}Item updated{{else}}Item created{{/if}} successfully', 'success');
          window.location.href = `/admin/content/${{COLLECTION}}`;
        }} else {{
          const error = await response.json();
          showToast(error.message || 'Failed to {{#if itemId}}update{{else}}create{{/if}} item', 'error');
        }}
      }} catch (err) {{
        showToast('Network error', 'error');
      }}
    }});
    
    loadItem();
  </script>
{{/if}}
"""

    # Modal component
    components["Modal.astro"] = """---
// Modal.astro - Reusable Modal Dialog
import Button from "@/components/ui/Button.astro";

interface Props {
  id: string
  title: string
  message?: string
  fields?: Array<{ 
    name: string 
    label: string 
    type: 'text' | 'textarea' | 'select' 
    required?: boolean 
    placeholder?: string
    options?: Array<string>
  }>
  showOnMount?: boolean
}

const { id, title, message, fields = [], showOnMount = false } = Astro.props;
---

<div class="fixed inset-0 z-50 flex items-center justify-center bg-faber-background/50 backdrop-blur-sm hidden" id="{{id}}">
  <div class="relative bg-faber-surface rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-semibold text-faber-text">{title}</h2>
      <button 
        on:click={{toggleModal}}
        class="text-faber-text hover:text-faber-dark/70"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>
    
    {{#if message}}
      <p class="mb-4 text-faber-text">{message}</p>
    {{/if}}
    
    {{#if fields}}
      <form class="space-y-4">
        {{#each fields}}
          {{#if eq type "input"}}
            <Input 
              name="{{name}}" 
              label="{{label}}" 
              placeholder="{{placeholder}}" 
              required="{{required}}" 
            />
          {{/if}}
          {{#if eq type "textarea"}}
            <Textarea 
              name="{{name}}" 
              label="{{label}}" 
              placeholder="{{placeholder}}" 
              required="{{required}}" 
              rows="{{rows}}" 
            />
          {{/if}}
          {{#if eq type "select"}}
            <Select 
              name="{{name}}" 
              label="{{label}}" 
              placeholder="{{placeholder}}" 
              required="{{required}}" 
              options="{{options}}" 
            />
          {{/if}}
        {{/each}}
        
        <div class="flex items-center justify-end pt-4">
          <Button variant="secondary" on:click={{toggleModal}}>
            Cancel
          </Button>
          <Button variant="primary" on:click={{submitForm}}>
            Submit
          </Button>
        </div>
      </form>
    {{/if}}
  </div>
</div>

<script is:inline>
  let isOpen = false;
  
  function toggleModal() {{
    isOpen = !isOpen;
    document.getElementById('{{id}}').classList.toggle('hidden', !isOpen);
    if (isOpen) {{
      document.getElementById('{{id}}').focus();
    }} else {{
      // Reset form on close if needed
      const form = document.getElementById('{{id}}').querySelector('form');
      if (form) form.reset();
    }}
  }}
  
  function submitForm() {{
    // Form submission handled by individual components
    const event = new CustomEvent('form-submitted', {{ 
      detail: Object.fromEntries(new FormData(document.getElementById('{{id}}).querySelector('form')).entries()) 
    }});
    document.getElementById('{{id}}').dispatchEvent(event);
  }}
  
  // Auto-open if specified
  {{#if showOnMount}}
    toggleModal();
  {{/if}}
</script>
"""

    # Toast component
    components["Toast.astro"] = """---
// Toast.astro - Notification Toast
--->
<div class="fixed bottom-4 right-4 z-50" part="toast">
  <div 
    class="hidden 
      px-4 py-3 rounded-lg 
      text-faber-text 
      flex items-center space-x-3
      animate-in [fade-in:0.15s_ease-out] 
      animate-out [fade-out:0.15s_ease-in]
      delay-2000
    "
    id="toast"
    role="alert"
    aria-live="polite"
  >
    <div class="flex-shrink-0">
      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <!-- Icon will be dynamically set -->
      </svg>
    </div>
    <div class="flex-1">
      <p class="text-sm font-medium" id="toast-message"></p>
    </div>
    <button 
      class="ml-2 h-5 w-5 flex items-center justify-center text-faber-text/50 hover:text-faber-text"
      id="toast-close"
    >
      <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
    </button>
  </div>
</div>

<script is:inline>
  let currentTimeout = null;
  
  function show(message, type = 'info') {{
    const toast = document.getElementById('toast');
    const icon = toast.querySelector('svg');
    const msgEl = document.getElementById('toast-message');
    const closeBtn = document.getElementById('toast-close');
    
    // Set icon based on type
    let iconHtml = '';
    switch (type) {{
      case 'success':
        iconHtml = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-2.147 5.658 11.955 11.955 0 00-5.834 9.86A11.94 11.94 0 013 15.75a11.92 11.92 0 00-3.332 5.584 11.92 11.92 0 00-2.569 2.29"></path>';
        break;
      case 'error':
        iconHtml = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>';
        break;
      case 'warning':
        iconHtml = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.956c-.026 0-.052-.002-.078-.005l3.413-1.313a2.89 0 01.008-2.07 2.895 2.895 0 018.468 3.049A12.09 12.09 0 0015.75 9.037a12.1 12.1 0 01-4.076-.505"></path>';
        break;
      default:
        iconHtml = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H3a2 2 0 00-2 2v9a2 2 0 002 2h9a2 2 0 002-2v-5a2 2 0 012-2h3a2 2 0 002-2v-.5a2 2 0 00-.586 1.414l5 5a2 2 0 001.415-1.415l5-5a2 2 0 001.414-1.415V3a2 2 0 00-2-2z"></path>';
        break;
    }}
    
    icon.innerHTML = iconHtml;
    msgEl.textContent = message;
    
    // Set background color based on type
    toast.className = `hidden 
      px-4 py-3 rounded-lg 
      text-faber-text 
      flex items-center space-x-3
      animate-in [fade-in:0.15s_ease-out] 
      animate-out [fade-out:0.15s_ease-in]
      delay-2000
      ${type === 'success' ? 'bg-green-100 text-green-800' : 
       type === 'error' ? 'bg-red-100 text-red-800' : 
       type === 'warning' ? 'bg-yellow-100 text-yellow-800' : 
       'bg-faber-primary/10 text-faber-text'}
    `;
    
    toast.classList.remove('hidden');
    
    if (currentTimeout) {{
      clearTimeout(currentTimeout);
    }}
    currentTimeout = setTimeout(() => {{
      toast.classList.add('hidden');
    }}, 3000);
  }}
  
  document.getElementById('toast-close')?.addEventListener('click', () => {{
    document.getElementById('toast').classList.add('hidden');
    if (currentTimeout) {{
      clearTimeout(currentTimeout);
    }}
  }});
  
  // Expose show method
  window.showToast = show;
</script>
"""

    return components


if __name__ == "__main__":
    print("Use via generate_admin_ui.py")