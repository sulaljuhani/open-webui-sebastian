<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { mobile, showSidebar, user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	import TaskItem, { type TodoistTaskNode } from './TaskItem.svelte';

	const i18n = getContext('i18n');

	let loaded = $state(false);
	let backendBaseUrl = $state('http://langgraph-agents:8000');
	let projectIdFilter = $state('');

	type TaskStatus = 'todo' | 'in_progress' | 'waiting' | 'done' | 'cancelled';

	type TodoistProject = {
		id: string;
		name: string;
		color?: string;
		sections: { id: string; name: string; section_order: number }[];
	};

	let projects: TodoistProject[] = $state([]);
	let taskTree: TodoistTaskNode[] = $state([]);

	const getHeaders = () => {
		const headers: Record<string, string> = { 'Content-Type': 'application/json' };
		if (typeof localStorage !== 'undefined') {
			const apiKey = localStorage.getItem('backend_api_key');
			if (apiKey) headers['X-API-Key'] = apiKey;
		}
		return headers;
	};

	const fetchTodoistMirror = async () => {
		if (typeof localStorage !== 'undefined') {
			backendBaseUrl = localStorage.getItem('backend_url') || backendBaseUrl;
		}

		const opts = { method: 'GET', headers: getHeaders() };

		const [projectsRes, tasksRes] = await Promise.allSettled([
			fetch(`${backendBaseUrl}/api/todoist/projects`, opts),
			fetch(
				`${backendBaseUrl}/api/todoist/tasks/tree${projectIdFilter ? `?project_id=${projectIdFilter}` : ''}`,
				opts
			)
		]);

		if (projectsRes.status === 'fulfilled' && projectsRes.value.ok) {
			projects = await projectsRes.value.json();
		}

		if (tasksRes.status === 'fulfilled' && tasksRes.value.ok) {
			taskTree = await tasksRes.value.json();
		} else {
			taskTree = [];
		}
	};

	const handleToggleComplete = async (taskId: string, currentStatus: TaskStatus) => {
		const newStatus: TaskStatus = currentStatus === 'done' ? 'todo' : 'done';

		try {
			// Update task status via Todoist REST API
			const response = await fetch(`https://api.todoist.com/rest/v2/tasks/${taskId}/${newStatus === 'done' ? 'close' : 'reopen'}`, {
				method: 'POST',
				headers: {
					'Authorization': `Bearer ${localStorage.getItem('todoist_api_token') || ''}`,
					'Content-Type': 'application/json'
				}
			});

			if (response.ok) {
				// Optimistically update UI
				taskTree = taskTree.map(task =>
					task.todoist_id === taskId ? { ...task, status: newStatus } : task
				);

				// Refresh from backend to ensure sync
				setTimeout(() => fetchTodoistMirror(), 1000);
			} else {
				console.error('Failed to toggle task status:', response.status);
			}
		} catch (error) {
			console.error('Error toggling task:', error);
		}
	};

	onMount(async () => {
		try {
			await fetchTodoistMirror();
		} catch (err) {
			console.error('Failed to fetch Todoist mirror data', err);
		} finally {
			loaded = true;
		}
	});
</script>

<!-- Page Layout -->
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
			<div class="max-w-7xl mx-auto space-y-6">
				<!-- Header -->
				<div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
					<div>
						<h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">Tasks</h1>
						<p class="text-sm text-gray-600 dark:text-gray-400">
							Mirrored from Todoist via the locked subtask layout.
						</p>
					</div>
					<div class="flex gap-2 flex-wrap">
						<select
							class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm px-3 py-2"
							bind:value={projectIdFilter}
							onchange={fetchTodoistMirror}
						>
							<option value="">All projects</option>
							{#each projects as project (project.id)}
								<option value={project.id}>{project.name}</option>
							{/each}
						</select>
						<button
							class="px-3 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
							onclick={fetchTodoistMirror}
						>
							Refresh
						</button>
					</div>
				</div>

				<!-- Project/Section list -->
				<div class="space-y-4">
					{#if taskTree.length === 0}
						<div class="text-center py-12 text-gray-500 dark:text-gray-500 border border-dashed border-gray-300 dark:border-gray-700 rounded-xl">
							No mirrored tasks found. Ask Sebastian to sync Todoist or add a task.
						</div>
					{:else}
						{#each projects as project (project.id)}
							<section class="rounded-xl border border-gray-200 dark:border-gray-800 bg-white/70 dark:bg-gray-900/60 backdrop-blur-sm shadow-sm">
								<header class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
									<div class="flex items-center gap-3">
										<div class="size-3 rounded-full" style={`background:${project.color || '#6b7280'}`}></div>
										<div>
											<h2 class="text-base font-semibold text-gray-900 dark:text-gray-100">
												{project.name}
											</h2>
											<p class="text-xs text-gray-500 dark:text-gray-500">
												{project.sections.length} sections · locked subtasks
											</p>
										</div>
									</div>
									<div class="text-xs text-gray-500 dark:text-gray-500">
										Project ID: {project.id}
									</div>
								</header>

								<div class="divide-y divide-gray-100 dark:divide-gray-800">
									{#if project.sections.length === 0}
										<div class="p-4 text-sm text-gray-500 dark:text-gray-500">No sections</div>
									{:else}
										{#each project.sections as section (section.id)}
											<div class="p-4 space-y-3">
												<div class="flex items-center justify-between">
													<h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">
														{section.name}
													</h3>
												</div>
												<div class="space-y-3">
													{#each taskTree.filter((t) => t.project_id === project.id && t.section_id === section.id && (!t.parent_id || t.parent_id === null)) as task (task.todoist_id)}
														<TaskItem task={task} allTasks={taskTree} onToggleComplete={handleToggleComplete} />
													{:else}
														<p class="text-sm text-gray-500 dark:text-gray-500">No tasks in this section.</p>
													{/each}
												</div>
											</div>
										{/each}
									{/if}
								</div>
							</section>
						{/each}
					{/if}
				</div>
			</div>
		</div>
	</div>
{:else}
	<div class="flex items-center justify-center h-screen">
		<Spinner className="size-8" />
	</div>
{/if}
