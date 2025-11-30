<script lang="ts">
    import { getContext, onDestroy, onMount } from 'svelte';
    import { mobile, showSidebar, user } from '$lib/stores';
    import { WEBUI_API_BASE_URL } from '$lib/constants';

    import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
    import Tooltip from '$lib/components/common/Tooltip.svelte';
    import Sidebar from '$lib/components/icons/Sidebar.svelte';
    import Spinner from '$lib/components/common/Spinner.svelte';
    import FullCalendar from '$lib/components/Calendar/FullCalendar.svelte';
    import EventDetailsModal from '$lib/components/Calendar/EventDetailsModal.svelte';
    import CreateEventModal from '$lib/components/Calendar/CreateEventModal.svelte';
    import ReminderDetailsModal from '$lib/components/Calendar/ReminderDetailsModal.svelte';

    const i18n = getContext('i18n');

    let loaded = $state(false);
    const ENV_BACKEND_URL = import.meta.env.VITE_LANGGRAPH_BACKEND_URL;
    let backendBaseUrl = $state('');
    let events = $state([]);
    let reminders = $state([]);
    let showEvents = $state(true);
    let showReminders = $state(true);
    let availableCalendars = $state([]);
    let selectedCalendarIds = $state(new Set());

    // Modal state
    let showEventDetailsModal = $state(false);
    let showReminderDetailsModal = $state(false);
    let showCreateEventModal = $state(false);
    let selectedEvent: any = $state(null);
    let selectedReminder: any = $state(null);
    let selectedDate: Date | null = $state(null);
    let createType = $state<'event' | 'reminder'>('event');

    const getHeaders = () => {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (typeof localStorage !== 'undefined') {
            const apiKey = localStorage.getItem('backend_api_key');
            if (apiKey) headers['X-API-Key'] = apiKey;
        }
        return headers;
    };

    const resolveBackendBaseUrl = () => {
        if (typeof localStorage !== 'undefined') {
            const stored = localStorage.getItem('backend_url');
            if (stored) {
                if (stored.includes('langgraph-agents') && typeof window !== 'undefined') {
                    return `${window.location.protocol}//${window.location.hostname}:8000`;
                }
                return stored;
            }
        }
        if (ENV_BACKEND_URL) {
            if (ENV_BACKEND_URL.includes('langgraph-agents') && typeof window !== 'undefined') {
                return `${window.location.protocol}//${window.location.hostname}:8000`;
            }
            return ENV_BACKEND_URL;
        }
        if (typeof window !== 'undefined') {
            return `${window.location.protocol}//${window.location.hostname}:8000`;
        }
        return 'http://localhost:8000';
    };

    const fetchCalendars = async () => {
        backendBaseUrl = resolveBackendBaseUrl();

        try {
            const response = await fetch(`${backendBaseUrl}/api/calendar/calendars`, {
                method: 'GET',
                headers: getHeaders()
            });

            if (response.ok) {
                const data = await response.json();
                availableCalendars = data.calendars || [];

                // Enable primary calendar by default (also respect Google's "primary" alias)
                if (availableCalendars.length > 0 && selectedCalendarIds.size === 0) {
                    const primaryCal = availableCalendars.find(c => c.primary);
                    if (primaryCal) {
                        selectedCalendarIds = new Set([primaryCal.id, 'primary']);
                    } else {
                        selectedCalendarIds = new Set([availableCalendars[0].id]);
                    }
                }
            }
        } catch (error) {
            console.error('Failed to fetch calendars:', error);
        }
    };

    const toggleCalendar = (calendarId: string) => {
        const newSet = new Set(selectedCalendarIds);
        if (newSet.has(calendarId)) {
            newSet.delete(calendarId);
        } else {
            newSet.add(calendarId);
        }
        selectedCalendarIds = newSet;
    };

    const fetchCalendarData = async () => {
        backendBaseUrl = resolveBackendBaseUrl();

        const opts = { method: 'GET', headers: getHeaders() };

        // Focus on a window around "now" to surface current Google events
        const now = new Date();
        const startWindow = new Date(now.getFullYear(), now.getMonth() - 6, 1);
        const endWindow = new Date(now.getFullYear(), now.getMonth() + 12, 0, 23, 59, 59);
        const eventsUrl = `${backendBaseUrl}/api/events?start_date=${encodeURIComponent(
            startWindow.toISOString()
        )}&end_date=${encodeURIComponent(endWindow.toISOString())}&limit=200`;
        const remindersUrl = `${backendBaseUrl}/api/reminders?is_completed=false&limit=200`;

        // try bounded window first; if backend fails, retry without date filters
        let eventsRes;
        let remindersRes;
        try {
            [eventsRes, remindersRes] = await Promise.allSettled([
                fetch(eventsUrl, opts),
                fetch(remindersUrl, opts)
            ]);
        } catch (e) {
            console.error('Initial calendar fetch failed, retrying without date window', e);
            [eventsRes, remindersRes] = await Promise.allSettled([
                fetch(`${backendBaseUrl}/api/events?limit=200`, opts),
                fetch(remindersUrl, opts)
            ]);
        }

        // Process events
        if (eventsRes.status === 'fulfilled' && eventsRes.value.ok) {
            const rawEvents = await eventsRes.value.json();
            const eventList = Array.isArray(rawEvents) ? rawEvents : rawEvents?.events || [];
            events = eventList || [];
            console.log('Calendar: events fetched', events.length);
            console.log('Calendar: sample event', events[0]);
        } else {
            console.error('Failed to fetch events', eventsRes);
            // retry without filters if first attempt failed with filters
            try {
                const fallback = await fetch(`${backendBaseUrl}/api/events?limit=200`, opts);
                if (fallback.ok) {
                    const rawEvents = await fallback.json();
                    const eventList = Array.isArray(rawEvents) ? rawEvents : rawEvents?.events || [];
                    events = eventList || [];
                    console.log('Calendar: events fetched via fallback', events.length);
                } else {
                    events = [];
                }
            } catch (err) {
                console.error('Fallback events fetch failed', err);
                events = [];
            }
        }

        // Process reminders
        if (remindersRes.status === 'fulfilled' && remindersRes.value.ok) {
            const rawReminders = await remindersRes.value.json();
            reminders = Array.isArray(rawReminders) ? rawReminders : rawReminders?.reminders || [];
            console.log('Calendar: reminders fetched', reminders.length);
            console.log('Calendar: sample reminder', reminders[0]);
        } else {
            console.error('Failed to fetch reminders', remindersRes);
            reminders = [];
        }
    };

    const handleEventClick = (event: any) => {
        console.log('Event clicked:', event);
        const type = event.type || event.extendedProps?.type;

        if (type === 'reminder') {
            const reminder = event.raw || reminders.find((r: any) => r.id === event.id || `reminder-${r.id}` === event.id);
            if (reminder) {
                selectedReminder = {
                    ...reminder,
                    remind_at: reminder.remind_at,
                    is_completed: reminder.is_completed ?? reminder.status === 'completed'
                };
                showReminderDetailsModal = true;
            }
            return;
        }

        // Find the original event data
        const originalEvent = event.raw || events.find((e: any) => e.id === event.id);
        if (originalEvent) {
            selectedEvent = {
                id: originalEvent.id,
                title: originalEvent.title,
                description: originalEvent.description || '',
                location: originalEvent.location || '',
                start_time: originalEvent.start_time,
                end_time: originalEvent.end_time,
                is_all_day: originalEvent.is_all_day,
                source: originalEvent.source || 'manual'
            };
            showEventDetailsModal = true;
        }
    };

    const handleDateClick = (date: Date) => {
        console.log('Date clicked:', date);
        selectedDate = date;
        createType = 'event';
        showCreateEventModal = true;
    };

    const handleEventDrop = async (event: any) => {
        if (event.type === 'reminder') return;

        // Update event times via API
        const response = await fetch(`${backendBaseUrl}/api/events/${event.id}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({
                start_time: event.start.toISOString(),
                end_time: event.end ? event.end.toISOString() : null
            })
        });

        if (!response.ok) {
            throw new Error('Failed to update event');
        }

        await fetchCalendarData();
    };

    const REFRESH_INTERVAL_MS = 60_000;
    let refreshTimer: NodeJS.Timeout | null = null;

    onMount(async () => {
        try {
            await fetchCalendars();
            await fetchCalendarData();

            // Auto-refresh while on page
            refreshTimer = setInterval(() => {
                fetchCalendarData();
            }, REFRESH_INTERVAL_MS);
        } catch (err) {
            console.error('Failed to fetch calendar data', err);
        } finally {
            loaded = true;
        }
    });

    onDestroy(() => {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
    });

    // Map calendar colors (include Google's "primary" alias)
    const getCalendarColorMap = () => {
        const map = new Map(availableCalendars.map(cal => [cal.id, cal.backgroundColor]));
        const primaryCal = availableCalendars.find(cal => cal.primary);
        if (primaryCal) {
            map.set('primary', primaryCal.backgroundColor);
        }
        return map;
    };

    const mappedEvents = $derived.by(() => {
        const calendarColorMap = getCalendarColorMap();
        const safeEvents = Array.isArray(events) ? events : [];
        return safeEvents
            .filter((e: any) => {
                if (e.google_calendar_id && selectedCalendarIds.size > 0) {
                    return selectedCalendarIds.has(e.google_calendar_id);
                }
                return true;
            })
            .map((e: any) => {
                const calendarColor = calendarColorMap.get(e.google_calendar_id) || '#3b82f6';
                const start = e.start_time ? new Date(e.start_time) : null;
                const end = e.end_time ? new Date(e.end_time) : null;
                return {
                    id: e.id,
                    title: e.title,
                    start,
                    end,
                    allDay: e.is_all_day,
                    backgroundColor: calendarColor,
                    borderColor: calendarColor,
                    extendedProps: {
                        description: e.description,
                        location: e.location,
                        type: 'event',
                        calendarId: e.google_calendar_id,
                        source: e.source,
                        raw: e
                    }
                };
            });
    });

    const mappedReminders = $derived.by(() => {
        const safeReminders = Array.isArray(reminders) ? reminders : [];
        return safeReminders
            .filter((r: any) => {
                const status = r.status ?? (r.is_completed ? 'completed' : 'pending');
                return status === 'pending';
            })
            .map((r: any) => ({
                id: `reminder-${r.id}`,
                title: `⏰ ${r.title}`,
                start: r.remind_at ? new Date(r.remind_at) : null,
                allDay: false,
                backgroundColor: '#f59e0b',
                borderColor: '#d97706',
                editable: false,
                extendedProps: {
                    description: r.description,
                    type: 'reminder',
                    raw: r
                }
            }));
    });

    // Combined events + reminders with toggles (guard against non-iterables)
    let allCalendarItems = $derived.by(() => {
        const items: any[] = [];
        if (showEvents && Array.isArray(mappedEvents)) {
            items.push(...mappedEvents);
        }
        if (showReminders && Array.isArray(mappedReminders)) {
            items.push(...mappedReminders);
        }
        console.log('Calendar: combined items', items.length);
        return items;
    });
</script>

{#if loaded}
    <div class="flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar ? 'md:max-w-[calc(100%-260px)]' : ''} max-w-full">
        <!-- Header (same as tasks page) -->
        <nav class="px-2 pt-1.5 backdrop-blur-xl w-full drag-region">
            <div class="flex items-center">
                {#if $mobile}
                    <div class="{$showSidebar ? 'md:hidden' : ''} flex flex-none items-center">
                        <Tooltip
                            content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
                            interactive={true}
                        >
                            <button
                                id="sidebar-toggle-button"
                                class="cursor-pointer flex rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850 transition"
                                onclick={() => showSidebar.set(!$showSidebar)}
                            >
                                <div class="self-center p-1.5">
                                    <Sidebar />
                                </div>
                            </button>
                        </Tooltip>
                    </div>
                {/if}

                <div class="ml-2 py-0.5 self-center flex items-center justify-between w-full">
                    <div class="">
                        <div
                            class="flex gap-1 scrollbar-none overflow-x-auto w-fit text-center text-sm font-medium bg-transparent py-1 touch-auto pointer-events-auto"
                        >
                            <a class="min-w-fit transition" href="/calendar">
                                {$i18n.t('Calendar')}
                            </a>
                        </div>
                    </div>

                    <div class="self-center flex items-center gap-1">
                        {#if $user !== undefined && $user !== null}
                            <UserMenu className="max-w-[240px]" role={$user?.role} help={true}>
                                <button
                                    class="select-none flex rounded-xl p-1.5 w-full hover:bg-gray-50 dark:hover:bg-gray-850 transition"
                                    aria-label="User Menu"
                                >
                                    <div class="self-center">
                                        <img
                                            src={`${WEBUI_API_BASE_URL}/users/${$user?.id}/profile/image`}
                                            class="size-6 object-cover rounded-full"
                                            alt="User profile"
                                            draggable="false"
                                        />
                                    </div>
                                </button>
                            </UserMenu>
                        {/if}
                    </div>
                </div>
            </div>
        </nav>

        <div class="pb-1 flex-1 max-h-full overflow-y-auto @container p-6">
            <div class="max-w-7xl mx-auto">
                <div class="flex flex-col gap-3 mb-4">
                    <div class="flex items-center gap-2 flex-wrap">
                        <button
                            class={`px-3.5 py-1.5 text-sm font-medium rounded-full border transition ${
                                showEvents
                                    ? 'bg-black text-white dark:bg-white dark:text-black border-transparent'
                                    : 'bg-gray-100 dark:bg-gray-850 text-gray-900 dark:text-gray-100 border-gray-200 dark:border-gray-700 hover:bg-gray-200 dark:hover:bg-gray-800'
                            }`}
                            onclick={() => (showEvents = !showEvents)}
                        >
                            Events
                        </button>
                        <button
                            class={`px-3.5 py-1.5 text-sm font-medium rounded-full border transition ${
                                showReminders
                                    ? 'bg-black text-white dark:bg-white dark:text-black border-transparent'
                                    : 'bg-gray-100 dark:bg-gray-850 text-gray-900 dark:text-gray-100 border-gray-200 dark:border-gray-700 hover:bg-gray-200 dark:hover:bg-gray-800'
                            }`}
                            onclick={() => (showReminders = !showReminders)}
                        >
                            Reminders
                        </button>
                    </div>
                </div>

                <!-- Calendar Selector -->
                {#if availableCalendars.length > 1}
                    <div class="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div class="text-sm font-medium mb-2 dark:text-gray-200">
                            {$i18n.t('Calendars')}
                        </div>
                        <div class="flex flex-wrap gap-2">
                            {#each availableCalendars as calendar (calendar.id)}
                                <button
                                    class="px-3 py-1.5 text-xs rounded-lg transition flex items-center gap-2 {selectedCalendarIds.has(calendar.id) ? 'opacity-100' : 'opacity-50 hover:opacity-75'}"
                                    style="background-color: {calendar.backgroundColor}; color: {calendar.foregroundColor}"
                                    onclick={() => toggleCalendar(calendar.id)}
                                >
                                    <span class="inline-block w-2 h-2 rounded-full bg-white"></span>
                                    {calendar.name}
                                    {#if calendar.primary}
                                        <span class="text-xs opacity-75">(Primary)</span>
                                    {/if}
                                </button>
                            {/each}
                        </div>
                    </div>
                {/if}

                <!-- FullCalendar Component -->
                <FullCalendar
                    events={allCalendarItems}
                    onEventClick={handleEventClick}
                    onDateClick={handleDateClick}
                    onEventDrop={handleEventDrop}
                />
            </div>
        </div>
    </div>

    <!-- Event Details Modal -->
    {#if showEventDetailsModal && selectedEvent}
        <EventDetailsModal
            bind:show={showEventDetailsModal}
            bind:event={selectedEvent}
            {backendBaseUrl}
            {getHeaders}
            on:save={fetchCalendarData}
            on:delete={fetchCalendarData}
        />
    {/if}

    {#if showReminderDetailsModal && selectedReminder}
        <ReminderDetailsModal
            bind:show={showReminderDetailsModal}
            bind:reminder={selectedReminder}
            {backendBaseUrl}
            {getHeaders}
            on:save={fetchCalendarData}
            on:delete={fetchCalendarData}
        />
    {/if}

    <!-- Create Event Modal -->
    {#if showCreateEventModal}
        <CreateEventModal
            bind:show={showCreateEventModal}
            bind:selectedDate
            defaultType={createType}
            {backendBaseUrl}
            {getHeaders}
            on:create={fetchCalendarData}
        />
    {/if}
{:else}
    <div class="flex items-center justify-center h-screen">
        <Spinner className="size-8" />
    </div>
{/if}
