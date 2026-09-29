log=/run/user/1001/flr0285-production-no-model-vulkan-trace.log; grep -E 'FLR0026_VK_(ACQUIRE|SWAPCHAIN|QUEUE_PRESENT|PRESENT_BOUNDARY|SUBMIT|FLUSH)' "$log" | tail -n 180; true
