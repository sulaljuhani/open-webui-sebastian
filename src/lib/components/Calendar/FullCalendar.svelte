<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { Calendar } from '@fullcalendar/core';
    import dayGridPlugin from '@fullcalendar/daygrid';
    import timeGridPlugin from '@fullcalendar/timegrid';
    import interactionPlugin from '@fullcalendar/interaction';
    import listPlugin from '@fullcalendar/list';

    type CalendarEvent = {
        id: string;
        title: string;
        start: string | Date | null;
        end?: string | Date | null;
        allDay?: boolean;
        backgroundColor?: string;
        borderColor?: string;
        extendedProps?: {
            description?: string;
            location?: string;
            type: 'event' | 'reminder';
        };
    };

    let {
        events = [] as CalendarEvent[],
        onEventClick = undefined as ((event: any) => void) | undefined,
        onDateClick = undefined as ((date: Date) => void) | undefined,
        onEventDrop = undefined as ((event: any) => Promise<void>) | undefined,
    } = $props();

    let calendarEl: HTMLElement;
    let calendar: Calendar;

    onMount(() => {
        calendar = new Calendar(calendarEl, {
            plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin],

            // Initial view
            initialView: 'dayGridMonth',

            // Header toolbar
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
            },

            // Event handling
            events: events,
            editable: true,
            droppable: true,

            // Callbacks
            eventClick: (info) => {
                if (onEventClick) {
                    onEventClick({
                        id: info.event.id,
                        title: info.event.title,
                        start: info.event.start,
                        end: info.event.end,
                        allDay: info.event.allDay,
                        extendedProps: info.event.extendedProps,
                        ...info.event.extendedProps
                    });
                }
            },

            dateClick: (info) => {
                if (onDateClick) {
                    onDateClick(info.date);
                }
            },

            eventDrop: async (info) => {
                if (onEventDrop) {
                    try {
                        await onEventDrop({
                            id: info.event.id,
                            start: info.event.start,
                            end: info.event.end,
                            type: info.event.extendedProps?.type,
                            extendedProps: info.event.extendedProps
                        });
                    } catch (error) {
                        info.revert();
                        console.error('Failed to update event:', error);
                    }
                }
            },

            // Appearance
            height: 'auto',
            themeSystem: 'standard',

            // Time format
            eventTimeFormat: {
                hour: '2-digit',
                minute: '2-digit',
                meridiem: 'short'
            }
        });

        calendar.render();
    });

    // Update events when they change
    $effect(() => {
        if (calendar && events) {
            const count = Array.isArray(events) ? events.length : 'n/a';
            console.log('FullCalendar: rendering events', count);
            if (Array.isArray(events) && events.length > 0) {
                console.log('FullCalendar: first event', events[0]);
            }
            calendar.removeAllEvents();
            calendar.addEventSource(events);
        }
    });

    onDestroy(() => {
        if (calendar) {
            calendar.destroy();
        }
    });
</script>

<div bind:this={calendarEl} class="fullcalendar-container"></div>

<style>
    .fullcalendar-container {
        padding: 1rem;
    }

    /* Dark mode support */
    :global(.dark) .fullcalendar-container {
        --fc-border-color: #374151;
        --fc-button-bg-color: #1f2937;
        --fc-button-border-color: #374151;
        --fc-button-hover-bg-color: #374151;
        --fc-button-hover-border-color: #4b5563;
        --fc-button-active-bg-color: #4b5563;
        --fc-button-active-border-color: #6b7280;
        --fc-event-bg-color: #3b82f6;
        --fc-event-border-color: #2563eb;
        --fc-event-text-color: #ffffff;
        --fc-page-bg-color: transparent;
        --fc-neutral-bg-color: #1f2937;
        --fc-neutral-text-color: #e5e7eb;
        --fc-list-event-hover-bg-color: #374151;
    }
</style>
