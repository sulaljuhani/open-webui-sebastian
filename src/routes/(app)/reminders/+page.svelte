<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { mobile, showSidebar, user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import ClockRotateRight from '$lib/components/icons/ClockRotateRight.svelte';

	const i18n = getContext('i18n');

	let loaded = $state(false);
	let reminders = $state<Reminder[]>([]);
	let backendBaseUrl = $state('http://langgraph-agents:8000');

	interface Reminder {
		id: string;
		title: string;
		description?: string;
		remind_at: string;
		priority: number;
		recurrence?: string;
		is_completed?: boolean;
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

	const fetchReminders = async () => {
		if (typeof localStorage !== 'undefined') {
			backendBaseUrl = localStorage.getItem('backend_url') || backendBaseUrl;
		}

		try {
			const response = await fetch(`${backendBaseUrl}/api/reminders`, {
				method: 'GET',
				headers: getHeaders()
			});

			if (response.ok) {
				const data = await response.json();
				reminders = data.reminders || [];
			}
		} catch (error) {
			console.error('Failed to fetch reminders:', error);
			// Show demo data
			reminders = [
				{
					id: '1',
					title: 'Take medication',
					description: 'Morning dose',
					remind_at: new Date(Date.now() + 3600000).toISOString(),
					priority: 2,
					is_completed: false,
					created_at: new Date().toISOString()
				},
				{
					id: '2',
					title: 'Call mom',
					remind_at: new Date(Date.now() + 7200000).toISOString(),
					priority: 1,
					is_completed: false,
					created_at: new Date().toISOString()
				}
			];
		}
	};

	const dismissReminder = async (reminderId: string) => {
		try {
			await fetch(`${backendBaseUrl}/api/reminders/${reminderId}`, {
				method: 'PUT',
				headers: getHeaders(),
				body: JSON.stringify({ is_completed: true })
			});
			await fetchReminders();
		} catch (error) {
			console.error('Failed to dismiss reminder:', error);
		}
	};

	const snoozeReminder = async (reminderId: string, minutes = 30) => {
		const reminder = reminders.find((r) => r.id === reminderId);
		if (!reminder) return;

		const newTime = new Date(reminder.remind_at);
		newTime.setMinutes(newTime.getMinutes() + minutes);

		try {
			await fetch(`${backendBaseUrl}/api/reminders/${reminderId}`, {
				method: 'PUT',
				headers: getHeaders(),
				body: JSON.stringify({ remind_at: newTime.toISOString() })
			});
			await fetchReminders();
		} catch (error) {
			console.error('Failed to snooze reminder:', error);
		}
	};

	const formatRelativeTime = (dateString: string) => {
		const now = new Date();
		const reminderTime = new Date(dateString);
		const diffMs = reminderTime.getTime() - now.getTime();
		const diffMins = Math.round(diffMs / 60000);

		if (diffMins < 0) {
			return 'Overdue';
		} else if (diffMins < 60) {
			return `in ${diffMins} min${diffMins !== 1 ? 's' : ''}`;
		} else if (diffMins < 1440) {
			const hours = Math.floor(diffMins / 60);
			return `in ${hours} hour${hours !== 1 ? 's' : ''}`;
		} else {
			const days = Math.floor(diffMins / 1440);
			return `in ${days} day${days !== 1 ? 's' : ''}`;
		}
	};

	const formatTime = (dateString: string) => {
		const date = new Date(dateString);
		return date.toLocaleString('en-US', {
			month: 'short',
			day: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		});
	};

	const getPriorityColor = (priority: number) => {
		switch (priority) {
			case 3:
				return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-300 dark:border-red-800';
			case 2:
				return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-300 dark:border-yellow-800';
			case 1:
				return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-300 dark:border-blue-800';
			case 0:
				return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-300 dark:border-green-800';
			default:
				return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400 border-gray-300 dark:border-gray-700';
		}
	};

	const getPriorityLabel = (priority: number) => {
		switch (priority) {
			case 3:
				return 'Urgent';
			case 2:
				return 'High';
			case 1:
				return 'Medium';
			case 0:
				return 'Low';
			default:
				return 'Unspecified';
		}
	};

	const isOverdue = (dateString: string) => {
		return new Date(dateString) < new Date();
	};

	onMount(async () => {
		await fetchReminders();
		loaded = true;

		// Refresh every minute to update relative times
		const interval = setInterval(async () => {
			await fetchReminders();
		}, 60000);

		return () => clearInterval(interval);
	});

	$: sortedReminders = [...reminders].sort(
		(a, b) => new Date(a.remind_at).getTime() - new Date(b.remind_at).getTime()
	);
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
							<a class="min-w-fit transition" href="/reminders">
								{$i18n.t('Reminders')}
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
					<h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">Reminders</h1>
					<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
						Time-sensitive notifications and alerts
					</p>
				</div>

				<!-- Reminders List -->
				<div class="space-y-3">
					{#each sortedReminders as reminder (reminder.id)}
						<div
							class="bg-white dark:bg-gray-900 rounded-lg shadow-sm border-2 {getPriorityColor(
								reminder.priority
							)} p-4 hover:shadow-md transition"
						>
							<div class="flex items-start gap-3">
								<!-- Icon -->
								<div class="flex-shrink-0 mt-0.5">
									<ClockRotateRight className="size-5 text-current" />
								</div>

								<!-- Content -->
								<div class="flex-1 min-w-0">
									<h3 class="text-base font-semibold text-gray-900 dark:text-gray-100">
										{reminder.title}
										{#if reminder.is_completed}
											<span class="ml-2 text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
												Completed
											</span>
										{:else if isOverdue(reminder.remind_at)}
											<span class="ml-2 text-xs px-2 py-0.5 rounded-full bg-red-500 text-white">
												Overdue
											</span>
										{/if}
									</h3>
									{#if reminder.description}
										<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
											{reminder.description}
										</p>
									{/if}
									<div class="flex items-center gap-3 mt-2 text-sm">
										<span class="text-xs px-2 py-0.5 rounded-full border {getPriorityColor(reminder.priority)}">
											{getPriorityLabel(reminder.priority)}
										</span>
										<span class="text-gray-600 dark:text-gray-400">
											{formatTime(reminder.remind_at)}
										</span>
										<span class="font-medium {!reminder.is_completed && isOverdue(reminder.remind_at) ? 'text-red-600 dark:text-red-400' : ''}">
											{formatRelativeTime(reminder.remind_at)}
										</span>
									</div>
								</div>

								<!-- Actions -->
								{#if !reminder.is_completed}
									<div class="flex-shrink-0 flex gap-2">
										<button
											class="px-3 py-1.5 text-sm rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition"
											onclick={() => snoozeReminder(reminder.id)}
										>
											Snooze
										</button>
										<button
											class="px-3 py-1.5 text-sm rounded-lg bg-blue-500 hover:bg-blue-600 text-white transition"
											onclick={() => dismissReminder(reminder.id)}
										>
											Dismiss
										</button>
									</div>
								{/if}
							</div>
						</div>
					{:else}
						<div class="text-center py-12 text-gray-500 dark:text-gray-500">
							No reminders found. Ask Sebastian to set reminders for you!
						</div>
					{/each}
				</div>

				<!-- Info message -->
				<div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
					<p class="text-sm text-blue-800 dark:text-blue-300">
						⏰ Reminders view is ready! Set reminders by chatting with Sebastian.
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
