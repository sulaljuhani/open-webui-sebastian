<script lang="ts">
    // TODO: Replace with your actual Metabase Public Embed Link
    let embedUrl = "http://192.168.0.12:3002/public/dashboard/YOUR_DASHBOARD_UUID"; 
</script>

<div class="w-full h-full flex flex-col overflow-hidden">
    <div class="px-6 py-4 border-b dark:border-gray-800 flex justify-between items-center bg-gray-50 dark:bg-gray-900">
        <div>
            <h1 class="text-xl font-semibold">Life Analytics</h1>
            <p class="text-xs text-gray-500 mt-1">Comprehensive view of your logged data</p>
        </div>
        <a href="http://192.168.0.12:3002" target="_blank" class="text-xs text-blue-500 hover:underline">Open Metabase &rarr;</a>
    </div>
    
    <div class="flex-1 w-full h-full bg-white dark:bg-gray-900 relative">
        {#if embedUrl.includes("YOUR_DASHBOARD_UUID")}
            <div class="absolute inset-0 flex flex-col items-center justify-center text-gray-500 p-8 text-center">
                <div class="max-w-md space-y-4">
                    <div class="text-6xl mb-4">📊</div>
                    <h2 class="text-2xl font-bold text-gray-800 dark:text-gray-200">Analytics Dashboard</h2>
                    <p>To view your data here, you need to connect Metabase.</p>
                    
                    <div class="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-left text-sm space-y-2 mt-4">
                        <p>1. Go to <a href="http://192.168.0.12:3002" target="_blank" class="text-blue-500 underline">Metabase (Port 3002)</a></p>
                        <p>2. Connect to Postgres (Host: postgres, DB: aistack)</p>
                        <p>3. Create a dashboard and enable "Public Sharing"</p>
                        <p>4. Copy the Public Link and update this file.</p>
                    </div>
                </div>
            </div>
        {:else}
            <iframe
                src={embedUrl}
                title="Life Analytics"
                frameborder="0"
                class="w-full h-full"
                allowtransparency
            ></iframe>
        {/if}
    </div>
</div>
