<script>
  import { currentProject, darkMode, addToast } from '../stores/app.js'
  import api from '../api/client.js'

  let projectName = ''
  let projectPath = ''
  let showNewProject = false
  let creating = false

  $: if ($currentProject) {
    projectName = $currentProject.name
    projectPath = $currentProject.path
  }

  async function createProject() {
    if (!projectName.trim() || !projectPath.trim()) {
      addToast('Please fill in all fields', 'error')
      return
    }

    creating = true
    try {
      const project = await api.projects.create({
        name: projectName.trim(),
        path: projectPath.trim(),
      })
      $currentProject = project
      showNewProject = false
      addToast('Project created', 'success')
    } catch (e) {
      addToast('Failed to create project', 'error')
    } finally {
      creating = false
    }
  }

  async function updateProject() {
    if (!$currentProject) return

    try {
      const updated = await api.projects.update($currentProject.id, {
        name: projectName.trim(),
        path: projectPath.trim(),
      })
      $currentProject = updated
      addToast('Project updated', 'success')
    } catch (e) {
      addToast('Failed to update project', 'error')
    }
  }

  async function deleteProject() {
    if (!$currentProject) return
    if (!confirm('Are you sure you want to delete this project?')) return

    try {
      await api.projects.delete($currentProject.id)
      $currentProject = null
      addToast('Project deleted', 'success')
    } catch (e) {
      addToast('Failed to delete project', 'error')
    }
  }
</script>

<div>
  <h1 class="text-2xl font-bold mb-6">Settings</h1>

  <div class="space-y-8">
    <div class="card p-6">
      <h2 class="text-lg font-semibold mb-4">Appearance</h2>
      <div class="flex items-center justify-between">
        <div>
          <p class="font-medium">Dark Mode</p>
          <p class="text-sm text-gray-500">Use dark theme</p>
        </div>
        <button
          class="relative w-12 h-6 rounded-full transition-colors"
          class:bg-primary-600={$darkMode}
          class:bg-gray-300={!$darkMode}
          on:click={() => ($darkMode = !$darkMode)}
        >
          <span
            class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform"
            class:translate-x-6={$darkMode}
          />
        </button>
      </div>
    </div>

    <div class="card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">Project Settings</h2>
        <button
          class="btn btn-secondary text-sm"
          on:click={() => (showNewProject = !showNewProject)}
        >
          {showNewProject ? 'Cancel' : '+ New Project'}
        </button>
      </div>

      {#if showNewProject}
        <div class="space-y-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div>
            <label class="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              class="input"
              placeholder="My Project"
              bind:value={projectName}
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Path</label>
            <input
              type="text"
              class="input"
              placeholder="/path/to/project"
              bind:value={projectPath}
            />
          </div>
          <button
            class="btn btn-primary"
            on:click={createProject}
            disabled={creating}
          >
            {creating ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      {:else if $currentProject}
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              class="input"
              bind:value={projectName}
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Path</label>
            <input
              type="text"
              class="input"
              bind:value={projectPath}
            />
          </div>
          <div class="flex items-center gap-4">
            <button class="btn btn-primary" on:click={updateProject}>
              Save Changes
            </button>
            <button class="btn btn-danger" on:click={deleteProject}>
              Delete Project
            </button>
          </div>
        </div>
      {:else}
        <p class="text-gray-500">No project selected. Create one to get started.</p>
      {/if}
    </div>

    <div class="card p-6">
      <h2 class="text-lg font-semibold mb-4">API Status</h2>
      <div class="text-sm">
        <p class="text-gray-500">Backend: <span class="text-green-600">Connected</span></p>
      </div>
    </div>
  </div>
</div>
