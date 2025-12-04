<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { mobile, showSidebar, user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import TaskItem from './TaskItem.svelte';
	import TaskDetailModal from './TaskDetailModal.svelte';

	const i18n = getContext('i18n');

	let loaded = $state(false);
	const ENV_BACKEND_URL = import.meta.env.VITE_LANGGRAPH_BACKEND_URL;
	const ENV_BACKEND_KEY = import.meta.env.VITE_LANGGRAPH_API_KEY;

	// Initialize with empty string - will be set by resolveBackendBaseUrl()
	let backendBaseUrl = $state('');
	let projectIdFilter = $state('');
	let fetchError = $state('');

	// Modal state
	let showTaskModal = $state(false);
	let selectedTask = $state<TodoistTaskNode | null>(null);
	let newTaskDraft: Partial<TodoistTaskNode> | null = $state(null);
	let creating = $state(false);

	type TaskStatus = 'todo' | 'in_progress' | 'waiting' | 'done' | 'cancelled';

	type TodoistProject = {
		id: string;
		name: string;
		color?: string;
		sections: { id: string; name: string; section_order: number }[];
	};

	type TodoistTaskNode = {
		id: string;
		todoist_id: string;
		content: string;
		description?: string;
		project_id?: string;
		section_id?: string;
		parent_id?: string;
		priority?: number;
		status: TaskStatus;
		due_date?: string | null;
		due_string?: string | null;
		labels?: string[];
		child_order?: number;
		children?: TodoistTaskNode[];
	};

	let projects: TodoistProject[] = $state([]);
	let taskTree: TodoistTaskNode[] = $state([]);

	const getApiKey = () => {
		if (typeof localStorage !== 'undefined') {
			const storedKey = localStorage.getItem('backend_api_key');
			if (storedKey) return storedKey;
		}
		return ENV_BACKEND_KEY || '';
	};

	const getHeaders = () => {
		const headers: Record<string, string> = { 'Content-Type': 'application/json' };
		const apiKey = getApiKey();
		if (apiKey) headers['X-API-Key'] = apiKey;
		return headers;
	};

	const isPrivateHost = (host: string) =>
		/^localhost$|^127\\.|^192\\.168\\.|^10\\.|^172\\.(1[6-9]|2[0-9]|3[0-1])\\.|^100\\./.test(host);

	const resolveBackendBaseUrl = () => {
		// 1) Explicit override stored by the user
		if (typeof localStorage !== 'undefined') {
			const stored = localStorage.getItem('backend_url');
			if (stored) {
				console.log('🔧 Using backend URL from localStorage:', stored);
				return stored;
			}
		}

		// 2) Local browsing (LAN/tailscale): reuse the frontend host on port 8000
		if (typeof window !== 'undefined' && isPrivateHost(window.location.hostname)) {
			const localUrl = `${window.location.protocol}//${window.location.hostname}:8000`;
			console.log('🔧 Using local backend URL:', localUrl);
			return localUrl;
		}

		// 3) Environment variable (expected to be a reachable host, e.g. api.suluhome.com)
		if (ENV_BACKEND_URL) {
			console.log('🔧 Using backend URL from environment:', ENV_BACKEND_URL);
			return ENV_BACKEND_URL;
		}

		// 4) Fallback to same host as frontend on port 8000
		if (typeof window !== 'undefined') {
			const fallbackUrl = `${window.location.protocol}//${window.location.hostname}:8000`;
			console.log('🔧 Using fallback backend URL (same host, port 8000):', fallbackUrl);
			return fallbackUrl;
		}

		// 5) Last resort: Docker internal hostname
		console.warn('⚠️ Using Docker internal hostname - this will NOT work from browser!');
		return 'http://langgraph-agents:8000';
	};

	const fetchTodoistMirror = async () => {
		backendBaseUrl = resolveBackendBaseUrl();
		fetchError = '';

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
			console.log('📋 Projects loaded:', projects.length, projects);
		} else {
			console.error('❌ Failed to load projects:', projectsRes);
		}

		if (tasksRes.status === 'fulfilled' && tasksRes.value.ok) {
			const tasks = await tasksRes.value.json();
			taskTree = tasks.map((task) => ({ ...task, id: task.todoist_id }));
			console.log('📝 Tasks loaded:', taskTree.length, taskTree);

			// Debug: Show task distribution
			const tasksByProject = taskTree.reduce((acc, task) => {
				const key = task.project_id || 'no-project';
				acc[key] = (acc[key] || 0) + 1;
				return acc;
			}, {} as Record<string, number>);
			console.log('📊 Tasks by project:', tasksByProject);

			const tasksBySection = taskTree.reduce((acc, task) => {
				const key = task.section_id || 'no-section';
				acc[key] = (acc[key] || 0) + 1;
				return acc;
			}, {} as Record<string, number>);
			console.log('📊 Tasks by section:', tasksBySection);

			const tasksWithParent = taskTree.filter(t => t.parent_id).length;
			const tasksWithoutParent = taskTree.filter(t => !t.parent_id).length;
			console.log(`📊 Tasks with parent: ${tasksWithParent}, without parent: ${tasksWithoutParent}`);
		} else {
			fetchError = tasksRes.status === 'fulfilled' ? `Failed to load tasks (${tasksRes.value.status})` : 'Failed to reach backend';
			taskTree = [];
			console.error('❌ Failed to load tasks:', tasksRes);
		}
	};

	const handleToggleComplete = async (taskId: string, currentStatus: TaskStatus) => {
		const newStatus = currentStatus === 'done' ? 'todo' : 'done';

		// Optimistically update UI first
		const originalTaskTree = [...taskTree];
		taskTree = taskTree.map((task) =>
			task.todoist_id === taskId ? { ...task, status: newStatus } : task
		);

		try {
			const response = await fetch(`${backendBaseUrl}/api/todoist/tasks/${taskId}/complete-local`, {
				method: 'POST',
				headers: getHeaders(),
				body: JSON.stringify({
					complete: newStatus === 'done'
				})
			});
			console.log('Task toggle response:', response.status, response.ok);

			if (!response.ok) {
				const error = await response.json();
				console.error('Failed to update task:', error.detail || response.statusText);
				// Revert optimistic update on failure
				taskTree = originalTaskTree;
				// TODO: Show user-friendly error toast
			}
		} catch (error) {
			console.error('Error toggling task:', error);
			// Revert optimistic update on network error
			taskTree = originalTaskTree;
			// TODO: Show user-friendly error toast
		}
	};

	const handleTaskClick = (task: TodoistTaskNode) => {
		selectedTask = task;
		showTaskModal = true;
	};

	const handleCreateClick = () => {
		newTaskDraft = {
			todoist_id: '',
			id: '',
			content: '',
			description: '',
			project_id: projectIdFilter || (projects[0]?.id ?? ''),
			priority: 1,
			status: 'todo',
		};
		selectedTask = newTaskDraft as TodoistTaskNode;
		showTaskModal = true;
	};

	const handleModalClose = () => {
		showTaskModal = false;
		selectedTask = null;
	};

	const handleTaskUpdate = async () => {
		// Refresh the task list after updating
		await fetchTodoistMirror();
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
					<div class="flex gap-2 flex-wrap">
						<select
							class="dark:bg-gray-900 w-fit pr-8 rounded-sm py-1.5 px-2.5 text-sm font-medium bg-transparent text-right outline-hidden"
							bind:value={projectIdFilter}
							onchange={fetchTodoistMirror}
						>
							<option value="">All projects</option>
							{#each projects as project (project.id)}
								<option value={project.id}>{project.name}</option>
							{/each}
						</select>
					</div>
					<div class="flex gap-2 flex-wrap justify-end">
						<button
							class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
							onclick={handleCreateClick}
						>
							Create Task
						</button>
					</div>
				</div>

				<!-- Project/Section list -->
				<div class="space-y-4">
					{#if taskTree.length === 0}
						<div class="text-center py-12 text-gray-500 dark:text-gray-500 border border-dashed border-gray-300 dark:border-gray-700 rounded-xl space-y-2">
							<div>
								{#if fetchError}
									<p class="font-semibold text-red-500">Tasks failed to load</p>
									<p class="text-sm">{fetchError}</p>
								{:else}
									<p>No tasks found.</p>
								{/if}
							</div>
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
												{project.sections.length} sections
											</p>
										</div>
									</div>
								</header>

								<div class="divide-y divide-gray-100 dark:divide-gray-800">
									{#if project.sections.length === 0}
										{@const unsectionedTasks = taskTree.filter((t) => t.project_id === project.id && (!t.section_id || t.section_id === null) && (!t.parent_id || t.parent_id === null) && t.status !== 'done')}
										<!-- Show unsectioned tasks when no sections exist -->
										{#if unsectionedTasks.length > 0}
											<div class="p-4 space-y-3">
												<div class="flex items-center justify-between">
													<h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">
														Unsectioned Tasks
													</h3>
													<div class="text-xs text-gray-500 dark:text-gray-500">
														{unsectionedTasks.length} tasks
													</div>
												</div>
												<div class="space-y-3">
													{#each unsectionedTasks as task (task.todoist_id)}
														<TaskItem task={task} allTasks={taskTree} onToggleComplete={handleToggleComplete} onTaskClick={handleTaskClick} />
													{/each}
												</div>
											</div>
										{:else}
											<div class="p-4 text-sm text-gray-500 dark:text-gray-500">No tasks in this project</div>
										{/if}
									{:else}
										{#each project.sections as section (section.id)}
											<div class="p-4 space-y-3">
												<div class="flex items-center justify-between">
													<h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">
														{section.name}
													</h3>
												</div>
												<div class="space-y-3">
													{#each taskTree.filter((t) => t.project_id === project.id && t.section_id === section.id && (!t.parent_id || t.parent_id === null) && t.status !== 'done') as task (task.todoist_id)}
														<TaskItem task={task} allTasks={taskTree} onToggleComplete={handleToggleComplete} onTaskClick={handleTaskClick} />
													{:else}
														<p class="text-sm text-gray-500 dark:text-gray-500">No tasks in this section.</p>
													{/each}
												</div>
											</div>
										{/each}
										<!-- Show unsectioned tasks at the end -->
										{#if taskTree.filter((t) => t.project_id === project.id && (!t.section_id || t.section_id === null) && (!t.parent_id || t.parent_id === null) && t.status !== 'done').length > 0}
											{@const unsectionedTasks = taskTree.filter((t) => t.project_id === project.id && (!t.section_id || t.section_id === null) && (!t.parent_id || t.parent_id === null) && t.status !== 'done')}
											<div class="p-4 space-y-3">
												<div class="flex items-center justify-between">
													<h3 class="text-sm font-semibold text-gray-800 dark:text-gray-200">
														Unsectioned Tasks
													</h3>
													<div class="text-xs text-gray-500 dark:text-gray-500">
														{unsectionedTasks.length} tasks
													</div>
												</div>
												<div class="space-y-3">
													{#each unsectionedTasks as task (task.todoist_id)}
														<TaskItem task={task} allTasks={taskTree} onToggleComplete={handleToggleComplete} onTaskClick={handleTaskClick} />
													{/each}
												</div>
											</div>
										{/if}
									{/if}
								</div>
							</section>
						{/each}
					{/if}
				</div>
			</div>
		</div>
	</div>

	<!-- Task Detail Modal -->
	<TaskDetailModal
		show={showTaskModal}
		task={selectedTask}
		backendBaseUrl={backendBaseUrl}
		getHeaders={getHeaders}
		onClose={handleModalClose}
		onUpdate={handleTaskUpdate}
	/>
{:else}
	<div class="flex items-center justify-center h-screen">
		<Spinner className="size-8" />
	</div>
{/if}
