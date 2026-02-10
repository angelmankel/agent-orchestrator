<script>
  import { onMount } from 'svelte'
  import { currentProject, addToast } from '../stores/app.js'
  import api from '../api/client.js'

  import IdeaCard from '../lib/IdeaCard.svelte'
  import IdeaModal from '../lib/IdeaModal.svelte'
  import NewIdeaModal from '../lib/NewIdeaModal.svelte'

  let ideas = []
  let loading = false
  let filter = 'all'
  let selectedIdea = null
  let showNewIdeaModal = false

  const statusFilters = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'refining', label: 'Refining' },
    { value: 'questions', label: 'Questions' },
    { value: 'approved', label: 'Approved' },
  ]

  $: if ($currentProject) {
    loadIdeas()
  }

  $: filteredIdeas = filter === 'all'
    ? ideas
    : ideas.filter(i => i.status === filter)

  async function loadIdeas() {
    if (!$currentProject) return
    loading = true
    try {
      ideas = await api.ideas.list({ project_id: $currentProject.id })
    } catch (e) {
      addToast('Failed to load ideas', 'error')
    } finally {
      loading = false
    }
  }

  async function handleRefine(idea) {
    try {
      await api.ideas.refine(idea.id)
      addToast('Refinement started', 'success')
      loadIdeas()
    } catch (e) {
      addToast('Failed to start refinement', 'error')
    }
  }

  async function handleApprove(idea) {
    try {
      await api.ideas.approve(idea.id)
      addToast('Idea approved and ticket created', 'success')
      selectedIdea = null
      loadIdeas()
    } catch (e) {
      addToast('Failed to approve idea', 'error')
    }
  }

  async function handleReject(idea, reason) {
    try {
      await api.ideas.reject(idea.id, reason)
      addToast('Idea rejected', 'info')
      selectedIdea = null
      loadIdeas()
    } catch (e) {
      addToast('Failed to reject idea', 'error')
    }
  }

  async function handleCreateIdea(data) {
    try {
      await api.ideas.create({
        ...data,
        project_id: $currentProject.id,
        source: 'web',
      })
      addToast('Idea created', 'success')
      showNewIdeaModal = false
      loadIdeas()
    } catch (e) {
      addToast('Failed to create idea', 'error')
    }
  }

  function getStatusIcon(status) {
    const icons = {
      pending: '⏳',
      refining: '🔄',
      questions: '❓',
      approved: '✅',
      rejected: '❌',
      converted: '📋',
    }
    return icons[status] || '•'
  }
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Ideas Inbox</h1>
    <button class="btn btn-primary" on:click={() => (showNewIdeaModal = true)}>
      + New Idea
    </button>
  </div>

  <div class="flex items-center gap-4 mb-6">
    <span class="text-sm text-gray-500">Filter:</span>
    {#each statusFilters as sf}
      <button
        class="px-3 py-1 rounded-full text-sm transition-colors"
        class:bg-primary-600={filter === sf.value}
        class:text-white={filter === sf.value}
        class:bg-gray-200={filter !== sf.value}
        class:dark:bg-gray-700={filter !== sf.value}
        on:click={() => (filter = sf.value)}
      >
        {sf.label}
      </button>
    {/each}
  </div>

  {#if loading}
    <div class="text-center py-12">
      <span class="text-gray-500">Loading...</span>
    </div>
  {:else if filteredIdeas.length === 0}
    <div class="card p-8 text-center">
      <p class="text-gray-500 dark:text-gray-400">No ideas found</p>
    </div>
  {:else}
    <div class="space-y-4">
      {#each filteredIdeas as idea (idea.id)}
        <IdeaCard
          {idea}
          on:click={() => (selectedIdea = idea)}
          on:refine={() => handleRefine(idea)}
        />
      {/each}
    </div>
  {/if}
</div>

{#if selectedIdea}
  <IdeaModal
    idea={selectedIdea}
    on:close={() => (selectedIdea = null)}
    on:approve={() => handleApprove(selectedIdea)}
    on:reject={(e) => handleReject(selectedIdea, e.detail)}
    on:updated={loadIdeas}
  />
{/if}

{#if showNewIdeaModal}
  <NewIdeaModal
    on:close={() => (showNewIdeaModal = false)}
    on:submit={(e) => handleCreateIdea(e.detail)}
  />
{/if}
