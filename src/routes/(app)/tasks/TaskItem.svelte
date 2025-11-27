<script lang="ts">
	import Check from '$lib/components/icons/Check.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import TaskItem from './TaskItem.svelte';

	export type TaskStatus = 'todo' | 'in_progress' | 'waiting' | 'done' | 'cancelled';

	export type TodoistTaskNode = {
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

const { task, allTasks, onToggleComplete } = $props<{
	task: TodoistTaskNode;
	allTasks: TodoistTaskNode[];
	onToggleComplete?: (taskId: string, currentStatus: TaskStatus) => void;
}>();

	const hasChildren = (t: TodoistTaskNode) => Boolean(t.children && t.children.length > 0);

	const handleCheckboxClick = () => {
		if (onToggleComplete) {
			onToggleComplete(task.todoist_id, task.status);
		}
	};

	const childrenFor = (parentId: string) =>
		allTasks
			.filter((t) => t.parent_id === parentId)
			.sort((a, b) => (a.child_order || 0) - (b.child_order || 0));

	const formatStatus = (status: TaskStatus) => status.replace(/_/g, ' ');

	const getPriorityTone = (priority?: number) => {
		switch (priority) {
			case 4:
			case 5:
				return 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300';
			case 3:
				return 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300';
			case 2:
			case 1:
				return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300';
			default:
				return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
		}
	};
</script>

<div class="task-wrapper">
	<div class="bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-800 rounded-lg p-3 flex gap-3">
		<button
			class="flex-shrink-0 mt-1 cursor-pointer hover:opacity-70 transition"
			onclick={handleCheckboxClick}
			aria-label={task.status === 'done' ? 'Mark as incomplete' : 'Mark as complete'}
		>
			<div class="w-5 h-5 rounded-full border-2 {task.status === 'done' ? 'border-green-500 bg-green-500' : 'border-gray-300 dark:border-gray-600'} flex items-center justify-center">
				{#if task.status === 'done'}
					<Check className="size-3 text-white" />
				{/if}
			</div>
		</button>
		<div class="flex-1 min-w-0 space-y-1">
			<div class="flex items-start justify-between gap-2">
				<div class="flex-1 min-w-0">
					<p class="text-sm font-semibold text-gray-900 dark:text-gray-100 break-words">
						{task.content}
					</p>
					{#if task.description}
						<p class="text-xs text-gray-600 dark:text-gray-400">{task.description}</p>
					{/if}
				</div>
				<div class="flex gap-2 items-center">
					<Badge className={getPriorityTone(task.priority)} label={`P${task.priority ?? 1}`} />
					<span class="text-[11px] px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400">
						{formatStatus(task.status)}
					</span>
				</div>
			</div>
			<div class="text-[11px] text-gray-600 dark:text-gray-500 flex gap-2 flex-wrap">
				{#if task.due_string}
					<span class="text-red-500">Due: {task.due_string}</span>
				{:else if task.due_date}
					<span>Due: {new Date(task.due_date).toLocaleString()}</span>
				{/if}
				{#if task.labels && task.labels.length}
					<span>Labels: {task.labels.join(', ')}</span>
				{/if}
			</div>
		</div>
	</div>

	{#if hasChildren(task)}
		<div class="ml-6 mt-2 border-l-2 border-gray-200 dark:border-gray-800 pl-3 space-y-2">
			{#each childrenFor(task.todoist_id) as child (child.todoist_id)}
				<TaskItem task={child} {allTasks} {onToggleComplete} />
			{/each}
		</div>
	{/if}
</div>
