<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	export type TaskStatus = 'todo' | 'in_progress' | 'waiting' | 'done' | 'cancelled';

	export type TodoistTaskNode = {
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

	type ModalProps = {
		show: boolean;
		task: TodoistTaskNode | null;
		backendBaseUrl: string;
		getHeaders: () => Record<string, string>;
		onClose: () => void;
		onUpdate: () => void;
	};

	let { show, task, backendBaseUrl, getHeaders, onClose, onUpdate } = $props<ModalProps>();
	let modalShow = $state(false);

	// Sync modalShow with show prop
	$effect(() => {
		modalShow = show;
	});

	// Call onClose when modal is closed
	$effect(() => {
		if (!modalShow && show) {
			onClose();
		}
	});

	let saving = $state(false);
	let editedTask = $state<Partial<TodoistTaskNode>>({});

	// Initialize edited task when task changes
	$effect(() => {
		if (task) {
			editedTask = {
				content: task.content,
				description: task.description || '',
				priority: task.priority || 1,
				due_string: task.due_string || '',
				labels: task.labels || []
			};
		}
	});

	const handleSave = async () => {
		if (!task) return;

		saving = true;
		try {
			const isNew = !task.todoist_id;
			if (isNew) {
				const response = await fetch(`${backendBaseUrl}/api/todoist/tasks/create-local`, {
					method: 'POST',
					headers: getHeaders(),
					body: JSON.stringify({
						content: editedTask.content,
						description: editedTask.description,
						priority: editedTask.priority,
						due_string: editedTask.due_string,
						project_id: task.project_id || task.todoist_project_id,
						section_id: task.section_id || task.todoist_section_id,
						parent_id: task.parent_id || task.todoist_parent_id
					})
				});

				if (!response.ok) {
					const error = await response.json().catch(() => ({}));
					toast.error(`Failed to create task: ${error.detail || response.statusText}`);
					return;
				}

				toast.success('Task created locally and will sync shortly');
				onUpdate();
				modalShow = false;
				return;
			}

			const response = await fetch(`${backendBaseUrl}/api/todoist/tasks/${task.todoist_id}/update-local`, {
				method: 'POST',
				headers: getHeaders(),
				body: JSON.stringify({
					content: editedTask.content,
					description: editedTask.description,
					priority: editedTask.priority,
					due_string: editedTask.due_string
				})
			});

			if (!response.ok) {
				const error = await response.json();
				toast.error(`Failed to update task: ${error.detail || response.statusText}`);
				return;
			}

			toast.success('Task updated successfully');
			onUpdate();
			modalShow = false;
		} catch (error) {
			console.error('Error updating task:', error);
			toast.error('Failed to update task. Please try again.');
		} finally {
			saving = false;
		}
	};

	const handleClose = () => {
		modalShow = false;
	};

	const getPriorityLabel = (priority?: number) => {
		switch (priority) {
			case 4: return 'Urgent (P4)';
			case 3: return 'High (P3)';
			case 2: return 'Medium (P2)';
			case 1: return 'Low (P1)';
			default: return 'None';
		}
	};
</script>

<Modal size="md" bind:show={modalShow}>
	<div>
		<!-- Header -->
		<div class="flex justify-between items-center dark:text-gray-300 px-5 pt-4 pb-2 border-b border-gray-200 dark:border-gray-800">
			<div class="text-lg font-semibold self-center">Task Details</div>
			<button
				class="self-center hover:bg-gray-100 dark:hover:bg-gray-800 p-1 rounded-lg transition"
				onclick={handleClose}
				aria-label="Close modal"
			>
				<XMark className="size-5" />
			</button>
		</div>

		{#if task}
			<!-- Content -->
			<form
				class="flex flex-col gap-4 px-5 py-4"
				onsubmit={(e) => {
					e.preventDefault();
					handleSave();
				}}
			>
				<!-- Task Title -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						Task Name
					</label>
					<input
						type="text"
						class="w-full px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
						bind:value={editedTask.content}
						required
					/>
				</div>

				<!-- Description -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						Description
					</label>
					<textarea
						class="w-full px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[100px]"
						bind:value={editedTask.description}
						placeholder="Add a description..."
					/>
				</div>

				<!-- Priority & Due Date -->
				<div class="grid grid-cols-2 gap-4">
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Priority
						</label>
						<select
							class="w-full px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							bind:value={editedTask.priority}
						>
							<option value={1}>Low (P1)</option>
							<option value={2}>Medium (P2)</option>
							<option value={3}>High (P3)</option>
							<option value={4}>Urgent (P4)</option>
						</select>
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Due Date
						</label>
						<input
							type="text"
							class="w-full px-3 py-2 bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							bind:value={editedTask.due_string}
							placeholder="tomorrow, next week, Dec 25"
						/>
					</div>
				</div>
				<p class="text-xs text-gray-500 -mt-2">Due date: use natural language like "tomorrow" or "next friday"</p>

				<!-- Action Buttons -->
				<div class="flex justify-end gap-2 pt-4 border-t border-gray-200 dark:border-gray-800">
					<button
						type="button"
						class="px-3.5 py-1.5 text-sm font-medium bg-gray-100 dark:bg-gray-850 text-gray-900 dark:text-gray-100 hover:bg-gray-200 dark:hover:bg-gray-800 transition rounded-full"
						onclick={handleClose}
						disabled={saving}
					>
						Cancel
					</button>
					<button
						type="submit"
						class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
						disabled={saving}
					>
						{#if saving}
							<Spinner className="size-4" />
							<span>Saving...</span>
						{:else}
							<span>Save Changes</span>
						{/if}
					</button>
				</div>
			</form>
		{/if}
	</div>
</Modal>
