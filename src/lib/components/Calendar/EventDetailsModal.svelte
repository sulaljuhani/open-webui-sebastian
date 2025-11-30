<script lang="ts">
    import { createEventDispatcher, getContext } from 'svelte';
    import { toast } from 'svelte-sonner';
    import Modal from '$lib/components/common/Modal.svelte';
    import XMark from '$lib/components/icons/XMark.svelte';

    const dispatch = createEventDispatcher();
    const i18n = getContext('i18n');

    export let show = false;
    export let event: any = null;
    export let backendBaseUrl: string;
    export let getHeaders: () => Record<string, string>;

    let editedEvent = { ...event };

    $: if (show && event) {
        editedEvent = { ...event };
    }

    const formatDateTimeLocal = (dateStr: string) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        // Format for datetime-local input: YYYY-MM-DDTHH:mm
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

    const saveEvent = async () => {
        try {
            const payload = {
                title: editedEvent.title,
                description: editedEvent.description || '',
                location: editedEvent.location || '',
                start_time: editedEvent.start_time,
                end_time: editedEvent.end_time,
                is_all_day: editedEvent.is_all_day || false
            };

            const response = await fetch(`${backendBaseUrl}/api/events/${event.id}`, {
                method: 'PUT',
                headers: getHeaders(),
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(error || 'Failed to update event');
            }

            toast.success('Event updated successfully');
            dispatch('save');
            show = false;
        } catch (error) {
            console.error('Error updating event:', error);
            toast.error(`Failed to update event: ${error.message}`);
        }
    };

    const deleteEvent = async () => {
        if (!confirm('Are you sure you want to delete this event?')) {
            return;
        }

        try {
            const response = await fetch(`${backendBaseUrl}/api/events/${event.id}`, {
                method: 'DELETE',
                headers: getHeaders()
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(error || 'Failed to delete event');
            }

            toast.success('Event deleted successfully');
            dispatch('delete');
            show = false;
        } catch (error) {
            console.error('Error deleting event:', error);
            toast.error(`Failed to delete event: ${error.message}`);
        }
    };
</script>

<Modal size="md" bind:show>
    <div>
        <div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
            <div class="text-lg font-medium self-center">
                {$i18n.t('Event Details')}
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

        {#if editedEvent}
            <form
                class="flex flex-col w-full px-5 py-4"
                on:submit|preventDefault={saveEvent}
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
                            bind:value={editedEvent.title}
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
                            bind:value={editedEvent.description}
                        />
                    </div>

                    <!-- Location -->
                    <div>
                        <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                            {$i18n.t('Location')}
                        </label>
                        <input
                            type="text"
                            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                            bind:value={editedEvent.location}
                        />
                    </div>

                    <!-- Date and Time -->
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                                {$i18n.t('Start')}
                            </label>
                            <input
                                type="datetime-local"
                                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                                value={formatDateTimeLocal(editedEvent.start_time)}
                                on:change={(e) => {
                                    editedEvent.start_time = parseLocalDateTime(e.target.value).toISOString();
                                }}
                                required
                            />
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                                {$i18n.t('End')}
                            </label>
                            <input
                                type="datetime-local"
                                class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                                value={formatDateTimeLocal(editedEvent.end_time)}
                                on:change={(e) => {
                                    editedEvent.end_time = parseLocalDateTime(e.target.value).toISOString();
                                }}
                                required
                            />
                        </div>
                    </div>

                    <!-- All Day Toggle -->
                    <div class="flex items-center">
                        <input
                            type="checkbox"
                            id="all-day"
                            class="rounded border-gray-300 dark:border-gray-600"
                            bind:checked={editedEvent.is_all_day}
                        />
                        <label for="all-day" class="ml-2 text-sm dark:text-gray-200">
                            {$i18n.t('All day event')}
                        </label>
                    </div>

                    <!-- Source indicator (read-only) -->
                    {#if editedEvent.source === 'google'}
                        <div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
                            <span class="inline-block w-2 h-2 rounded-full bg-blue-500"></span>
                            Synced from Google Calendar
                        </div>
                    {/if}
                </div>

                <!-- Action buttons -->
                <div class="flex justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <button
                        type="button"
                        class="px-4 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700 transition"
                        on:click={deleteEvent}
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
