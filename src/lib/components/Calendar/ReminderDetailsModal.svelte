<script lang="ts">
    import { createEventDispatcher, getContext } from 'svelte';
    import { toast } from 'svelte-sonner';
    import Modal from '$lib/components/common/Modal.svelte';
    import XMark from '$lib/components/icons/XMark.svelte';

    const dispatch = createEventDispatcher();
    const i18n = getContext('i18n');

    export let show = false;
    export let reminder: any = null;
    export let backendBaseUrl: string;
    export let getHeaders: () => Record<string, string>;

    let editedReminder = { ...reminder };

    $: if (show && reminder) {
        editedReminder = { ...reminder };
    }

    const formatDateTimeLocal = (dateStr: string) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    };

    const parseLocalDateTime = (localDateStr: string) => {
        if (!localDateStr) return new Date();
        return new Date(localDateStr);
    };

    const saveReminder = async () => {
        try {
            const payload = {
                title: editedReminder.title,
                description: editedReminder.description || '',
                remind_at: parseLocalDateTime(editedReminder.remind_at).toISOString(),
                priority: Number(editedReminder.priority ?? 1),
                recurrence: editedReminder.recurrence || 'none',
                is_completed: !!editedReminder.is_completed
            };

            const response = await fetch(`${backendBaseUrl}/api/reminders/${reminder.id}`, {
                method: 'PUT',
                headers: getHeaders(),
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(error || 'Failed to update reminder');
            }

            toast.success('Reminder updated successfully');
            dispatch('save');
            show = false;
        } catch (error) {
            console.error('Error updating reminder:', error);
            toast.error(`Failed to update reminder: ${error.message}`);
        }
    };

    const deleteReminder = async () => {
        if (!confirm('Are you sure you want to delete this reminder?')) {
            return;
        }

        try {
            const response = await fetch(`${backendBaseUrl}/api/reminders/${reminder.id}`, {
                method: 'DELETE',
                headers: getHeaders()
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(error || 'Failed to delete reminder');
            }

            toast.success('Reminder deleted successfully');
            dispatch('delete');
            show = false;
        } catch (error) {
            console.error('Error deleting reminder:', error);
            toast.error(`Failed to delete reminder: ${error.message}`);
        }
    };
</script>

<Modal size="md" bind:show>
    <div>
        <div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
            <div class="text-lg font-medium self-center">
                {$i18n.t('Reminder Details')}
            </div>
            <button
                class="self-center"
                on:click={() => {
                    show = false;
                }}
            >
                <XMark className="size-5" />
            </button>
        </div>

        {#if editedReminder}
            <form
                class="flex flex-col w-full px-5 py-4"
                on:submit|preventDefault={saveReminder}
            >
                <div class="space-y-4">
                    <!-- Title -->
                    <div>
                        <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                            {$i18n.t('Title')}
                        </label>
                        <input
                            type="text"
                            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                            bind:value={editedReminder.title}
                            required
                        />
                    </div>

                    <!-- Description -->
                    <div>
                        <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                            {$i18n.t('Description')}
                        </label>
                        <textarea
                            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                            rows="3"
                            bind:value={editedReminder.description}
                        />
                    </div>

                    <!-- Remind At -->
                    <div>
                        <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                            {$i18n.t('Remind At')}
                        </label>
                        <input
                            type="datetime-local"
                            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                            value={formatDateTimeLocal(editedReminder.remind_at)}
                            on:change={(e) => {
                                editedReminder.remind_at = parseLocalDateTime(e.target.value).toISOString();
                            }}
                            required
                        />
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                                {$i18n.t('Priority')}
                            </label>
                            <select
                                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                                bind:value={editedReminder.priority}
                            >
                                <option value="0">Low</option>
                                <option value="1">Medium</option>
                                <option value="2">High</option>
                                <option value="3">Urgent</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                                {$i18n.t('Recurrence')}
                            </label>
                            <select
                                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                                bind:value={editedReminder.recurrence}
                            >
                                <option value="none">None</option>
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                                <option value="yearly">Yearly</option>
                            </select>
                        </div>
                    </div>

                    <div class="flex items-center">
                        <input
                            type="checkbox"
                            id="reminder-completed"
                            class="rounded border-gray-300 dark:border-gray-600"
                            bind:checked={editedReminder.is_completed}
                        />
                        <label for="reminder-completed" class="ml-2 text-sm dark:text-gray-200">
                            {$i18n.t('Mark as completed')}
                        </label>
                    </div>
                </div>

                <!-- Action buttons -->
                <div class="flex justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <button
                        type="button"
                        class="px-4 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700 transition"
                        on:click={deleteReminder}
                    >
                        {$i18n.t('Delete')}
                    </button>
                    <div class="flex gap-2">
                        <button
                            type="button"
                            class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
                            on:click={() => {
                                show = false;
                            }}
                        >
                            {$i18n.t('Cancel')}
                        </button>
                        <button
                            type="submit"
                            class="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
                        >
                            {$i18n.t('Save')}
                        </button>
                    </div>
                </div>
            </form>
        {/if}
    </div>
</Modal>
