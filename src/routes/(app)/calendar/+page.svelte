<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { mobile, showSidebar, user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	let loaded = $state(false);
	let events = $state([]);
	let currentDate = new Date();
	let currentMonth = $state(currentDate.getMonth());
	let currentYear = $state(currentDate.getFullYear());
	let calendarDays = $state([]);
	let backendBaseUrl = $state('http://langgraph-agents:8000');

	// Derived state for events by date
	let eventsByDate = $derived(
		(events || []).reduce((acc, event) => {
			const key = event.start_time?.slice(0, 10);
			if (key) {
				acc[key] = acc[key] ? [...acc[key], event] : [event];
			}
			return acc;
		}, {} as Record<string, any[]>)
	);

	const monthNames = [
		'January', 'February', 'March', 'April', 'May', 'June',
		'July', 'August', 'September', 'October', 'November', 'December'
	];

	const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

	const generateCalendar = () => {
		const firstDay = new Date(currentYear, currentMonth, 1);
		const lastDay = new Date(currentYear, currentMonth + 1, 0);
		const prevLastDay = new Date(currentYear, currentMonth, 0);

		const firstDayIndex = firstDay.getDay();
		const lastDayDate = lastDay.getDate();
		const prevLastDayDate = prevLastDay.getDate();

		calendarDays = [];

		// Previous month days
		for (let i = firstDayIndex; i > 0; i--) {
			calendarDays.push({
				day: prevLastDayDate - i + 1,
				isCurrentMonth: false,
				date: new Date(currentYear, currentMonth - 1, prevLastDayDate - i + 1)
			});
		}

		// Current month days
		for (let i = 1; i <= lastDayDate; i++) {
			calendarDays.push({
				day: i,
				isCurrentMonth: true,
				isToday:
					i === currentDate.getDate() &&
					currentMonth === new Date().getMonth() &&
					currentYear === new Date().getFullYear(),
				date: new Date(currentYear, currentMonth, i)
			});
		}

		// Next month days
		const remainingDays = 42 - calendarDays.length; // 6 rows * 7 days
		for (let i = 1; i <= remainingDays; i++) {
			calendarDays.push({
				day: i,
				isCurrentMonth: false,
				date: new Date(currentYear, currentMonth + 1, i)
			});
		}
	};

	const getHeaders = () => {
		const headers: Record<string, string> = { 'Content-Type': 'application/json' };
		if (typeof localStorage !== 'undefined') {
			const apiKey = localStorage.getItem('backend_api_key');
			if (apiKey) headers['X-API-Key'] = apiKey;
		}
		return headers;
	};

	const fetchEvents = async () => {
		if (typeof localStorage !== 'undefined') {
			backendBaseUrl = localStorage.getItem('backend_url') || backendBaseUrl;
		}

		try {
			const response = await fetch(`${backendBaseUrl}/api/events`, {
				method: 'GET',
				headers: getHeaders()
			});

			if (response.ok) {
				const data = await response.json();
				events = data.events || [];
			}
		} catch (error) {
			console.error('Failed to fetch events:', error);
		}
	};

	const previousMonth = () => {
		currentMonth--;
		if (currentMonth < 0) {
			currentMonth = 11;
			currentYear--;
		}
		generateCalendar();
	};

	const nextMonth = () => {
		currentMonth++;
		if (currentMonth > 11) {
			currentMonth = 0;
			currentYear++;
		}
		generateCalendar();
	};

	const goToToday = () => {
		const today = new Date();
		currentMonth = today.getMonth();
		currentYear = today.getFullYear();
		generateCalendar();
	};

	const eventsForDate = (date: Date) => {
		const key = date.toISOString().slice(0, 10);
		return eventsByDate[key] || [];
	};

	onMount(async () => {
		generateCalendar();
		await fetchEvents();
		loaded = true;
	});
</script>

{#if loaded}
	<div
		class="flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
			? 'md:max-w-[calc(100%-260px)]'
			: ''} max-w-full"
	>
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
				<!-- Calendar Header -->
				<div class="flex items-center justify-between mb-6">
					<h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">
						{monthNames[currentMonth]}
						{currentYear}
					</h1>
					<div class="flex gap-2">
						<button
							class="px-3 py-1.5 text-sm rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition"
							onclick={goToToday}
						>
							Today
						</button>
						<button
							class="px-3 py-1.5 text-sm rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition"
							onclick={previousMonth}
						>
							←
						</button>
						<button
							class="px-3 py-1.5 text-sm rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition"
							onclick={nextMonth}
						>
							→
						</button>
					</div>
				</div>

				<!-- Calendar Grid -->
				<div class="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800">
					<!-- Day Names -->
					<div class="grid grid-cols-7 gap-px bg-gray-200 dark:bg-gray-800 rounded-t-lg overflow-hidden">
						{#each dayNames as dayName}
							<div class="bg-white dark:bg-gray-900 p-3 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
								{dayName}
							</div>
						{/each}
					</div>

					<!-- Calendar Days -->
					<div class="grid grid-cols-7 gap-px bg-gray-200 dark:bg-gray-800 rounded-b-lg overflow-hidden">
						{#each calendarDays as { day, isCurrentMonth, isToday, date }}
							<div
								class="bg-white dark:bg-gray-900 min-h-[100px] p-2 {isCurrentMonth
									? 'text-gray-900 dark:text-gray-100'
									: 'text-gray-400 dark:text-gray-600'} {isToday
									? 'ring-2 ring-blue-500 ring-inset'
									: ''} hover:bg-gray-50 dark:hover:bg-gray-850 transition cursor-pointer"
							>
								<div class="text-sm font-medium mb-1 {isToday ? 'text-blue-600 dark:text-blue-400' : ''}">
									{day}
								</div>
								{#if eventsForDate(date).length}
									<div class="mt-1 space-y-1">
										{#each eventsForDate(date).slice(0, 3) as event (event.id)}
											<div class="text-xs px-2 py-1 rounded-md bg-blue-50 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 truncate">
												{event.title}
											</div>
										{/each}
										{#if eventsForDate(date).length > 3}
											<div class="text-[11px] text-blue-500 dark:text-blue-300">
												+{eventsForDate(date).length - 3} more
											</div>
										{/if}
									</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>

				<!-- Info message -->
				<div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
					<p class="text-sm text-blue-800 dark:text-blue-300">
						📅 Calendar view is ready! Events from your backend will appear here.
					</p>
				</div>
			</div>
		</div>
	</div>
{:else}
	<div class="flex items-center justify-center h-screen">
		<Spinner className="size-8" />
	</div>
{/if}
