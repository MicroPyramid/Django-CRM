<script>
	import { Plus } from '@lucide/svelte';
	import DealCard from './DealCard.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { cn } from '$lib/utils.js';

	/**
	 * @typedef {Object} Opportunity
	 * @property {string} id
	 * @property {string} name
	 * @property {number | null} amount
	 * @property {string} stage
	 * @property {number | null} probability
	 * @property {string | null} closedOn
	 * @property {{ id: string, name: string, email?: string } | null} account
	 * @property {{ id: string, name: string, email?: string } | null} owner
	 */

	/**
	 * @type {{
	 *   opportunities?: Opportunity[],
	 *   onCardClick?: (opportunity: Opportunity) => void,
	 *   onStageChange?: (opportunityId: string, newStage: string) => void,
	 *   onCreateNew?: (stage: string) => void,
	 * }}
	 */
	let { opportunities = [], onCardClick, onStageChange, onCreateNew } = $props();

	// Define stage columns
	const stages = [
		{ id: 'PROSPECTING', label: 'Prospecting', color: 'bg-gray-500' },
		{ id: 'QUALIFICATION', label: 'Qualification', color: 'bg-blue-500' },
		{ id: 'PROPOSAL', label: 'Proposal', color: 'bg-purple-500' },
		{ id: 'NEGOTIATION', label: 'Negotiation', color: 'bg-orange-500' },
		{ id: 'CLOSED_WON', label: 'Won', color: 'bg-green-500' },
		{ id: 'CLOSED_LOST', label: 'Lost', color: 'bg-red-500' }
	];

	// Group opportunities by stage
	const opportunitiesByStage = $derived.by(() => {
		/** @type {{ [key: string]: Opportunity[] }} */
		const grouped = {};
		stages.forEach((stage) => {
			grouped[stage.id] = [];
		});
		opportunities.forEach((opp) => {
			if (grouped[opp.stage]) {
				grouped[opp.stage].push(opp);
			} else {
				// Default to PROSPECTING if stage not found
				grouped['PROSPECTING'].push(opp);
			}
		});
		return grouped;
	});

	// Calculate totals per stage
	const stageTotals = $derived.by(() => {
		/** @type {{ [key: string]: { count: number, value: number } }} */
		const totals = {};
		stages.forEach((stage) => {
			const stageOpps = opportunitiesByStage[stage.id] || [];
			totals[stage.id] = {
				count: stageOpps.length,
				value: stageOpps.reduce((sum, opp) => sum + (opp.amount || 0), 0)
			};
		});
		return totals;
	});

	// Drag and drop state
	let draggedOpportunity = $state(/** @type {Opportunity | null} */ (null));
	let dragOverStage = $state(/** @type {string | null} */ (null));

	/**
	 * Format currency for column header
	 * @param {number} amount
	 */
	function formatCurrency(amount) {
		if (amount >= 1000000) {
			return '$' + (amount / 1000000).toFixed(1) + 'M';
		}
		if (amount >= 1000) {
			return '$' + Math.round(amount / 1000) + 'k';
		}
		return '$' + amount;
	}

	/**
	 * Handle drag start
	 * @param {DragEvent} e
	 * @param {Opportunity} opportunity
	 */
	function handleDragStart(e, opportunity) {
		draggedOpportunity = opportunity;
		if (e.dataTransfer) {
			e.dataTransfer.effectAllowed = 'move';
			e.dataTransfer.setData('text/plain', opportunity.id);
		}
	}

	/**
	 * Handle drag over
	 * @param {DragEvent} e
	 * @param {string} stageId
	 */
	function handleDragOver(e, stageId) {
		e.preventDefault();
		if (e.dataTransfer) {
			e.dataTransfer.dropEffect = 'move';
		}
		dragOverStage = stageId;
	}

	/**
	 * Handle drag leave
	 */
	function handleDragLeave() {
		dragOverStage = null;
	}

	/**
	 * Handle drop
	 * @param {DragEvent} e
	 * @param {string} stageId
	 */
	function handleDrop(e, stageId) {
		e.preventDefault();
		if (draggedOpportunity && draggedOpportunity.stage !== stageId) {
			onStageChange?.(draggedOpportunity.id, stageId);
		}
		draggedOpportunity = null;
		dragOverStage = null;
	}

	/**
	 * Handle drag end
	 */
	function handleDragEnd() {
		draggedOpportunity = null;
		dragOverStage = null;
	}
</script>

<div class="flex h-full gap-4 overflow-x-auto pb-4">
	{#each stages as stage (stage.id)}
		{@const stageData = stageTotals[stage.id]}
		{@const stageOpps = opportunitiesByStage[stage.id]}
		<div
			class={cn(
				'bg-muted/30 flex w-[280px] shrink-0 flex-col rounded-lg',
				dragOverStage === stage.id && 'ring-ring ring-2 ring-offset-2'
			)}
			role="region"
			aria-label="{stage.label} column"
			ondragover={(e) => handleDragOver(e, stage.id)}
			ondragleave={handleDragLeave}
			ondrop={(e) => handleDrop(e, stage.id)}
		>
			<!-- Column Header -->
			<div class="border-border/50 flex items-center justify-between border-b px-3 py-2.5">
				<div class="flex items-center gap-2">
					<div class={cn('h-2 w-2 rounded-full', stage.color)}></div>
					<h3 class="text-foreground text-sm font-semibold">{stage.label}</h3>
					<span class="bg-muted text-muted-foreground rounded-full px-2 py-0.5 text-xs font-medium">
						{stageData.count}
					</span>
				</div>
				<span class="text-muted-foreground text-xs font-medium">
					{formatCurrency(stageData.value)}
				</span>
			</div>

			<!-- Column Content -->
			<div class="flex-1 overflow-y-auto p-2">
				<div class="space-y-2">
					{#each stageOpps as opportunity (opportunity.id)}
						<div
							role="button"
							tabindex="0"
							draggable="true"
							ondragstart={(e) => handleDragStart(e, opportunity)}
							ondragend={handleDragEnd}
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									onCardClick?.(opportunity);
								}
							}}
							class={cn(
								'transition-opacity',
								draggedOpportunity?.id === opportunity.id && 'opacity-50'
							)}
						>
							<DealCard {opportunity} onclick={() => onCardClick?.(opportunity)} />
						</div>
					{/each}

					{#if stageOpps.length === 0}
						<div class="flex flex-col items-center justify-center py-8 text-center">
							<p class="text-muted-foreground text-sm">No deals</p>
						</div>
					{/if}
				</div>
			</div>

			<!-- Add Button -->
			{#if onCreateNew && !['CLOSED_WON', 'CLOSED_LOST'].includes(stage.id)}
				<div class="border-border/50 border-t p-2">
					<Button
						variant="ghost"
						size="sm"
						class="text-muted-foreground hover:text-foreground w-full justify-start"
						onclick={() => onCreateNew(stage.id)}
						disabled={false}
					>
						<Plus class="mr-2 h-4 w-4" />
						Add Deal
					</Button>
				</div>
			{/if}
		</div>
	{/each}
</div>
