<script>
  import { onMount } from 'svelte'
  import { currentProject, addToast } from '../stores/app.js'
  import api from '../api/client.js'

  import TicketCard from '../lib/TicketCard.svelte'
  import TicketModal from '../lib/TicketModal.svelte'

  let tickets = []
  let loading = false
  let selectedTicket = null

  $: if ($currentProject) {
    loadQueue()
  }

  $: groupedTickets = {
    in_progress: tickets.filter(t => t.status === 'in_progress'),
    review: tickets.filter(t => t.status === 'review'),
    queued: tickets.filter(t => t.status === 'queued'),
    blocked: tickets.filter(t => t.status === 'blocked'),
  }

  async function loadQueue() {
    if (!$currentProject) return
    loading = true
    try {
      tickets = await api.tickets.queue($currentProject.id)
    } catch (e) {
      addToast('Failed to load queue', 'error')
    } finally {
      loading = false
    }
  }

  async function handleStart(ticket) {
    try {
      await api.tickets.start(ticket.id)
      addToast('Ticket started', 'success')
      loadQueue()
    } catch (e) {
      addToast('Failed to start ticket', 'error')
    }
  }

  async function handleApprove(ticket, comment) {
    try {
      await api.tickets.approve(ticket.id, comment)
      addToast('Ticket approved', 'success')
      selectedTicket = null
      loadQueue()
    } catch (e) {
      addToast('Failed to approve ticket', 'error')
    }
  }

  async function handleRequestChanges(ticket, feedback) {
    try {
      await api.tickets.requestChanges(ticket.id, feedback)
      addToast('Changes requested', 'info')
      selectedTicket = null
      loadQueue()
    } catch (e) {
      addToast('Failed to request changes', 'error')
    }
  }

  function getStatusIcon(status) {
    const icons = {
      queued: '⚪',
      in_progress: '🔵',
      review: '🟢',
      blocked: '🔴',
      done: '✅',
      cancelled: '❌',
    }
    return icons[status] || '•'
  }
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Development Queue</h1>
  </div>

  {#if loading}
    <div class="text-center py-12">
      <span class="text-gray-500">Loading...</span>
    </div>
  {:else}
    {#if groupedTickets.in_progress.length > 0}
      <div class="mb-8">
        <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>🔵</span> In Progress
        </h2>
        <div class="space-y-4">
          {#each groupedTickets.in_progress as ticket (ticket.id)}
            <TicketCard
              {ticket}
              on:click={() => (selectedTicket = ticket)}
            />
          {/each}
        </div>
      </div>
    {/if}

    {#if groupedTickets.review.length > 0}
      <div class="mb-8">
        <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>🟢</span> Ready for Review
        </h2>
        <div class="space-y-4">
          {#each groupedTickets.review as ticket (ticket.id)}
            <TicketCard
              {ticket}
              showReviewButton
              on:click={() => (selectedTicket = ticket)}
            />
          {/each}
        </div>
      </div>
    {/if}

    {#if groupedTickets.queued.length > 0}
      <div class="mb-8">
        <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>⚪</span> Queued
        </h2>
        <div class="space-y-4">
          {#each groupedTickets.queued as ticket (ticket.id)}
            <TicketCard
              {ticket}
              showStartButton
              on:click={() => (selectedTicket = ticket)}
              on:start={() => handleStart(ticket)}
            />
          {/each}
        </div>
      </div>
    {/if}

    {#if groupedTickets.blocked.length > 0}
      <div class="mb-8">
        <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <span>🔴</span> Blocked
        </h2>
        <div class="space-y-4">
          {#each groupedTickets.blocked as ticket (ticket.id)}
            <TicketCard
              {ticket}
              on:click={() => (selectedTicket = ticket)}
            />
          {/each}
        </div>
      </div>
    {/if}

    {#if tickets.length === 0}
      <div class="card p-8 text-center">
        <p class="text-gray-500 dark:text-gray-400">No tickets in queue</p>
      </div>
    {/if}
  {/if}
</div>

{#if selectedTicket}
  <TicketModal
    ticket={selectedTicket}
    on:close={() => (selectedTicket = null)}
    on:approve={(e) => handleApprove(selectedTicket, e.detail)}
    on:requestChanges={(e) => handleRequestChanges(selectedTicket, e.detail)}
    on:updated={loadQueue}
  />
{/if}
