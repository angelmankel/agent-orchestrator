<script>
  import { currentPage, currentProject, darkMode } from '../stores/app.js'

  export let projects = []

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'ideas', label: 'Ideas Inbox', icon: '💡' },
    { id: 'queue', label: 'Dev Queue', icon: '🔧' },
    { id: 'agents', label: 'Agents', icon: '🤖' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ]
</script>

<aside class="fixed left-0 top-0 h-screen w-64 bg-gray-900 text-white flex flex-col">
  <div class="p-4 border-b border-gray-700">
    <h1 class="text-xl font-bold">Agent Orchestrator</h1>
  </div>

  <div class="p-4 border-b border-gray-700">
    <label class="block text-sm text-gray-400 mb-1">Project</label>
    <select
      class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
      bind:value={$currentProject}
    >
      {#if projects.length === 0}
        <option value={null}>No projects</option>
      {/if}
      {#each projects as project}
        <option value={project}>{project.name}</option>
      {/each}
    </select>
  </div>

  <nav class="flex-1 p-4">
    <ul class="space-y-1">
      {#each navItems as item}
        <li>
          <button
            class="w-full text-left px-3 py-2 rounded-lg flex items-center gap-3 transition-colors"
            class:bg-primary-600={$currentPage === item.id}
            class:hover:bg-gray-800={$currentPage !== item.id}
            on:click={() => ($currentPage = item.id)}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        </li>
      {/each}
    </ul>
  </nav>

  <div class="p-4 border-t border-gray-700">
    <button
      class="w-full text-left px-3 py-2 rounded-lg flex items-center gap-3 hover:bg-gray-800 transition-colors"
      on:click={() => ($darkMode = !$darkMode)}
    >
      <span>{$darkMode ? '☀️' : '🌙'}</span>
      <span>{$darkMode ? 'Light Mode' : 'Dark Mode'}</span>
    </button>
  </div>
</aside>
