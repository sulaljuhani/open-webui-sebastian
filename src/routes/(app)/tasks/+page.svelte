<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { mobile, showSidebar, user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Check from '$lib/components/icons/Check.svelte';

	const i18n = getContext('i18n');

	let loaded = false;
	let tasks = [];
	let filter = 'all'; // all, active, completed
	let backendBaseUrl = 'http://langgraph-agents:8000';

	type TaskStatus = 'todo' | 'in_progress' | 'waiting' | 'done' | 'cancelled';

	interface Task {
		id: string;
		title: string;
		description?: string;
		status: TaskStatus;
		priority?: number;
		due_date?: string;
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

	const fetchTasks = async () => {
		if (typeof localStorage !== 'undefined') {
			backendBaseUrl = localStorage.getItem('backend_url') || backendBaseUrl;
		}

		try {
			const response = await fetch(`${backendBaseUrl}/api/tasks`, {
				method: 'GET',
				headers: getHeaders()
			});

			if (response.ok) {
				const data = await response.json();
				tasks = data.tasks || [];
			}
		} catch (error) {
			console.error('Failed to fetch tasks:', error);
			// Show demo data for now
			tasks = [
				{
					id: '1',
					title: 'Connect to backend API',
					description: 'Set up API key in local storage',
					status: 'in_progress',
					priority: 4,
					created_at: new Date().toISOString()
				},
				{
					id: '2',
					title: 'Test task management',
					description: 'Create, update, and complete tasks',
					status: 'todo',
					priority: 3,
					created_at: new Date().toISOString()
				}
			];
		}
	};

	const toggleTaskStatus = async (taskId: string) => {
		const task = tasks.find((t) => t.id === taskId);
		if (!task) return;

		const newStatus: TaskStatus = task.status === 'done' ? 'todo' : 'done';

		// Optimistic update
		tasks = tasks.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t));

		try {
			await fetch(`${backendBaseUrl}/api/tasks/${taskId}`, {
				method: 'PUT',
				headers: getHeaders(),
				body: JSON.stringify({ status: newStatus })
			});
		} catch (error) {
			console.error('Failed to update task:', error);
			// Revert on error
			tasks = tasks.map((t) => (t.id === taskId ? { ...t, status: task.status } : t));
		}
	};

	const getPriorityColor = (priority?: number) => {
		switch (priority) {
			case 5:
			case 4:
				return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
			case 3:
				return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
			case 2:
			case 1:
				return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
			default:
				return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400';
		}
	};

	const formatStatus = (status: TaskStatus) => status.replace(/_/g, ' ');

	const isClosedStatus = (status: TaskStatus) => ['done', 'cancelled'].includes(status);

	const filteredTasks = () => {
		switch (filter) {
			case 'active':
				return tasks.filter((t) => !isClosedStatus(t.status));
			case 'completed':
				return tasks.filter((t) => isClosedStatus(t.status));
			default:
				return tasks;
		}
	};

	onMount(async () => {
		await fetchTasks();
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
							<a class="min-w-fit transition" href="/tasks">
								{$i18n.t('Tasks')}
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
				<!-- Header -->
				<div class="flex items-center justify-between mb-6">
					<h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">Tasks</h1>
					<div class="flex gap-2">
						<button
							class="px-3 py-1.5 text-sm rounded-lg {filter === 'all'
								? 'bg-blue-500 text-white'
								: 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'} transition"
							on:click={() => (filter = 'all')}
						>
							All ({tasks.length})
						</button>
						<button
							class="px-3 py-1.5 text-sm rounded-lg {filter === 'active'
								? 'bg-blue-500 text-white'
								: 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'} transition"
							on:click={() => (filter = 'active')}
						>
							Active ({tasks.filter((t) => !isClosedStatus(t.status)).length})
						</button>
						<button
							class="px-3 py-1.5 text-sm rounded-lg {filter === 'completed'
								? 'bg-blue-500 text-white'
								: 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'} transition"
							on:click={() => (filter = 'completed')}
						>
							Completed ({tasks.filter((t) => isClosedStatus(t.status)).length})
						</button>
					</div>
				</div>

				<!-- Tasks List -->
				<div class="space-y-3">
					{#each filteredTasks() as task (task.id)}
						<div
							class="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-800 p-4 hover:shadow-md transition"
						>
							<div class="flex items-start gap-3">
								<!-- Checkbox -->
								<button
									class="mt-0.5 flex-shrink-0 w-5 h-5 rounded border-2 {task.status ===
									'done'
										? 'bg-blue-500 border-blue-500'
										: 'border-gray-300 dark:border-gray-600 hover:border-blue-500'} transition flex items-center justify-center"
									on:click={() => toggleTaskStatus(task.id)}
								>
									{#if task.status === 'done'}
										<Check className="size-3 text-white" />
									{/if}
								</button>

								<!-- Task Content -->
								<div class="flex-1 min-w-0">
									<h3
										class="text-base font-medium {task.status === 'done'
											? 'line-through text-gray-500 dark:text-gray-600'
											: 'text-gray-900 dark:text-gray-100'}"
									>
										{task.title}
									</h3>
									{#if task.description}
										<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
											{task.description}
										</p>
									{/if}

									<!-- Metadata -->
									<div class="flex flex-wrap items-center gap-2 mt-2">
										{#if task.priority}
											<span class="text-xs px-2 py-0.5 rounded-full {getPriorityColor(task.priority)}">
												Priority {task.priority}
											</span>
										{/if}
										{#if task.due_date}
											<span class="text-xs text-gray-500 dark:text-gray-500">
												Due: {new Date(task.due_date).toLocaleDateString()}
											</span>
										{/if}
										<span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400">
											{formatStatus(task.status)}
										</span>
									</div>
								</div>
							</div>
						</div>
					{:else}
						<div class="text-center py-12 text-gray-500 dark:text-gray-500">
							No tasks found. Ask Sebastian to create some tasks for you!
						</div>
					{/each}
				</div>

				<!-- Info message -->
				<div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
					<p class="text-sm text-blue-800 dark:text-blue-300">
						✅ Tasks view is ready! Create tasks by chatting with Sebastian.
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
