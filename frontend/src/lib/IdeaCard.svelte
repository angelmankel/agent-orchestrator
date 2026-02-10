<script>
  import { createEventDispatcher } from 'svelte'

  export let idea

  const dispatch = createEventDispatcher()

  const statusIcons = {
    pending: '⏳',
    refining: '🔄',
    questions: '❓',
    approved: '✅',
    rejected: '❌',
    converted: '📋',
  }

  const statusLabels = {
    pending: 'Pending',
    refining: 'Refining...',
    questions: 'Questions',
    approved: 'Ready to approve',
    rejected: 'Rejected',
    converted: 'Converted',
  }

  function formatDate(dateStr) {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    return 'Just now'
  }
</script>

<button
  class="card p-4 w-full text-left hover:shadow-md transition-shadow"
  on:click={() => dispatch('click')}
>
  <div class="flex items-start justify-between">
    <div class="flex-1">
      <div class="flex items-center gap-2 mb-1">
        <span>{statusIcons[idea.status]}</span>
        <h3 class="font-semibold">{idea.title}</h3>
      </div>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-2 line-clamp-2">
        {idea.description}
      </p>
      <div class="flex items-center gap-3 text-xs text-gray-400">
        <span>Submitted {formatDate(idea.created_at)}</span>
        <span class="badge" class:badge-pending={idea.priority > 0}>
          {idea.priority > 5 ? 'Critical' : idea.priority > 0 ? 'High' : 'Normal'} priority
        </span>
      </div>
    </div>

    <div class="ml-4 text-right">
      <span class="badge" class:badge-pending={idea.status === 'questions'} class:badge-info={idea.status === 'refining'}>
        {statusLabels[idea.status]}
      </span>

      {#if idea.status === 'pending'}
        <button
          class="btn btn-primary text-sm mt-2"
          on:click|stopPropagation={() => dispatch('refine')}
        >
          Refine
        </button>
      {/if}
    </div>
  </div>
</button>

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
