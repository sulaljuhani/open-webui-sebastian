<script lang="ts">
    import { createEventDispatcher, getContext } from 'svelte';
    import { toast } from 'svelte-sonner';
    import Modal from '$lib/components/common/Modal.svelte';
    import XMark from '$lib/components/icons/XMark.svelte';

    const dispatch = createEventDispatcher();
    const i18n = getContext('i18n');

    export let show = false;
    export let selectedDate: Date | null = null;
    export let defaultType: 'event' | 'reminder' = 'event';
    export let backendBaseUrl: string;
    export let getHeaders: () => Record<string, string>;

    let selectedType: 'event' | 'reminder' = defaultType;
    let newEvent = {
        title: '',
        description: '',
        location: '',
        start_time: '',
        end_time: '',
        is_all_day: false
    };
    let newReminder = {
        title: '',
        description: '',
        remind_at: '',
        priority: 1,
        recurrence: 'none'
    };

    $: if (show && selectedDate) {
        // Initialize with selected date
        const startDate = new Date(selectedDate);
        startDate.setHours(9, 0, 0, 0); // Default to 9 AM
        const endDate = new Date(selectedDate);
        endDate.setHours(10, 0, 0, 0); // Default to 10 AM (1 hour duration)

        newEvent = {
            title: '',
            description: '',
            location: '',
            start_time: formatDateTimeLocal(startDate.toISOString()),
            end_time: formatDateTimeLocal(endDate.toISOString()),
            is_all_day: false
        };

        newReminder = {
            title: '',
            description: '',
            remind_at: formatDateTimeLocal(startDate.toISOString()),
            priority: 1,
            recurrence: 'none'
        };

        selectedType = defaultType;
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

    const createEvent = async () => {
        try {
            const payload = {
                title: newEvent.title,
                description: newEvent.description || '',
                location: newEvent.location || '',
                start_time: parseLocalDateTime(newEvent.start_time).toISOString(),
                end_time: parseLocalDateTime(newEvent.end_time).toISOString(),
                is_all_day: newEvent.is_all_day,
                attendees: []
            };

            const response = await fetch(`${backendBaseUrl}/api/events/create`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(error || 'Failed to create event');
            }

            toast.success('Event created successfully');
            dispatch('create');
            show = false;
        } catch (error) {
            console.error('Error creating event:', error);
            toast.error(`Failed to create event: ${error.message}`);
        }
    };

    const createReminder = async () => {
        try {
            const remindAtDate = parseLocalDateTime(newReminder.remind_at);
            if (remindAtDate <= new Date()) {
                toast.error('Remind at time must be in the future');
                return;
            }

            const payload = {
                title: newReminder.title,
                description: newReminder.description || '',
                remind_at: remindAtDate.toISOString(),
                priority: Number(newReminder.priority),
                recurrence: newReminder.recurrence || 'none'
            };

            const response = await fetch(`${backendBaseUrl}/api/reminders/create`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(error || 'Failed to create reminder');
            }

            toast.success('Reminder created successfully');
            dispatch('create', { type: 'reminder' });
            show = false;
        } catch (error) {
            console.error('Error creating reminder:', error);
            toast.error(`Failed to create reminder: ${error.message}`);
        }
    };

    const createItem = async () => {
        if (selectedType === 'reminder') {
            return createReminder();
        }
        return createEvent();
    };
</script>

<Modal size="md" bind:show>
    <div>
        <div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
            <div class="text-lg font-medium self-center">
                {selectedType === 'event' ? $i18n.t('Create Event') : $i18n.t('Create Reminder')}
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

        <form
            class="flex flex-col w-full px-5 py-4"
            on:submit|preventDefault={createItem}
        >
            <div class="space-y-4">
                <div class="flex w-full justify-between items-center">
                    <div class="text-xs font-medium">{$i18n.t('Create')}</div>
                    <div class="flex items-center relative">
                        <select
                            class="dark:bg-gray-900 pr-8 rounded-sm py-2 px-2 text-xs bg-transparent text-right border border-gray-200 dark:border-gray-700 rounded-lg"
                            bind:value={selectedType}
                        >
                            <option value="event">{$i18n.t('Event')}</option>
                            <option value="reminder">{$i18n.t('Reminder')}</option>
                        </select>
                    </div>
                </div>

                <!-- Title -->
                <div>
                    <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                        {$i18n.t('Title')}
                    </label>
                    <input
                        type="text"
                        class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                        value={selectedType === 'event' ? newEvent.title : newReminder.title}
                        on:input={(e) => {
                            if (selectedType === 'event') newEvent.title = e.target.value;
                            else newReminder.title = e.target.value;
                        }}
                        placeholder={selectedType === 'event' ? 'Event title' : 'Reminder title'}
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
                        value={selectedType === 'event' ? newEvent.description : newReminder.description}
                        on:input={(e) => {
                            if (selectedType === 'event') newEvent.description = e.target.value;
                            else newReminder.description = e.target.value;
                        }}
                        placeholder={selectedType === 'event' ? 'Add description...' : 'Add reminder notes...'}
                    />
                </div>

                {#if selectedType === 'event'}
                    <!-- Location -->
                    <div>
                        <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                            {$i18n.t('Location')}
                        </label>
                        <input
                            type="text"
                            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                            bind:value={newEvent.location}
                            placeholder="Add location..."
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
                                bind:value={newEvent.start_time}
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
                                bind:value={newEvent.end_time}
                                required
                            />
                        </div>
                    </div>

                    <!-- All Day Toggle -->
                    <div class="flex items-center">
                        <input
                            type="checkbox"
                            id="create-all-day"
                            class="rounded border-gray-300 dark:border-gray-600"
                            bind:checked={newEvent.is_all_day}
                        />
                        <label for="create-all-day" class="ml-2 text-sm dark:text-gray-200">
                            {$i18n.t('All day event')}
                        </label>
                    </div>

                    <!-- Help text -->
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                        This event will be created locally and can optionally be synced to Google Calendar.
                    </div>
                {:else}
                    <!-- Reminder Date and Time -->
                    <div>
                        <label class="block text-sm font-medium mb-2 dark:text-gray-200">
                            {$i18n.t('Remind At')}
                        </label>
                        <input
                            type="datetime-local"
                            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
                            bind:value={newReminder.remind_at}
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
                                bind:value={newReminder.priority}
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
                                bind:value={newReminder.recurrence}
                            >
                                <option value="none">None</option>
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                                <option value="yearly">Yearly</option>
                            </select>
                        </div>
                    </div>
                {/if}
            </div>

            <!-- Action buttons -->
            <div class="flex justify-end gap-2 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                    type="button"
                    class="px-3.5 py-1.5 text-sm font-medium bg-gray-100 dark:bg-gray-850 text-gray-900 dark:text-gray-100 hover:bg-gray-200 dark:hover:bg-gray-800 transition rounded-full"
                    on:click={() => {
                        show = false;
                    }}
                >
                    {$i18n.t('Cancel')}
                </button>
                <button
                    type="submit"
                    class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
                >
                    {selectedType === 'event' ? $i18n.t('Create Event') : $i18n.t('Create Reminder')}
                </button>
            </div>
        </form>
    </div>
</Modal>
