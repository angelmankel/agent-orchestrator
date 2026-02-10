<script>
  import { onMount } from 'svelte'
  import { currentProject } from '../stores/app.js'
  import api from '../api/client.js'

  let stats = {
    ideas: { pending: 0, questions: 0, ready: 0 },
    tickets: { queued: 0, inProgress: 0, done: 0 },
    usage: { cost: 0, tokens: 0 }
  }

  let recentActivity = []
  let needsAttention = []

  $: if ($currentProject) {
    loadDashboard()
  }

  async function loadDashboard() {
    if (!$currentProject) return

    try {
      const [ideas, tickets, pendingQuestions] = await Promise.all([
        api.ideas.list({ project_id: $currentProject.id }),
        api.tickets.list({ project_id: $currentProject.id }),
        api.questions.pending($currentProject.id),
      ])

      stats.ideas.pending = ideas.filter(i => i.status === 'pending').length
      stats.ideas.questions = ideas.filter(i => i.status === 'questions').length
      stats.ideas.ready = ideas.filter(i => i.status === 'approved').length

      stats.tickets.queued = tickets.filter(t => t.status === 'queued').length
      stats.tickets.inProgress = tickets.filter(t => t.status === 'in_progress').length
      stats.tickets.done = tickets.filter(t => t.status === 'done').length

      needsAttention = []
      if (pendingQuestions.length > 0) {
        needsAttention.push({ type: 'questions', count: pendingQuestions.length })
      }
      const reviewTickets = tickets.filter(t => t.status === 'review')
      if (reviewTickets.length > 0) {
        needsAttention.push({ type: 'review', count: reviewTickets.length })
      }

    } catch (e) {
      console.error('Failed to load dashboard:', e)
    }
  }

  onMount(loadDashboard)
</script>

<div>
  <h1 class="text-2xl font-bold mb-6">Dashboard</h1>

  {#if !$currentProject}
    <div class="card p-8 text-center">
      <p class="text-gray-500 dark:text-gray-400 mb-4">No project selected</p>
      <p class="text-sm text-gray-400">Create a project to get started</p>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="card p-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Ideas</h3>
        <div class="space-y-1">
          <div class="flex justify-between">
            <span>Pending</span>
            <span class="font-semibold">{stats.ideas.pending}</span>
          </div>
          <div class="flex justify-between">
            <span>Awaiting answers</span>
            <span class="font-semibold">{stats.ideas.questions}</span>
          </div>
          <div class="flex justify-between">
            <span>Ready to approve</span>
            <span class="font-semibold">{stats.ideas.ready}</span>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Development</h3>
        <div class="space-y-1">
          <div class="flex justify-between">
            <span>Queued</span>
            <span class="font-semibold">{stats.tickets.queued}</span>
          </div>
          <div class="flex justify-between">
            <span>In progress</span>
            <span class="font-semibold">{stats.tickets.inProgress}</span>
          </div>
          <div class="flex justify-between">
            <span>Completed</span>
            <span class="font-semibold">{stats.tickets.done}</span>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">This Month</h3>
        <div class="space-y-1">
          <div class="flex justify-between">
            <span>Cost</span>
            <span class="font-semibold">${stats.usage.cost.toFixed(2)}</span>
          </div>
          <div class="flex justify-between">
            <span>Tokens</span>
            <span class="font-semibold">{(stats.usage.tokens / 1000).toFixed(0)}k</span>
          </div>
        </div>
      </div>
    </div>

    {#if needsAttention.length > 0}
      <div class="card p-6 mb-8">
        <h3 class="text-lg font-semibold mb-4">Needs Attention</h3>
        <div class="space-y-2">
          {#each needsAttention as item}
            <div class="flex items-center gap-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <span class="text-yellow-600">⚠️</span>
              {#if item.type === 'questions'}
                <span>{item.count} idea{item.count !== 1 ? 's' : ''} waiting for your answers</span>
              {:else if item.type === 'review'}
                <span>{item.count} ticket{item.count !== 1 ? 's' : ''} ready for review</span>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <div class="card p-6">
      <h3 class="text-lg font-semibold mb-4">Recent Activity</h3>
      {#if recentActivity.length === 0}
        <p class="text-gray-500 dark:text-gray-400 text-sm">No recent activity</p>
      {:else}
        <div class="space-y-3">
          {#each recentActivity as activity}
            <div class="flex items-center gap-3 text-sm">
              <span class="text-gray-400">{activity.time}</span>
              <span>{activity.message}</span>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>
