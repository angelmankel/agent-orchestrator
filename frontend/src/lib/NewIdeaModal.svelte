<script>
  import { createEventDispatcher } from 'svelte'

  const dispatch = createEventDispatcher()

  let title = ''
  let description = ''
  let priority = 0

  function submit() {
    if (!title.trim() || !description.trim()) {
      return
    }

    dispatch('submit', {
      title: title.trim(),
      description: description.trim(),
      priority,
    })
  }
</script>

<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
  <div class="bg-white dark:bg-gray-800 rounded-xl max-w-lg w-full">
    <div class="border-b border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
      <h2 class="text-xl font-bold">New Idea</h2>
      <button class="text-2xl text-gray-400 hover:text-gray-600" on:click={() => dispatch('close')}>
        &times;
      </button>
    </div>

    <form class="p-6 space-y-4" on:submit|preventDefault={submit}>
      <div>
        <label class="block text-sm font-medium mb-1">Title</label>
        <input
          type="text"
          class="input"
          placeholder="Brief title for your idea"
          bind:value={title}
          required
        />
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">Description</label>
        <textarea
          class="input"
          rows="4"
          placeholder="Describe your idea in detail..."
          bind:value={description}
          required
        />
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">Priority</label>
        <select class="input" bind:value={priority}>
          <option value={0}>Normal</option>
          <option value={5}>High</option>
          <option value={10}>Critical</option>
        </select>
      </div>

      <div class="flex justify-end gap-3 pt-4">
        <button type="button" class="btn btn-secondary" on:click={() => dispatch('close')}>
          Cancel
        </button>
        <button type="submit" class="btn btn-primary">
          Submit Idea
        </button>
      </div>
    </form>
  </div>
</div>
