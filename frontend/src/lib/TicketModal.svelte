<script>
  import { createEventDispatcher, onMount } from 'svelte'
  import { addToast } from '../stores/app.js'
  import api from '../api/client.js'

  export let ticket

  const dispatch = createEventDispatcher()

  let subtasks = []
  let reviewSummary = null
  let loading = false
  let feedback = ''

  onMount(loadData)

  async function loadData() {
    loading = true
    try {
      const [subs, review] = await Promise.all([
        api.tickets.listSubtasks(ticket.id),
        ticket.status === 'review' ? api.tickets.getReviewSummary(ticket.id) : null,
      ])
      subtasks = subs
      reviewSummary = review
    } catch (e) {
      console.error('Failed to load ticket data:', e)
    } finally {
      loading = false
    }
  }

  function handleApprove() {
    const comment = prompt('Approval comment (optional):')
    dispatch('approve', comment)
  }

  function handleRequestChanges() {
    if (!feedback.trim()) {
      addToast('Please provide feedback', 'error')
      return
    }
    dispatch('requestChanges', feedback.trim())
  }

  const statusIcons = {
    pending: '⚪',
    in_progress: '🔵',
    done: '✅',
    skipped: '⏭️',
  }
</script>

<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
  <div class="bg-white dark:bg-gray-800 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
    <div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold">{ticket.title}</h2>
        <div class="flex items-center gap-2 mt-1 text-sm text-gray-500">
          <span class="badge badge-info">{ticket.type}</span>
          <span>Priority: {ticket.priority}</span>
        </div>
      </div>
      <button class="text-2xl text-gray-400 hover:text-gray-600" on:click={() => dispatch('close')}>
        &times;
      </button>
    </div>

    <div class="p-6 space-y-6">
      <div>
        <h3 class="text-sm font-medium text-gray-500 mb-2">Description</h3>
        <p class="text-gray-700 dark:text-gray-300">{ticket.description}</p>
      </div>

      {#if subtasks.length > 0}
        <div>
          <h3 class="text-sm font-medium text-gray-500 mb-2">Subtasks</h3>
          <div class="space-y-2">
            {#each subtasks as subtask}
              <div class="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                <span>{statusIcons[subtask.status]}</span>
                <span class:line-through={subtask.status === 'done'}>{subtask.title}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      {#if reviewSummary}
        <div>
          <h3 class="text-sm font-medium text-gray-500 mb-2">Review Summary</h3>

          {#if reviewSummary.build_results.length > 0}
            <div class="mb-3">
              <span class="text-sm font-medium">Build: </span>
              {#if reviewSummary.build_results[0]?.success}
                <span class="text-green-600">✅ Success</span>
              {:else}
                <span class="text-red-600">❌ Failed</span>
              {/if}
            </div>
          {/if}

          {#if reviewSummary.test_results.length > 0}
            <div class="mb-3">
              <span class="text-sm font-medium">Tests: </span>
              {#if reviewSummary.test_results[0]?.success}
                <span class="text-green-600">✅ Passed</span>
              {:else}
                <span class="text-red-600">❌ Failed</span>
              {/if}
            </div>
          {/if}

          {#if reviewSummary.review_results.length > 0}
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <h4 class="font-medium text-sm mb-2">Automated Review</h4>
              {#if reviewSummary.review_results[0]?.checklist}
                <ul class="text-sm space-y-1">
                  {#each Object.entries(reviewSummary.review_results[0].checklist) as [key, value]}
                    <li class="flex items-center gap-2">
                      <span>{value ? '✅' : '❌'}</span>
                      <span>{key.replace(/_/g, ' ')}</span>
                    </li>
                  {/each}
                </ul>
              {/if}
              {#if reviewSummary.review_results[0]?.issues?.length > 0}
                <div class="mt-2">
                  <h5 class="text-sm font-medium">Issues:</h5>
                  <ul class="text-sm text-yellow-600">
                    {#each reviewSummary.review_results[0].issues as issue}
                      <li>⚠️ {issue.description}</li>
                    {/each}
                  </ul>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/if}

      {#if ticket.result}
        <div>
          <h3 class="text-sm font-medium text-gray-500 mb-2">Result</h3>
          <pre class="text-xs bg-gray-50 dark:bg-gray-700 p-3 rounded-lg overflow-x-auto">{JSON.stringify(ticket.result, null, 2)}</pre>
        </div>
      {/if}

      {#if ticket.status === 'review'}
        <div>
          <h3 class="text-sm font-medium text-gray-500 mb-2">Your Feedback</h3>
          <textarea
            class="input"
            rows="3"
            placeholder="Enter feedback if requesting changes..."
            bind:value={feedback}
          />
        </div>
      {/if}
    </div>

    {#if ticket.status === 'review'}
      <div class="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 flex justify-end gap-3">
        <button class="btn btn-secondary" on:click={handleRequestChanges}>
          Request Changes
        </button>
        <button class="btn btn-primary" on:click={handleApprove}>
          Approve & Complete
        </button>
      </div>
    {/if}
  </div>
</div>
