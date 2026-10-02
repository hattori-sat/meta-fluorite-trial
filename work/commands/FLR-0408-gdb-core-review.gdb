set pagination off
set print thread-events off
info threads
thread apply all bt 8
info registers
p $_siginfo
x/16i $pc-24
info sharedlibrary
info proc mappings
quit
