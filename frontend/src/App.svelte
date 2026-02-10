<script>
  import { onMount } from 'svelte'
  import { currentPage, currentProject, darkMode, toasts, removeToast } from './stores/app.js'
  import api from './api/client.js'

  import Sidebar from './lib/Sidebar.svelte'
  import Dashboard from './routes/Dashboard.svelte'
  import Ideas from './routes/Ideas.svelte'
  import Queue from './routes/Queue.svelte'
  import Agents from './routes/Agents.svelte'
  import Settings from './routes/Settings.svelte'

  let projects = []

  onMount(async () => {
    try {
      projects = await api.projects.list()
      if (projects.length > 0) {
        $currentProject = projects[0]
      }
    } catch (e) {
      console.error('Failed to load projects:', e)
    }
  })

  $: pageComponent = {
    dashboard: Dashboard,
    ideas: Ideas,
    queue: Queue,
    agents: Agents,
    settings: Settings,
  }[$currentPage] || Dashboard
</script>

<div class="min-h-screen flex">
  <Sidebar {projects} />

  <main class="flex-1 ml-64 p-8">
    <svelte:component this={pageComponent} />
  </main>
</div>

<!-- Toast notifications -->
<div class="fixed bottom-4 right-4 z-50 space-y-2">
  {#each $toasts as toast (toast.id)}
    <div
      class="px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-slide-in"
      class:bg-green-600={toast.type === 'success'}
      class:bg-red-600={toast.type === 'error'}
      class:bg-blue-600={toast.type === 'info'}
      class:text-white={true}
    >
      <span>{toast.message}</span>
      <button
        class="opacity-70 hover:opacity-100"
        on:click={() => removeToast(toast.id)}
      >
        &times;
      </button>
    </div>
  {/each}
</div>

<style>
  @keyframes slide-in {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  .animate-slide-in {
    animation: slide-in 0.3s ease-out;
  }
</style>
