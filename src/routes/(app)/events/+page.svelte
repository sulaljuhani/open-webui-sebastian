<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { mobile, showSidebar, user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	let loaded = false;
	let events = [];
	let backendBaseUrl = 'http://langgraph-agents:8000';

	interface Event {
		id: string;
		title: string;
		description?: string;
		start_time: string;
		end_time?: string;
		location?: string;
		created_at: string;
	}

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
			// Show demo data
			events = [
				{
					id: '1',
					title: 'Team Meeting',
					description: 'Weekly sync with the team',
					start_time: new Date(Date.now() + 86400000).toISOString(),
					location: 'Conference Room A',
					created_at: new Date().toISOString()
				},
				{
					id: '2',
					title: 'Doctor Appointment',
					description: 'Annual checkup',
					start_time: new Date(Date.now() + 172800000).toISOString(),
					location: 'Medical Center',
					created_at: new Date().toISOString()
				}
			];
		}
	};

	const formatDate = (dateString: string) => {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			weekday: 'short',
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	};

	const formatTime = (dateString: string) => {
		const date = new Date(dateString);
		return date.toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit'
		});
	};

	const isToday = (dateString: string) => {
		const date = new Date(dateString);
		const today = new Date();
		return (
			date.getDate() === today.getDate() &&
			date.getMonth() === today.getMonth() &&
			date.getFullYear() === today.getFullYear()
		);
	};

	const isPast = (dateString: string) => {
		return new Date(dateString) < new Date();
	};

	const groupedEvents = () => {
		const sorted = [...events].sort(
			(a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
		);

		const upcoming = sorted.filter((e) => !isPast(e.start_time));
		const past = sorted.filter((e) => isPast(e.start_time));

		return { upcoming, past };
	};

	onMount(async () => {
		await fetchEvents();
		loaded = true;
	});

	$: grouped = groupedEvents();
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
								on:click={() => {
									showSidebar.set(!$showSidebar);
								}}
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
							<a class="min-w-fit transition" href="/events">
								{$i18n.t('Events')}
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
			<div class="max-w-4xl mx-auto">
				<!-- Header -->
				<div class="mb-6">
					<h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">Events</h1>
					<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
						Upcoming and past events
					</p>
				</div>

				<!-- Upcoming Events -->
				{#if grouped.upcoming.length > 0}
					<div class="mb-8">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
							Upcoming Events ({grouped.upcoming.length})
						</h2>
						<div class="space-y-3">
							{#each grouped.upcoming as event (event.id)}
								<div
									class="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-4 hover:shadow-md transition"
								>
									<div class="flex gap-4">
										<!-- Date Badge -->
										<div
											class="flex-shrink-0 w-16 h-16 rounded-lg flex flex-col items-center justify-center {isToday(
												event.start_time
											)
												? 'bg-blue-500 text-white'
												: 'bg-gray-100 dark:bg-gray-800'}"
										>
											<div class="text-xs font-medium {isToday(event.start_time) ? '' : 'text-gray-600 dark:text-gray-400'}">
												{new Date(event.start_time).toLocaleDateString('en-US', { month: 'short' })}
											</div>
											<div class="text-2xl font-bold {isToday(event.start_time) ? '' : 'text-gray-900 dark:text-gray-100'}">
												{new Date(event.start_time).getDate()}
											</div>
										</div>

										<!-- Event Details -->
										<div class="flex-1 min-w-0">
											<h3 class="text-base font-semibold text-gray-900 dark:text-gray-100">
												{event.title}
												{#if isToday(event.start_time)}
													<span class="ml-2 text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
														Today
													</span>
												{/if}
											</h3>
											{#if event.description}
												<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
													{event.description}
												</p>
											{/if}
											<div class="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-600 dark:text-gray-400">
												<span>🕐 {formatTime(event.start_time)}</span>
												{#if event.location}
													<span>📍 {event.location}</span>
												{/if}
											</div>
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Past Events -->
				{#if grouped.past.length > 0}
					<div>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
							Past Events ({grouped.past.length})
						</h2>
						<div class="space-y-3 opacity-60">
							{#each grouped.past as event (event.id)}
								<div
									class="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-4"
								>
									<div class="flex gap-4">
										<!-- Date Badge -->
										<div
											class="flex-shrink-0 w-16 h-16 rounded-lg bg-gray-100 dark:bg-gray-800 flex flex-col items-center justify-center"
										>
											<div class="text-xs font-medium text-gray-600 dark:text-gray-400">
												{new Date(event.start_time).toLocaleDateString('en-US', { month: 'short' })}
											</div>
											<div class="text-2xl font-bold text-gray-900 dark:text-gray-100">
												{new Date(event.start_time).getDate()}
											</div>
										</div>

										<!-- Event Details -->
										<div class="flex-1 min-w-0">
											<h3 class="text-base font-semibold text-gray-900 dark:text-gray-100">
												{event.title}
											</h3>
											{#if event.description}
												<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
													{event.description}
												</p>
											{/if}
											<div class="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-600 dark:text-gray-400">
												<span>🕐 {formatDate(event.start_time)} at {formatTime(event.start_time)}</span>
												{#if event.location}
													<span>📍 {event.location}</span>
												{/if}
											</div>
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				{#if events.length === 0}
					<div class="text-center py-12 text-gray-500 dark:text-gray-500">
						No events found. Ask Sebastian to create some events for you!
					</div>
				{/if}

				<!-- Info message -->
				<div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
					<p class="text-sm text-blue-800 dark:text-blue-300">
						📆 Events view is ready! Schedule events by chatting with Sebastian.
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
