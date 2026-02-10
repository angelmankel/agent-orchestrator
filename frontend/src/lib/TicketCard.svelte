<script>
  import { createEventDispatcher } from 'svelte'

  export let ticket
  export let showStartButton = false
  export let showReviewButton = false

  const dispatch = createEventDispatcher()

  const typeLabels = {
    feature: 'Feature',
    bugfix: 'Bugfix',
    refactor: 'Refactor',
    chore: 'Chore',
  }

  const statusIcons = {
    queued: '⚪',
    in_progress: '🔵',
    review: '🟢',
    blocked: '🔴',
    done: '✅',
    cancelled: '❌',
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
        <span>{statusIcons[ticket.status]}</span>
        <h3 class="font-semibold">{ticket.title}</h3>
      </div>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-2 line-clamp-2">
        {ticket.description}
      </p>
      <div class="flex items-center gap-3 text-xs text-gray-400">
        <span class="badge badge-info">{typeLabels[ticket.type]}</span>
        <span>Created {formatDate(ticket.created_at)}</span>
        {#if ticket.priority > 0}
          <span class="badge badge-pending">
            {ticket.priority > 5 ? 'Critical' : 'High'}
          </span>
        {/if}
      </div>
    </div>

    <div class="ml-4 flex flex-col items-end gap-2">
      {#if showStartButton}
        <button
          class="btn btn-primary text-sm"
          on:click|stopPropagation={() => dispatch('start')}
        >
          Start
        </button>
      {/if}

      {#if showReviewButton}
        <button
          class="btn btn-primary text-sm"
          on:click|stopPropagation={() => dispatch('click')}
        >
          Review
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
