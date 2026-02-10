<script>
  import { onMount } from 'svelte'
  import { currentProject, addToast } from '../stores/app.js'
  import api from '../api/client.js'

  let agents = []
  let loading = false
  let filter = 'all'

  const typeFilters = [
    { value: 'all', label: 'All' },
    { value: 'development', label: 'Development' },
    { value: 'refinement', label: 'Refinement' },
    { value: 'support', label: 'Support' },
    { value: 'planning', label: 'Planning' },
  ]

  $: if ($currentProject) {
    loadAgents()
  }

  $: filteredAgents = filter === 'all'
    ? agents
    : agents.filter(a => a.type === filter)

  $: groupedAgents = {
    development: filteredAgents.filter(a => a.type === 'development'),
    refinement: filteredAgents.filter(a => a.type === 'refinement'),
    support: filteredAgents.filter(a => a.type === 'support'),
    planning: filteredAgents.filter(a => a.type === 'planning'),
  }

  async function loadAgents() {
    loading = true
    try {
      agents = await api.agents.list({
        project_id: $currentProject?.id,
        active_only: false,
      })
    } catch (e) {
      addToast('Failed to load agents', 'error')
    } finally {
      loading = false
    }
  }

  async function toggleActive(agent) {
    try {
      await api.agents.update(agent.id, { is_active: !agent.is_active })
      addToast(`Agent ${agent.is_active ? 'disabled' : 'enabled'}`, 'success')
      loadAgents()
    } catch (e) {
      addToast('Failed to update agent', 'error')
    }
  }

  onMount(loadAgents)
</script>

<div>
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Agents</h1>
  </div>

  <div class="flex items-center gap-4 mb-6">
    <span class="text-sm text-gray-500">Filter:</span>
    {#each typeFilters as tf}
      <button
        class="px-3 py-1 rounded-full text-sm transition-colors"
        class:bg-primary-600={filter === tf.value}
        class:text-white={filter === tf.value}
        class:bg-gray-200={filter !== tf.value}
        class:dark:bg-gray-700={filter !== tf.value}
        on:click={() => (filter = tf.value)}
      >
        {tf.label}
      </button>
    {/each}
  </div>

  {#if loading}
    <div class="text-center py-12">
      <span class="text-gray-500">Loading...</span>
    </div>
  {:else if filteredAgents.length === 0}
    <div class="card p-8 text-center">
      <p class="text-gray-500 dark:text-gray-400">No agents found</p>
    </div>
  {:else}
    {#each Object.entries(groupedAgents).filter(([_, a]) => a.length > 0) as [type, typeAgents]}
      <div class="mb-8">
        <h2 class="text-lg font-semibold mb-4 capitalize">{type}</h2>
        <div class="space-y-4">
          {#each typeAgents as agent (agent.id)}
            <div class="card p-4">
              <div class="flex items-start justify-between">
                <div class="flex items-start gap-3">
                  <span class="text-2xl">🤖</span>
                  <div>
                    <h3 class="font-semibold">{agent.name}</h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                      {agent.description}
                    </p>
                    <div class="flex items-center gap-3 mt-2 text-xs text-gray-400">
                      <span class="badge badge-info">{agent.model}</span>
                      <span>{agent.project_id ? 'Project' : 'Global'}</span>
                      {#if !agent.is_active}
                        <span class="badge badge-error">Disabled</span>
                      {/if}
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    class="btn btn-secondary text-sm py-1 px-3"
                    on:click={() => toggleActive(agent)}
                  >
                    {agent.is_active ? 'Disable' : 'Enable'}
                  </button>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/each}
  {/if}
</div>
