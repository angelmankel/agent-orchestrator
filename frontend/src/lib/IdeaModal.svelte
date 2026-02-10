<script>
  import { createEventDispatcher, onMount } from 'svelte'
  import { addToast } from '../stores/app.js'
  import api from '../api/client.js'

  export let idea

  const dispatch = createEventDispatcher()

  let questions = []
  let loading = false
  let currentQuestionIndex = 0
  let answerText = ''

  onMount(loadQuestions)

  async function loadQuestions() {
    loading = true
    try {
      questions = await api.ideas.getQuestions(idea.id)
    } catch (e) {
      addToast('Failed to load questions', 'error')
    } finally {
      loading = false
    }
  }

  $: pendingQuestions = questions.filter(q => q.status === 'pending')
  $: currentQuestion = pendingQuestions[currentQuestionIndex]

  async function submitAnswer() {
    if (!answerText.trim()) {
      addToast('Please enter an answer', 'error')
      return
    }

    try {
      await api.questions.answer(currentQuestion.id, answerText.trim())
      addToast('Answer submitted', 'success')
      answerText = ''
      await loadQuestions()
      dispatch('updated')
    } catch (e) {
      addToast('Failed to submit answer', 'error')
    }
  }

  async function skipQuestion() {
    try {
      await api.questions.skip(currentQuestion.id)
      await loadQuestions()
      dispatch('updated')
    } catch (e) {
      addToast('Failed to skip question', 'error')
    }
  }

  function handleReject() {
    const reason = prompt('Reason for rejection (optional):')
    dispatch('reject', reason)
  }
</script>

<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
  <div class="bg-white dark:bg-gray-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
    <div class="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
      <h2 class="text-xl font-bold">{idea.title}</h2>
      <button class="text-2xl text-gray-400 hover:text-gray-600" on:click={() => dispatch('close')}>
        &times;
      </button>
    </div>

    <div class="p-6 space-y-6">
      <div>
        <h3 class="text-sm font-medium text-gray-500 mb-2">Description</h3>
        <p class="text-gray-700 dark:text-gray-300">{idea.description}</p>
      </div>

      {#if loading}
        <div class="text-center py-4">Loading questions...</div>
      {:else if pendingQuestions.length > 0}
        <div class="border border-primary-200 dark:border-primary-800 rounded-lg p-4 bg-primary-50 dark:bg-primary-900/20">
          <div class="text-sm text-gray-500 mb-2">
            Question {currentQuestionIndex + 1} of {pendingQuestions.length}
          </div>
          <p class="font-medium mb-2">{currentQuestion.question}</p>
          {#if currentQuestion.context}
            <p class="text-sm text-gray-500 mb-4">{currentQuestion.context}</p>
          {/if}

          <textarea
            class="input mb-3"
            rows="3"
            placeholder="Your answer..."
            bind:value={answerText}
          />

          <div class="flex justify-end gap-2">
            <button class="btn btn-secondary text-sm" on:click={skipQuestion}>
              Skip
            </button>
            <button class="btn btn-primary text-sm" on:click={submitAnswer}>
              Submit Answer
            </button>
          </div>
        </div>
      {:else if questions.some(q => q.status === 'answered')}
        <div>
          <h3 class="text-sm font-medium text-gray-500 mb-2">Answered Questions</h3>
          <div class="space-y-3">
            {#each questions.filter(q => q.status === 'answered') as q}
              <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                <p class="font-medium text-sm">{q.question}</p>
                <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">{q.answer}</p>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      {#if idea.metadata}
        <div>
          <h3 class="text-sm font-medium text-gray-500 mb-2">Metadata</h3>
          <pre class="text-xs bg-gray-50 dark:bg-gray-700 p-3 rounded-lg overflow-x-auto">{JSON.stringify(idea.metadata, null, 2)}</pre>
        </div>
      {/if}
    </div>

    <div class="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 flex justify-end gap-3">
      <button class="btn btn-danger" on:click={handleReject}>
        Reject
      </button>
      <button class="btn btn-primary" on:click={() => dispatch('approve')}>
        Approve
      </button>
    </div>
  </div>
</div>
